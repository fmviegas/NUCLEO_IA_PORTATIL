#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import py_compile
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BENCH = ROOT / "app" / "benchmark.py"
CAL = ROOT / "app" / "calibration_manager.py"
VERSION = ROOT / "VERSION.json"
STATE = ROOT / "state"
BACKUP_ROOT = ROOT / "backup"

def fail(msg):
    print()
    print("ERRO:", msg)
    print()
    raise SystemExit(1)

for p in (BENCH, CAL):
    if not p.exists():
        fail(f"Arquivo necessário não encontrado: {p}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_ROOT / f"pre_v0_6_2_1_{stamp}"
(backup / "app").mkdir(parents=True, exist_ok=True)
shutil.copy2(BENCH, backup / "app" / "benchmark.py")
shutil.copy2(CAL, backup / "app" / "calibration_manager.py")
if VERSION.exists():
    shutil.copy2(VERSION, backup / "VERSION.json")

print("1/4 - Backup criado:")
print("     ", backup)

bench = BENCH.read_text(encoding="utf-8-sig")
delta_count = bench.count("Δ")
bench = bench.replace("Δ", "delta")
BENCH.write_text(bench, encoding="utf-8")
print(f"2/4 - benchmark.py corrigido ({delta_count} símbolo(s) Delta convertido(s) para ASCII).")

cal = CAL.read_text(encoding="utf-8-sig")
marker = 'child_env["PYTHONIOENCODING"] = "utf-8"'
if marker not in cal:
    old = (
        '            self.proc = subprocess.Popen(\n'
        '                [sys.executable, "-u", str(script)],\n'
        '                cwd=str(self.root),\n'
        '                stdout=subprocess.PIPE,\n'
        '                stderr=subprocess.STDOUT,\n'
        '                text=True,\n'
        '                encoding="utf-8",\n'
        '                errors="replace",\n'
        '                bufsize=1,\n'
        '                creationflags=creationflags,\n'
        '            )\n'
    )
    new = (
        '            child_env = os.environ.copy()\n'
        '            child_env["PYTHONIOENCODING"] = "utf-8"\n'
        '            child_env["PYTHONUTF8"] = "1"\n'
        '\n'
        '            self.proc = subprocess.Popen(\n'
        '                [sys.executable, "-u", str(script)],\n'
        '                cwd=str(self.root),\n'
        '                stdout=subprocess.PIPE,\n'
        '                stderr=subprocess.STDOUT,\n'
        '                text=True,\n'
        '                encoding="utf-8",\n'
        '                errors="replace",\n'
        '                bufsize=1,\n'
        '                creationflags=creationflags,\n'
        '                env=child_env,\n'
        '            )\n'
    )
    if old not in cal:
        fail(
            "Não encontrei o bloco esperado em app\\calibration_manager.py. "
            "Nenhuma substituição insegura foi feita."
        )
    cal = cal.replace(old, new)

CAL.write_text(cal, encoding="utf-8")
print("3/4 - Processos Python da calibração configurados para UTF-8.")

if VERSION.exists():
    try:
        v = json.loads(VERSION.read_text(encoding="utf-8-sig"))
    except Exception:
        v = {}
    v["version"] = "0.6.2.1"
    v["channel"] = "hotfix"
    v["hotfix"] = "Windows redirected-console UTF-8 / CP1252 compatibility"
    VERSION.write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")

try:
    py_compile.compile(str(BENCH), doraise=True)
    py_compile.compile(str(CAL), doraise=True)
except Exception as exc:
    shutil.copy2(backup / "app" / "benchmark.py", BENCH)
    shutil.copy2(backup / "app" / "calibration_manager.py", CAL)
    if (backup / "VERSION.json").exists():
        shutil.copy2(backup / "VERSION.json", VERSION)
    fail(f"Validação Python falhou; arquivos originais restaurados. Detalhe: {exc}")

STATE.mkdir(parents=True, exist_ok=True)
state = {
    "product": "NÚCLEO IA PORTÁTIL",
    "version": "0.6.2.1",
    "type": "hotfix",
    "backup_dir": str(backup),
    "fixes": [
        "benchmark output no longer depends on Greek Delta under CP1252",
        "calibration child Python processes forced to UTF-8",
    ],
}
(STATE / "v0_6_2_1_hotfix.json").write_text(
    json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
)

print("4/4 - Validação Python: OK")
print()
print("==============================================================")
print("HOTFIX V0.6.2.1 APLICADO COM SUCESSO")
print("==============================================================")
print()
print("Agora abra INICIAR_NUCLEO_IA.bat e execute a recalibração novamente.")
