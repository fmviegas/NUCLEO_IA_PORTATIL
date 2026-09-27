#!/usr/bin/env bash
# 04_iniciar.sh — preflight + inicia o NUCLEO.
#   ./04_iniciar.sh          -> verifica e INICIA o servidor (1a vez calibra ~10 min)
#   ./04_iniciar.sh --check  -> so' verifica, NAO inicia
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
if [ -t 1 ]; then G=$'\e[32m'; R=$'\e[31m'; N=$'\e[0m'; else G=; R=; N=; fi
fail=0; ok(){ echo "  ${G}[OK]${N} $1"; }; bad(){ echo "  ${R}[X]${N} $1"; fail=1; }
CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
echo "== 04 preflight =="

PY=".venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] && ok "python: $PY" || bad "python3 nao encontrado (rode 03 ou instale python3)"

# plat resolve o motor Linux
if [ -n "$PY" ]; then
  "$PY" -c "import sys; sys.path.insert(0,'app'); import plat; print('  motor resolvido:', plat.engine_exe('.', 'cpu','llama-server'))" \
    && ok "plat.py resolve o caminho do motor" || bad "plat.py falhou (app/plat.py existe?)"
fi

# binarios
have=0
for b in cpu cuda; do
  if   [ -x "linux/engine/$b/llama-server" ]; then ok "motor $b executavel"; have=1
  elif [ -f "linux/engine/$b/llama-server" ]; then bad "motor $b existe SEM +x (rode 01)"
  fi
done
[ "$have" = 1 ] || bad "nenhum llama-server executavel (rode 02)"
# testa se roda de fato (pega .so faltando)
if [ -x "linux/engine/cpu/llama-server" ]; then
  LD_LIBRARY_PATH="$ROOT/linux/engine/cpu:${LD_LIBRARY_PATH:-}" linux/engine/cpu/llama-server --version >/dev/null 2>&1 \
    && ok "llama-server (cpu) executa" || bad "llama-server (cpu) NAO executa (falta .so? use 02 --build)"
fi

# libs de publicacao (opcional)
if [ -n "$PY" ] && "$PY" -c "import docx,ebooklib,lxml,pypdf" 2>/dev/null; then ok "libs de publicacao ok"; else echo "  (-) libs de publicacao ausentes (rode 03) — chat/analise funcionam sem elas"; fi

if [ "$fail" != 0 ]; then echo "${R}Corrija os itens [X] acima e rode de novo.${N}"; exit 1; fi
echo "${G}Preflight OK.${N}"

if [ "$CHECK" = 1 ]; then echo "(--check: nao iniciei o servidor)"; exit 0; fi
echo "== iniciando NUCLEO (Ctrl+C para parar) =="
exec "$ROOT/linux/nucleo.sh"
