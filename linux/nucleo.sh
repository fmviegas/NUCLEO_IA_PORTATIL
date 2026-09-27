#!/usr/bin/env bash
# NUCLEO IA PORTATIL — lancador Linux (equivalente ao INICIAR_NUCLEO_IA.bat)
# Ativa o .venv se existir e sobe o backend em 127.0.0.1.
set -euo pipefail

# raiz do projeto = pasta-pai deste script
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

if [ ! -f "app/server.py" ]; then
  echo "ERRO: app/server.py nao encontrado em $ROOT" >&2
  exit 3
fi

# Python: usa o venv do projeto se existir, senao o python3 do sistema
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="$(command -v python3 || true)"
fi
if [ -z "${PY:-}" ]; then
  echo "ERRO: python3 nao encontrado. Instale python3 (e crie .venv com as libs)." >&2
  exit 2
fi

echo "NUCLEO IA PORTATIL (Linux) — iniciando com: $PY"
exec "$PY" app/server.py
