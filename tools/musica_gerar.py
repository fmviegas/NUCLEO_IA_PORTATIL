#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
musica_gerar.py — gera UMA música com o ACE-Step 1.5 (engine/acestep).

Roda com o Python do PRÓPRIO ACE-Step (engine/acestep/python_embeded), não com o
runtime do NÚCLEO: torch/torchao/transformers do ACE-Step ficam isolados lá.
Quem chama é app/server.py (/api/musica/gerar), depois de pausar o motor do chat.

Entrada: --job <arquivo.json> com caption, roteiro, bpm, tom, compasso, duracao,
seed (opcional), saida (pasta) e nome (base do arquivo).

Saída no stdout: linhas "@@ {json}" com o andamento (fase, progresso, erro,
pronto); o resto é log comum. Grava <nome>.mp3 + <nome>.json (parâmetros e
semente, para refazer igual).

Modo 4 GB (GTX 1050): DiT turbo em INT8 (exige compile_model=True), tudo o que
não está em uso vai para a RAM, sem o LM de 5 Hz. Ver BIBLIA §27.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACE = ROOT / "engine" / "acestep"

# instrução + metadados (bpm/tom/compasso/duração) somam ~54 tokens e entram
# DEPOIS da descrição no texto de 256 tokens do ACE-Step: estourar corta os metadados
LIMITE_TOKENS = 256
FIXOS_TOKENS = 54
COMPASSOS = {"", "2", "3", "4", "6"}

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass


def evento(**kw) -> None:
    print("@@ " + json.dumps(kw, ensure_ascii=False), flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera uma música com o ACE-Step (modo 4 GB).")
    ap.add_argument("--job", required=True)
    args = ap.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))

    caption = str(job.get("caption") or "").strip()
    roteiro = str(job.get("roteiro") or "").strip() or "[Instrumental]"
    compasso = str(job.get("compasso") or "")
    if not caption:
        evento(tipo="erro", mensagem="A descrição da música está vazia.")
        return 2
    if compasso not in COMPASSOS:
        evento(tipo="erro", mensagem="Compasso inválido: o ACE-Step aceita 2/4, 3/4, 4/4 e 6/8.")
        return 2
    saida = Path(job["saida"])
    saida.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(ACE))
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level="WARNING", colorize=False, format="{level}: {message}")

    from transformers import AutoTokenizer
    tk = AutoTokenizer.from_pretrained(str(ACE / "checkpoints" / "Qwen3-Embedding-0.6B"))
    n_cap = len(tk(caption).input_ids)
    n_rot = len(tk(roteiro).input_ids)
    evento(tipo="tokens", descricao=n_cap, limite_descricao=LIMITE_TOKENS - FIXOS_TOKENS, roteiro=n_rot)
    if n_cap + FIXOS_TOKENS > LIMITE_TOKENS:
        evento(tipo="erro", mensagem=(f"A descrição tem {n_cap} tokens; o limite é {LIMITE_TOKENS - FIXOS_TOKENS}. "
                                      "Passe detalhes de cada parte para o roteiro."))
        return 2

    from acestep.gpu_config import get_gpu_config
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    gpu = get_gpu_config()
    max_dur = int(getattr(gpu, "max_duration_without_lm", 360) or 360)
    dur = max(10, min(int(job.get("duracao") or 120), max_dur))
    if dur != int(job.get("duracao") or 120):
        evento(tipo="aviso", mensagem=f"Duração ajustada para {dur} s (máximo nesta placa sem o LM).")
    quant = "int8_weight_only" if getattr(gpu, "quantization_default", True) else None

    evento(tipo="fase", fase="carregando", mensagem="Carregando o modelo de música (1 a 3 min)…")
    t0 = time.time()
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=str(ACE), config_path="acestep-v15-turbo", device="cuda",
                                     offload_to_cpu=True, offload_dit_to_cpu=True,
                                     quantization=quant, compile_model=bool(quant))
    if not ok:
        evento(tipo="erro", mensagem="Não consegui carregar o ACE-Step: " + str(msg)[:400])
        return 1
    evento(tipo="fase", fase="gerando", mensagem=f"Modelo carregado em {time.time() - t0:.0f} s. Gerando {dur} s de música…")

    def progresso(valor, desc=None, **_):
        try:
            evento(tipo="progresso", valor=round(float(valor), 3), etapa=str(desc or ""))
        except Exception:
            pass

    seed = int(job["seed"]) if str(job.get("seed") or "").strip().lstrip("-").isdigit() else -1
    params = GenerationParams(task_type="text2music", caption=caption, lyrics=roteiro,
                              bpm=int(job["bpm"]) if job.get("bpm") else None,
                              keyscale=str(job.get("tom") or ""), timesignature=compasso,
                              duration=dur, seed=seed, thinking=False)
    t1 = time.time()
    r = generate_music(dit, LLMHandler(), params, GenerationConfig(batch_size=1, audio_format="mp3"),
                       save_dir=str(saida / "_ace"), progress=progresso)
    if not r.success:
        evento(tipo="erro", mensagem="A geração falhou: " + str(r.error)[:400])
        return 1
    audio = r.audios[0]
    nome = str(job.get("nome") or "musica")
    destino = saida / f"{nome}.mp3"
    Path(audio["path"]).replace(destino)
    shutil.rmtree(saida / "_ace", ignore_errors=True)
    semente = (audio.get("params") or {}).get("seed")
    ficha = {k: job.get(k) for k in ("album", "faixa", "titulo", "caption", "roteiro", "bpm", "tom", "compasso")}
    ficha.update(duracao=dur, seed=semente, gerado_em=time.strftime("%Y-%m-%d %H:%M:%S"),
                 tempo_geracao_s=round(time.time() - t1), tokens_descricao=n_cap, tokens_roteiro=n_rot,
                 modelo="ACE-Step 1.5 turbo (INT8, sem LM)")
    (saida / f"{nome}.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    evento(tipo="pronto", arquivo=destino.name, seed=semente, segundos=round(time.time() - t1), duracao=dur)
    return 0


if __name__ == "__main__":
    sys.exit(main())
