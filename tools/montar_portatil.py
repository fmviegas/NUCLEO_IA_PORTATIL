#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
montar_portatil.py — Monta uma cópia PORTÁTIL do NÚCLEO IA PORTÁTIL num destino
(ex.: pendrive), copiando SÓ o essencial de operação e deixando de fora tudo que
é de desenvolvimento (backups, histórico, docs, fontes de build, validadores de
versão, __pycache__ etc.).

Uso:
    python tools/montar_portatil.py --dest G:\\NUCLEO_IA_PORTATIL
    python tools/montar_portatil.py --dest G:\\NUCLEO_IA_PORTATIL --modelos fast
    python tools/montar_portatil.py --dest G:\\NUCLEO_IA_PORTATIL --dry-run

Opções:
    --modelos all | fast | min | none
        all  = 4B + 8B + 30B (padrão; ~19 GB)
        fast = 4B + 8B (~7 GB)
        min  = só 4B (~2,4 GB)
        none = não copia modelos (o alvo baixa/instala depois)
    --dry-run   apenas simula: mostra o que copiaria, tamanho total e espaço livre.
    --force     prossegue mesmo com avisos não-críticos (não ignora FAT32/sem espaço).

Segurança:
    - RECUSA copiar se o destino for FAT32 e houver arquivo > 4 GB (limite do FAT32).
      → reformate o pendrive em exFAT (recomendado) ou NTFS.
    - RECUSA se o espaço livre no destino for insuficiente.
    - Nunca apaga nada no destino; apenas cria/atualiza arquivos.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Pastas essenciais copiadas por inteiro (menos os EXCLUDES abaixo).
INCLUDE_DIRS = ["app", "ui", "config", "runtime", "engine", "tools"]

# Arquivos de raiz essenciais (lançadores de operação + versão).
INCLUDE_ROOT_FILES = [
    "VERSION.json",
    "INICIAR_NUCLEO_IA.bat", "CRIAR_LIVRO.bat", "OUTLINE.bat", "ESCREVER.bat",
    "REVISAR.bat", "PUBLICAR_LIVRO.bat", "PLANO_LIVRO.bat", "HUMANIZAR.bat",
    "CALIBRAR_ADVANCED.bat", "SMOKE_MODELO.bat", "VALIDAR_MODELO.bat",
    "RESTAURAR_NVIDIA.bat", "SIMULAR_SEM_NVIDIA.bat",
]

# Pastas de estado/trabalho criadas VAZIAS no destino (o app popula no 1º uso).
CRIAR_VAZIAS = [
    "workspace/livros", "workspace/sessions", "sessions", "logs",
    "cache/downloads", "state", "profiles",
]

# Modelos por tier.
CODER = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
MODELOS = {
    "min":  ["Qwen3-4B-Q4_K_M.gguf"],
    "fast": ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf"],
    "code": ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf", CODER],
    "all":  ["Qwen3-4B-Q4_K_M.gguf", "Qwen3-8B-Q4_K_M.gguf",
             "Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf", CODER],
    "none": [],
}

FAT32_LIMIT = 4 * 1024 ** 3  # 4 GiB por arquivo


def _excluir(rel: str) -> bool:
    """True se o caminho relativo (com '/') deve ser PULADO na cópia."""
    partes = rel.replace("\\", "/").split("/")
    if "__pycache__" in partes:
        return True
    low = rel.replace("\\", "/").lower()
    # backends/arquivos corrompidos ou de backup deixados em engine/ etc.
    if "corrompido" in low or "_bak" in low or ".bak" in low:
        return True
    # dev/obsoleto dentro das pastas incluídas
    if low.startswith("tools/legacy"):
        return True
    if low.startswith("tools/validar_v0_9_"):   # validadores de versão (dev)
        return True
    # NÃO excluir app/manifests/: o autotune.py (calibração) importa
    # app/manifests/manifest_v0_5.json no topo. Sem ele a máquina nova não calibra.
    if low.endswith(".pyc"):
        return True
    return False


def coletar_arquivos(modelos_tier: str):
    """Lista (origem_abs, rel) dos arquivos a copiar + o total em bytes."""
    itens = []
    total = 0
    # pastas essenciais
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
    # arquivos de raiz
    for f in INCLUDE_ROOT_FILES:
        p = ROOT / f
        if p.is_file():
            itens.append((p, f)); total += p.stat().st_size
    # modelos selecionados
    for nome in MODELOS.get(modelos_tier, []):
        p = ROOT / "models" / nome
        if p.is_file():
            itens.append((p, f"models/{nome}")); total += p.stat().st_size
        else:
            print(f"   ⚠ modelo não encontrado (ignorado): {nome}")
    return itens, total


def maior_arquivo(itens):
    return max((p.stat().st_size for p, _ in itens), default=0)


def detectar_fs(dest: Path) -> str | None:
    """Tenta descobrir o sistema de arquivos do destino (Windows/PowerShell)."""
    if os.name != "nt":
        return None
    drive = os.path.splitdrive(str(dest.resolve()))[0]  # ex.: 'G:'
    letra = drive.rstrip(":")
    if not letra:
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Volume -DriveLetter {letra}).FileSystem"],
            capture_output=True, text=True, timeout=15,
        )
        fs = (out.stdout or "").strip()
        return fs or None
    except Exception:
        return None


def human(n: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.1f} {u}"
        n /= 1024


