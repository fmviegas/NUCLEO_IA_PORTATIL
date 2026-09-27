#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Portão de validação de modelo (V0.7 / §25).

Valida um arquivo GGUF ANTES de adicioná-lo ao Catálogo de Modelos, SEM
executar o modelo. Confere:
  - existência e tamanho;
  - magic/versão GGUF;
  - metadados (arquitetura, contexto, chat template, quantização) lidos do
    próprio GGUF (parsing de cabeçalho, sem carregar pesos);
  - SHA256 (compara com o esperado, se informado ou vindo do registry);
  - arquitetura em lista conhecida (aviso se desconhecida).

Uso:
  python tools/validar_modelo.py <arquivo.gguf> [--sha256 HEX] [--json]
  python tools/validar_modelo.py --id <model_id>        (valida via registry)

Saída: relatório [OK]/[AVISO]/[FALHA] + uma sugestão de entrada de registry.
Código de saída 0 se não houver FALHA; 1 caso contrário.
Nunca executa o modelo; apenas lê bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

# Windows: garante saída UTF-8 (evita acentos embaralhados no console — lição 20.3).
for _stream in ("stdout", "stderr"):
    try:
        getattr(sys, _stream).reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
REGISTRY = ROOT / "config" / "models_registry.json"
LLAMA_CPP_BUILD = "b10516"

KNOWN_ARCHS = {"qwen3", "qwen3moe", "qwen2", "qwen2moe", "qwen", "llama", "phi3", "gemma", "gemma2", "mistral"}

# Tipos de valor GGUF
(GGUF_U8, GGUF_I8, GGUF_U16, GGUF_I16, GGUF_U32, GGUF_I32,
 GGUF_F32, GGUF_BOOL, GGUF_STR, GGUF_ARR, GGUF_U64, GGUF_I64, GGUF_F64) = range(13)

_SCALAR_FMT = {
    GGUF_U8: "<B", GGUF_I8: "<b", GGUF_U16: "<H", GGUF_I16: "<h",
    GGUF_U32: "<I", GGUF_I32: "<i", GGUF_F32: "<f", GGUF_BOOL: "<B",
    GGUF_U64: "<Q", GGUF_I64: "<q", GGUF_F64: "<d",
}
_SCALAR_SIZE = {t: struct.calcsize(f) for t, f in _SCALAR_FMT.items()}


class GGUFError(RuntimeError):
    pass


def _rd(f, n):
    b = f.read(n)
    if len(b) != n:
        raise GGUFError("EOF inesperado ao ler cabeçalho GGUF.")
    return b


def _read_scalar(f, t):
    fmt = _SCALAR_FMT[t]
    val = struct.unpack(fmt, _rd(f, _SCALAR_SIZE[t]))[0]
    if t == GGUF_BOOL:
        return bool(val)
    return val


def _read_str(f):
    (ln,) = struct.unpack("<Q", _rd(f, 8))
    if ln > 64 * 1024 * 1024:
        raise GGUFError("String de metadado absurdamente grande.")
    return _rd(f, ln).decode("utf-8", errors="replace")


def _skip_value(f, t, want_key=False):
    """Lê/pula um valor GGUF; retorna o valor para escalares/strings, None p/ arrays."""
    if t in _SCALAR_SIZE:
        return _read_scalar(f, t)
    if t == GGUF_STR:
        return _read_str(f)
    if t == GGUF_ARR:
        (elem_t,) = struct.unpack("<I", _rd(f, 4))
        (count,) = struct.unpack("<Q", _rd(f, 8))
        if elem_t in _SCALAR_SIZE:
            f.seek(_SCALAR_SIZE[elem_t] * count, 1)  # pula em bloco
        elif elem_t == GGUF_STR:
            for _ in range(count):
                (ln,) = struct.unpack("<Q", _rd(f, 8))
                f.seek(ln, 1)
        else:
            raise GGUFError(f"Tipo de array não suportado: {elem_t}")
        return None
    raise GGUFError(f"Tipo de metadado desconhecido: {t}")


