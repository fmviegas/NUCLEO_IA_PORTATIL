#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
biblia_ctx.py — condensa a BÍBLIA para caber no contexto, por PRIORIDADE de campo.

Antes: corte seco em N caracteres (b[:N]). Como o bloco de voz (viés, tique,
banidos, tetos) fica no FIM da bíblia, era justamente ele que se perdia.

Agora a bíblia é lida como campos ("Rótulo: valor", valor podendo seguir em
várias linhas) e, se passar do limite:
  0. campos só com placeholder ("[...]", "[definir — ...]") saem sempre;
  1. campos de prioridade baixa são ENCURTADOS (no fim de frase/palavra);
  2. se ainda não couber, são REMOVIDOS (do menos para o mais importante);
  3. em último caso os essenciais são encurtados — nunca removidos.
A ordem original dos campos é preservada.

API:
    condensar(texto, limite, foco="escrita"|"outline") -> str
"""
from __future__ import annotations

import re
import unicodedata

# prioridade: 0 = essencial (nunca sai) · 1 = importante · 2 = acessório
_PRIORIDADE = [
    # voz / estilo — molda a prosa de TODA cena
    ("vies", 0), ("tique", 0), ("nao usar", 0), ("tetos", 0), ("tom", 0),
    ("ponto de vista", 0), ("premissa", 0), ("promessa", 0),
    ("titulo", 0), ("genero:", 0),
    # núcleo da história / do livro técnico
    ("protagonista", 1), ("conflito", 1), ("personagens-chave", 1),
    ("tema", 1), ("tese", 1), ("estrutura", 1), ("publico", 1),
    ("tipo de livro", 1), ("area", 1), ("nivel", 1), ("ferramenta", 1),
    # acessório
    ("genero e subgenero", 2), ("epoca", 2), ("personagens secundarios", 2),
    ("fontes", 2), ("autor", 2), ("estagio", 2),
]
# no outline a espinha da história pesa mais que a voz
_BOOST_OUTLINE = {"estrutura": 0, "protagonista": 0, "conflito": 0, "personagens-chave": 0}

_CAMPO_RE = re.compile(r"^([A-Za-zÀ-ÿ][^:\n]{0,80}?):(\s.*|)$")
_VAZIO_RE = re.compile(r":\s*(\[[^\]]*\])?\s*$")   # "Rótulo:" ou "Rótulo: [placeholder]"
_CORTE_MIN = 160      # um campo encurtado mantém ao menos isto
_MARCA = " […]"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def _prioridade(rotulo: str, foco: str) -> int:
    r = _norm(rotulo)
    if foco == "outline":
        for chave, p in _BOOST_OUTLINE.items():
            if r.startswith(chave):
                return p
    # "Gênero e subgênero" tem de casar antes de "Gênero:"
    for chave, p in sorted(_PRIORIDADE, key=lambda x: -len(x[0])):
        if chave.endswith(":"):
            if r + ":" == chave:
                return p
        elif r.startswith(chave):
            return p
    return 1          # campo que o usuário acrescentou: importante por padrão


def _blocos(texto: str):
    """Quebra a bíblia em blocos [rotulo, linhas]. Linhas que não abrem campo
    (continuação de valor multi-linha, listas) ficam no bloco anterior."""
    blocos = [["", []]]
    for ln in texto.splitlines():
        if ln.startswith(">"):            # notas de preenchimento do template
            continue
        m = _CAMPO_RE.match(ln)
        h = re.match(r"^#{2,6}\s+(.+)$", ln)
        if m:
            blocos.append([m.group(1).strip(), [ln]])
        elif h:
            blocos.append([h.group(1).strip(), [ln]])
        else:
            blocos[-1][1].append(ln)
    return [b for b in blocos if any(x.strip() for x in b[1])]


def _so_placeholder(rotulo: str, linhas) -> bool:
    if not rotulo:
        return False
    corpo = "\n".join(linhas).strip()
    if "\n" in corpo:                  # valor multi-linha: tem conteúdo real
        return False
    # o rótulo pode ter ":" dentro (ex.: "Tetos (ex.: ...)"), então olha o FIM
    return bool(_VAZIO_RE.search(corpo))


def _encurtar(txt: str, alvo: int) -> str:
    if len(txt) <= alvo:
        return txt
    corte = txt[:max(alvo - len(_MARCA), 1)]
    fim = max(corte.rfind(". "), corte.rfind(".\n"), corte.rfind("; "))
    if fim >= alvo * 0.6:
        return corte[:fim + 1] + _MARCA
    esp = corte.rfind(" ")
    return (corte[:esp] if esp > alvo * 0.5 else corte).rstrip(" ,;:") + _MARCA


def condensar(texto: str, limite: int, foco: str = "escrita") -> str:
    texto = (texto or "").strip()
    if not texto:
        return ""
    itens = []
    for rot, linhas in _blocos(texto):
        if _so_placeholder(rot, linhas):
            continue
        itens.append({"p": _prioridade(rot, foco) if rot else 0,
                      "txt": "\n".join(linhas).strip("\n")})

    def total():
        vivos = [i["txt"] for i in itens if i["txt"]]
        return sum(len(t) for t in vivos) + max(len(vivos) - 1, 0)

    if total() <= limite:
        return "\n".join(i["txt"] for i in itens if i["txt"]).strip()

    # 1) encurta acessórios, depois importantes (os mais longos primeiro)
    for p in (2, 1):
        for i in sorted([i for i in itens if i["p"] == p], key=lambda i: -len(i["txt"])):
            excesso = total() - limite
            if excesso <= 0:
                break
            # corta só o que falta, sem descer abaixo do mínimo
            i["txt"] = _encurtar(i["txt"], max(len(i["txt"]) - excesso, _CORTE_MIN))
    # 2) remove acessórios, depois importantes (de baixo pra cima)
    for p in (2, 1):
        for i in reversed([i for i in itens if i["p"] == p]):
            if total() <= limite:
                break
            i["txt"] = ""
    # 3) último recurso: encurta os essenciais, o mais longo primeiro, até caber
    while total() > limite:
        vivos = [i for i in itens if i["txt"]]
        maior = max(vivos, key=lambda i: len(i["txt"]))
        excesso = total() - limite
        alvo = max(len(maior["txt"]) - excesso, _CORTE_MIN)
        novo = _encurtar(maior["txt"], alvo)
        if novo == maior["txt"] or len(novo) >= len(maior["txt"]):
            # nada mais a encurtar com folga: corte duro final, para garantir o teto
            out = "\n".join(i["txt"] for i in itens if i["txt"])
            return _encurtar(out, limite)
        maior["txt"] = novo
    return "\n".join(i["txt"] for i in itens if i["txt"]).strip()
