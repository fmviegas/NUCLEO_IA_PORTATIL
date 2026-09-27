#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))

import hardware as core
import catalog as cat
import plat

MANIFEST = json.loads((APP_DIR / "manifests" / "manifest_v0_5.json").read_text(encoding="utf-8-sig"))
POLICY = MANIFEST["policy"]
PROFILES = ROOT / "profiles" / "machines"
CONFIG = ROOT / "state" / "calibration"
PROBES = ROOT / "state" / "probes"
LOGS = ROOT / "logs" / "autotune"

for d in (PROFILES, CONFIG, PROBES, LOGS):
    d.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


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
        rows = []
        for line in p.stdout.splitlines():
            vals = [x.strip() for x in line.split(",")]
            if len(vals) >= 2:
                try:
                    rows.append((float(vals[0]), float(vals[1])))
                except ValueError:
                    pass
        return max(rows, key=lambda x: x[1]) if rows else None
    except Exception:
        return None


def supports(cli: Path, option: str):
    try:
        p = subprocess.run(
            [str(cli), "--help"], cwd=str(cli.parent),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20
        )
        return option in (p.stdout + "\n" + p.stderr)
    except Exception:
        return False


def parse_generation_tps(text: str):
    patterns = [
        r"eval time\s*=\s*[\d.]+\s*ms\s*/\s*\d+\s*tokens.*?\(\s*([\d.]+)\s*tokens per second\s*\)",
        r"generation[^0-9]*([\d.]+)\s*(?:t/s|tokens per second)",
    ]
    for pat in patterns:
        vals = re.findall(pat, text, flags=re.I | re.S)
        if vals:
            try:
                return float(vals[-1])
            except ValueError:
                pass
    return None


