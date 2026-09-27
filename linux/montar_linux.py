#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
montar_linux.py — Monta a arvore LINUX portatil do NUCLEO IA PORTATIL num destino.

Copia SO' o multiplataforma (app, ui, config, tools, models) + a pasta linux/ inteira
(motor Linux, lancadores .sh, guia) e EXCLUI o que e' Windows (engine/windows,
runtime/python, *.bat, *.dll, *.exe, *.ps1, validadores de versao, __pycache__).
Cria as pastas de trabalho vazias, pre-semeia perfis e escreve um marcador.

Rode preferencialmente NO LINUX (o destino costuma ser uma particao ext4 do SSD, que o
Windows nao grava). Tambem roda no Windows para preparar numa area exFAT de staging.

Uso:
    python3 linux/montar_linux.py --dest /media/voce/SSD/NUCLEO_IA_PORTATIL --modelos all
    python3 linux/montar_linux.py --dest /mnt/ssd/NUCLEO --modelos fast --dry-run

--modelos all | code | fast | min | none   (mesmos tiers do montar_portatil.py)

Este script apenas MONTA os arquivos; nao inicia nada. A arvore so' RODA depois de:
  1) binarios Linux do llama.cpp em linux/engine/{cpu,cuda}/  (ver LEIA-ME.txt)
  2) .venv com as 4 libs (docx/ebooklib/lxml/pypdf)
Ver linux/PORTATIL_LINUX.md.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # linux/montar_linux.py -> raiz do projeto

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Pastas copiadas por inteiro (menos os EXCLUDES). 'linux' traz motor+.sh+guia.
INCLUDE_DIRS = ["app", "ui", "config", "tools", "linux"]

# Pastas de estado/trabalho criadas VAZIAS no destino.
CRIAR_VAZIAS = [
    "workspace/livros", "workspace/sessions", "sessions", "logs",
    "cache/downloads", "state", "profiles/machines",
]

CODER = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
MODELOS = {
    "min":  ["Qwen3-4B-Q4_K_M.gguf"],
    "fast": ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf"],
    "code": ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf", CODER],
    "all":  ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf",
             "Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf", CODER],
    "none": [],
}


def _excluir(rel: str) -> bool:
    low = rel.replace("\\", "/").lower()
    partes = low.split("/")
    if "__pycache__" in partes:
        return True
    if low.endswith((".pyc", ".bat", ".ps1", ".dll", ".exe")):
        return True
    if "corrompido" in low or "_bak" in low or ".bak" in low:
        return True
    if low.startswith("tools/legacy"):
        return True
    if low.startswith("tools/validar_v0_9_"):   # validadores de versao (dev)
        return True
    if low == "tools/montar_portatil.py":        # montador do Windows nao vai p/ Linux
        return True
    return False


def coletar(modelos_tier: str):
    itens, total = [], 0
    for d in INCLUDE_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if _excluir(rel):
                continue
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            itens.append((p, rel)); total += sz
    for f in ("VERSION.json", "BIBLIA_NUCLEO_IA_PORTATIL.md"):
        p = ROOT / f
        if p.is_file():
            itens.append((p, f)); total += p.stat().st_size
    for nome in MODELOS.get(modelos_tier, []):
        p = ROOT / "models" / nome
        if p.is_file():
            itens.append((p, f"models/{nome}")); total += p.stat().st_size
        else:
            print(f"   AVISO modelo nao encontrado (ignorado): {nome}")
    return itens, total


def human(n: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f} {u}"
        n /= 1024