def copiar(itens, dest: Path):
    total = sum(p.stat().st_size for p, _ in itens)
    feito = 0
    grandes = 0
    for i, (src, rel) in enumerate(itens, 1):
        alvo = dest / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        sz = src.stat().st_size
        if sz >= 100 * 1024 ** 2:  # arquivos grandes: avisa individualmente
            grandes += 1
            print(f"   [{human(feito)}/{human(total)}] copiando {rel} ({human(sz)})…", flush=True)
        shutil.copy2(src, alvo)
        feito += sz
    print(f"   [{human(feito)}/{human(total)}] concluído ({len(itens)} arquivos, "
          f"{grandes} grande(s)).")


def montar(dest: Path, modelos_tier: str, dry_run: bool, force: bool) -> int:
    if dest.resolve() == ROOT or ROOT in dest.resolve().parents:
        print("ERRO: o destino não pode ser a própria pasta do NÚCLEO (nem estar dentro dela).")
        return 2

    print("=" * 68)
    print("  MONTAR PORTÁTIL — NÚCLEO IA PORTÁTIL")
    print("=" * 68)
    print(f"Origem : {ROOT}")
    print(f"Destino: {dest}")
    print(f"Modelos: {modelos_tier}  ({', '.join(MODELOS.get(modelos_tier)) or 'nenhum'})")
    print("Coletando lista de arquivos…")

    itens, total = coletar_arquivos(modelos_tier)
    maior = maior_arquivo(itens)
    print(f"Arquivos a copiar: {len(itens)}  ·  total: {human(total)}  ·  "
          f"maior arquivo: {human(maior)}")

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"\n✗ NÃO consegui criar/acessar o destino: {dest}\n   ({e})\n"
              "   Verifique se o pendrive está conectado, com letra correta, "
              "formatado (exFAT/NTFS) e gravável.")
        return 1

    # Espaço livre no destino
    try:
        livre = shutil.disk_usage(dest).free
        print(f"Espaço livre no destino: {human(livre)}")
    except Exception as e:
        livre = None
        print(f"⚠ não consegui medir o espaço livre ({e}).")

    # Sistema de arquivos (FAT32 = veto p/ arquivos > 4 GB)
    fs = detectar_fs(dest)
    print(f"Sistema de arquivos do destino: {fs or 'desconhecido'}")

    problemas = []
    if fs and fs.upper() == "FAT32" and maior >= FAT32_LIMIT:
        problemas.append(
            f"Destino é FAT32 e há arquivo de {human(maior)} (> 4 GB). "
            "FAT32 não suporta arquivos > 4 GB — reformate o pendrive em exFAT (recomendado) ou NTFS."
        )
    if livre is not None and total > livre:
        problemas.append(
            f"Espaço insuficiente: precisa de {human(total)}, livre {human(livre)}."
        )

    if problemas:
        print("\n✗ NÃO É POSSÍVEL COPIAR:")
        for p in problemas:
            print(f"   - {p}")
        return 1

    if fs is None:
        print("⚠ não identifiquei o sistema de arquivos; se for FAT32, a cópia de "
              "modelos > 4 GB vai falhar. Prefira exFAT.")

    if dry_run:
        print("\n[DRY-RUN] Nada foi copiado. Tudo caberia e passaria nas checagens acima.")
        return 0

    print("\nCopiando…")
    copiar(itens, dest)

    # pastas de trabalho vazias
    for d in CRIAR_VAZIAS:
        (dest / d).mkdir(parents=True, exist_ok=True)

    # pré-semear perfis de máquina já calibrados: numa máquina JÁ conhecida a
    # cópia não recalibra (sobe na hora); numa máquina NOVA o machine_id não casa
    # e ela calibra sozinha no 1º uso. Perfis são pequenos (~4 KB cada).
    prof_src = ROOT / "profiles" / "machines"
    if prof_src.is_dir():
        prof_dst = dest / "profiles" / "machines"
        prof_dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for j in prof_src.glob("*.json"):
            shutil.copy2(j, prof_dst / j.name); n += 1
        if n:
            print(f"   perfis de máquina copiados: {n} (mesma máquina não recalibra)")

    # marcador
    from datetime import datetime
    ver = ""
    try:
        import json
        ver = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8-sig")).get("version", "")
    except Exception:
        pass
    (dest / "PORTATIL.txt").write_text(
        "NÚCLEO IA PORTÁTIL — cópia portátil\n"
        f"Versão: {ver}\n"
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"Modelos incluídos: {', '.join(MODELOS.get(modelos_tier)) or 'nenhum'}\n\n"
        "Para usar: rode INICIAR_NUCLEO_IA.bat neste pendrive (Windows com driver "
        "NVIDIA para GPU; sem NVIDIA, cai no modo CPU). Na 1ª vez numa máquina nova, "
        "o NÚCLEO detecta o hardware e calibra automaticamente.\n",
        encoding="utf-8")

    print("\n" + "=" * 68)
    print("  PORTÁTIL MONTADA ✓")
    print("=" * 68)
    print(f"Local: {dest}")
    print("Rode INICIAR_NUCLEO_IA.bat no destino. (1º uso numa máquina nova recalibra.)")
    return 0


def _cli() -> int:
    ap = argparse.ArgumentParser(description="Monta uma cópia portátil do NÚCLEO num destino.")
    ap.add_argument("--dest", required=True, help="pasta destino (ex.: G:\\NUCLEO_IA_PORTATIL)")
    ap.add_argument("--modelos", default="all", choices=list(MODELOS.keys()))
    ap.add_argument("--dry-run", action="store_true", help="só simula (não copia)")
    ap.add_argument("--force", action="store_true", help="prossegue com avisos não-críticos")
    args = ap.parse_args()
    try:
        return montar(Path(args.dest), args.modelos, args.dry_run, args.force)
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
        return 130


if __name__ == "__main__":
    raise SystemExit(_cli())
