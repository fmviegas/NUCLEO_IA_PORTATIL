#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Catálogo de Modelos (V0.7 Fase 3, fatia 1).

SOMENTE LEITURA nesta fatia: carrega o registry, avalia viabilidade por
hardware e propõe o mapa papel→modelo. NÃO altera o motor nem a calibração.

Retrocompatível:
- Se `config/models_registry.json` não existir, um registry padrão é
  sintetizado a partir dos dois modelos Qwen3 conhecidos.
- `present` é derivado da existência do arquivo em `models/`.

Tiers previstos (metadados): LEVE (1.5–3B), RAPIDO (4B), QUALIDADE (8B),
AVANCADO (12–14B), PESADO (20B+). O tier LEVE existe no schema, mas só é
oferecido quando houver um modelo pequeno realmente validado.
"""
from __future__ import annotations

import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
REGISTRY_REL = "config/models_registry.json"
MODELS_REL = "models"

TIERS = ["LEVE", "RAPIDO", "QUALIDADE", "AVANCADO", "PESADO"]


class CatalogError(RuntimeError):
    pass


def _default_registry() -> dict:
    """Registry sintetizado (fallback) com os dois Qwen3 conhecidos."""
    return {
        "registry_version": 1,
        "synthesized": True,
        "models": [
            {
                "id": "qwen3-4b-q4km",
                "file": "Qwen3-4B-Q4_K_M.gguf",
                "family": "Qwen3", "params_b": 4.0, "quantization": "Q4_K_M",
                "size_gb": 2.5, "context_default": 4096, "license": "Apache-2.0",
                "sha256": "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5",
                "chat_template": "qwen3", "tier": "RAPIDO",
                "roles": ["fast", "light"], "bench_key": "4b",
                "requirements": {"min_ram_gb": 6, "min_vram_gb_cuda": 3, "cpu_only_ok": True},
                "llama_cpp_min_build": "b10516", "status": "validated",
            },
            {
                "id": "qwen3-8b-q4km",
                "file": "Qwen3-8B-Q4_K_M.gguf",
                "family": "Qwen3", "params_b": 8.2, "quantization": "Q4_K_M",
                "size_gb": 5.03, "context_default": 4096, "license": "Apache-2.0",
                "sha256": "d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785",
                "chat_template": "qwen3", "tier": "QUALIDADE",
                "roles": ["quality"], "bench_key": "8b",
                "requirements": {"min_ram_gb": 10, "min_vram_gb_cuda": 4,
                                 "cpu_only_ok": True, "cpu_only_slow": True},
                "llama_cpp_min_build": "b10516", "status": "validated",
            },
        ],
    }


def _normalize_model(m: dict, models_dir: Path) -> dict:
    m = dict(m)
    req = dict(m.get("requirements") or {})
    req.setdefault("min_ram_gb", 0)
    req.setdefault("min_vram_gb_cuda", 0)
    req.setdefault("cpu_only_ok", True)
    m["requirements"] = req
    m.setdefault("roles", [])
    m.setdefault("tier", "")
    m.setdefault("status", "unverified")
    m.setdefault("params_b", 0.0)
    # present = arquivo existe em models/
    fname = str(m.get("file") or "")
    try:
        m["present"] = bool(fname) and (models_dir / fname).is_file()
    except OSError:
        m["present"] = False
    return m


def load_registry(root: Path = ROOT) -> dict:
    """Carrega o registry (ou sintetiza) e normaliza cada modelo."""
    root = Path(root)
    path = root / REGISTRY_REL
    reg = None
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict) and isinstance(data.get("models"), list):
                reg = data
        except Exception:
            reg = None
    if reg is None:
        reg = _default_registry()
    models_dir = root / MODELS_REL
    reg = dict(reg)
    reg["models"] = [_normalize_model(m, models_dir) for m in reg.get("models", [])]
    return reg


def caps_from_hardware(hw, cuda_available: bool | None = None) -> dict:
    """Extrai {cuda_available, vram_gb, ram_gb, cores} de um HardwareInfo.

    `cuda_available` pode ser passado (ex.: já considerando simulação); se None,
    deriva de hw.nvidia_detected."""
    if cuda_available is None:
        cuda_available = bool(getattr(hw, "nvidia_detected", False))
    vram = 0.0
    for g in getattr(hw, "gpus", []) or []:
        if getattr(g, "vendor", "") == "NVIDIA":
            vram = max(vram, float(getattr(g, "vram_gb", 0) or 0))
    return {
        "cuda_available": bool(cuda_available),
        "vram_gb": vram,
        "ram_gb": float(getattr(hw, "ram_total_gb", 0) or 0),
        "cores": int(getattr(hw, "physical_cores", 0) or 0),
    }


def _fits(m: dict, caps: dict) -> dict:
    req = m["requirements"]
    fits_cuda = bool(caps.get("cuda_available")) and \
        float(caps.get("vram_gb", 0)) >= float(req.get("min_vram_gb_cuda", 0))
    fits_cpu = bool(req.get("cpu_only_ok", True)) and \
        float(caps.get("ram_gb", 0)) >= float(req.get("min_ram_gb", 0))
    return {"fits_cuda": fits_cuda, "fits_cpu": fits_cpu}


def viable_models(caps: dict, registry: dict | None = None, root: Path = ROOT) -> list:
    """Modelos presentes, validados e que rodam nesta máquina (cuda OU cpu)."""
    reg = registry or load_registry(root)
    out = []
    for m in reg.get("models", []):
        if not m.get("present"):
            continue
        if m.get("status") != "validated":
            continue
        fit = _fits(m, caps)
        if fit["fits_cuda"] or fit["fits_cpu"]:
            mm = dict(m)
            mm.update(fit)
            out.append(mm)
    return out


def select_roles(caps: dict, registry: dict | None = None, root: Path = ROOT) -> dict:
    """Mapa papel→modelo por hardware. Não altera nada; só recomenda.

    - fast = menor modelo viável com role fast/light (senão o menor viável);
    - quality = maior modelo viável com role quality (senão cai para fast).
    """
    vm = viable_models(caps, registry, root)
    fast_c = [m for m in vm if ("fast" in m["roles"] or "light" in m["roles"])]
    quality_c = [m for m in vm if "quality" in m["roles"]]
    fast = min(fast_c, key=lambda m: m["params_b"], default=None)
    if fast is None and vm:
        fast = min(vm, key=lambda m: m["params_b"])
    quality = max(quality_c, key=lambda m: m["params_b"], default=None)
    quality_is_fallback = quality is None and fast is not None
    if quality is None:
        quality = fast
    return {
        "fast": fast["id"] if fast else None,
        "quality": quality["id"] if quality else None,
        "quality_is_fallback": quality_is_fallback,
        "viable_ids": [m["id"] for m in vm],
        "caps": caps,
    }


def get_model(model_id: str, registry: dict | None = None, root: Path = ROOT) -> dict | None:
    reg = registry or load_registry(root)
    for m in reg.get("models", []):
        if m.get("id") == model_id:
            return m
    return None


if __name__ == "__main__":
    # Diagnóstico rápido: imprime o catálogo e a seleção para o hardware atual.
    import sys
    sys.path.insert(0, str(APP_DIR))
    try:
        import hardware as hw_mod
        hw = hw_mod.detect_safe() if hasattr(hw_mod, "detect_safe") else hw_mod.detect_windows()
        caps = caps_from_hardware(hw)
    except Exception as exc:
        caps = {"cuda_available": False, "vram_gb": 0.0, "ram_gb": 0.0, "cores": 0}
        print("Aviso: detecção indisponível:", exc)
    reg = load_registry()
    print("registry:", "sintetizado" if reg.get("synthesized") else REGISTRY_REL,
          "| modelos:", len(reg["models"]))
    for m in reg["models"]:
        print(f"  - {m['id']:16} tier={m['tier']:9} present={m['present']} status={m['status']}")
    print("caps:", caps)
    print("select_roles:", json.dumps(select_roles(caps, reg), ensure_ascii=False))
