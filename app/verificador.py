#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificador.py — verificação estática de código Python para o menu CÓDIGO.

Lê o código com `ast` (biblioteca padrão) e NUNCA o executa. Devolve FATOS
certos — erros de escrita que o modelo local pequeno (7B) deixa passar ou
erra ao explicar (teste real 18/11: 'BOLA2'/'Bold3'/'df_bold5' marcados como
"impacto baixo", def quebrado fora do Bloqueante):

  1. erro de sintaxe, com a linha (continua procurando depois de cada um);
  2. nome usado e nunca definido no código colado;
  3. nome de coluna quase igual a outro declarado no código ('BOLA2' x 'Bola2');
  4. várias colunas numa tupla df['a', 'b'] (o pandas pede lista df[['a', 'b']]).

Pega erro de ESCRITA, não de lógica: o resto continua com o modelo.
"""
from __future__ import annotations

import ast
import builtins
import re

MAX_FATOS = 15
_BLOCO = re.compile(r"```([^\n`]*)\n(.*?)(?:```|\Z)", re.S)
_TITULO = re.compile(r"^\s*(?:\*\*|`|#+\s*)?([\w./\\-]+\.\w+)(?:\*\*|`)?\s*:?\s*$")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__builtins__", "__spec__",
                                  "__package__", "__loader__", "__path__", "__annotations__"}


def _curto(s: str, n: int = 60) -> str:
    """Nome citado num fato nunca passa de n caracteres (um identificador gigante estouraria o prompt)."""
    return s if len(s) <= n else s[: n - 1] + "…"


def _blocos(codigo: str) -> list[tuple[str, str]]:
    """(nome, texto) de cada trecho Python. Sem cercas ``` = o campo inteiro é um trecho."""
    achados = list(_BLOCO.finditer(codigo))
    if not achados:
        return [("", codigo)]
    saida = []
    for m in achados:
        lang = m.group(1).strip().lower()
        if lang and lang not in ("python", "py", "python3", "pycon"):
            continue
        antes = codigo[:m.start()].rstrip().splitlines()
        nome = ""
        if antes:
            t = _TITULO.match(antes[-1])
            if t:
                nome = t.group(1)
        saida.append((nome, m.group(2)))
    return saida


def _sintaxe(texto: str) -> tuple[ast.AST | None, list[dict]]:
    """Faz o parse; a cada erro, neutraliza a linha (pass, ou 'if True:' se ela abria
    um bloco) e tenta de novo, para achar mais de um erro. Linhas não mudam de lugar."""
    linhas = texto.split("\n")
    erros, vistos = [], set()
    for _ in range(12):
        try:
            return ast.parse("\n".join(linhas)), erros
        except SyntaxError as e:
            n = e.lineno or 0
            if n < 1 or n > len(linhas) or n in vistos:
                return None, erros
            vistos.add(n)
            original = linhas[n - 1]
            erros.append({"linha": n, "tipo": "sintaxe",
                          "msg": f"erro de sintaxe ({_curto(str(e.msg), 80)}): `{_curto(original.strip(), 120)}`"})
            recuo = original[: len(original) - len(original.lstrip())]
            seguinte = next((l for l in linhas[n:] if l.strip()), "")
            abre_bloco = len(seguinte) - len(seguinte.lstrip()) > len(recuo)
            linhas[n - 1] = recuo + ("if True:" if abre_bloco else "pass")
    return None, erros


def _lev1(a: str, b: str) -> bool:
    """Distância de edição exatamente 1 (troca, inclusão ou remoção de um caractere).
    Diferença só num DÍGITO não conta: Bola1/Bola2 ou Bola/Bola1 são série, não erro."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        dif = [(x, y) for x, y in zip(a, b) if x != y]
        return len(dif) == 1 and not (dif[0][0].isdigit() and dif[0][1].isdigit())
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:] and not b[i].isdigit()


def _parecido(a: str, b: str) -> bool:
    return a != b and (a.lower() == b.lower() or _lev1(a.lower(), b.lower()))


def _melhor(nome: str, candidatos) -> str | None:
    """O parecido mais provável: primeiro só maiúscula/minúscula diferente, depois 1 letra."""
    cands = list(candidatos)
    return (next((c for c in cands if c != nome and c.lower() == nome.lower()), None)
            or next((c for c in cands if _parecido(nome, c)), None))


def _nomes(arvore: ast.AST) -> list[dict]:
    if any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names) for n in ast.walk(arvore)):
        return []          # import * define nomes que não dá para ver
    definidos = set(_BUILTINS)
    for n in ast.walk(arvore):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            definidos.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definidos.add(n.name)
        elif isinstance(n, ast.arg):
            definidos.add(n.arg)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                definidos.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            definidos.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            definidos.update(n.names)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            definidos.add(n.name)
    fatos, vistos = [], set()
    for n in ast.walk(arvore):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in definidos and n.id not in vistos:
            vistos.add(n.id)
            fatos.append({"linha": n.lineno, "tipo": "nome",
                          "msg": f"`{_curto(n.id)}` é usado mas não é definido em nenhum lugar do código colado "
                                 f"(NameError ao rodar, a menos que venha de outro arquivo)"})
    return fatos


def _colunas(arvore: ast.AST) -> list[dict]:
    """Nomes de coluna: strings usadas como chave (x['a']) ou em listas/tuplas de 2+ strings.
    Uma coluna citada uma vez só e quase igual a outra citada 2+ vezes é provável erro;
    um atributo df.X que não existe como string mas é quase igual a uma coluna, também."""
    contagem: dict[str, int] = {}
    linha_de: dict[str, int] = {}

    def conta(s: str, linha: int):
        if _IDENT.match(s) and len(s) >= 3:
            contagem[s] = contagem.get(s, 0) + 1
            linha_de.setdefault(s, linha)

    for n in ast.walk(arvore):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            conta(n.slice.value, n.lineno)
        elif isinstance(n, (ast.List, ast.Tuple)):
            strs = [e for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(strs) >= 2:
                for e in strs:
                    conta(e.value, e.lineno)
    todas_strings = {n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    fortes = sorted((s for s, c in contagem.items() if c >= 2), key=lambda s: -contagem[s])

    fatos, vistos = [], set()
    for s, c in contagem.items():
        if c == 1:
            alvo = _melhor(s, fortes)
            if alvo and s not in vistos:
                vistos.add(s)
                fatos.append({"linha": linha_de[s], "tipo": "coluna",
                              "msg": f"coluna '{_curto(s)}' aparece uma vez só e é quase igual a '{_curto(alvo)}' (usada em outros lugares) — provável erro de digitação"})
    for n in ast.walk(arvore):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.attr not in todas_strings:
            alvo = _melhor(n.attr, fortes) or _melhor(n.attr, contagem)   # prefere a coluna mais usada
            chave = f"{n.value.id}.{n.attr}"
            if alvo and chave not in vistos:
                vistos.add(chave)
                fatos.append({"linha": n.lineno, "tipo": "coluna",
                              "msg": f"`{_curto(chave)}` não existe como coluna no código; é quase igual a '{_curto(alvo)}' — "
                                     f"provável erro de digitação (AttributeError/KeyError ao rodar)"})
    return fatos


def _tuplas(arvore: ast.AST) -> list[dict]:
    fatos = []
    for n in ast.walk(arvore):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Tuple) and len(n.slice.elts) >= 2 \
                and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.slice.elts):
            nomes = ", ".join(repr(_curto(e.value, 30)) for e in n.slice.elts[:3]) + (", ..." if len(n.slice.elts) > 3 else "")
            fatos.append({"linha": n.lineno, "tipo": "tupla",
                          "msg": f"várias colunas numa tupla [{nomes}] — no pandas isso dá erro; use lista: [[{nomes}]]"})
    return fatos


def verificar_python(codigo: str) -> list[dict]:
    """Fatos [{arquivo, linha, tipo, msg}] do código Python colado (vazio = nada achado)."""
    fatos = []
    for nome, texto in _blocos(codigo or ""):
        if not texto.strip():
            continue
        arvore, erros = _sintaxe(texto)
        achados = list(erros)
        if arvore is not None:
            achados += _nomes(arvore) + _colunas(arvore) + _tuplas(arvore)
        for f in sorted(achados, key=lambda f: f["linha"]):
            fatos.append(dict(f, arquivo=nome))
    return fatos[:MAX_FATOS]


def formatar(fatos: list[dict]) -> str:
    """Linhas para o prompt e para a tela."""
    return "\n".join(
        f"- {(f['arquivo'] + ', ') if f.get('arquivo') else ''}linha {f['linha']}: {f['msg']}" for f in fatos)
