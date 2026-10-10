#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gguf_advisor.py — Consultor de modelos GGUF para o hardware da máquina.

A partir da RAM total e da VRAM (NVIDIA) detectadas pelo app/hardware.py,
classifica os modelos GGUF em três faixas:

  - "folga"    : roda com folga de memória (recomendado)
  - "limite"   : roda, mas no limite (feche apps; contexto curto; mais lento)
  - "nao_roda" : não cabe na RAM desta máquina (inviável, entraria em swap)

Heurística deliberadamente CONSERVADORA. Para llama.cpp com offload parcial à
GPU, o gargalo de "roda ou não" é a RAM (o modelo inteiro precisa caber em
RAM+VRAM úteis); a VRAM entra como acelerador (quantas camadas na GPU).
O Diagnóstico do painel usa SOMENTE os modelos salvos na pasta models/
(modelos_da_pasta: tamanho real do arquivo). GGUF_MODELS é só a tabela de
referência do validador. Tudo offline.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# llama.cpp carrega o GGUF via mmap: o arquivo pode ocupar quase toda a RAM
# (cache de páginas) e ainda rodar — apertado — com leve paginação em disco.
# Por isso o modelo de memória é ADITIVO (arquivo + KV/buffers), não multiplicativo.
OS_RESERVE_GB = 1.2          # RAM mínima para o SO respirar
FOLGA_FRAC = 0.70           # até 70% da RAM útil = roda com folga
LIMITE_FRAC = 1.05          # até ~105% (leve paginação via mmap) = roda no limite
# VRAM reservada para o próprio driver/estado antes de acomodar camadas.
VRAM_RESERVE_GB = 0.8


def _kv_e_buffers(size_gb: float) -> float:
    """KV cache (contexto moderado) + buffers de compute, ~cresce com o modelo."""
    return 0.8 + 0.06 * float(size_gb)

# Tabela curada (tamanho ~ do arquivo GGUF em GB). quant representativo por linha.
# Ordenada do menor para o maior. size_gb = tamanho aproximado do arquivo.
GGUF_MODELS: List[Dict[str, Any]] = [
    {"nome": "Qwen2.5-0.5B",            "params": "0.5B",     "quant": "Q4_K_M",  "size_gb": 0.4},
    {"nome": "Llama-3.2-1B",            "params": "1B",       "quant": "Q4_K_M",  "size_gb": 0.8},
    {"nome": "Qwen2.5-1.5B",            "params": "1.5B",     "quant": "Q4_K_M",  "size_gb": 1.1},
    {"nome": "Gemma-2-2B",              "params": "2B",       "quant": "Q4_K_M",  "size_gb": 1.7},
    {"nome": "Llama-3.2-3B",            "params": "3B",       "quant": "Q4_K_M",  "size_gb": 2.0},
    {"nome": "Qwen3-4B",               "params": "4B",       "quant": "Q4_K_M",  "size_gb": 2.5,
     "nucleo": "RÁPIDO"},
    {"nome": "Mistral-7B",              "params": "7B",       "quant": "Q4_K_M",  "size_gb": 4.4},
    {"nome": "Qwen2.5-Coder-7B",       "params": "7B",       "quant": "Q4_K_M",  "size_gb": 4.4,
     "tag": "código"},
    {"nome": "Qwen3-8B",               "params": "8B",       "quant": "Q4_K_M",  "size_gb": 4.9,
     "nucleo": "QUALIDADE"},
    {"nome": "Llama-3.1-8B",            "params": "8B",       "quant": "Q4_K_M",  "size_gb": 4.9},
    {"nome": "Gemma-2-9B",              "params": "9B",       "quant": "Q4_K_M",  "size_gb": 5.4},
    {"nome": "Qwen2.5-Coder-14B",      "params": "14B",      "quant": "Q4_K_M",  "size_gb": 8.4,
     "tag": "código"},
    {"nome": "Qwen3-14B",              "params": "14B",      "quant": "Q4_K_M",  "size_gb": 9.0},
    {"nome": "Phi-4 (14B)",            "params": "14B",      "quant": "Q4_K_M",  "size_gb": 9.1},
    {"nome": "Qwen3-30B-A3B (MoE)",    "params": "30B-A3B",  "quant": "IQ3_XXS", "size_gb": 12.8,
     "nucleo": "AVANÇADO"},
    {"nome": "Gemma-2-27B",           "params": "27B",      "quant": "Q4_K_M",  "size_gb": 16.4},
    {"nome": "Qwen2.5-32B",           "params": "32B",      "quant": "Q4_K_M",  "size_gb": 19.9},
    {"nome": "Llama-3.3-70B",         "params": "70B",      "quant": "Q4_K_M",  "size_gb": 42.5},
    {"nome": "Qwen3-Coder-Next (MoE)", "params": "80B-A3B",  "quant": "Q4_K_M",  "size_gb": 45.1,
     "tag": "código"},
]


