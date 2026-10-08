#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baixar_modelos.py — Baixa os modelos CATALOGADOS (status 'catalogued') do
config/models_registry.json direto do Hugging Face, confere o SHA256 de cada
arquivo e grava state/models_verified/<id>.json. Só depois disso o catálogo
considera o modelo utilizável e a calibração (CALIBRAR_MELHORES.bat) pode
escolhê-lo.

- Retoma download interrompido (arquivo .part + cabeçalho Range).
- Confere espaço livre antes de começar.
- Modelo dividido em partes e mmproj (visão) vêm juntos.
- Mostra quais modelos CABEM nesta máquina (mesma regra do catálogo).

Uso:
    python tools/baixar_modelos.py                  # menu interativo
    python tools/baixar_modelos.py --listar
    python tools/baixar_modelos.py --ids qwen35-9b-q4km,qwen3-coder-30b-a3b-q4km
    python tools/baixar_modelos.py --recomendados   # só os que cabem aqui
    python tools/baixar_modelos.py --todos --sim    # tudo, sem perguntar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

import catalog as cat  # noqa: E402

MODELS = ROOT / cat.MODELS_REL
VERIFIED = ROOT / cat.VERIFIED_REL
CHUNK = 8 * 1024 * 1024
MARGEM_DISCO = 2 * 1024 ** 3
CLASSES = {"media": "máquina média", "forte": "GPU 24 GB / 32 GB+ RAM", "estacao": "estação 64–128 GB"}


def _caps():
    try:
        import hardware as core
        return cat.caps_from_hardware(core.detect_safe())
    except Exception as exc:  # detecção nunca impede o download
        print(f"Aviso: não detectei o hardware ({exc}); 'cabe aqui' fica em branco.")
        return None


def _gb(n: float) -> str:
    return f"{n / 1e9:.1f} GB"


def _total(m: dict) -> int:
    return sum(int(h["size"]) for h in m["hf_files"])


def _falta(m: dict) -> int:
    """Bytes que ainda faltam baixar (desconta .part e arquivos completos)."""
    n = 0
    for h in m["hf_files"]:
        dest = MODELS / h["dest"]
        if dest.is_file() and dest.stat().st_size == int(h["size"]):
            continue
        part = dest.with_name(dest.name + ".part")
        n += int(h["size"]) - (part.stat().st_size if part.is_file() else 0)
    return n