def real_chat_probe(cli: Path, model: Path, threads: int, gpu_layers: int,
                    context_size: int, model_key: str, mmproj: Path | None = None):
    before = nvidia_memory()
    samples = []
    stop = threading.Event()

    cmd = [
        str(cli), "-m", str(model),
        "-t", str(threads),
        "-ngl", str(gpu_layers),
        "-c", str(context_size),
        "-p",
        "Explique em poucas frases por que uma GPU acelera a inferencia de IA local.",
        "-n", str(POLICY["minimum_chat_probe_tokens"]),
    ]
    # Modo VISAO: carrega o projetor multimodal na sonda tambem, para que a
    # amostragem de VRAM ja conte o encoder de imagem, nao so os pesos do LLM.
    if mmproj and supports(cli, "--mmproj"):
        cmd += ["--mmproj", str(mmproj)]
    if supports(cli, "--reasoning"):
        cmd += ["--reasoning", "off"]

    # NUCLEO_V0622_SINGLE_TURN
    # A sonda mede uma única resposta e deve encerrar imediatamente.
    if supports(cli, "--single-turn"):
        cmd += ["--single-turn"]
    elif supports(cli, "-st"):
        cmd += ["-st"]

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    proc = subprocess.Popen(
        cmd, cwd=str(cli.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        creationflags=flags
    )

    def sampler():
        while not stop.is_set():
            m = nvidia_memory()
            if m:
                samples.append(m)
            stop.wait(0.35)

    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    try:
        out, err = proc.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        code = 124
    else:
        code = proc.returncode
    finally:
        stop.set()
        t.join(timeout=3)

    combined = (out or "") + "\n" + (err or "")
    (LOGS / f"probe_{model_key}_ngl{gpu_layers}.log").write_text(
        combined, encoding="utf-8", errors="replace"
    )

    peak_used = max((x[0] for x in samples), default=(before[0] if before else None))
    total = max((x[1] for x in samples), default=(before[1] if before else None))
    headroom = (total - peak_used) if total is not None and peak_used is not None else None
    tps = parse_generation_tps(combined)

    return {
        "exit_code": code,
        "success": code == 0,
        "gpu_layers": gpu_layers,
        "generation_tps": tps,
        "peak_vram_used_mib": round(peak_used, 1) if peak_used is not None else None,
        "vram_total_mib": round(total, 1) if total is not None else None,
        "vram_headroom_mib": round(headroom, 1) if headroom is not None else None,
    }


def stabilize_mode(model_key: str, benchmark_mode: dict, spec: dict, hw):
    profile = dict(benchmark_mode["chosen_profile"])
    profile["benchmark_peak_gpu_layers"] = profile.get("gpu_layers", 0)
    profile["benchmark_peak_generation_tps"] = profile.get("generation_tps")
    profile["profile_kind"] = "chat_stable"
    profile["autotune_version"] = "0.5"

    if profile.get("backend") != "cuda" or not hw.nvidia_driver_ok:
        profile["gpu_layers"] = 0
        profile["backend"] = "cpu"
        profile["stability_reason"] = "CUDA indisponivel; CPU selecionada."
        return profile, []

    cli = plat.engine_exe(ROOT, "cuda", "llama-cli")
    model = ROOT / profile["model"]
    start_layers = int(profile.get("gpu_layers", 0))
    layers = start_layers
    probes = []
    benchmark_tps = float(profile.get("generation_tps") or 0.0)

    while layers > 0:
        print(f"  Sonda real {model_key.upper()} - {layers} GPU layers...")
        probe = real_chat_probe(
            cli, model, int(profile["cpu_threads"]), layers,
            int(profile.get("context_size") or POLICY["chat_context_size"]),
            model_key
        )
        probes.append(probe)

        headroom_ok = (
            probe["vram_headroom_mib"] is None or
            probe["vram_headroom_mib"] >= POLICY["minimum_vram_headroom_mib"]
        )
        speed_ok = (
            probe["generation_tps"] is None or benchmark_tps <= 0 or
            probe["generation_tps"] >= benchmark_tps * POLICY["cuda_speed_floor_vs_benchmark"]
        )

        if probe["success"] and headroom_ok and speed_ok:
            profile["gpu_layers"] = layers
            if probe["generation_tps"] is not None:
                profile["observed_chat_generation_tps"] = probe["generation_tps"]
            profile["observed_vram_used_mib"] = probe["peak_vram_used_mib"]
            profile["observed_vram_total_mib"] = probe["vram_total_mib"]
            profile["observed_vram_headroom_mib"] = probe["vram_headroom_mib"]
            profile["stability_reason"] = "Sonda real aprovada com margem de VRAM."
            return profile, probes

        layers -= int(POLICY["layer_backoff_step"])

    # Se nenhuma configuração CUDA ficou estável, cai para CPU.
    profile["backend"] = "cpu"
    profile["gpu_layers"] = 0
    profile["llama_cli"] = plat.engine_exe_rel(ROOT, "cpu", "llama-cli")
    profile["stability_reason"] = "CUDA sem perfil estavel; fallback CPU."
    return profile, probes


def main():
    print("=" * 78)
    print("         NÚCLEO IA PORTÁTIL — AUTOTUNE ESTÁVEL V0.5")
    print("=" * 78)
    print(f"SO: {plat.SO}. Nova máquina: benchmark + sonda de chat real + margem de VRAM.")
    print()

    hw = core.detect_safe()
    mid = core.machine_id(hw)
    print("Machine ID:", mid)
    print("CPU:", hw.cpu)
    print(f"RAM: {hw.ram_total_gb:.2f} GB")

    benchmark_script = APP_DIR / "benchmark.py"
    comparison_path = CONFIG / "comparison_v0_4.json"

    # Reutiliza um comparativo somente se for da mesma máquina.
    same_machine = False
    if comparison_path.exists():
        try:
            old = load_json(comparison_path)
            same_machine = old.get("machine_id") == mid
        except Exception:
            pass

    if not same_machine:
        if not benchmark_script.exists():
            print("benchmark_v0_4.py não encontrado.")
            return 3
        print("\nExecutando benchmark base V0.4...")
        rc = subprocess.call([sys.executable, str(benchmark_script)], cwd=str(ROOT))
        if rc != 0:
            print("Benchmark base falhou.")
            return rc or 4

    comparison = load_json(comparison_path)
    modes = {}
    model_ids = {}

    # V0.7 Fase 3: calibração dirigida pelo Catálogo de Modelos.
    # Só calibramos modelos presentes, validados e VIÁVEIS neste hardware;
    # numa máquina onde o QUALIDADE (8B) não cabe, ele é PULADO (não falha).
    registry = cat.load_registry(ROOT)
    caps = cat.caps_from_hardware(hw)  # cuda a partir do hardware real
    viable_ids = {m["id"] for m in cat.viable_models(caps, registry, ROOT)}
    print("Catálogo:", "sintetizado" if registry.get("synthesized") else "config/models_registry.json",
          "| caps:", caps)

    def _mode_of(m):
        roles = m.get("roles", [])
        if "quality" in roles:
            return "quality"
        if "fast" in roles or "light" in roles:
            return "fast"
        return None

    # Ordem estável: fast antes de quality.
    ordered = sorted(
        registry.get("models", []),
        key=lambda m: 0 if _mode_of(m) == "fast" else 1,
    )
    mode_labels = {"fast": "RÁPIDO", "quality": "QUALIDADE"}
    for m in ordered:
        mode_key = _mode_of(m)
        bk = m.get("bench_key")
        if mode_key is None or not bk:
            continue
        if m["id"] not in viable_ids:
            print(f"  - pulando {m['id']} ({mode_key}): não viável neste hardware.")
            continue
        if bk not in comparison.get("models", {}):
            print(f"  - pulando {m['id']}: sem benchmark '{bk}' no comparativo.")
            continue
        if mode_key in modes:
            continue  # já calibrado por outro modelo do mesmo papel
        p, probes = stabilize_mode(
            bk, comparison["models"][bk], comparison["models"][bk]["spec"], hw
        )
        p["mode_name"] = mode_labels[mode_key]
        p["model_id"] = m["id"]
        p["fallback_cpu_threads"] = comparison["models"][bk]["best_cpu"]["threads"]
        modes[mode_key] = p
        model_ids[mode_key] = m["id"]
        save_json(PROBES / f"{mid}_{bk}.json", probes)

    if not modes:
        print("Nenhum modelo calibrável/viável encontrado para este hardware.")
        return 5

    fast_tps = float(modes.get("fast", {}).get("observed_chat_generation_tps")
                     or modes.get("fast", {}).get("generation_tps") or 0)
    quality_tps = float(modes.get("quality", {}).get("observed_chat_generation_tps")
                        or modes.get("quality", {}).get("generation_tps") or 0)

    recommended = "fast"
    if fast_tps > 0 and quality_tps >= POLICY["auto_quality_min_generation_tps"]:
        if quality_tps / fast_tps >= POLICY["auto_quality_min_ratio_vs_fast"]:
            recommended = "quality"

    # V0.7 Fase 1: identidade estável (id v2) + confiança de detecção.
    try:
        mid_v2 = core.machine_id_v2(hw)
        fingerprint = core.machine_fingerprint(hw)
        det_conf = core.detection_confidence(hw)
    except Exception:
        mid_v2, fingerprint, det_conf = None, None, None
    if det_conf and det_conf.get("level") == "low":
        print("AVISO: confiança de detecção BAIXA -", ", ".join(det_conf.get("reasons", [])))

    profile = {
        "project": "NÚCLEO IA PORTÁTIL",
        "version": "0.5",
        "profile_schema_version": 3,
        "catalog_version": registry.get("registry_version"),
        "machine_id": mid,
        "machine_id_v2": mid_v2,
        "machine_fingerprint": fingerprint,
        "detection_confidence": det_conf,
        "model_ids": model_ids,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hardware_summary": {
            "manufacturer": hw.manufacturer,
            "model": hw.model,
            "cpu": hw.cpu,
            "physical_cores": hw.physical_cores,
            "logical_threads": hw.logical_threads,
            "ram_total_gb": hw.ram_total_gb,
        },
        "recommended_auto": recommended,
        "modes": modes,
        "policy": {
            "minimum_vram_headroom_mib": POLICY["minimum_vram_headroom_mib"],
            "selection": "chat_stable_over_benchmark_peak",
        },
    }

    save_json(PROFILES / f"{mid}.json", profile)
    print("\nPerfil V0.5 salvo:")
    print(PROFILES / f"{mid}.json")
    print("Modo AUTO recomendado:", recommended.upper())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCalibração cancelada.")
        raise SystemExit(130)
