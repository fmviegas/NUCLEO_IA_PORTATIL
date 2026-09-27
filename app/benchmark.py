#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Comparativo V0.4

Compara Qwen3-4B Q4_K_M vs Qwen3-8B Q4_K_M no MESMO llama.cpp:
- CPU 4/6/8 threads (dinâmico conforme hardware)
- CUDA com offload progressivo e refino
- prompt processing / generation tokens/s
- checagem do número de camadas realmente offloaded quando log disponível
- sonda separada de RAM/VRAM aproximadas para o melhor perfil de cada modelo
- grava perfis independentes para chat 4B e 8B
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
CONFIG = ROOT / "state" / "calibration"
PROFILES = ROOT / "state" / "benchmark_profiles"
LOGS = ROOT / "logs" / "benchmark"
COMPARISON = ROOT / "state" / "comparison"
for d in (CONFIG, PROFILES, LOGS, COMPARISON):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(APP_DIR))
import hardware as core
import plat

MANIFEST = json.loads((APP_DIR / "manifests" / "manifest_v0_4.json").read_text(encoding="utf-8"))
BENCH = MANIFEST["benchmark"]


@dataclass
class Point:
    model_key: str
    backend: str
    threads: int
    gpu_layers_requested: int
    gpu_layers_observed: Optional[int]
    prompt_tps: Optional[float]
    generation_tps: Optional[float]
    success: bool
    exit_code: int
    duration_s: float
    error_kind: str = ""
    error_excerpt: str = ""


def save_json(path: Path, data: Any):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_capture(cmd: List[str], timeout=420) -> Tuple[int, str, str, float]:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    start = time.perf_counter()
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, cwd=str(Path(cmd[0]).parent),
            creationflags=flags
        )
        return p.returncode, p.stdout, p.stderr, time.perf_counter() - start
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, out, err + "\nTIMEOUT", time.perf_counter() - start
    except Exception as exc:
        return 1, "", str(exc), time.perf_counter() - start


def extract_json(text: str):
    s = text.strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    # JSONL fallback
    rows = []
    for line in s.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    if rows:
        return rows
    # Array/object embedded in text
    starts = [x for x in (s.find("["), s.find("{")) if x >= 0]
    if starts:
        start = min(starts)
        for end in range(len(s), start, -1):
            try:
                return json.loads(s[start:end])
            except Exception:
                continue
    raise ValueError("saída JSON do llama-bench não reconhecida")


def rows(data):
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for k in ("results", "benchmarks", "data"):
            if isinstance(data.get(k), list):
                return [x for x in data[k] if isinstance(x, dict)]
        return [data]
    return []


def numeric(row, *keys):
    for k in keys:
        if row.get(k) is not None:
            try:
                return float(row[k])
            except Exception:
                pass
    return None


def classify(rs):
    pp, tg = [], []
    for r in rs:
        p = numeric(r, "n_prompt")
        g = numeric(r, "n_gen")
        t = numeric(r, "avg_ts", "avg_tps", "tokens_per_second")
        if t is None:
            continue
        if p and p > 0 and (not g or g == 0):
            pp.append(t)
        elif g and g > 0 and (not p or p == 0):
            tg.append(t)
    return (
        round(sum(pp)/len(pp), 2) if pp else None,
        round(sum(tg)/len(tg), 2) if tg else None,
    )


def classify_error(text: str, code: int):
    t = text.lower()
    if code == 124:
        return "timeout"
    if any(x in t for x in (
        "out of memory", "cuda out of memory", "cudamalloc",
        "failed to allocate", "cuda error 2"
    )):
        return "oom"
    if any(x in t for x in ("no cuda", "failed to load cuda", "ggml_cuda")):
        return "cuda"
    if code != 0:
        return "process_error"
    return ""


