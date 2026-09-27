#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))

import hardware as core

PROFILES = ROOT / "profiles" / "machines"
MANIFEST = json.loads(
    (APP_DIR / "manifests" / "manifest_v0_5.json").read_text(encoding="utf-8-sig")
)

DISPLAY_MODE = {"fast": "RÁPIDO", "quality": "QUALIDADE"}


def safe_exists(path: Path):
    try:
        return path.exists(), None
    except OSError as exc:
        return False, exc


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def nvidia_memory():
    exe = shutil.which("nvidia-smi.exe") or shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        p = subprocess.run(
            [exe, "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=8
        )
        vals = []
        for line in p.stdout.splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 2:
                try:
                    vals.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass
        return max(vals, key=lambda x: x[1]) if vals else None
    except Exception:
        return None


def storage_issue(path: Path, exc: OSError):
    code = getattr(exc, "winerror", None)
    if code == 1392:
        return f"arquivo ilegível (Windows 1392): {path.name}"
    return f"erro de armazenamento em {path.name}: {exc}"


def mode_health(mode):
    issues = []

    model = ROOT / mode["model"]
    ok, err = safe_exists(model)
    if not ok:
        issues.append(storage_issue(model, err) if err else "modelo ausente")

    if mode.get("backend") == "cuda":
        cli = ROOT / "engine/windows/cuda/llama-cli.exe"
        ok, err = safe_exists(cli)
        if not ok:
            issues.append(storage_issue(cli, err) if err else "motor CUDA ausente")

        mem = nvidia_memory()
        required = mode.get("observed_vram_used_mib")
        reserve = MANIFEST["policy"]["minimum_vram_headroom_mib"]
        if mem and required:
            used_now, total = mem
            if total - used_now < float(required) + reserve:
                issues.append("VRAM ocupada por outros programas")
    else:
        cli = ROOT / "engine/windows/cpu/llama-cli.exe"
        ok, err = safe_exists(cli)
        if not ok:
            issues.append(storage_issue(cli, err) if err else "motor CPU ausente")

    return issues


def print_mode(name, mode):
    issues = mode_health(mode)
    status = "OK" if not issues else "ATENÇÃO: " + ", ".join(issues)
    tps = mode.get("observed_chat_generation_tps") or mode.get("generation_tps")
    print(f"{name:<10} {Path(mode['model']).name:<25} ~{tps} t/s | {status}")


def run_chat(profile_path, mode):
    return subprocess.call(
        [sys.executable, str(APP_DIR / "chat.py"),
         "--profile", str(profile_path), "--mode", mode],
        cwd=str(ROOT)
    )


def recalibrate():
    print("\nA calibração usa CPU/GPU intensamente por alguns minutos.")
    ans = input("Continuar? [s/N]: ").strip().lower()
    if ans not in ("s", "sim", "y", "yes"):
        return False
    rc = subprocess.call([sys.executable, str(APP_DIR / "autotune.py")], cwd=str(ROOT))
    return rc == 0


def main():
    if os.name != "nt":
        print("A versão consolidada V0.5 está calibrada para Windows x64.")
        return 2

    print("Detectando computador...")
    try:
        hw = core.detect_windows()
        mid = core.machine_id(hw)
    except OSError as exc:
        print("\nERRO DE ARMAZENAMENTO/HARDWARE")
        print(str(exc))
        return 10

    profile_path = PROFILES / f"{mid}.json"

    if not profile_path.exists():
        print("\nNova máquina detectada.")
        print("Machine ID:", mid)
        print("CPU:", hw.cpu)
        print(f"RAM: {hw.ram_total_gb:.2f} GB")
        print("\nNenhum perfil V0.5 encontrado.")
        ans = input("Executar calibração automática agora? [S/n]: ").strip().lower()
        if ans not in ("", "s", "sim", "y", "yes"):
            return 0
        if not recalibrate():
            print("Não foi possível criar o perfil.")
            return 3

    while True:
        try:
            profile = load_json(profile_path)
        except Exception as exc:
            print("\nNão foi possível ler o perfil desta máquina:")
            print(exc)
            return 11

        modes = profile.get("modes", {})
        auto = profile.get("recommended_auto", "fast")

        print("\n" + "=" * 82)
        print("              NÚCLEO IA PORTÁTIL — V0.5 CONSOLIDADA")
        print("=" * 82)
        print(f"Computador......: {hw.manufacturer} {hw.model}")
        print(f"Machine ID......: {mid}")
        print(f"CPU.............: {hw.cpu}")
        print(f"RAM.............: {hw.ram_total_gb:.2f} GB")
        for g in hw.gpus:
            if g.vendor == "NVIDIA":
                print(f"GPU.............: {g.name} ({g.vram_gb:.2f} GB)")
        print()

        if "fast" in modes:
            print_mode("RÁPIDO", modes["fast"])
        if "quality" in modes:
            print_mode("QUALIDADE", modes["quality"])

        print(f"AUTO recomenda.: {DISPLAY_MODE.get(auto, auto.upper())}")
        print("-" * 82)
        print("[1] Iniciar modo RÁPIDO")
        print("[2] Iniciar modo QUALIDADE")
        print("[3] Iniciar modo AUTO")
        print("[4] Recalibrar esta máquina")
        print("[5] Informações do perfil")
        print("[6] Sair")

        op = input("\n> ").strip()

        if op == "1":
            if "fast" not in modes:
                print("Modo RÁPIDO indisponível.")
                continue
            issues = mode_health(modes["fast"])
            if issues:
                print("\nNão é seguro iniciar o modo RÁPIDO:")
                for x in issues:
                    print(" -", x)
                continue
            run_chat(profile_path, "fast")

        elif op == "2":
            if "quality" not in modes:
                print("Modo QUALIDADE indisponível.")
                continue
            issues = mode_health(modes["quality"])
            if issues:
                print("\nAviso:", ", ".join(issues))
                ans = input("Iniciar mesmo assim? [s/N]: ").strip().lower()
                if ans not in ("s", "sim", "y", "yes"):
                    continue
            run_chat(profile_path, "quality")

        elif op == "3":
            chosen = auto if auto in modes else (
                "fast" if "fast" in modes else next(iter(modes))
            )
            issues = mode_health(modes[chosen])
            if issues and chosen != "fast" and "fast" in modes:
                print("\nAUTO detectou restrição no modo QUALIDADE; usando RÁPIDO.")
                chosen = "fast"
                issues = mode_health(modes[chosen])
            if issues:
                print("\nAUTO não encontrou um perfil seguro:")
                for x in issues:
                    print(" -", x)
                continue
            run_chat(profile_path, chosen)

        elif op == "4":
            if recalibrate():
                print("Perfil atualizado.")

        elif op == "5":
            print(json.dumps(profile, indent=2, ensure_ascii=False))
            input("\nEnter para voltar...")

        elif op == "6":
            print("\nEncerrando.")
            return 0

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
        raise SystemExit(130)
