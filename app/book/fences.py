#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fences.py — saneia cercas de código (```) que o modelo deixa no texto do livro.

Problema: o modelo às vezes abre um ``` e não fecha (ou embrulha a resposta
inteira em ```markdown). Como as cenas são emendadas, um ``` aberto numa cena
"engole" tudo o que vem depois — no capítulo e no DOCX/EPUB (vira bloco de
código monoespaçado até o fim do arquivo).

Regras:
  * FICÇÃO: não há código — toda linha de cerca sai; o conteúdo fica.
  * TÉCNICO:
      1. resposta inteira embrulhada em ```markdown/```md/```text → desembrulha;
      2. cercas ```markdown/```md/```text no meio → saem (é prosa, não código);
      3. cerca aberta e não fechada → fecha ANTES do primeiro parágrafo de prosa
         que vier depois do código (ou no fim, se for tudo código); cerca aberta
         sem nada depois → sai.
Idempotente: rodar duas vezes dá o mesmo resultado.

API:
    sanear(texto, fiction) -> (texto, n_correcoes)
"""
from __future__ import annotations

import re

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+#.\-]*)\s*$")
_PROSA_LANGS = {"markdown", "md", "text", "txt", "plaintext", "prosa"}
_SIMBOLOS_CODIGO = set("=(){}[]<>;")


def _cerca(linha: str):
    m = _FENCE.match(linha)
    return (m.group(1)[0], m.group(2).lower()) if m else None


def _linha_prosa(ln: str) -> bool:
    s = ln.strip()
    if not s or not s[0].isalpha() or ln[:1] in (" ", "\t"):
        return False
    if len(s.split()) < 6:
        return False
    sim = sum(1 for c in s if c in _SIMBOLOS_CODIGO)
    return sim / len(s) < 0.02


def _paragrafo_prosa(linhas) -> bool:
    ls = [x for x in linhas if x.strip()]
    return bool(ls) and all(_linha_prosa(x) for x in ls)


def _fecha_aberta(linhas, i_abre):
    """Índice onde inserir o ``` de fechamento para uma cerca aberta em i_abre:
    antes do 1º parágrafo de prosa após o código; senão, no fim."""
    j, n = i_abre + 1, len(linhas)
    viu_codigo = False
    while j < n:
        if not linhas[j].strip():
            j += 1
            continue
        k = j
        while k < n and linhas[k].strip():
            k += 1
        par = linhas[j:k]
        if viu_codigo and _paragrafo_prosa(par):
            fim = j
            while fim > i_abre + 1 and not linhas[fim - 1].strip():
                fim -= 1
            return fim
        viu_codigo = True
        j = k
    fim = n
    while fim > i_abre + 1 and not linhas[fim - 1].strip():
        fim -= 1
    return fim


def sanear(texto: str, fiction: bool):
    if not texto or ("```" not in texto and "~~~" not in texto):
        return texto, 0
    linhas = texto.split("\n")
    n = 0

    if fiction:
        novas = [ln for ln in linhas if not _cerca(ln)]
        return "\n".join(novas), len(linhas) - len(novas)

    # 1) embrulho inteiro em ```markdown ... ```
    nao_vazias = [i for i, ln in enumerate(linhas) if ln.strip()]
    if len(nao_vazias) >= 2:
        a, b = nao_vazias[0], nao_vazias[-1]
        ca, cb = _cerca(linhas[a]), _cerca(linhas[b])
        if ca and cb and ca[1] in _PROSA_LANGS and not cb[1]:
            linhas = linhas[:a] + linhas[a + 1:b] + linhas[b + 1:]
            n += 1

    # 2) percorre: tira cercas de "prosa", fecha as abertas
    out, i, aberta = [], 0, None   # aberta = (indice_em_out, char)
    while i < len(linhas):
        ln = linhas[i]
        c = _cerca(ln)
        if c is None:
            out.append(ln)
        elif aberta is None:
            if c[1] in _PROSA_LANGS:
                # ```markdown no meio: só sai se tiver par; o conteúdo fica
                fecha = next((k for k in range(i + 1, len(linhas))
                              if (_c := _cerca(linhas[k])) and not _c[1]), None)
                if fecha is not None:
                    out.extend(linhas[i + 1:fecha])
                    n += 1
                    i = fecha + 1
                    continue
                n += 1           # sem par: só descarta a linha
            else:
                aberta = (len(out), c[0])
                out.append(ln)
        else:
            if not c[1] and c[0] == aberta[1]:
                aberta = None
            out.append(ln)
        i += 1

    if aberta is not None:
        idx = aberta[0]
        if not any(x.strip() for x in out[idx + 1:]):
            out = out[:idx] + out[idx + 1:]          # cerca aberta no vazio
        else:
            pos = _fecha_aberta(out, idx)
            out = out[:pos] + [aberta[1] * 3] + out[pos:]
        n += 1
        # o que vier depois do fechamento pode ter outra cerca solta: repete
        resto, m = sanear("\n".join(out), fiction=False)
        return resto, n + m
    return "\n".join(out), n