def observed_layers(text: str) -> Optional[int]:
    patterns = [
        r"offloaded\s+(\d+)\s*/\s*(\d+)\s+layers",
        r"offloaded\s+(\d+)\s+repeating layers",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            return int(m.group(1))
    return None


def bench_one(exe: Path, model: Path, model_key: str,
              backend: str, threads: int, ngl: int) -> Point:
    cmd = [
        str(exe), "-m", str(model),
        "-p", str(BENCH["prompt_tokens"]),
        "-n", str(BENCH["generation_tokens"]),
        "-r", str(BENCH["repetitions"]),
        "-t", str(threads),
        "-ngl", str(ngl),
        "-o", "json",
    ]
    code, out, err, duration = run_capture(cmd)
    combined = (out + "\n" + err).strip()
    log = LOGS / f"v0_4_{model_key}_{backend}_t{threads}_ngl{ngl}.log"
    log.write_text(combined, encoding="utf-8", errors="replace")
    obs = observed_layers(combined)

    if code != 0:
        return Point(
            model_key, backend, threads, ngl, obs, None, None, False,
            code, round(duration, 2), classify_error(combined, code),
            combined[-1400:]
        )
    try:
        pp, tg = classify(rows(extract_json(out)))
        ok = pp is not None or tg is not None
        return Point(
            model_key, backend, threads, ngl, obs, pp, tg, ok,
            code, round(duration, 2), "" if ok else "parse_no_metrics",
            "" if ok else combined[-1400:]
        )
    except Exception as exc:
        return Point(
            model_key, backend, threads, ngl, obs, None, None, False,
            code, round(duration, 2), "parse_error",
            f"{exc}\n{combined[-1200:]}"
        )


def thread_candidates(physical: int, logical: int):
    physical = max(1, physical)
    logical = max(physical, logical)
    if logical > physical:
        mid = physical + max(1, (logical - physical)//2)
        vals = [physical, mid, logical]
    else:
        vals = [max(1, physical//2), physical]
    return sorted(set(min(16, x) for x in vals))


def initial_layers(total: int):
    return sorted(set(max(1, round(total*f)) for f in BENCH["cuda_initial_layer_fractions"]))


def best(points: List[Point]):
    vals = [p for p in points if p.success and p.generation_tps is not None]
    return max(vals, key=lambda p: p.generation_tps) if vals else None


def refine(exe, model, model_key, threads, total, points):
    ok = best(points)
    if not ok or ok.gpu_layers_requested >= total:
        return []
    failed = sorted(
        p.gpu_layers_requested for p in points
        if (not p.success) and p.gpu_layers_requested > ok.gpu_layers_requested
    )
    upper = failed[0]-1 if failed else total
    if upper <= ok.gpu_layers_requested:
        return []

    # Binary-ish refinement until interval is small, max 4 extra points.
    out = []
    low = ok.gpu_layers_requested
    high = upper
    tested = {p.gpu_layers_requested for p in points}
    for _ in range(4):
        if high <= low:
            break
        mid = (low + high + 1)//2
        if mid in tested:
            break
        p = bench_one(exe, model, model_key, "cuda", threads, mid)
        out.append(p)
        tested.add(mid)
        if p.success:
            low = mid
        else:
            high = mid - 1
    return out


# --- Resource probe ---------------------------------------------------------
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def system_ram_used_mb() -> Optional[float]:
    if os.name != "nt":
        return None
    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(st)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return None
    return (st.ullTotalPhys - st.ullAvailPhys) / 1024**2


def gpu_used_mb() -> Optional[float]:
    exe = shutil.which("nvidia-smi.exe") or shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        p = subprocess.run(
            [exe, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=8,
            encoding="utf-8", errors="replace"
        )
        vals = []
        for line in p.stdout.splitlines():
            try:
                vals.append(float(line.strip()))
            except Exception:
                pass
        return max(vals) if vals else None
    except Exception:
        return None


def resource_probe(exe: Path, model: Path, threads: int, ngl: int):
    before_ram = system_ram_used_mb()
    before_gpu = gpu_used_mb()
    samples_ram, samples_gpu = [], []
    stop = threading.Event()

    cmd = [
        str(exe), "-m", str(model),
        "-p", "128", "-n", "64", "-r", "1",
        "-t", str(threads), "-ngl", str(ngl), "-o", "json",
    ]

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    proc = subprocess.Popen(
        cmd, cwd=str(exe.parent),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags
    )

    def sampler():
        while not stop.is_set():
            r = system_ram_used_mb()
            if r is not None:
                samples_ram.append(r)
            # nvidia-smi is heavier; sample GPU every loop but at 0.5 s.
            g = gpu_used_mb()
            if g is not None:
                samples_gpu.append(g)
            stop.wait(0.5)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    try:
        proc.wait(timeout=420)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    finally:
        stop.set()
        th.join(timeout=3)

    peak_ram = max(samples_ram) if samples_ram else None
    peak_gpu = max(samples_gpu) if samples_gpu else None
    return {
        "note": "Aproximação por diferença de uso global; processos em segundo plano podem influenciar.",
        "baseline_system_ram_used_mb": round(before_ram, 1) if before_ram is not None else None,
        "peak_system_ram_used_mb": round(peak_ram, 1) if peak_ram is not None else None,
        "approx_system_ram_delta_mb": (
            round(max(0.0, peak_ram - before_ram), 1)
            if peak_ram is not None and before_ram is not None else None
        ),
        "baseline_gpu_used_mb": round(before_gpu, 1) if before_gpu is not None else None,
        "peak_gpu_used_mb": round(peak_gpu, 1) if peak_gpu is not None else None,
        "approx_gpu_delta_mb": (
            round(max(0.0, peak_gpu - before_gpu), 1)
            if peak_gpu is not None and before_gpu is not None else None
        ),
        "probe_exit_code": proc.returncode,
    }


def rel(p: Path):
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(p)


def compare_model(key: str, hw, cpu_exe: Path, cuda_exe: Path):
    spec = MANIFEST["models"][key]
    model = ROOT / "models" / spec["filename"]

    cpus = []
    threads = thread_candidates(hw.physical_cores, hw.logical_threads)
    print(f"\n{key.upper()} — CPU: {threads}")
    for t in threads:
        print(f"  CPU t={t}...", end=" ", flush=True)
        p = bench_one(cpu_exe, model, key, "cpu", t, 0)
        cpus.append(p)
        print(f"tg={p.generation_tps} | pp={p.prompt_tps}" if p.success else f"FALHOU ({p.error_kind})")

    bc = best(cpus)
    if not bc:
        raise RuntimeError(f"{key}: nenhum benchmark CPU válido")

    cudas = []
    if hw.nvidia_driver_ok:
        print(f"{key.upper()} — CUDA:")
        for ngl in initial_layers(spec["layers"]):
            print(f"  CUDA ngl={ngl}...", end=" ", flush=True)
            p = bench_one(cuda_exe, model, key, "cuda", bc.threads, ngl)
            cudas.append(p)
            if p.success:
                obs = f" obs={p.gpu_layers_observed}" if p.gpu_layers_observed is not None else ""
                print(f"tg={p.generation_tps} | pp={p.prompt_tps}{obs}")
            else:
                print(f"FALHOU ({p.error_kind})")
                if p.error_kind == "oom":
                    break

        extras = refine(cuda_exe, model, key, bc.threads, spec["layers"], cudas)
        for p in extras:
            cudas.append(p)
            print(
                f"  Refino ngl={p.gpu_layers_requested}: "
                + (f"tg={p.generation_tps}" if p.success else f"FALHOU ({p.error_kind})")
            )

    bg = best(cudas)
    chosen = bc
    if bg and (bg.generation_tps or 0) >= (bc.generation_tps or 0) * (1 + BENCH["cuda_min_gain_over_cpu"]):
        chosen = bg

    engine = cuda_exe if chosen.backend == "cuda" else cpu_exe
    print(f"{key.upper()} — sonda RAM/VRAM no melhor perfil...")
    resources = resource_probe(
        engine, model, chosen.threads,
        chosen.gpu_layers_requested if chosen.backend == "cuda" else 0
    )

    profile = {
        "model_key": key,
        "model": rel(model),
        "model_sha256": spec["sha256"],
        "backend": chosen.backend,
        "cpu_threads": chosen.threads,
        "gpu_layers": chosen.gpu_layers_requested if chosen.backend == "cuda" else 0,
        "context_size": BENCH["context_size"],
        "llama_cli": rel(plat.engine_exe(
            ROOT, "cuda" if chosen.backend == "cuda" else "cpu", "llama-cli")),
        "generation_tps": chosen.generation_tps,
        "prompt_tps": chosen.prompt_tps,
    }

    return {
        "spec": spec,
        "cpu_benchmarks": [asdict(x) for x in cpus],
        "cuda_benchmarks": [asdict(x) for x in cudas],
        "best_cpu": asdict(bc),
        "best_cuda": asdict(bg) if bg else None,
        "chosen_profile": profile,
        "resource_probe": resources,
    }


def main():
    print("=" * 78)
    print("        NÚCLEO IA PORTÁTIL — V0.4 — COMPARATIVO 4B vs 8B")
    print("=" * 78)

    required = [
        plat.engine_exe(ROOT, "cpu", "llama-bench"),
        plat.engine_exe(ROOT, "cuda", "llama-bench"),
        ROOT / "models" / MANIFEST["models"]["4b"]["filename"],
        ROOT / "models" / MANIFEST["models"]["8b"]["filename"],
    ]
    missing = [str(x.relative_to(ROOT)) for x in required if not x.exists()]
    if missing:
        print("\nFaltam componentes:")
        for x in missing:
            print(" -", x)
        print("\nSe o 8B estiver faltando, execute 00_PREPARAR_MODELO_8B_V0_4.bat")
        return 3

    hw = core.detect_safe()
    mid = core.machine_id(hw)
    print(f"Machine ID: {mid}")
    print(f"CPU: {hw.cpu}")
    print(f"RAM: {hw.ram_total_gb:.2f} GB")
    for g in hw.gpus:
        print(f"GPU: {g.name} | {g.vram_gb:.2f} GB")

    cpu_exe = plat.engine_exe(ROOT, "cpu", "llama-bench")
    cuda_exe = plat.engine_exe(ROOT, "cuda", "llama-bench")

    models = {}
    for key in ("4b", "8b"):
        models[key] = compare_model(key, hw, cpu_exe, cuda_exe)
        save_json(CONFIG / f"runtime_profile_{key}_v0_4.json", models[key]["chosen_profile"])

    p4 = models["4b"]["chosen_profile"]
    p8 = models["8b"]["chosen_profile"]

    speed_ratio = (
        round((p8["generation_tps"] / p4["generation_tps"]) * 100, 1)
        if p4["generation_tps"] and p8["generation_tps"] else None
    )
    speed_loss = round(100 - speed_ratio, 1) if speed_ratio is not None else None

    summary = {
        "generation_speed_8b_as_percent_of_4b": speed_ratio,
        "generation_speed_loss_8b_vs_4b_percent": speed_loss,
        "faster_model": (
            "8b" if (p8["generation_tps"] or 0) > (p4["generation_tps"] or 0) else "4b"
        ),
        "quality_winner": None,
        "quality_note": "V0.4 não inventa um vencedor de qualidade: compare os dois chats com PROMPTS_COMPARACAO_V0_4.txt.",
        "policy_note": "Decisão final 4B vs 8B será feita após desempenho + avaliação humana de qualidade.",
    }

    result = {
        "app": "NÚCLEO IA PORTÁTIL",
        "autotune_version": "0.4",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "machine_id": mid,
        "hardware": asdict(hw),
        "manifest": MANIFEST,
        "models": models,
        "comparison_summary": summary,
    }
    save_json(CONFIG / "comparison_v0_4.json", result)
    save_json(PROFILES / f"{mid}_comparison_v0_4.json", result)

    print("\n" + "=" * 78)
    print("RESUMO V0.4")
    print("=" * 78)
    for key, p in (("4B", p4), ("8B", p8)):
        rp = models[key.lower()]["resource_probe"]
        print(
            f"{key}: {p['backend'].upper()} | t={p['cpu_threads']} | "
            f"ngl={p['gpu_layers']} | geração={p['generation_tps']} t/s | "
            f"prompt={p['prompt_tps']} t/s"
        )
        print(
            f"    RAM delta~{rp.get('approx_system_ram_delta_mb')} MB | "
            f"VRAM delta~{rp.get('approx_gpu_delta_mb')} MB"
        )
    print(f"\n8B mantém ~{speed_ratio}% da velocidade de geração do 4B.")
    print("\nResultado: state\\calibration\\comparison_v0_4.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        raise SystemExit(130)
