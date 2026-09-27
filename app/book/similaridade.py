#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
similaridade.py — Redundância SEMÂNTICA por frase (TF-IDF + cosseno), stdlib.

O dedup léxico (Jaccard de parágrafos, corte de refrão exato) não pega a
circularidade CONCEITUAL: a mesma tese reescrita com outras palavras, espalhada
em frases-tese ao longo do capítulo (padrão típico de modelos grandes). Este
módulo mede sobreposição temática por FRASE, ponderando termos distintivos
(TF-IDF), e RELATA pares suspeitos — sem apagar nada, porque muitos pares de
cosseno alto são legítimos (exemplos numéricos diferentes, paralelismos), e
deletar cegamente estragaria o texto. Cortar é decisão do autor.

Uso como módulo:
    from similaridade import analisar_livro, analisar_texto
API pura (sem I/O de rede), offline.
"""
from __future__ import annotations
import math
import re
import unicodedata
from collections import Counter

_STOP = set("""a o e de da do das dos em no na nos nas um uma uns umas por para com sem sob ao aos
as que se ou os foi ser sao e tem ter mais menos muito pouco ja como quando onde qual quais
seu sua seus suas isso isto esse essa este esta aquele aquela nao sim entre pois porque
mas porem entao aqui ali la cada todo toda todos todas qualquer ele ela eles elas voce
nos me te lhe lhes num numa dele dela deles delas ate sobre apenas so tambem depois antes
durante cujo cuja ser estar haver fazer pode deve ser esta sera""".split())


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _toks(s: str):
    return [t for t in re.findall(r"[a-z0-9]+", _norm(s)) if len(t) >= 3 and t not in _STOP]


def _sem_numeros(s: str) -> str:
    """Frase sem dígitos/símbolos, para detectar 'mesmo esqueleto, outro número'."""
    s = re.sub(r"[\d%.,:/+\-–—=]", " ", _norm(s))
    return " ".join(w for w in s.split() if len(w) >= 3 and w not in _STOP)


def frases(texto: str):
    """Frases de PROSA (ignora blocos de código, títulos, tabelas e citações)."""
    linhas, em_codigo, prosa = texto.splitlines(), False, []
    for ln in linhas:
        s = ln.strip()
        if s.startswith("```"):
            em_codigo = not em_codigo
            continue
        if em_codigo or not s or s.startswith(("#", ">", "|", "<!--")):
            continue
        prosa.append(s)
    txt = " ".join(prosa)
    fr = re.split(r"(?<=[.!?])\s+", txt)
    return [f.strip() for f in fr if len(f.split()) >= 6]


def _tfidf(docs_tok):
    n = len(docs_tok)
    df = Counter()
    for d in docs_tok:
        for t in set(d):
            df[t] += 1
    vecs = []
    for d in docs_tok:
        tf = Counter(d)
        v = {}
        for t, c in tf.items():
            idf = math.log((n + 1) / (df[t] + 1)) + 1
            v[t] = (c / len(d)) * idf
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / nrm for t, x in v.items()})
    return vecs


def _cos(a, b) -> float:
    small, big = (a, b) if len(a) < len(b) else (b, a)
    return sum(x * big.get(t, 0.0) for t, x in small.items())


def _variante_numerica(a: str, b: str) -> bool:
    """True se as frases são o MESMO esqueleto com números diferentes
    (ex.: 'F1 de 9,1%' vs 'F1 de 66,7%') — NÃO é redundância, é exemplo."""
    if not re.search(r"\d", a) or not re.search(r"\d", b):
        return False
    sa, sb = set(_sem_numeros(a).split()), set(_sem_numeros(b).split())
    if not sa or not sb:
        return False
    jac = len(sa & sb) / len(sa | sb)
    return jac >= 0.85


def analisar_texto(texto: str, limiar: float = 0.5, top: int = 40):
    """Pares de frases semanticamente próximos DENTRO de um texto.
    Retorna lista de dicts {score, i, j, a, b} já filtrada de variantes numéricas."""
    fr = frases(texto)
    if len(fr) < 2:
        return [], len(fr)
    vecs = _tfidf([_toks(f) for f in fr])
    pares = []
    for i in range(len(fr)):
        for j in range(i + 1, len(fr)):
            c = _cos(vecs[i], vecs[j])
            if c < limiar:
                continue
            if _variante_numerica(fr[i], fr[j]):
                continue
            pares.append({"score": round(c, 2), "i": i, "j": j, "a": fr[i], "b": fr[j]})
    pares.sort(key=lambda p: -p["score"])
    return pares[:top], len(fr)


def analisar_livro(files, limiar: float = 0.5):
    """Redundância semântica INTRA-capítulo (por arquivo) e CROSS-capítulo.
    `files` é lista de Path. Retorna dict {intra: {nome: pares}, cross: [...]}."""
    from pathlib import Path
    intra = {}
    corpora = []
    for f in files:
        f = Path(f)
        texto = f.read_text(encoding="utf-8-sig", errors="replace")
        pares, n = analisar_texto(texto, limiar=limiar)
        intra[f.name] = {"pares": pares, "frases": n}
        corpora.append((f.name, frases(texto)))

    # cross-capítulo: frases de arquivos diferentes muito próximas
    cross = []
    flat = [(nome, k, fr) for nome, lst in corpora for k, fr in enumerate(lst)]
    if len(flat) >= 2:
        vecs = _tfidf([_toks(fr) for _, _, fr in flat])
        for x in range(len(flat)):
            for y in range(x + 1, len(flat)):
                if flat[x][0] == flat[y][0]:
                    continue  # mesmo arquivo já coberto no intra
                c = _cos(vecs[x], vecs[y])
                if c < max(limiar, 0.55):
                    continue
                if _variante_numerica(flat[x][2], flat[y][2]):
                    continue
                cross.append({"score": round(c, 2),
                              "entre": f"{flat[x][0]} × {flat[y][0]}",
                              "a": flat[x][2], "b": flat[y][2]})
        cross.sort(key=lambda p: -p["score"])
        cross = cross[:20]
    return {"intra": intra, "cross": cross}
