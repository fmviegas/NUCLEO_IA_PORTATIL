#!/usr/bin/env bash
# 02_binarios.sh — coloca os binarios Linux do llama.cpp em linux/engine/{cpu,cuda}/.
#   ./02_binarios.sh              -> BAIXA a build CPU do release oficial (rapido)
#   ./02_binarios.sh --build      -> COMPILA a CPU do fonte (mais confiavel)
#   ./02_binarios.sh --build --cuda -> COMPILA CPU + CUDA (precisa driver + nvcc)
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
MODE="download"; CUDA=0
for a in "$@"; do case "$a" in --build) MODE="build";; --cuda) CUDA=1;; esac; done

copiar(){ # $1=pasta-origem  $2=backend(cpu|cuda)
  mkdir -p "linux/engine/$2"
  for b in llama-server llama-cli llama-bench; do
    f="$(find "$1" -type f -name "$b" 2>/dev/null | head -1)"
    [ -n "$f" ] && install -m 0755 "$f" "linux/engine/$2/$b" && echo "    -> $2/$b"
  done
  # .so acompanhantes (libllama/libggml) ficam junto do binario
  find "$1" -type f -name "*.so*" -exec cp -f {} "linux/engine/$2/" \; 2>/dev/null || true
}

if [ "$MODE" = "download" ]; then
  echo "== 02 baixar binarios CPU (release oficial ggml-org/llama.cpp) =="
  command -v unzip >/dev/null || { echo "instale: sudo apt install -y unzip"; exit 1; }
  if   command -v curl >/dev/null; then DL(){ curl -fsSL "$1"; }; DLO(){ curl -fsSL "$1" -o "$2"; }
  elif command -v wget >/dev/null; then DL(){ wget -qO- "$1"; }; DLO(){ wget -q "$1" -O "$2"; }
  else echo "instale curl ou wget"; exit 1; fi
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  echo "  procurando asset CPU Ubuntu x64 no ultimo release…"
  URL="$(DL https://api.github.com/repos/ggml-org/llama.cpp/releases/latest | python3 -c '
import sys,json
d=json.load(sys.stdin); u=""
for a in d.get("assets",[]):
    n=a["name"].lower()
    if n.endswith(".zip") and "ubuntu" in n and ("x64" in n or "amd64" in n) and "cuda" not in n and "vulkan" not in n and "arm" not in n:
        u=a["browser_download_url"]; break
print(u)')"
  if [ -z "$URL" ]; then
    echo "  nao achei asset CPU pronto. Compile:  ./linux/setup/02_binarios.sh --build"
    exit 2
  fi
  echo "  baixando: $URL"
  DLO "$URL" "$TMP/cpu.zip"
  unzip -oq "$TMP/cpu.zip" -d "$TMP/cpu"
  copiar "$TMP/cpu" cpu
  echo "  CPU pronto. Para GPU:  ./linux/setup/02_binarios.sh --build --cuda"
  echo "OK 02 (download)."
else
  echo "== 02 compilar llama.cpp do fonte (CPU$( [ "$CUDA" = 1 ] && echo ' + CUDA' )) =="
  echo "  instalando dependencias (sudo apt)…"
  sudo apt-get update -y
  sudo apt-get install -y build-essential cmake git libcurl4-openssl-dev
  SRC="$ROOT/cache/llama.cpp-src"
  if [ -d "$SRC/.git" ]; then git -C "$SRC" pull --ff-only || true; else git clone --depth 1 https://github.com/ggml-org/llama.cpp "$SRC"; fi
  echo "  compilando CPU…"
  cmake -S "$SRC" -B "$SRC/build-cpu" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
  cmake --build "$SRC/build-cpu" -j"$(nproc)" --target llama-server llama-cli llama-bench
  copiar "$SRC/build-cpu" cpu
  if [ "$CUDA" = 1 ]; then
    command -v nvcc >/dev/null 2>&1 || echo "  AVISO: nvcc ausente — instale o CUDA toolkit (ex.: sudo apt install -y nvidia-cuda-toolkit) e rode de novo."
    echo "  compilando CUDA…"
    cmake -S "$SRC" -B "$SRC/build-cuda" -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
    cmake --build "$SRC/build-cuda" -j"$(nproc)" --target llama-server llama-cli llama-bench
    copiar "$SRC/build-cuda" cuda
  fi
  echo "OK 02 (build)."
fi
