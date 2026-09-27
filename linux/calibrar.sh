#!/usr/bin/env bash
# NUCLEO IA PORTATIL — calibracao avancada no Linux (equivalente ao CALIBRAR_ADVANCED.bat)
# Repassa argumentos: ./scripts/calibrar.sh --mode advanced   (ou --mode code)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="$(command -v python3 || true)"
fi
if [ -z "${PY:-}" ]; then
  echo "ERRO: python3 nao encontrado." >&2
  exit 2
fi

exec "$PY" tools/calibrar_advanced.py "$@"
