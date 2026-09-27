#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state" / "v0_6_2_1_hotfix.json"

if not STATE_FILE.exists():
    print("Estado do hotfix V0.6.2.1 não encontrado.")
    raise SystemExit(1)

state = json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
backup = Path(state["backup_dir"])

for name in ("benchmark.py", "calibration_manager.py"):
    src = backup / "app" / name
    dst = ROOT / "app" / name
    if src.exists():
        shutil.copy2(src, dst)

version_backup = backup / "VERSION.json"
if version_backup.exists():
    shutil.copy2(version_backup, ROOT / "VERSION.json")

print("Rollback do hotfix V0.6.2.1 concluído.")
