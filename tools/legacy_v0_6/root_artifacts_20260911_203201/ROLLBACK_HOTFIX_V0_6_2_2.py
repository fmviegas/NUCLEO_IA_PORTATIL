#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state" / "v0_6_2_2_hotfix.json"

if not STATE_FILE.exists():
    print("Estado do hotfix V0.6.2.2 não encontrado.")
    raise SystemExit(1)

state = json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
backup = Path(state["backup_dir"])

src = backup / "app" / "autotune.py"
if src.exists():
    shutil.copy2(src, ROOT / "app" / "autotune.py")

version_backup = backup / "VERSION.json"
if version_backup.exists():
    shutil.copy2(version_backup, ROOT / "VERSION.json")

print("Rollback do hotfix V0.6.2.2 concluído.")