def montar(dest: Path, modelos_tier: str, dry_run: bool) -> int:
    if dest.resolve() == ROOT or ROOT in dest.resolve().parents:
        print("ERRO: destino nao pode ser a propria pasta do NUCLEO (nem dentro dela).")
        return 2

    print("=" * 68)
    print("  MONTAR LINUX — NUCLEO IA PORTATIL")
    print("=" * 68)
    print(f"Origem : {ROOT}")
    print(f"Destino: {dest}")
    print(f"Modelos: {modelos_tier}  ({', '.join(MODELOS.get(modelos_tier)) or 'nenhum'})")
    print("Coletando lista de arquivos...")

    itens, total = coletar(modelos_tier)
    maior = max((p.stat().st_size for p, _ in itens), default=0)
    print(f"Arquivos a copiar: {len(itens)}  ·  total: {human(total)}  ·  "
          f"maior: {human(maior)}")

    tem_bin = any(rel.startswith("linux/engine/") and Path(rel).name in
                  ("llama-server", "llama-cli", "llama-bench") for _, rel in itens)
    if not tem_bin:
        print("   AVISO: linux/engine/ ainda nao tem binarios (llama-server/cli/bench).")
        print("          A copia funciona, mas so' RODA depois de coloca-los (ver LEIA-ME.txt).")

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"\nX NAO consegui criar/acessar o destino: {dest}\n   ({e})")
        return 1

    try:
        livre = shutil.disk_usage(dest).free
        print(f"Espaco livre no destino: {human(livre)}")
        if total > livre:
            print(f"\nX Espaco insuficiente: precisa {human(total)}, livre {human(livre)}.")
            return 1
    except Exception as e:
        print(f"AVISO nao medi o espaco livre ({e}).")

    if dry_run:
        print("\n[DRY-RUN] Nada foi copiado. Passaria nas checagens acima.")
        return 0

    print("\nCopiando...")
    feito = 0
    for src, rel in itens:
        alvo = dest / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        sz = src.stat().st_size
        if sz >= 100 * 1024 ** 2:
            print(f"   [{human(feito)}/{human(total)}] {rel} ({human(sz)})...", flush=True)
        shutil.copy2(src, alvo)
        feito += sz
    print(f"   [{human(feito)}/{human(total)}] concluido ({len(itens)} arquivos).")

    for d in CRIAR_VAZIAS:
        (dest / d).mkdir(parents=True, exist_ok=True)

    prof_src = ROOT / "profiles" / "machines"
    if prof_src.is_dir():
        prof_dst = dest / "profiles" / "machines"
        prof_dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for j in prof_src.glob("*.json"):
            shutil.copy2(j, prof_dst / j.name); n += 1
        if n:
            print(f"   perfis de maquina copiados: {n}")

    # bit de execucao nos .sh e nos binarios do motor (se ja existirem)
    import os as _os
    import stat as _stat
    for alvo in list((dest / "linux").glob("*.sh")) + \
                list((dest / "linux" / "engine").rglob("llama-*")):
        try:
            _os.chmod(alvo, _os.stat(alvo).st_mode | _stat.S_IXUSR | _stat.S_IXGRP | _stat.S_IXOTH)
        except OSError:
            pass

    ver = ""
    try:
        import json
        ver = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8-sig")).get("version", "")
    except Exception:
        pass
    (dest / "PORTATIL_LINUX.txt").write_text(
        "NUCLEO IA PORTATIL — copia portatil LINUX\n"
        f"Versao base: {ver}\n"
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"Modelos: {', '.join(MODELOS.get(modelos_tier)) or 'nenhum'}\n\n"
        "Para usar:\n"
        "  1) Coloque binarios Linux do llama.cpp em linux/engine/{cpu,cuda}/ (ver LEIA-ME.txt).\n"
        "  2) python3 -m venv .venv && . .venv/bin/activate && pip install \\\n"
        "       'python-docx>=1.2.0' 'ebooklib>=0.20' lxml 'pypdf>=6.18'\n"
        "  3) chmod +x linux/*.sh linux/engine/*/llama-*\n"
        "  4) ./linux/nucleo.sh   (1a vez numa maquina nova recalibra a base sozinha)\n",
        encoding="utf-8")

    print("\n" + "=" * 68)
    print("  ARVORE LINUX MONTADA")
    print("=" * 68)
    print(f"Local: {dest}")
    print("Leia PORTATIL_LINUX.txt no destino para os passos finais. (Nada foi iniciado.)")
    return 0


def _cli() -> int:
    ap = argparse.ArgumentParser(description="Monta a arvore Linux portatil do NUCLEO.")
    ap.add_argument("--dest", required=True, help="pasta destino no Linux (ex.: /media/voce/SSD/NUCLEO)")
    ap.add_argument("--modelos", default="all", choices=list(MODELOS.keys()))
    ap.add_argument("--dry-run", action="store_true", help="so' simula (nao copia)")
    args = ap.parse_args()
    try:
        return montar(Path(args.dest), args.modelos, args.dry_run)
    except KeyboardInterrupt:
        print("\nCancelado pelo usuario.")
        return 130


if __name__ == "__main__":
    raise SystemExit(_cli())
