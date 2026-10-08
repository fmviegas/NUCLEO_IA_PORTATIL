#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrar_advanced.py — Calibração dirigida do modo AVANÇADO (Qwen3-30B-A3B MoE).

Diferente do autotune completo (que reconstrói o perfil só com fast/quality),
este tool calibra APENAS o modo `advanced` e grava a entrada de volta no perfil
da máquina, preservando fast/quality. Reaproveita a sonda de chat real do
autotune (llama-cli + amostragem de VRAM via nvidia-smi) e faz uma varredura de
gpu_layers de cima para baixo, escolhendo o MAIOR nível estável (com margem de
VRAM >= minimum_vram_headroom_mib).

Uso:
    python tools/calibrar_advanced.py                 # varre a partir de --ngl-inicial
    python tools/calibrar_advanced.py --ngl-inicial 24 --threads 4
    python tools/calibrar_advanced.py --id qwen3-30b-a3b-iq3
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

import hardware as core           # noqa: E402
import catalog as cat             # noqa: E402
import autotune as at             # noqa: E402  (reutiliza real_chat_probe, POLICY, nvidia_memory)

PROFILES = ROOT / "profiles" / "machines"
PROBES = ROOT / "state" / "probes"
PROBES.mkdir(parents=True, exist_ok=True)


def _backup_profile(path: Path):
    bdir = ROOT / "backup"
    bdir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = bdir / f"pre_calibra_advanced_{path.stem}_{stamp}.json"
    dst.write_bytes(path.read_bytes())
    return dst


MODOS_AUTO = [("advanced", "AVANCADO"), ("code", "CODIGO"), ("vision", "VISAO")]


def _ngl_estimado(entry: dict, model_path: Path, hw) -> int:
    """Ponto de partida da varredura de gpu_layers numa máquina qualquer:
    todas as camadas se o modelo cabe na VRAM com folga; senão a fração que
    cabe. (O padrão fixo 18 era da GTX 1050 4 GB.)"""
    try:
        import validar_modelo as vm
        meta = vm.read_gguf_metadata(model_path)["meta"]
        arch = meta.get("general.architecture", "")
        camadas = int(meta.get(f"{arch}.block_count") or 0)
    except Exception:
        camadas = 0
    if not camadas:
        return 18
    vram = float(getattr(hw, "gpu_vram_budget_gb", 0) or 0)
    size = float(entry.get("size_gb") or 1)
    if vram >= size + 1.5:
        return camadas
    return max(0, min(camadas, int(camadas * max(vram - 1.0, 0) / size) + 2))


