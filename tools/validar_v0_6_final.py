#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = []
def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))

version_path = ROOT / "VERSION.json"
try:
    version = json.loads(version_path.read_text(encoding="utf-8-sig"))
    check("VERSION.json", version.get("version") == "0.6", str(version.get("version")))
except Exception as exc:
    check("VERSION.json", False, str(exc))

required = [
    "app/server.py",
    "app/engine_manager.py",
    "app/calibration_manager.py",
    "app/maintenance_manager.py",
    "app/sessions.py",
    "app/autotune.py",
    "app/benchmark.py",
    "app/hardware.py",
    "ui/index.html",
    "ui/app.css",
    "ui/app.js",
    "runtime/python/python.exe",
    "engine/windows/cpu/llama-server.exe",
    "engine/windows/cuda/llama-server.exe",
    "models/Qwen3-4B-Q4_K_M.gguf",
    "models/Qwen3-8B-Q4_K_M.gguf",
]
for rel in required:
    p = ROOT / rel
    try:
        ok = p.exists()
    except OSError:
        ok = False
    check(rel, ok, "")

for rel in [
    "app/server.py",
    "app/engine_manager.py",
    "app/calibration_manager.py",
    "app/maintenance_manager.py",
    "app/sessions.py",
    "app/autotune.py",
    "app/benchmark.py",
    "app/hardware.py",
]:
    p = ROOT / rel
    if p.exists():
        try:
            py_compile.compile(str(p), doraise=True)
            check("compile " + rel, True)
        except Exception as exc:
            check("compile " + rel, False, str(exc))

profiles = list((ROOT / "profiles" / "machines").glob("*.json"))
check("profiles\\machines", bool(profiles), f"{len(profiles)} perfil(is)")

sessions_root = ROOT / "sessions"
check("sessions", sessions_root.exists(), "")

print()
print("=" * 70)
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.6 FINAL")
print("=" * 70)
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

print("Resultado: V0.6 FINAL íntegra.")
raise SystemExit(0)
