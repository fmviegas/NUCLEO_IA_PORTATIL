#!/usr/bin/env bash
# 00_diagnostico.sh — checa o ambiente Linux e aponta o que falta/esta errado.
# NAO altera nada. Rode primeiro. Se precisar de ajuda, cole a saida deste script.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
if [ -t 1 ]; then G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; N=$'\e[0m'; else G=; Y=; R=; N=; fi
ok(){   echo "  ${G}[OK]${N} $1"; }
warn(){ echo "  ${Y}[!]${N}  $1"; }
bad(){  echo "  ${R}[X]${N}  $1"; }

echo "======================================================================"
echo "  NUCLEO IA PORTATIL — DIAGNOSTICO LINUX"
echo "======================================================================"
echo "Projeto: $ROOT"
if [ -r /etc/os-release ]; then . /etc/os-release; echo "SO: ${PRETTY_NAME:-?}  |  kernel $(uname -r)  |  $(uname -m)"; fi
echo "----------------------------------------------------------------------"

if [ "$(id -u)" = "0" ]; then warn "rodando como ROOT — prefira usuario normal (senao os arquivos ficam do root)"; else ok "usuario normal: $(whoami)"; fi

# FILESYSTEM (causa #1 de 'permission'/'link nao encontrado')
FS="$(findmnt -no FSTYPE --target "$ROOT" 2>/dev/null || stat -f -c %T "$ROOT" 2>/dev/null || echo '?')"
case "$FS" in
  ext4|ext3|ext2|btrfs|xfs|zfs) ok "filesystem do projeto: $FS (guarda permissoes e links)";;
  exfat|vfat|fat*|msdos|ntfs*|fuseblk)
     bad "filesystem do projeto: $FS — NAO guarda bit de execucao nem symlink!"
     echo "         >> ISSO causa 'Permission denied' e 'link nao encontrado'."
     echo "         >> MOVA o projeto p/ ext4:  cp -a \"$ROOT\" ~/NUCLEO && cd ~/NUCLEO";;
  *) warn "filesystem do projeto: $FS (se for exFAT/NTFS, mova p/ ext4)";;
esac

# estrutura do projeto presente?
[ -f app/server.py ] && ok "app/server.py presente" || bad "app/server.py AUSENTE — a copia do projeto nao esta completa aqui"
[ -f linux/nucleo.sh ] && ok "linux/nucleo.sh presente" || bad "linux/nucleo.sh AUSENTE — copie a pasta linux/ do projeto"

# python / ferramentas
if command -v python3 >/dev/null; then ok "python3: $(python3 --version 2>&1)"; else bad "python3 AUSENTE -> sudo apt install -y python3 python3-venv python3-pip"; fi
python3 -c 'import venv' 2>/dev/null && ok "modulo venv presente" || warn "modulo venv ausente -> sudo apt install -y python3-venv"
command -v unzip >/dev/null && ok "unzip presente" || warn "unzip ausente (p/ 02 baixar) -> sudo apt install -y unzip"

# GPU
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU="$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)"
  ok "GPU NVIDIA: ${GPU:-detectada}  (modo CUDA possivel)"
  command -v nvcc >/dev/null 2>&1 && ok "nvcc presente (da p/ compilar CUDA)" || warn "nvcc ausente — so' importa se for COMPILAR CUDA (02 --build --cuda)"
else
  warn "sem nvidia-smi — vai rodar em CPU (funciona, so' mais lento)"
fi

# CRLF nos .sh (causa #2)
CRLF=0
for f in linux/*.sh linux/setup/*.sh; do
  [ -f "$f" ] && grep -lq $'\r' "$f" 2>/dev/null && { CRLF=1; warn "CRLF (Windows) em $f -> rode 01"; }
done
[ "$CRLF" = 0 ] && ok "scripts .sh sem CRLF"

# motor
for b in cpu cuda; do
  d="linux/engine/$b"
  if   [ -x "$d/llama-server" ]; then ok "motor $b: llama-server presente e executavel"
  elif [ -f "$d/llama-server" ]; then warn "motor $b: llama-server existe mas SEM +x -> rode 01"
  else warn "motor $b: llama-server AUSENTE -> rode 02"; fi
done

# venv + libs
if [ -x ".venv/bin/python" ]; then
  ok ".venv presente"
  for m in docx ebooklib lxml pypdf; do
    .venv/bin/python -c "import $m" 2>/dev/null && ok "  lib $m ok" || warn "  lib $m ausente -> rode 03"
  done
else
  warn ".venv ausente -> rode 03 (chat/analise rodam sem ela; publicar precisa)"
fi

# pastas de trabalho
miss=""
for d in workspace/livros sessions logs cache/downloads state profiles/machines; do [ -d "$d" ] || miss="$miss $d"; done
[ -z "$miss" ] && ok "pastas de trabalho ok" || warn "faltam pastas ->$miss  (rode 01)"

echo "======================================================================"
echo "  fim do diagnostico"
echo "======================================================================"
