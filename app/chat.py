#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
import plat


def abs_path(v):
    p = Path(v)
    return p if p.is_absolute() else ROOT / p


def supports(cli, option):
    try:
        p = subprocess.run(
            [str(cli), "--help"], cwd=str(cli.parent),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20
        )
        return option in (p.stdout + "\n" + p.stderr)
    except Exception:
        return False


def build_cmd(profile, backend_override=None):
    backend = backend_override or profile.get("backend", "cpu")
    if backend == "cuda":
        cli = plat.engine_exe(ROOT, "cuda", "llama-cli")
        ngl = int(profile.get("gpu_layers", 0))
    else:
        cli = plat.engine_exe(ROOT, "cpu", "llama-cli")
        ngl = 0

    model = abs_path(profile["model"])
    threads = int(
        profile.get("cpu_threads")
        if backend == profile.get("backend")
        else profile.get("fallback_cpu_threads", profile.get("cpu_threads", 4))
    )

    config_dir = ROOT / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    sysfile = config_dir / "system_runtime_v0_5.txt"
    sysfile.write_text(
        f"""Você é o assistente local do produto NÚCLEO IA PORTÁTIL.
Responda em português do Brasil por padrão.
Modo atual: {profile.get('mode_name', 'LOCAL')}.
Modelo-base: {model.name}.
Backend atual: {backend.upper()}.
Diferencie sempre produto e modelo-base.
Não exponha cadeia de pensamento, rascunhos ou blocos Start thinking/End thinking.
Seja claro, objetivo e tecnicamente correto.
""", encoding="utf-8"
    )

    cmd = [
        str(cli), "-m", str(model), "-t", str(threads),
        "-ngl", str(ngl), "-c", str(profile.get("context_size", 4096)),
        "-cnv", "-co", "auto", "-sysf", str(sysfile)
    ]
    if supports(cli, "--reasoning"):
        cmd += ["--reasoning", "off"]
    elif supports(cli, "--chat-template-kwargs"):
        cmd += ["--chat-template-kwargs", '{"enable_thinking":false}']

    return cli, model, backend, threads, ngl, cmd


def launch(profile):
    cli, model, backend, threads, ngl, cmd = build_cmd(profile)

    if not cli.exists():
        print("Motor não encontrado:", cli)
        return 3
    if not model.exists():
        print("Modelo não encontrado:", model)
        return 4

    print("=" * 76)
    print("                 NÚCLEO IA PORTÁTIL — V0.5")
    print("=" * 76)
    print(f"Modo............: {profile.get('mode_name')}")
    print(f"Modelo..........: {model.name}")
    print(f"Backend.........: {backend.upper()}")
    print(f"Threads.........: {threads}")
    print(f"GPU layers......: {ngl}")
    print(f"Contexto........: {profile.get('context_size', 4096)}")
    if profile.get("observed_chat_generation_tps") is not None:
        print(f"Velocidade ref..: ~{profile.get('observed_chat_generation_tps')} t/s")
    if profile.get("observed_vram_headroom_mib") is not None:
        print(f"Folga VRAM ref..: ~{profile.get('observed_vram_headroom_mib')} MiB")
    print("Sair............: /exit ou Ctrl+C")
    print("=" * 76)

    rc = subprocess.call(cmd, cwd=str(cli.parent))

    # Fallback automático somente se CUDA falhar ao carregar/executar.
    if rc != 0 and backend == "cuda":
        print("\nCUDA retornou erro. Tentando fallback automático para CPU...")
        cli2, model2, backend2, threads2, ngl2, cmd2 = build_cmd(profile, "cpu")
        if not cli2.exists():
            print("Motor CPU também não está disponível.")
            return rc
        print(f"Fallback: CPU | threads={threads2} | GPU layers=0")
        return subprocess.call(cmd2, cwd=str(cli2.parent))

    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--mode", choices=["fast", "quality"], required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.profile).read_text(encoding="utf-8-sig"))
    profile = data["modes"][args.mode]
    return launch(profile)


if __name__ == "__main__":
    raise SystemExit(main())
