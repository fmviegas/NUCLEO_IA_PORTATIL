#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificador.py — verificação estática de código Python para o menu CÓDIGO.

Lê o código com `ast` (biblioteca padrão) e NUNCA o executa. Devolve FATOS
que o modelo local pequeno (7B) deixa passar ou erra ao explicar.

CERTOS, gravidade "bloqueante":
  1. erro de sintaxe, com a linha (continua procurando depois de cada um);
  2. nome usado e nunca definido no código colado;
  3. nome de coluna quase igual a outro declarado no código ('BOLA2' x 'Bola2');
  4. várias colunas numa tupla df['a', 'b'] (o pandas pede lista df[['a', 'b']]);
  5. .resample() com texto que não é frequência do pandas ('Data' em vez de 'MS'),
     direto ou como valor padrão do parâmetro passado.

SUSPEITAS de lógica, gravidade "conferir" (podem ser intencionais):
  6. função que diz devolver "todos/todas/cada" mas pega só o 1º elemento;
  7. arquivo que só define funções e não chama nenhuma (sem main);
  8. df[[várias colunas]].value_counts(): conta COMBINAÇÕES de linhas, não valores
     (teste real 18/11: o gráfico de frequência saiu com 40 barras de valor 1);
  9. função definida e nunca chamada (código morto esconde erro: o resample('Data')
     ficou numa função que ninguém chamava).

