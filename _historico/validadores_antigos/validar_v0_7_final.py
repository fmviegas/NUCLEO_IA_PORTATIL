#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import py_compile
import sys
from pathlib import Path

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]

checks = []
def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))

# 1) VERSION.json
try:
    version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8-sig"))
    check("VERSION.json version=0.7", version.get("version") == "0.7", str(version.get("version")))
    check("VERSION.json release=final", version.get("release") == "final", str(version.get("release")))
except Exception as exc:
    check("VERSION.json", False, str(exc))

# 2) Arquivos obrigatorios
required = [
    "app/server.py", "app/engine_manager.py", "app/calibration_manager.py",
    "app/maintenance_manager.py", "app/sessions.py", "app/autotune.py",
    "app/benchmark.py", "app/hardware.py", "app/file_analysis.py",
    "app/workspace.py", "app/catalog.py",
    "config/models_registry.json", "tools/validar_modelo.py",
    "ui/index.html", "ui/app.css", "ui/app.js",
    "runtime/python/python.exe",
    "engine/windows/cpu/llama-server.exe",
    "engine/windows/cuda/llama-server.exe",
    "models/Qwen3-4B-Q4_K_M.gguf",
    "models/Qwen3-8B-Q4_K_M.gguf",
]
for rel in required:
    try:
        ok = (ROOT / rel).exists()
    except OSError:
        ok = False
    check(rel, ok, "")

# 3) Compilacao
for rel in [
    "app/server.py", "app/engine_manager.py", "app/calibration_manager.py",
    "app/maintenance_manager.py", "app/sessions.py", "app/autotune.py",
    "app/benchmark.py", "app/hardware.py", "app/file_analysis.py",
    "app/workspace.py", "app/catalog.py", "tools/validar_modelo.py",
]:
    p = ROOT / rel
    if p.exists():
        try:
            py_compile.compile(str(p), doraise=True)
            check("compile " + rel, True)
        except Exception as exc:
            check("compile " + rel, False, str(exc))

# 4) Funcoes-chave da V0.7
def has_all(rel, needles):
    p = ROOT / rel
    if not p.exists():
        return False
    txt = p.read_text(encoding="utf-8", errors="replace")
    return all(n in txt for n in needles)

check("hardware: deteccao defensiva + id v2",
      has_all("app/hardware.py", ["detect_safe", "machine_id_v2", "detection_confidence"]))
check("engine: cuda_available + resolve_model_path + reaper",
      has_all("app/engine_manager.py", ["_cuda_available", "_resolve_model_path", "_reap_orphan_servers"]))
check("catalog: viable_models + select_roles",
      has_all("app/catalog.py", ["viable_models", "select_roles", "caps_from_hardware"]))
check("autotune: calibracao via catalogo (schema v3)",
      has_all("app/autotune.py", ["import catalog", "profile_schema_version", "model_ids"]))
check("file_analysis: leitura semantica de planilhas",
      has_all("app/file_analysis.py", ["_classify_structure", "_extract_form_block", "_column_blocks"]))

# 5) Integridade SHA256
manifest_path = ROOT / "app" / "manifests" / "manifest_v0_7_final.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mism = []
    for rel, meta in manifest.get("files", {}).items():
        p = ROOT / rel
        if not p.exists():
            mism.append(rel + " (ausente)")
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != meta.get("sha256"):
            mism.append(rel + " (hash)")
    check("integridade SHA256 (manifest)", not mism, "OK" if not mism else "; ".join(mism[:6]))
except Exception as exc:
    check("integridade SHA256 (manifest)", False, str(exc))

# 6) Marcadores dos alphas consolidados
for st in ["v0_7_a1_install.json", "v0_7_a2_install.json", "v0_7_a3_install.json",
           "v0_7_a4_install.json", "v0_7_a5_install.json", "v0_7_a6_install.json"]:
    check("state/" + st, (ROOT / "state" / st).exists(), "")

profiles = list((ROOT / "profiles" / "machines").glob("*.json"))
check("profiles/machines", bool(profiles), f"{len(profiles)} perfil(is)")

print()
print("=" * 72)
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.7 FINAL")
print("=" * 72)
failures = 0
for name, ok, detail in checks:
    status = "OK" if ok else "FALHA"
    if not ok:
        failures += 1
    suffix = f" — {detail}" if detail else ""
    print(f"[{status:5}] {name}{suffix}")
print()
if failures:
    print(f"Resultado: {failures} falha(s).")
    raise SystemExit(1)
print("Resultado: V0.7 FINAL íntegra.")
raise SystemExit(0)