def main():
    ap = argparse.ArgumentParser(description="Calibra o modo AVANÇADO (30B-A3B).")
    ap.add_argument("--id", default="qwen3-30b-a3b-iq3", help="model_id do catálogo")
    ap.add_argument("--ngl-inicial", type=int, default=18, help="gpu_layers inicial da varredura")
    ap.add_argument("--threads", type=int, default=None, help="threads (padrão: núcleos físicos)")
    ap.add_argument("--context", type=int, default=None, help="context_size (padrão: policy)")
    ap.add_argument("--mode", default="advanced", help="chave do modo no perfil (advanced|code|...)")
    ap.add_argument("--mode-name", default=None, help="rótulo do modo (padrão: MODE em maiúsculas)")
    ap.add_argument("--model-key", default="30b-a3b", help="rótulo curto do modelo (logs/probes)")
    ap.add_argument("--auto", action="store_true",
                    help="escolhe sozinho o MELHOR modelo do catálogo que cabe nesta máquina p/ --mode")
    ap.add_argument("--todos", action="store_true",
                    help="--auto para os modos AVANCADO (livros), CODIGO e VISAO, em sequência")
    ap.add_argument("--sim", action="store_true", help="troca de modelo sem perguntar (--auto/--todos)")
    args = ap.parse_args()

    if sys.platform != "win32":
        print("Calibração roda no Windows (llama-cli cuda).")
        return 2

    if not (args.auto or args.todos):
        return calibrar(args, args.id, args.mode, args.mode_name or args.mode.upper(), args.model_key, args.ngl_inicial)

    hw = core.detect_windows()
    caps = cat.caps_from_hardware(hw)
    registry = cat.load_registry(ROOT)
    modos = MODOS_AUTO if args.todos else [(args.mode, args.mode_name or args.mode.upper())]
    print(f"Escolha automática | RAM {caps['ram_gb']:.0f} GB | VRAM {caps['vram_gb']:.0f} GB | CUDA {caps['cuda_available']}")
    rc_final = 0
    for mode_key, mode_name in modos:
        best = cat.best_for_mode(mode_key, caps, registry, ROOT)
        if not best:
            print(f"\n[{mode_name}] nenhum modelo baixado/validado cabe nesta máquina — modo mantido como está.")
            continue
        atual = ((json.loads((PROFILES / f"{core.machine_id(hw)}.json").read_text(encoding="utf-8-sig"))
                  .get("model_ids") or {}).get(mode_key)
                 if (PROFILES / f"{core.machine_id(hw)}.json").exists() else None)
        print(f"\n[{mode_name}] melhor modelo aqui: {best['id']} (rank {cat.rank(best):g})"
              + (f" — antes: {atual}" if atual and atual != best["id"] else ""))
        if atual == best["id"]:
            print("  já está calibrado com ele — nada a fazer (use --id para recalibrar).")
            continue
        if atual and not args.sim:
            # maior nem sempre é melhor numa máquina no limite (fica mais lento)
            if input(f"  Trocar {atual} -> {best['id']} e calibrar? (s/N) ").strip().lower() != "s":
                print("  mantido.")
                continue
        ngl = args.ngl_inicial if "--ngl-inicial" in sys.argv else \
            _ngl_estimado(best, ROOT / "models" / best["file"], hw)
        rc = calibrar(args, best["id"], mode_key, mode_name, best["id"], ngl)
        rc_final = rc_final or rc
    return rc_final


