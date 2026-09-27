#!/usr/bin/env bash
# 01_preparar.sh — normaliza CRLF, cria pastas de trabalho, aplica +x e conserta o dono.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
echo "== 01 preparar (CRLF + pastas + permissoes) =="

# 1) normaliza fim-de-linha dos .sh (evita 'bad interpreter'/'not found')
for f in linux/*.sh linux/setup/*.sh; do [ -f "$f" ] && sed -i 's/\r$//' "$f"; done
echo "  [ok] fim-de-linha dos .sh normalizado (LF)"

# 2) cria pastas de trabalho (o app popula no 1o uso)
for d in workspace/livros workspace/sessions sessions logs cache/downloads state profiles/machines; do
  mkdir -p "$ROOT/$d"
done
echo "  [ok] pastas de trabalho criadas"

# 3) permissao de execucao em scripts e binarios (se presentes)
chmod +x linux/*.sh linux/setup/*.sh 2>/dev/null || true
chmod +x linux/engine/cpu/llama-* linux/engine/cuda/llama-* 2>/dev/null || true
echo "  [ok] +x aplicado em scripts e binarios do motor"

# 4) se os arquivos forem de root (copia feita com sudo), devolve ao usuario
owner="$(stat -c %U "$ROOT" 2>/dev/null || echo "$USER")"
if [ "$owner" = "root" ] && [ "$(id -u)" != "0" ]; then
  echo "  [..] arquivos pertencem a root; ajustando dono para $USER (pede sudo)…"
  sudo chown -R "$USER:$(id -gn)" "$ROOT" && echo "  [ok] dono ajustado para $USER"
fi

# aviso se o FS nao guarda +x
FS="$(findmnt -no FSTYPE --target "$ROOT" 2>/dev/null || echo '?')"
case "$FS" in
  exfat|vfat|fat*|ntfs*|fuseblk) echo "  [X]  ATENCAO: filesystem $FS NAO mantem o +x. Mova o projeto p/ ext4 (~/NUCLEO).";;
esac

echo "OK 01."