def _sha256(path: Path, rotulo: str) -> str:
    h = hashlib.sha256()
    total = path.stat().st_size or 1
    feito, ultimo = 0, 0.0
    with path.open("rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
            feito += len(b)
            agora = time.time()
            if agora - ultimo > 2:
                print(f"\r    conferindo SHA256 {rotulo}: {feito * 100 // total}%   ", end="", flush=True)
                ultimo = agora
    print(f"\r    conferindo SHA256 {rotulo}: 100%   ")
    return h.hexdigest()


def _baixar_arquivo(repo: str, h: dict) -> None:
    dest = MODELS / h["dest"]
    size = int(h["size"])
    if dest.is_file() and dest.stat().st_size == size:
        print(f"  ✓ {h['dest']} já está completo.")
        return
    part = dest.with_name(dest.name + ".part")
    url = f"https://huggingface.co/{repo}/resolve/main/{urllib.request.quote(h['src'])}"
    for tentativa in range(1, 6):
        ja = part.stat().st_size if part.is_file() else 0
        if ja >= size:
            break
        req = urllib.request.Request(url, headers={"User-Agent": "nucleo-ia-portatil/1.0"})
        if ja:
            req.add_header("Range", f"bytes={ja}-")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if ja and r.status != 206:      # servidor ignorou o Range: recomeça
                    ja = 0
                modo = "ab" if ja else "wb"
                t0, base, ultimo = time.time(), ja, 0.0
                with part.open(modo) as f:
                    while True:
                        b = r.read(CHUNK)
                        if not b:
                            break
                        f.write(b)
                        ja += len(b)
                        agora = time.time()
                        if agora - ultimo > 2:
                            vel = (ja - base) / max(agora - t0, 0.1)
                            resto = (size - ja) / vel if vel > 0 else 0
                            print(f"\r  ↓ {h['dest']}: {ja * 100 // size}% ({_gb(ja)} de {_gb(size)}) "
                                  f"{vel / 1e6:.1f} MB/s, faltam ~{int(resto // 60)} min   ", end="", flush=True)
                            ultimo = agora
            print()
            break
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            print(f"\n  ! falha na tentativa {tentativa}/5 ({exc}); retomando em 10 s...")
            time.sleep(10)
    if not part.is_file() or part.stat().st_size != size:
        raise RuntimeError(f"download incompleto de {h['dest']} (rode de novo para retomar)")
    part.replace(dest)


def baixar(m: dict) -> bool:
    print(f"\n=== {m['id']}  ({_gb(_total(m))}, {CLASSES.get(m.get('machine_class'), '?')})")
    try:
        for h in m["hf_files"]:
            _baixar_arquivo(m["hf_repo"], h)
        for h in m["hf_files"]:
            dig = _sha256(MODELS / h["dest"], h["dest"])
            if dig != h["sha256"]:
                bad = MODELS / h["dest"]
                bad.replace(bad.with_name(bad.name + ".corrompido"))
                print(f"  ✗ SHA256 NÃO confere em {h['dest']} — renomeado p/ .corrompido. Rode de novo.")
                return False
    except RuntimeError as exc:
        print(f"  ✗ {exc}")
        return False
    VERIFIED.mkdir(parents=True, exist_ok=True)
    (VERIFIED / f"{m['id']}.json").write_text(json.dumps({
        "id": m["id"], "sha256": m["sha256"], "hf_repo": m["hf_repo"],
        "files": [{"dest": h["dest"], "sha256": h["sha256"], "size": h["size"]} for h in m["hf_files"]],
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ {m['id']} baixado e conferido. Agora rode CALIBRAR_MELHORES.bat.")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Baixa modelos catalogados (Hugging Face) com conferência de SHA256.")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--ids", default="")
    ap.add_argument("--recomendados", action="store_true", help="só os que cabem nesta máquina")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--sim", action="store_true", help="não pede confirmação")
    args = ap.parse_args()

    reg = cat.load_registry(ROOT)
    lista = [m for m in reg["models"] if m.get("hf_repo") and m.get("hf_files")]
    caps = _caps()
    cabe = {}
    for m in lista:
        if caps:
            fit = cat._fits(m, caps)
            cabe[m["id"]] = fit["fits_cuda"] or fit["fits_cpu"]

    print("=" * 78)
    print("   NÚCLEO IA PORTÁTIL — MODELOS PESADOS (catálogo para máquinas maiores)")
    print("=" * 78)
    if caps:
        print(f"Esta máquina: RAM {caps['ram_gb']:.0f} GB | VRAM {caps['vram_gb']:.0f} GB | "
              f"CUDA {'sim' if caps['cuda_available'] else 'não'}")
    for i, m in enumerate(lista, 1):
        estado = "PRONTO" if m.get("verified_download") else ("baixado?" if m.get("present") else "—")
        aqui = "" if not caps else ("cabe aqui" if cabe[m["id"]] else "não cabe aqui")
        print(f" {i}. {m['id']:<26} {_gb(_total(m)):>9}  {', '.join(m['roles']):<16} "
              f"{CLASSES.get(m.get('machine_class'), ''):<24} {estado:<8} {aqui}")
    if args.listar:
        return 0

    if args.todos:
        escolha = lista
    elif args.recomendados:
        escolha = [m for m in lista if cabe.get(m["id"])]
    elif args.ids:
        ids = {x.strip() for x in args.ids.split(",") if x.strip()}
        escolha = [m for m in lista if m["id"] in ids]
        faltando = ids - {m["id"] for m in escolha}
        if faltando:
            print("IDs desconhecidos:", ", ".join(sorted(faltando)))
            return 2
    else:
        print("\nDigite os números separados por vírgula, R = só os que cabem aqui, T = todos, Enter = sair.")
        resp = input("> ").strip().lower()
        if not resp:
            return 0
        if resp == "t":
            escolha = lista
        elif resp == "r":
            escolha = [m for m in lista if cabe.get(m["id"])]
        else:
            try:
                escolha = [lista[int(x) - 1] for x in resp.replace(" ", "").split(",") if x]
            except (ValueError, IndexError):
                print("Opção inválida.")
                return 2
    escolha = [m for m in escolha if not m.get("verified_download")]
    if not escolha:
        print("Nada a baixar (já está tudo pronto, ou nenhum modelo cabe nesta máquina).")
        return 0

    precisa = sum(_falta(m) for m in escolha)
    livre = shutil.disk_usage(MODELS).free
    print(f"\nVai baixar: {', '.join(m['id'] for m in escolha)}")
    print(f"Precisa de {_gb(precisa)}; livre no disco: {_gb(livre)}.")
    if precisa + MARGEM_DISCO > livre:
        print("Espaço insuficiente (com margem de 2 GB). Escolha menos modelos ou libere espaço.")
        return 3
    if not args.sim and input("Confirmar? (s/N) ").strip().lower() != "s":
        return 0

    MODELS.mkdir(exist_ok=True)
    ok = [baixar(m) for m in escolha]
    print(f"\nConcluído: {sum(ok)} de {len(ok)} modelo(s) prontos.")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
