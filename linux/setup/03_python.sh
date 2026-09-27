#!/usr/bin/env bash
# 03_python.sh — cria o .venv e instala as libs de publicacao (docx/epub/pdf).
# O backend do NUCLEO e' stdlib puro; estas libs so' sao necessarias p/ PUBLICAR livros.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
echo "== 03 venv + libs de publicacao =="
command -v python3 >/dev/null || { echo "instale: sudo apt install -y python3 python3-venv python3-pip"; exit 1; }
python3 -c 'import venv' 2>/dev/null || { echo "  instalando python3-venv (sudo)…"; sudo apt-get install -y python3-venv; }
[ -x ".venv/bin/python" ] || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install "python-docx>=1.2.0" "ebooklib>=0.20" lxml "pypdf>=6.18"
echo "  verificando imports…"
.venv/bin/python -c "import docx,ebooklib,lxml,pypdf; print('  libs OK')"
echo "OK 03."