def read_gguf_metadata(path: Path, max_kv: int = 100000) -> dict:
    """Lê magic/versão e os metadados KV do GGUF (sem tocar nos tensores)."""
    with open(path, "rb") as f:
        magic = _rd(f, 4)
        if magic != b"GGUF":
            raise GGUFError("Assinatura GGUF ausente (não é um .gguf válido).")
        (version,) = struct.unpack("<I", _rd(f, 4))
        if version == 1:
            (tensor_count,) = struct.unpack("<I", _rd(f, 4))
            (kv_count,) = struct.unpack("<I", _rd(f, 4))
        else:
            (tensor_count,) = struct.unpack("<Q", _rd(f, 8))
            (kv_count,) = struct.unpack("<Q", _rd(f, 8))
        meta = {}
        n = min(kv_count, max_kv)
        for _ in range(n):
            key = _read_str(f)
            (vtype,) = struct.unpack("<I", _rd(f, 4))
            val = _skip_value(f, vtype)
            if val is not None:
                meta[key] = val
    return {
        "gguf_version": version,
        "tensor_count": tensor_count,
        "kv_count": kv_count,
        "meta": meta,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _tier_guess(params_b: float) -> str:
    if params_b <= 0:
        return ""
    if params_b < 3.5:
        return "LEVE"
    if params_b < 5:
        return "RAPIDO"
    if params_b < 10:
        return "QUALIDADE"
    if params_b < 16:
        return "AVANCADO"
    return "PESADO"


def _params_from_meta(meta: dict, size_gb: float) -> float:
    # tenta general.size_label (ex.: "4B", "8.2B"); senão estima grosso por tamanho.
    label = str(meta.get("general.size_label") or "")
    import re
    m = re.search(r"([\d.]+)\s*B", label, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return 0.0


def load_registry_entry(model_id: str):
    if not REGISTRY.exists():
        return None
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    for m in data.get("models", []):
        if m.get("id") == model_id:
            return m
    return None


def main():
    ap = argparse.ArgumentParser(description="Valida um GGUF para o Catálogo de Modelos.")
    ap.add_argument("file", nargs="?", help="Caminho do .gguf (ou use --id).")
    ap.add_argument("--id", help="Valida via registry (usa file+sha256 do id).")
    ap.add_argument("--sha256", help="SHA256 esperado (hex).")
    ap.add_argument("--json", action="store_true", help="Saída em JSON.")
    args = ap.parse_args()

    checks = []
    def check(name, ok, detail=""):
        checks.append((name, None if ok is None else bool(ok), detail))

    expected_sha = args.sha256
    reg_entry = None
    if args.id:
        reg_entry = load_registry_entry(args.id)
        if not reg_entry:
            print(f"FALHA: id '{args.id}' não encontrado em {REGISTRY}")
            return 1
        path = MODELS_DIR / str(reg_entry.get("file") or "")
        expected_sha = expected_sha or reg_entry.get("sha256")
    elif args.file:
        path = Path(args.file)
        if not path.is_absolute() and not path.exists():
            alt = MODELS_DIR / path.name
            if alt.exists():
                path = alt
    else:
        ap.print_help()
        return 2

    # 1) existência + tamanho
    exists = path.exists() and path.is_file()
    check("arquivo existe", exists, str(path))
    if not exists:
        _report(checks, None, args.json)
        return 1
    size = path.stat().st_size
    size_gb = round(size / (1024 ** 3), 3)
    check("tamanho", size > 0, f"{size_gb} GB")

    # 2) GGUF header + metadados
    info = None
    try:
        info = read_gguf_metadata(path)
        check("assinatura GGUF", True, f"versão {info['gguf_version']}")
    except Exception as exc:
        check("assinatura GGUF", False, str(exc))

    meta = (info or {}).get("meta", {})
    arch = str(meta.get("general.architecture") or "")
    name = str(meta.get("general.name") or "")
    ctx = None
    if arch:
        ctx = meta.get(f"{arch}.context_length")
    chat_tmpl = meta.get("tokenizer.chat_template")
    quant = meta.get("general.file_type")
    params_b = _params_from_meta(meta, size_gb)

    if info is not None:
        check("arquitetura detectada", bool(arch), arch or "n/d")
        check("arquitetura conhecida", (arch.lower() in KNOWN_ARCHS) if arch else None,
              arch or "n/d")
        check("context_length", bool(ctx), str(ctx) if ctx else "n/d")
        check("chat template presente", chat_tmpl is not None,
              "sim" if chat_tmpl is not None else "ausente (usar fallback do NÚCLEO)")

    # 3) SHA256
    print("Calculando SHA256 (pode levar alguns segundos)...", file=sys.stderr)
    actual_sha = sha256_file(path)
    if expected_sha:
        ok = actual_sha.lower() == str(expected_sha).lower()
        check("SHA256 confere", ok, actual_sha if ok else f"obtido {actual_sha} != esperado {expected_sha}")
    else:
        check("SHA256 (sem esperado; registre este)", None, actual_sha)

    # 4) compat build (informativo — não executa o modelo)
    check("compat llama.cpp (informativo)", None,
          f">= {LLAMA_CPP_BUILD}; confirme rodando de fato antes de marcar validated")

    # Sugestão de entrada de registry
    suggestion = {
        "id": args.id or (name.lower().replace(" ", "-") if name else path.stem.lower()),
        "file": path.name,
        "family": arch or "desconhecida",
        "params_b": params_b,
        "quantization": "",
        "size_gb": size_gb,
        "context_default": int(ctx) if isinstance(ctx, int) else 4096,
        "license": "",
        "sha256": actual_sha,
        "chat_template": arch or "generic",
        "tier": _tier_guess(params_b),
        "roles": [],
        "requirements": {"min_ram_gb": 0, "min_vram_gb_cuda": 0, "cpu_only_ok": True},
        "llama_cpp_min_build": LLAMA_CPP_BUILD,
        "status": "unverified"
    }

    return _report(checks, suggestion, args.json)


def _report(checks, suggestion, as_json):
    failures = sum(1 for _, ok, _ in checks if ok is False)
    if as_json:
        print(json.dumps({
            "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
            "failures": failures,
            "suggested_registry_entry": suggestion,
        }, ensure_ascii=False, indent=2))
        return 1 if failures else 0

    print()
    print("=" * 72)
    print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO DE MODELO (§25)")
    print("=" * 72)
    for name, ok, detail in checks:
        tag = "AVISO" if ok is None else ("OK" if ok else "FALHA")
        suffix = f" — {detail}" if detail else ""
        print(f"[{tag:5}] {name}{suffix}")
    print()
    if suggestion:
        print("Sugestão de entrada para config/models_registry.json:")
        print("(revise roles/tier/requirements/license e só então status=validated)")
        print(json.dumps(suggestion, ensure_ascii=False, indent=2))
        print()
    if failures:
        print(f"Resultado: {failures} FALHA(s). NÃO adicionar como 'validated'.")
        return 1
    print("Resultado: sem falhas. Revise os AVISOS antes de marcar 'validated'.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