_SPLIT_RE = re.compile(r"-(\d{5})-of-(\d{5})$")
_QUANT_RE = re.compile(r"((?:UD-)?(?:I?Q\d[A-Z0-9_]*|F16|F32|BF16))$", re.I)
_PARAMS_RE = re.compile(r"(\d+(?:\.\d+)?B(?:-A\d+B)?)(?=[-_.]|$)", re.I)


def modelos_da_pasta(models_dir, registry_models: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """Modelos GGUF que estão DE FATO na pasta models/ (tamanho real do arquivo).
    Projetores de visão (mmproj-*) não são modelos e ficam de fora; as partes de um
    split (-00001-of-00003) contam como um modelo só. O registry, se passado, só
    acrescenta o rótulo do NÚCLEO (tier) — nunca inclui modelo que não está na pasta."""
    pasta = Path(models_dir)
    if not pasta.is_dir():
        return []
    tiers = {}
    for m in registry_models or []:
        base = _SPLIT_RE.sub("", str(m.get("file") or "")[:-5]).lower()
        if base:
            tiers[base] = m
    grupos: Dict[str, Dict[str, Any]] = {}
    for f in sorted(pasta.glob("*.gguf"), key=lambda x: x.name.lower()):
        if not f.is_file() or f.name.lower().startswith("mmproj"):
            continue
        stem = f.stem
        sp = _SPLIT_RE.search(stem)
        base = _SPLIT_RE.sub("", stem)
        g = grupos.setdefault(base.lower(), {"base": base, "bytes": 0, "partes": 0, "esperadas": 1})
        g["bytes"] += f.stat().st_size
        g["partes"] += 1
        if sp:
            g["esperadas"] = int(sp.group(2))
    out = []
    for chave, g in grupos.items():
        base = g["base"]
        q = _QUANT_RE.search(base)
        quant = q.group(1) if q else "?"
        nome = base[:q.start()].rstrip("-_.") if q else base
        p = _PARAMS_RE.search(nome)
        item = {"nome": nome, "params": p.group(1).upper() if p else "?", "quant": quant,
                "size_gb": g["bytes"] / (1024 ** 3)}
        reg = tiers.get(chave)
        if reg and not p and reg.get("params_b"):
            item["params"] = f"{float(reg['params_b']):g}B"
        if reg and reg.get("tier"):
            item["nucleo"] = str(reg["tier"]).replace("_", " ")
        tags = []
        if "coder" in nome.lower():
            tags.append("código")
        if g["partes"] < g["esperadas"]:
            tags.append(f"incompleto: {g['partes']} de {g['esperadas']} partes")
        if tags:
            item["tag"] = " · ".join(tags)
        out.append(item)
    out.sort(key=lambda m: m["size_gb"])
    return out


def _gpu_hint(size_gb: float, vram_gb: float, cuda: bool) -> str:
    if not cuda or vram_gb <= 0:
        return "CPU apenas (sem GPU CUDA)"
    disp = max(0.0, vram_gb - VRAM_RESERVE_GB)
    if size_gb + VRAM_RESERVE_GB <= vram_gb:
        return "cabe 100% na GPU (rápido)"
    pct = max(0, min(95, round(100.0 * disp / size_gb)))
    return f"~{pct}% das camadas na GPU (resto na CPU)"


def classify(ram_gb: float, vram_gb: float, cuda_available: bool = True,
             modelos: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Classifica os modelos em folga/limite/nao_roda para (ram_gb, vram_gb)."""
    modelos = GGUF_MODELS if modelos is None else modelos
    usable = max(0.0, float(ram_gb) - OS_RESERVE_GB)
    grupos: Dict[str, List[Dict[str, Any]]] = {"folga": [], "limite": [], "nao_roda": []}
    for m in modelos:
        footprint = float(m["size_gb"]) + _kv_e_buffers(m["size_gb"])
        if footprint <= usable * FOLGA_FRAC:
            verdict = "folga"
        elif footprint <= usable * LIMITE_FRAC:
            verdict = "limite"
        else:
            verdict = "nao_roda"
        item = {
            "nome": m["nome"], "params": m["params"], "quant": m["quant"],
            "size_gb": round(float(m["size_gb"]), 1),
            "footprint_gb": round(footprint, 1),
            "verdict": verdict,
            "gpu": _gpu_hint(float(m["size_gb"]), float(vram_gb), cuda_available),
        }
        if m.get("nucleo"):
            item["nucleo"] = m["nucleo"]
        if m.get("tag"):
            item["tag"] = m["tag"]
        grupos[verdict].append(item)
    return {
        "ram_total_gb": round(float(ram_gb), 2),
        "vram_gb": round(float(vram_gb), 2),
        "cuda_available": bool(cuda_available),
        "ram_util_estimada_gb": round(usable, 1),
        "reserva_so_gb": OS_RESERVE_GB,
        "grupos": grupos,
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


def build_report_text(diag: Dict[str, Any]) -> str:
    """Relatório .txt legível a partir do dict de diagnóstico completo."""
    hw = diag.get("hardware", {})
    adv = diag.get("gguf", {})
    L: List[str] = []
    L.append("DIAGNÓSTICO DE HARDWARE PARA IA LOCAL — NÚCLEO IA PORTÁTIL")
    L.append("=" * 68)
    L.append(f"Gerado em: {adv.get('gerado_em', '')}")
    L.append("")
    L.append("MÁQUINA")
    L.append("-" * 68)
    L.append(f"CPU            : {hw.get('cpu', '?')}")
    L.append(f"Núcleos/threads: {hw.get('physical_cores', '?')} / {hw.get('logical_threads', '?')}")
    L.append(f"RAM total      : {adv.get('ram_total_gb', '?')} GB "
             f"(disponível agora: {hw.get('ram_available_gb', '?')} GB)")
    L.append(f"GPU            : {hw.get('gpu_nome', 'nenhuma NVIDIA')} · VRAM {adv.get('vram_gb', 0)} GB")
    L.append(f"RAM útil p/ modelo (estimada): {adv.get('ram_util_estimada_gb', '?')} GB "
             f"(reserva SO {adv.get('reserva_so_gb', '?')} GB; llama.cpp usa mmap)")
    L.append("")
    if adv.get("pasta_modelos"):
        L.append(f"Modelos avaliados: somente os salvos em {adv['pasta_modelos']} "
                 f"({adv.get('total_modelos', 0)})")
        L.append("")
    rotulos = [("folga", "✅ RODA COM FOLGA (recomendado)"),
               ("limite", "⚠️  RODA NO LIMITE (feche apps; contexto curto; mais lento)"),
               ("nao_roda", "⛔ NÃO RODA (não cabe na RAM — entraria em swap)")]
    for chave, titulo in rotulos:
        L.append(titulo)
        L.append("-" * 68)
        itens = adv.get("grupos", {}).get(chave, [])
        if not itens:
            L.append("  (nenhum)")
        for m in itens:
            extra = ""
            if m.get("tag"):
                extra += f" [{m['tag']}]"
            if m.get("nucleo"):
                extra += f" [NÚCLEO:{m['nucleo']}]"
            L.append(f"  • {m['nome']} ({m['params']}, {m['quant']}) — "
                     f"~{m['size_gb']} GB · {m['gpu']}{extra}")
        L.append("")
    L.append("Observações: estimativas conservadoras. O consumo real varia com o")
    L.append("tamanho do contexto (KV cache), quantização, backend e nº de camadas")
    L.append("na GPU. 'Não roda' = inviável em RAM; ainda assim pode caber com quant")
    L.append("mais agressiva (IQ3/IQ2) ou contexto mínimo.")
    return "\n".join(L) + "\n"