TROCA EXATA: quando a correção é certa (3, 4, 5, 8), o fato traz a posição e o
texto novo. aplicar_trocas() faz as trocas sem o modelo — o 7B devolveu duas
vezes o mesmo código com o mesmo erro quando pedimos para ele corrigir.
"""
from __future__ import annotations

import ast
import builtins
import re
import unicodedata

try:        # nomes de atributos/métodos de pandas, numpy, matplotlib e da biblioteca padrão
    from verificador_api import NOMES_DE_API
except ImportError:                                   # pragma: no cover
    NOMES_DE_API = frozenset()

MAX_FATOS = 20
_BLOCO = re.compile(r"```([^\n`]*)\n(.*?)(?:```|\Z)", re.S)
_TITULO = re.compile(r"^\s*(?:\*\*|`|#+\s*)?([\w./\\-]+\.\w+)(?:\*\*|`)?\s*:?\s*$")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__builtins__", "__spec__",
                                  "__package__", "__loader__", "__path__", "__annotations__"}
_LINGUAGENS_PY = ("python", "py", "python3", "pycon")


def _curto(s: str, n: int = 60) -> str:
    """Nome citado num fato nunca passa de n caracteres (um identificador gigante estouraria o prompt)."""
    return s if len(s) <= n else s[: n - 1] + "…"


def _mostra(s: str, n: int = 90) -> str:
    """Trecho de código numa linha só, para mensagem."""
    return _curto(re.sub(r"\s+", " ", s).strip(), n)


# ----------------------------------------------------------------- blocos de código

def _blocos(codigo: str, estrito: bool = False) -> list[tuple[str, str, int, int]]:
    """(nome, texto, ini, fim) de cada trecho Python; ini/fim = posição do texto em `codigo`.
    Sem cercas ``` = o campo inteiro é um trecho. estrito (resposta do modelo): bloco sem
    linguagem só conta se tiver cara de Python — um ``` com 'python app/main.py' não é código."""
    achados = list(_BLOCO.finditer(codigo))
    if not achados:
        return [] if estrito else [("", codigo, 0, len(codigo))]
    saida = []
    for m in achados:
        lang = m.group(1).strip().lower()
        if lang and lang not in _LINGUAGENS_PY:
            continue
        if estrito and not lang and not re.search(r"^\s*(import |from \w|def |class )", m.group(2), re.M):
            continue
        antes = codigo[:m.start()].rstrip().splitlines()
        nome = ""
        if antes:
            t = _TITULO.match(antes[-1])
            if t:
                nome = t.group(1)
        saida.append((nome, m.group(2), m.start(2), m.end(2)))
    return saida


# ----------------------------------------------------------------- sintaxe e posições

def _sintaxe(texto: str) -> tuple[ast.AST | None, list[dict], str]:
    """Faz o parse; a cada erro, neutraliza a linha (pass, ou 'if True:' se ela abria um
    bloco) e tenta de novo, para achar mais de um erro. Devolve também o texto reparado
    (mesmo número de linhas: só as linhas com erro mudam)."""
    linhas = texto.split("\n")
    erros, vistos = [], set()
    for _ in range(12):
        try:
            return ast.parse("\n".join(linhas)), erros, "\n".join(linhas)
        except SyntaxError as e:
            n = e.lineno or 0
            if n < 1 or n > len(linhas) or n in vistos:
                return None, erros, "\n".join(linhas)
            vistos.add(n)
            original = linhas[n - 1]
            erros.append({"linha": n, "tipo": "sintaxe",
                          "msg": f"erro de sintaxe ({_curto(str(e.msg), 80)}): `{_curto(original.strip(), 120)}`"})
            recuo = original[: len(original) - len(original.lstrip())]
            seguinte = next((l for l in linhas[n:] if l.strip()), "")
            abre_bloco = len(seguinte) - len(seguinte.lstrip()) > len(recuo)
            linhas[n - 1] = recuo + ("if True:" if abre_bloco else "pass")
    return None, erros, "\n".join(linhas)


class _Fonte:
    """Posição de um nó do AST no texto ORIGINAL. O parse pode ter usado linhas
    neutralizadas (erro de sintaxe), mas as outras linhas são idênticas; as colunas
    do AST são em bytes UTF-8 e viram posição de caractere aqui."""

    def __init__(self, original: str, reparado: str):
        self.t = original
        self.rep = reparado.split("\n")
        self.ini = [0]
        for linha in original.split("\n")[:-1]:
            self.ini.append(self.ini[-1] + len(linha) + 1)

    def _pos(self, ln: int, col: int) -> int:
        return self.ini[ln - 1] + len(self.rep[ln - 1].encode("utf-8")[:col].decode("utf-8", "ignore"))

    def span(self, n: ast.AST) -> tuple[int, int]:
        return self._pos(n.lineno, n.col_offset), self._pos(n.end_lineno, n.end_col_offset)

    def seg(self, n: ast.AST) -> str:
        a, b = self.span(n)
        return self.t[a:b]

    def troca(self, n: ast.AST, para: str) -> dict:
        a, b = self.span(n)
        return {"ini": a, "fim": b, "de": self.t[a:b], "para": para}


def _com_troca(fato: dict, troca: dict | None) -> dict:
    if troca and troca["de"] != troca["para"]:
        fato["troca"] = troca
        fato["msg"] += f" — troque `{_mostra(troca['de'], 160)}` por `{_mostra(troca['para'], 160)}`"
    return fato


# ----------------------------------------------------------------- semelhança de nomes

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


# ----------------------------------------------------------------- checagens certas

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


def _colunas(arvore: ast.AST, fonte: _Fonte) -> list[dict]:
    """Nomes de coluna: strings usadas como chave (x['a']) ou em listas/tuplas de 2+ strings.
    Uma coluna citada uma vez só e quase igual a outra citada 2+ vezes é provável erro;
    um atributo df.X que não existe como string mas é quase igual a uma coluna, também."""
    contagem: dict[str, int] = {}
    no_de: dict[str, ast.Constant] = {}

    def conta(no: ast.Constant):
        s = no.value
        if _IDENT.match(s) and len(s) >= 3:
            contagem[s] = contagem.get(s, 0) + 1
            no_de.setdefault(s, no)

    for n in ast.walk(arvore):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            conta(n.slice)
        elif isinstance(n, (ast.List, ast.Tuple)):
            strs = [e for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(strs) >= 2:
                for e in strs:
                    conta(e)
    todas_strings = {n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    fortes = sorted((s for s, c in contagem.items() if c >= 2), key=lambda s: -contagem[s])

    fatos, vistos = [], set()
    for s, c in contagem.items():
        if c == 1:
            alvo = _melhor(s, fortes)
            if alvo and s not in vistos:
                vistos.add(s)
                no = no_de[s]
                fatos.append(_com_troca(
                    {"linha": no.lineno, "tipo": "coluna",
                     "msg": f"coluna '{_curto(s)}' aparece uma vez só e é quase igual a '{_curto(alvo)}' "
                            f"(usada em outros lugares) — provável erro de digitação"},
                    fonte.troca(no, fonte.seg(no).replace(s, alvo, 1))))
    for n in ast.walk(arvore):
        # atributo que é API da biblioteca (df.values, s.index, ax.plot...) nunca é "coluna errada":
        # teste real 18/11 — com uma coluna 'value', ball_counts.values virou ball_counts.value
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.attr not in todas_strings \
                and n.attr not in NOMES_DE_API:
            alvo = _melhor(n.attr, fortes) or _melhor(n.attr, contagem)   # prefere a coluna mais usada
            if alvo and (n.attr.lower() == alvo.lower() + "s" or alvo.lower() == n.attr.lower() + "s"):
                alvo = None                     # singular/plural: ambíguo demais para afirmar erro
            chave = f"{n.value.id}.{n.attr}"
            if alvo and chave not in vistos:
                vistos.add(chave)
                fatos.append(_com_troca(
                    {"linha": n.lineno, "tipo": "coluna",
                     "msg": f"`{_curto(chave)}` não existe como coluna no código; é quase igual a '{_curto(alvo)}' — "
                            f"provável erro de digitação (AttributeError/KeyError ao rodar)"},
                    fonte.troca(n, f"{n.value.id}.{alvo}")))
    return fatos


def _tuplas(arvore: ast.AST, fonte: _Fonte) -> list[dict]:
    fatos = []
    for n in ast.walk(arvore):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Tuple) and len(n.slice.elts) >= 2 \
                and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.slice.elts):
            nomes = ", ".join(repr(_curto(e.value, 30)) for e in n.slice.elts[:3]) + (", ..." if len(n.slice.elts) > 3 else "")
            fatos.append(_com_troca(
                {"linha": n.lineno, "tipo": "tupla",
                 "msg": f"várias colunas numa tupla [{nomes}] — no pandas isso dá erro; use lista: [[{nomes}]]"},
                fonte.troca(n.slice, "[" + fonte.seg(n.slice) + "]")))
    return fatos


# Frequências (offset aliases) do pandas, sem diferenciar maiúsculas: um componente com
# multiplicador e âncora opcionais ('MS', '15min', 'W-SUN', 'QS-JAN') ou vários, cada um
# com número ('1h30min'). 'Data' não casa — e é o erro que o 7B repetiu.
_ALIAS = (r"(?:CBMS|CBME|CBM|CBH|BMS|BME|BQS|BQE|BYS|BYE|BAS|SMS|SME|WOM|MIN|BM|BQ|BY|BA|BH|SM|ME|MS|QE|QS"
          r"|YE|YS|AS|US|NS|B|C|D|W|M|Q|Y|A|H|T|S|L|U|N)")
_FREQ = re.compile(rf"^(?:\d*{_ALIAS}(?:-[A-Z0-9]{{3,4}})?|(?:\d+{_ALIAS})+)$", re.I)


def _resample(arvore: ast.AST, fonte: _Fonte) -> list[dict]:
    """df.resample(regra): regra de texto que não é frequência do pandas -> ValueError ao rodar."""
    fatos = []
    padroes_por_no = {}
    for fn in ast.walk(arvore):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = fn.args
            pos = a.posonlyargs + a.args
            pad = {arg.arg: d for arg, d in zip(pos[len(pos) - len(a.defaults):], a.defaults)}
            pad.update({arg.arg: d for arg, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None})
            for n in ast.walk(fn):
                padroes_por_no[id(n)] = pad
    for n in ast.walk(arvore):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "resample"):
            continue
        regra = n.args[0] if n.args else next((k.value for k in n.keywords if k.arg == "rule"), None)
        texto, via = None, ""
        if isinstance(regra, ast.Constant) and isinstance(regra.value, str):
            texto = regra.value
        elif isinstance(regra, ast.Name):
            d = padroes_por_no.get(id(n), {}).get(regra.id)
            if isinstance(d, ast.Constant) and isinstance(d.value, str):
                texto, via = d.value, f" (valor padrão do parâmetro `{_curto(regra.id, 30)}`)"
        if texto is not None and not _FREQ.match(texto.strip()):
            a_c, b_c = fonte.span(n)
            a_r, b_r = fonte.span(regra)
            troca = {"ini": a_c, "fim": b_c, "de": fonte.t[a_c:b_c],
                     "para": fonte.t[a_c:a_r] + "'MS'" + fonte.t[b_r:b_c]}
            fatos.append(_com_troca(
                {"linha": n.lineno, "tipo": "resample",
                 "msg": f"`.resample('{_curto(texto, 30)}'...)`{via}: '{_curto(texto, 30)}' não é uma frequência "
                        f"do pandas (ex.: 'D', 'W', 'MS' = mensal, 'ME', 'YS') — ValueError ao rodar"},
                troca))
    return fatos


# ----------------------------------------------------------------- suspeitas

def _sem_chamada(arvore: ast.AST, linhas: int) -> list[dict]:
    """O arquivo define funções mas nada no nível do módulo chama coisa alguma
    (sem `if __name__ == '__main__'`, sem main()) — rodar o arquivo não faz nada."""
    corpo = getattr(arvore, "body", [])
    defs = [s for s in corpo if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not defs or any(d.name.startswith("test") for d in defs):    # arquivo de pytest: é assim mesmo
        return []
    executa = [s for s in corpo if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                                      ast.Import, ast.ImportFrom))
               and any(isinstance(x, ast.Call) for x in ast.walk(s))]
    if executa:
        return []
    return [{"linha": max(linhas, 1), "tipo": "sem_chamada", "gravidade": "conferir",
             "msg": f"o arquivo define {len(defs)} função(ões) mas não chama nenhuma e não tem "
                    f"`if __name__ == \"__main__\":` — rodar este arquivo não faz nada "
                    f"(se for um módulo importado por outro, ignore)"}]


def _nao_usadas(arvore: ast.AST) -> list[dict]:
    """Função do módulo definida e nunca citada (nem chamada, nem passada adiante).
    Decoradas (rotas), privadas (_x), main e testes ficam de fora."""
    defs = [s for s in getattr(arvore, "body", [])
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and not s.decorator_list
            and not s.name.startswith(("_", "test")) and s.name != "main"]
    if not defs:
        return []
    citados = ({n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)}
               | {n.attr for n in ast.walk(arvore) if isinstance(n, ast.Attribute)}
               | {n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant) and isinstance(n.value, str)})
    return [{"linha": d.lineno, "tipo": "nao_usada", "gravidade": "conferir",
             "msg": f"`{_curto(d.name)}` é definida mas nunca é chamada — código morto esconde erro "
                    f"(ninguém roda o que está nela); use-a ou apague"}
            for d in defs if d.name not in citados]


def _value_counts(arvore: ast.AST, fonte: _Fonte) -> list[dict]:
    """df[['a', 'b', ...]].value_counts() conta COMBINAÇÕES de linhas (cada linha inteira),
    não cada valor — num sorteio, cada concurso vira uma barra com valor 1."""
    pd_alias = next((a.asname or a.name for n in ast.walk(arvore) if isinstance(n, ast.Import)
                     for a in n.names if a.name == "pandas"), None)
    fatos = []
    for n in ast.walk(arvore):
        if not (isinstance(n, ast.Call) and not n.args and not n.keywords and isinstance(n.func, ast.Attribute)
                and n.func.attr == "value_counts"):
            continue
        sub = n.func.value
        if isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.List) and len(sub.slice.elts) >= 2 \
                and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in sub.slice.elts):
            troca = fonte.troca(n, f"{pd_alias}.Series({fonte.seg(sub)}.to_numpy().ravel()).value_counts()") \
                if pd_alias else None
            fatos.append(_com_troca(
                {"linha": n.lineno, "tipo": "value_counts", "gravidade": "conferir",
                 "msg": f"`.value_counts()` em várias colunas ({len(sub.slice.elts)}) conta COMBINAÇÕES de linhas "
                        f"(cada linha inteira), não cada valor — para contar os valores, junte as colunas antes"},
                troca))
    return fatos


_PROMETE_TODOS = re.compile(r"\b(todos|todas|cada|all|every|each)\b")


def _sem_acento(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _so_o_primeiro(arvore: ast.AST) -> list[dict]:
    """A função promete 'todos/todas/cada' no nome ou na docstring, mas indexa [0] —
    devolve só o primeiro elemento. Uma vez por função."""
    fatos = []
    for fn in ast.walk(arvore):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        promessa = _sem_acento(fn.name.replace("_", " ") + " " + (ast.get_docstring(fn) or ""))
        if not _PROMETE_TODOS.search(promessa):
            continue
        no_return = {id(n) for r in ast.walk(fn) if isinstance(r, ast.Return) and r.value is not None
                     for n in ast.walk(r.value)}

        def _linha_pandas(v: ast.AST) -> bool:      # df.values[0], df.iloc[0], s.to_numpy()[0]
            return (isinstance(v, ast.Attribute) and v.attr in ("values", "iloc", "array")) or (
                isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr in ("to_numpy", "tolist"))

        # [0] comum (partes[0] num laço "para cada linha") não conta: só acesso de linha do
        # pandas ou [0] dentro do valor devolvido
        usos = [n for n in ast.walk(fn)
                if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and n.slice.value == 0
                and (_linha_pandas(n.value) or id(n) in no_return)]
        if usos:
            trecho = _curto(ast.unparse(usos[0]), 50)
            fatos.append({"linha": usos[0].lineno, "tipo": "primeiro", "gravidade": "conferir",
                          "msg": f"`{fn.name}` diz devolver todos/cada, mas pega só o primeiro elemento "
                                 f"(`{trecho}`{f', e mais {len(usos) - 1} vez(es)' if len(usos) > 1 else ''}) "
                                 f"— confira se não deveria usar todas as linhas"})
    return fatos


# ----------------------------------------------------------------- API

def _arquivo_completo(arvore: ast.AST) -> bool:
    """Bloco que é um ARQUIVO inteiro, não um trecho: começa com import (depois da docstring)
    e tem `if __name__` ou 3+ funções. Teste real 18/11: na Revisar o ajuste devolveu o
    arquivo inteiro sem main, e a conferência em modo "trechos" não avisou."""
    corpo = [s for s in getattr(arvore, "body", [])
             if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
    if not corpo or not isinstance(corpo[0], (ast.Import, ast.ImportFrom)):
        return False
    tem_main = any(isinstance(s, ast.If) and "__name__" in ast.unparse(s.test) for s in corpo)
    n_defs = sum(isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for s in corpo)
    return tem_main or n_defs >= 3


def _fatos_bloco(nome: str, texto: str, completo: bool, n_blocos: int) -> tuple[list[dict], list[dict]]:
    """(certos, suspeitas) de um bloco, já com arquivo e gravidade. completo=False (trechos de
    Revisar/Depurar) vira True quando o bloco é claramente um arquivo inteiro."""
    arvore, erros, reparado = _sintaxe(texto)
    certos, suspeitas = list(erros), []
    if arvore is not None and not completo:
        completo = _arquivo_completo(arvore)
    if arvore is not None:
        fonte = _Fonte(texto, reparado)
        certos += _colunas(arvore, fonte) + _tuplas(arvore, fonte) + _resample(arvore, fonte)
        if completo:
            certos += _nomes(arvore)
            # vários arquivos na resposta: módulos que só definem funções são normais
            sem_chamada = _sem_chamada(arvore, len(texto.rstrip().split("\n"))) if n_blocos == 1 else []
            nao_usadas = _nao_usadas(arvore) if n_blocos == 1 and not sem_chamada else []
            suspeitas += _so_o_primeiro(arvore) + _value_counts(arvore, fonte) + sem_chamada + nao_usadas
    certos = [dict(f, arquivo=nome, gravidade="bloqueante") for f in sorted(certos, key=lambda f: f["linha"])]
    suspeitas = [dict(f, arquivo=nome) for f in sorted(suspeitas, key=lambda f: f["linha"])]
    return certos, suspeitas


def verificar_python(codigo: str, resposta: bool = False, completo: bool = True) -> list[dict]:
    """Fatos [{arquivo, linha, tipo, gravidade, msg, troca?}] do código Python (vazio = nada achado).
    Os certos (bloqueante) vêm antes das suspeitas (conferir).
    resposta=True: confere a RESPOSTA do modelo (só blocos ```python ou com cara de Python).
    completo=False: são trechos (Revisar/Depurar mostram só a função alterada) — sem nome
    indefinido nem suspeitas, que num trecho solto (sem os imports) seriam alarme falso."""
    blocos = [b for b in _blocos(codigo or "", estrito=resposta) if b[1].strip()]
    certos, suspeitas = [], []
    for nome, texto, _, _ in blocos:
        c, s = _fatos_bloco(nome, texto, completo, len(blocos))
        certos += c
        suspeitas += s
    return (certos + suspeitas)[:MAX_FATOS]


def aplicar_trocas(resposta: str, completo: bool = True) -> dict:
    """Faz as TROCAS EXATAS no código da resposta, sem o modelo. Devolve:
    resposta = o texto inteiro com os blocos trocados; markdown = só os blocos que mudaram
    (para mostrar); trocas = [{arquivo, linha, de, para, gravidade}]."""
    blocos = [b for b in _blocos(resposta or "", estrito=True) if b[1].strip()]
    nova, partes, feitas = resposta or "", [], []
    for nome, texto, ini, fim in reversed(blocos):          # de trás para frente: posições valem
        c, s = _fatos_bloco(nome, texto, completo, len(blocos))
        com_troca = sorted((f for f in c + s if f.get("troca")), key=lambda f: -f["troca"]["ini"])
        novo, usados = texto, []
        for f in com_troca:
            a, b = f["troca"]["ini"], f["troca"]["fim"]
            if novo[a:b] != f["troca"]["de"] or any(a < y and b > x for x, y in usados):
                continue                                    # trocas que se sobrepõem: só a 1ª
            novo = novo[:a] + f["troca"]["para"] + novo[b:]
            usados.append((a, b))
            feitas.append({"arquivo": nome, "linha": f["linha"], "gravidade": f["gravidade"],
                           "de": _mostra(f["troca"]["de"], 160), "para": _mostra(f["troca"]["para"], 160)})
        if novo != texto:
            nova = nova[:ini] + novo + nova[fim:]
            partes.insert(0, (f"**{nome}**\n" if nome else "") + "```python\n" + novo.rstrip("\n") + "\n```")
    feitas.sort(key=lambda t: (t["arquivo"], t["linha"]))
    return {"resposta": nova, "markdown": "\n\n".join(partes), "trocas": feitas}


def formatar(fatos: list[dict]) -> str:
    """Linhas para o prompt e para a tela, com a gravidade na frente de cada uma."""
    return "\n".join(
        f"- [{'Conferir' if f.get('gravidade') == 'conferir' else 'Bloqueante'}] "
        f"{(f['arquivo'] + ', ') if f.get('arquivo') else ''}linha {f['linha']}: {f['msg']}" for f in fatos)
