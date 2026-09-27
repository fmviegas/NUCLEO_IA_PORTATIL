#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plat.py — Camada de resolucao do MOTOR (llama.cpp) por sistema operacional.

Fonte unica para onde ficam os binarios e qual o sufixo do executavel, para que o
mesmo codigo rode em Windows e em Linux sem espalhar caminhos fixos.

Layout dos binarios:
    Windows :  <root>/engine/windows/<backend>/llama-<nome>.exe   (identico a' V0.9.20)
    Linux   :  <root>/linux/engine/<backend>/llama-<nome>          (sem sufixo)

<backend> = "cpu" | "cuda"
<nome>    = "server" | "cli" | "bench"   (uso: engine_exe(root, backend, "llama-server"))

No Windows o resultado e' BYTE-A-BYTE o mesmo caminho de antes desta camada; portanto
aplicar plat.py nao altera o comportamento da versao Windows.
"""
from __future__ import annotations

import os
from pathlib import Path

# True no Windows; False em Linux/macOS.
IS_WINDOWS = (os.name == "nt")

# Identificador de SO usado em mensagens/paths logicos.
SO = "windows" if IS_WINDOWS else "linux"

# Sufixo do executavel do motor.
EXE_SUFFIX = ".exe" if IS_WINDOWS else ""


def engine_root(root) -> Path:
    """Pasta-base do motor para o SO atual.
    Windows: <root>/engine/windows   ·   Linux: <root>/linux/engine
    """
    root = Path(root)
    if IS_WINDOWS:
        return root / "engine" / "windows"
    return root / "linux" / "engine"


def engine_dir(root, backend: str) -> Path:
    """Pasta do backend ('cpu' | 'cuda') para o SO atual."""
    return engine_root(root) / backend


def engine_exe(root, backend: str, nome: str) -> Path:
    """Caminho absoluto do binario do motor.

    `nome` e' o nome SEM sufixo, ex.: 'llama-server', 'llama-cli', 'llama-bench'.
    """
    return engine_dir(root, backend) / (nome + EXE_SUFFIX)


def engine_exe_rel(root, backend: str, nome: str) -> str:
    """Mesmo que engine_exe, porem relativo a' `root` e em barras POSIX
    (para gravar em perfis/JSON de forma estavel e portavel)."""
    try:
        return engine_exe(root, backend, nome).relative_to(Path(root)).as_posix()
    except ValueError:
        return engine_exe(root, backend, nome).as_posix()


def engine_bin_names():
    """Nomes dos tres binarios do motor JA' com o sufixo do SO atual
    (para checagens de presenca/manutencao)."""
    s = EXE_SUFFIX
    return [f"llama-server{s}", f"llama-cli{s}", f"llama-bench{s}"]
