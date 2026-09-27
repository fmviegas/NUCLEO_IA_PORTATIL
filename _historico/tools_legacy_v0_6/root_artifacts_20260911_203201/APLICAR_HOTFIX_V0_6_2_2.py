#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import py_compile
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUTOTUNE = ROOT / "app" / "autotune.py"
VERSION = ROOT / "VERSION.json"
STATE = ROOT / "state"
BACKUP_ROOT = ROOT / "backup"

def fail(msg):
    print()
    print("ERRO:", msg)
    print()
    raise SystemExit(1)

if not AUTOTUNE.exists():
    fail(f"Arquivo necessário não encontrado: {AUTOTUNE}")

text = AUTOTUNE.read_text(encoding="utf-8-sig")

# Idempotência.
if 'NUCLEO_V0622_SINGLE_TURN' in text:
    print("Hotfix V0.6.2.2 já está aplicado.")
    raise SystemExit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_ROOT / f"pre_v0_6_2_2_{stamp}"
(backup / "app").mkdir(parents=True, exist_ok=True)
shutil.copy2(AUTOTUNE, backup / "app" / "autotune.py")
if VERSION.exists():
    shutil.copy2(VERSION, backup / "VERSION.json")

print("1/4 - Backup criado:")
print("     ", backup)

needle = (
    '    if supports(cli, "--reasoning"):\n'
    '        cmd += ["--reasoning", "off"]\n'
)

replacement = (
    '    if supports(cli, "--reasoning"):\n'
    '        cmd += ["--reasoning", "off"]\n'
    '\n'
    '    # NUCLEO_V0622_SINGLE_TURN\n'
    '    # Qwen3 possui chat template e o llama-cli pode entrar em modo\n'
    '    # conversacional automaticamente. Para uma sonda de benchmark,\n'
    '    # queremos exatamente uma resposta e encerramento imediato.\n'
    '    if supports(cli, "--single-turn"):\n'
    '        cmd += ["--single-turn"]\n'
    '    elif supports(cli, "-st"):\n'
    '        cmd += ["-st"]\n'
)

if needle not in text:
    fail(
        "Não encontrei o bloco esperado de reasoning em app\\autotune.py. "
        "Nenhuma alteração foi feita."
    )

text = text.replace(needle, replacement, 1)

# stdin fechado: a sonda jamais deve ficar aguardando nova entrada do usuário.
popen_needle = (
    '        stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n'
    '        text=True, encoding="utf-8", errors="replace",\n'
    '        creationflags=flags\n'
)

popen_replacement = (
    '        stdin=subprocess.DEVNULL,\n'
    '        stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n'
    '        text=True, encoding="utf-8", errors="replace",\n'
    '        creationflags=flags\n'
)

if popen_needle not in text:
    fail(
        "Não encontrei o bloco esperado de subprocess.Popen em app\\autotune.py. "
        "Nenhuma alteração foi feita."
    )

text = text.replace(popen_needle, popen_replacement, 1)
AUTOTUNE.write_text(text, encoding="utf-8")

print("2/4 - Sonda real configurada como single-turn.")
print("3/4 - stdin da sonda fechado para impedir espera interativa.")

if VERSION.exists():
    try:
        v = json.loads(VERSION.read_text(encoding="utf-8-sig"))
    except Exception:
        v = {}
    v["version"] = "0.6.2.2"
    v["channel"] = "hotfix"
    v["hotfix"] = "AutoTune llama-cli single-turn probe"
    VERSION.write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")

try:
    py_compile.compile(str(AUTOTUNE), doraise=True)
except Exception as exc:
    shutil.copy2(backup / "app" / "autotune.py", AUTOTUNE)
    if (backup / "VERSION.json").exists():
        shutil.copy2(backup / "VERSION.json", VERSION)
    fail(f"Validação Python falhou; arquivo original restaurado. Detalhe: {exc}")

STATE.mkdir(parents=True, exist_ok=True)
state = {
    "product": "NÚCLEO IA PORTÁTIL",
    "version": "0.6.2.2",
    "type": "hotfix",
    "backup_dir": str(backup),
    "fixes": [
        "real chat probe uses llama-cli --single-turn when supported",
        "real chat probe stdin is DEVNULL to prevent interactive wait",
    ],
}
(STATE / "v0_6_2_2_hotfix.json").write_text(
    json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
)

print("4/4 - Validação Python: OK")
print()
print("==============================================================")
print("HOTFIX V0.6.2.2 APLICADO COM SUCESSO")
print("==============================================================")
print()
print("Reabra o NÚCLEO e execute Detalhes > Recalibrar computador.")
print("O benchmark base da mesma máquina será reutilizado quando disponível.")