def calibrar(args, model_id: str, mode_key: str, mode_name: str, model_key: str, ngl_inicial: int):
    hw = core.detect_windows()
    mid = core.machine_id(hw)
    prof_path = PROFILES / f"{mid}.json"
    if not prof_path.exists():
        print(f"Perfil não encontrado: {prof_path}. Rode a calibração base (autotune) antes.")
        return 3
    profile = json.loads(prof_path.read_text(encoding="utf-8-sig"))

    registry = cat.load_registry(ROOT)
    entry = None
    for m in registry.get("models", []):
        if m.get("id") == model_id:
            entry = m
            break
    if not entry:
        print(f"model_id não encontrado no registry: {model_id}")
        return 4
    model_path = ROOT / "models" / entry["file"]
    if not model_path.exists():
        print(f"modelo ausente: {model_path}")
        return 4
    mmproj_path = None
    if entry.get("mmproj_file") and mode_key == "vision":
        cand = ROOT / "models" / entry["mmproj_file"]
        if cand.exists():
            mmproj_path = cand
        else:
            print(f"AVISO: mmproj do catálogo não encontrado ({cand}); calibrando sem visão na sonda.")

    threads = args.threads or int(getattr(hw, "physical_cores", 4) or 4)
    ctx = args.context or int(at.POLICY.get("chat_context_size", 4096))
    if not args.context and mode_key == "code":
        # menu CÓDIGO: pedido + código colado + resposta longa não cabem em 4K
        ctx = 16384 if float(getattr(hw, "ram_total_gb", 0) or 0) >= 12 else 8192
    step = int(at.POLICY.get("layer_backoff_step", 3))
    min_head = float(at.POLICY.get("minimum_vram_headroom_mib", 400))
    cli = ROOT / "engine" / "windows" / "cuda" / "llama-cli.exe"

    print("=" * 72)
    print(f"     NÚCLEO IA PORTÁTIL — CALIBRAÇÃO DIRIGIDA DO MODO {mode_name}")
    print("=" * 72)
    print(f"Máquina : {mid}  | CPU {getattr(hw,'physical_cores','?')}c/{getattr(hw,'logical_threads','?')}t | RAM {hw.ram_total_gb:.2f} GB")
    print(f"Modelo  : {entry['file']}  (id {model_id})")
    print(f"Sonda   : threads={threads} ctx={ctx} | varredura ngl {ngl_inicial}→ passo -{step} | headroom≥{min_head:.0f} MiB")
    if not getattr(hw, "nvidia_driver_ok", False):
        print("AVISO: driver NVIDIA não OK — a calibração cairá para CPU (ngl=0).")

    probes = []
    escolhido = None
    if getattr(hw, "nvidia_driver_ok", False):
        layers = int(ngl_inicial)
        while layers > 0:
            print(f"\n  Sonda {mode_name} — {layers} GPU layers...", flush=True)
            pr = at.real_chat_probe(cli, model_path, threads, layers, ctx, model_key, mmproj=mmproj_path)
            probes.append(pr)
            head = pr.get("vram_headroom_mib")
            head_ok = (head is None) or (head >= min_head)
            print(f"    exit={pr['exit_code']} tps={pr.get('generation_tps')} "
                  f"vram_used={pr.get('peak_vram_used_mib')} headroom={head}")
            if pr["success"] and head_ok:
                escolhido = pr
                break
            layers -= step
        save = PROBES / f"{mid}_{model_key}.json"
        save.write_text(json.dumps(probes, indent=2, ensure_ascii=False), encoding="utf-8")

    modo = dict(profile.get("modes", {}).get(mode_key, {}))
    if modo.get("model_id") not in (None, model_id):
        # trocou de modelo: medidas do anterior não valem mais
        for k in [k for k in modo if k.startswith(("observed_", "benchmark_peak_")) or k == "generation_tps"]:
            del modo[k]
        modo["model_key"] = model_key
    modo.setdefault("model_key", model_key)
    modo["model"] = f"models\\{entry['file']}"
    modo["model_sha256"] = entry.get("sha256", modo.get("model_sha256", ""))
    modo["context_size"] = ctx
    modo["cpu_threads"] = threads
    modo["fallback_cpu_threads"] = threads
    modo["llama_cli"] = "engine\\windows\\cuda\\llama-cli.exe"
    modo["mode_name"] = mode_name
    modo["model_id"] = model_id
    modo["mmproj"] = bool(entry.get("mmproj_file")) and mode_key == "vision"
    modo["profile_kind"] = "chat_stable"
    modo["autotune_version"] = "0.9.4-advanced"

    if escolhido:
        modo["backend"] = "cuda"
        modo["gpu_layers"] = escolhido["gpu_layers"]
        modo["benchmark_peak_gpu_layers"] = escolhido["gpu_layers"]
        if escolhido.get("generation_tps") is not None:
            modo["generation_tps"] = escolhido["generation_tps"]
            modo["observed_chat_generation_tps"] = escolhido["generation_tps"]
            modo["benchmark_peak_generation_tps"] = escolhido["generation_tps"]
        modo["observed_vram_used_mib"] = escolhido.get("peak_vram_used_mib")
        modo["observed_vram_total_mib"] = escolhido.get("vram_total_mib")
        modo["observed_vram_headroom_mib"] = escolhido.get("vram_headroom_mib")
        modo["stability_reason"] = "Sonda real aprovada com margem de VRAM (calibração dirigida)."
    else:
        modo["backend"] = "cpu"
        modo["gpu_layers"] = 0
        modo["llama_cli"] = "engine\\windows\\cpu\\llama-cli.exe"
        modo["stability_reason"] = ("Sem perfil CUDA estável na varredura; fallback CPU."
                                    if getattr(hw, "nvidia_driver_ok", False)
                                    else "Driver NVIDIA indisponível; CPU.")

    bkp = _backup_profile(prof_path)
    profile.setdefault("modes", {})[mode_key] = modo
    profile.setdefault("model_ids", {})[mode_key] = model_id
    prof_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "-" * 72)
    if escolhido:
        print(f"CALIBRADO: backend=cuda gpu_layers={modo['gpu_layers']} "
              f"tps={modo.get('observed_chat_generation_tps')} "
              f"headroom={modo.get('observed_vram_headroom_mib')} MiB")
    else:
        print(f"CALIBRADO: backend={modo['backend']} gpu_layers={modo['gpu_layers']} ({modo['stability_reason']})")
    print(f"Perfil   : {prof_path}")
    print(f"Backup   : {bkp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
