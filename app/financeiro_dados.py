#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
financeiro_dados.py — módulo FINANCEIRO no painel (fase B).

Espelha a planilha do usuário (cópia local em workspace/financeiro/modelo/ControleFinanceiro.xlsx):
12 meses de entradas/saídas, resumo U5–U10, cartão (grade mensal), contas
(saldo anterior/entrada/saída/líquido por mês) e evolução anual. Um arquivo por
ano em workspace/financeiro/<ano>.json (local, fora do git).

  carregar(ano)            -> dados (novo ano herda saldo/contas/cadastro do anterior)
  salvar(ano, dados)       -> dados normalizados (gravação atômica)
  anos()                   -> [anos com arquivo]
  calcular(dados)          -> números idênticos às fórmulas da planilha
  exportar(ano, versao)    -> (bytes, nome): a planilha preenchida com os dados
  prompt_analise(ano)      -> texto p/ a IA local analisar o ano (sem inventar números)

As fórmulas aqui e em ui/financeiro_calc.js (cálculo ao vivo no painel) seguem a
planilha; tools/testar_financeiro_modulo.py confere os três contra o Excel.
"""
from __future__ import annotations

import copy
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import financeiro as F

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "workspace" / "financeiro"

MAX_LINHAS_MES = 50       # linhas 6..55 de cada aba mensal
MAX_CARTAO = 100          # linhas 17..116 do C.Crédito
MAX_CONTAS = 7            # linhas 4..10 de Contas e Cadastro
MAX_TIPOS = 13            # receitas D14:D26, despesas D29:D41
MAX_TXT = 120
STATUS = ("", "Sim", "Não")

RECEITAS_PADRAO = ["Salário", "Investimentos", "Juros", "Outros"]
DESPESAS_PADRAO = ["Alimentação", "Educação", "Higiene", "Impostos", "Lazer",
                   "Moradia", "Saúde", "Seguros", "Transporte"]
MESES = F.MESES
MESES_NOME = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
              "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


# ---------------------------------------------------------------------------
# modelo / normalização
# ---------------------------------------------------------------------------

def vazio(ano: int) -> dict:
    return {
        "versao": 1, "ano": int(ano),
        "cadastro": {"receitas": list(RECEITAS_PADRAO), "despesas": list(DESPESAS_PADRAO)},
        "meses": [{"entradas": [], "saidas": [], "investimento": 0.0, "saldo_inicial": 0.0}
                  for _ in range(12)],
        "cartao": [],
        "contas": [],
    }


def _ano(ano) -> int:
    a = int(ano)
    if not 2000 <= a <= 2100:
        raise ValueError("ano fora do intervalo 2000–2100")
    return a


def _num(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        x = float(v)
    else:
        s = str(v).strip().replace("R$", "").replace(" ", "")
        if "," in s:                       # pt-BR: 1.234,56
            s = s.replace(".", "").replace(",", ".")
        x = float(s)
    if x != x or abs(x) > 1e12:            # NaN / absurdo
        raise ValueError("valor numérico inválido")
    return round(x, 2)


def _txt(v) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()[:MAX_TXT]


def _dia(v):
    if v in (None, ""):
        return None
    d = int(float(v))
    return d if 1 <= d <= 31 else None


def _status(v) -> str:
    s = _txt(v)
    if s.lower() in ("nao", "não", "n"):
        return "Não"
    if s.lower() in ("sim", "s"):
        return "Sim"
    return ""


def _linha(l: dict, campo_status: str) -> dict:
    return {"descricao": _txt(l.get("descricao")), "tipo": _txt(l.get("tipo")),
            "valor": _num(l.get("valor")), "dia": _dia(l.get("dia")),
            campo_status: _status(l.get(campo_status))}


def _vazia(l: dict) -> bool:
    return not (l["descricao"] or l["tipo"] or l["valor"] or l["dia"])


def normalizar(d: dict, ano: int) -> dict:
    """Valida e limita tudo ao que cabe na planilha (linhas, tipos, contas)."""
    out = vazio(ano)
    cad = d.get("cadastro") or {}
    for k, padrao in (("receitas", RECEITAS_PADRAO), ("despesas", DESPESAS_PADRAO)):
        lst = [_txt(x) for x in (cad.get(k) if isinstance(cad.get(k), list) else padrao)]
        out["cadastro"][k] = [x for x in lst if x][:MAX_TIPOS]
    meses = d.get("meses") if isinstance(d.get("meses"), list) else []
    for i in range(12):
        m = meses[i] if i < len(meses) and isinstance(meses[i], dict) else {}
        ent = [_linha(l, "recebido") for l in (m.get("entradas") or []) if isinstance(l, dict)]
        sai = [_linha(l, "pago") for l in (m.get("saidas") or []) if isinstance(l, dict)]
        ent = [l for l in ent if not _vazia(l)]
        sai = [l for l in sai if not _vazia(l)]
        if len(ent) > MAX_LINHAS_MES or len(sai) > MAX_LINHAS_MES:
            raise ValueError(f"{MESES_NOME[i]}: no máximo {MAX_LINHAS_MES} entradas e "
                             f"{MAX_LINHAS_MES} saídas (limite da planilha)")
        out["meses"][i] = {"entradas": ent, "saidas": sai,
                           "investimento": _num(m.get("investimento")),
                           "saldo_inicial": _num(m.get("saldo_inicial")) if i == 0 else 0.0}
    cartao = []
    for c in (d.get("cartao") or []):
        if not isinstance(c, dict):
            continue
        ms = c.get("meses") if isinstance(c.get("meses"), list) else []
        linha = {"cartao": _txt(c.get("cartao")), "descricao": _txt(c.get("descricao")),
                 "valor_total": _num(c.get("valor_total")),
                 "parcelas": int(_num(c.get("parcelas"))) if c.get("parcelas") not in (None, "") else None,
                 "meses": [_num(ms[k]) if k < len(ms) else 0.0 for k in range(12)]}
        if linha["cartao"] or linha["descricao"] or linha["valor_total"] or any(linha["meses"]):
            cartao.append(linha)
    if len(cartao) > MAX_CARTAO:
        raise ValueError(f"cartão: no máximo {MAX_CARTAO} lançamentos (limite da planilha)")
    out["cartao"] = cartao
    contas = []
    for c in (d.get("contas") or []):
        if not isinstance(c, dict):
            continue
        ms = c.get("meses") if isinstance(c.get("meses"), list) else []
        contas.append({"nome": _txt(c.get("nome")), "saldo_inicial": _num(c.get("saldo_inicial")),
                       "meses": [{"entrada": _num((ms[k] or {}).get("entrada")) if k < len(ms) and isinstance(ms[k], dict) else 0.0,
                                  "saida": _num((ms[k] or {}).get("saida")) if k < len(ms) and isinstance(ms[k], dict) else 0.0}
                                 for k in range(12)]})
    if len(contas) > MAX_CONTAS:
        raise ValueError(f"no máximo {MAX_CONTAS} contas (limite da planilha)")
    out["contas"] = contas
    return out


# ---------------------------------------------------------------------------
# cálculo (espelho das fórmulas da planilha)
# ---------------------------------------------------------------------------

def calcular(d: dict) -> dict:
    meses, saldo_ant, investido = [], None, 0.0
    for i, m in enumerate(d["meses"]):
        u5 = round(sum(l["valor"] for l in m["entradas"]), 2)            # G56
        u6 = round(sum(l["valor"] for l in m["saidas"]), 2)              # O56
        u7 = round(u5 - u6, 2)
        u8 = m["investimento"]
        u9 = m["saldo_inicial"] if i == 0 else saldo_ant                 # Fev..Dez: =mês anterior!U10
        u10 = round((u7 + u9) - u8, 2)
        saldo_ant = u10
        investido = round(investido + u8, 2)                              # Evolução linha 42
        meses.append({
            "entradas": u5, "saidas": u6, "diferenca": u7, "investimento": u8,
            "saldo_anterior": round(u9, 2), "saldo_global": u10, "investido_acumulado": investido,
            "pct_entradas": [round(l["valor"] / u5, 6) if u5 else None for l in m["entradas"]],
            "pct_saidas": [round(l["valor"] / u6, 6) if u6 else None for l in m["saidas"]],
            "a_pagar": round(sum(l["valor"] for l in m["saidas"] if l["pago"] == "Não"), 2),
            "a_receber": round(sum(l["valor"] for l in m["entradas"] if l["recebido"] == "Não"), 2),
        })
    tot = {k: round(sum(m[k] for m in meses), 2) for k in ("entradas", "saidas", "diferenca", "investimento")}
    cartao_linhas = []
    for c in d["cartao"]:
        total = round(sum(c["meses"]), 2)
        confere = None if not c["valor_total"] else (
            "OK" if abs(c["valor_total"] - total) < 0.005 else round(c["valor_total"] - total, 2))
        cartao_linhas.append({"total": total, "confere": confere})
    cartao_meses = [round(sum(c["meses"][k] for c in d["cartao"]), 2) for k in range(12)]
    contas = []
    for c in d["contas"]:
        ant, linhas = c["saldo_inicial"], []
        for k in range(12):
            liq = round((ant + c["meses"][k]["entrada"]) - c["meses"][k]["saida"], 2)
            linhas.append({"saldo_anterior": round(ant, 2), "liquido": liq})
            ant = liq
        contas.append(linhas)
    return {"meses": meses, "totais": tot, "saldo_final": meses[-1]["saldo_global"],
            "cartao": {"linhas": cartao_linhas, "meses": cartao_meses,
                       "total": round(sum(cartao_meses), 2),
                       "divergentes": sum(1 for l in cartao_linhas if l["confere"] not in (None, "OK"))},
            "contas": contas}


# ---------------------------------------------------------------------------
# armazenamento
# ---------------------------------------------------------------------------

def _arq(ano: int) -> Path:
    return DIR / f"{_ano(ano)}.json"


def anos() -> list:
    if not DIR.is_dir():
        return []
    return sorted(int(p.stem) for p in DIR.glob("*.json") if re.fullmatch(r"\d{4}", p.stem))


def carregar(ano) -> dict:
    ano = _ano(ano)
    p = _arq(ano)
    if p.exists():
        d = normalizar(json.loads(p.read_text(encoding="utf-8")), ano)
        d["novo"] = False
        return d
    d = vazio(ano)
    ant = _arq(ano - 1) if ano > 2000 else None
    if ant is not None and ant.exists():          # herda do ano anterior
        dp = normalizar(json.loads(ant.read_text(encoding="utf-8")), ano - 1)
        cp = calcular(dp)
        d["cadastro"] = copy.deepcopy(dp["cadastro"])
        d["meses"][0]["saldo_inicial"] = cp["saldo_final"]
        d["contas"] = [{"nome": c["nome"], "saldo_inicial": cp["contas"][i][11]["liquido"],
                        "meses": [{"entrada": 0.0, "saida": 0.0} for _ in range(12)]}
                       for i, c in enumerate(dp["contas"])]
        d["herdado_de"] = ano - 1
    d["novo"] = True
    return d


def salvar(ano, dados: dict) -> dict:
    ano = _ano(ano)
    d = normalizar(dados, ano)
    DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(DIR), prefix=f".{ano}_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _arq(ano))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return d


# ---------------------------------------------------------------------------
# exportação: preenche a planilha do usuário (fiel ou aprimorada)
# ---------------------------------------------------------------------------

def _col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _put(sd, ref: str, valor):
    """Grava valor (número/texto) mantendo o estilo da célula; None/'' limpa."""
    r = int(re.search(r"\d+", ref).group(0))
    row = F._row(sd, r, criar=True)
    if valor is None or valor == "":
        F._set_cell(row, ref)
    elif isinstance(valor, (int, float)):
        F._set_cell(row, ref, numero=valor)
    else:
        F._set_cell(row, ref, texto=str(valor))


def _num_ou_vazio(x):
    return x if x else None


def preencher(xlsx: bytes, d: dict) -> bytes:
    zin = zipfile.ZipFile(io.BytesIO(xlsx))
    abas = F._mapa_abas(zin)
    novos = {}

    for i, mes in enumerate(MESES):
        ws = F._xml(zin.read(abas[mes]))
        sd = ws.find(F._X + "sheetData")
        m = d["meses"][i]
        for k in range(MAX_LINHAS_MES):
            r = 6 + k
            e = m["entradas"][k] if k < len(m["entradas"]) else None
            s = m["saidas"][k] if k < len(m["saidas"]) else None
            for col, campo in (("E", "descricao"), ("F", "tipo"), ("G", "valor"), ("H", "dia"), ("J", "recebido")):
                _put(sd, f"{col}{r}", (_num_ou_vazio(e[campo]) if campo == "valor" else e[campo]) if e else None)
            for col, campo in (("M", "descricao"), ("N", "tipo"), ("O", "valor"), ("P", "dia"), ("R", "pago")):
                _put(sd, f"{col}{r}", (_num_ou_vazio(s[campo]) if campo == "valor" else s[campo]) if s else None)
        _put(sd, "U8", _num_ou_vazio(m["investimento"]))
        if i == 0:
            _put(sd, "U9", _num_ou_vazio(m["saldo_inicial"]))
        novos[abas[mes]] = F._bytes(ws)

    # Contas e Cadastro
    ws = F._xml(zin.read(abas["Contas e Cadastro"]))
    sd = ws.find(F._X + "sheetData")
    for k in range(MAX_CONTAS):
        r = 4 + k
        c = d["contas"][k] if k < len(d["contas"]) else None
        _put(sd, f"D{r}", c["nome"] if c else None)
        _put(sd, f"E{r}", _num_ou_vazio(c["saldo_inicial"]) if c else None)
        for mi in range(12):
            base = 5 + 4 * mi                       # E, I, M, ... (Saldo Anterior de cada mês)
            _put(sd, f"{_col(base + 1)}{r}", _num_ou_vazio(c["meses"][mi]["entrada"]) if c else None)
            _put(sd, f"{_col(base + 2)}{r}", _num_ou_vazio(c["meses"][mi]["saida"]) if c else None)
    for k in range(MAX_TIPOS):
        rec, desp = d["cadastro"]["receitas"], d["cadastro"]["despesas"]
        _put(sd, f"D{14 + k}", rec[k] if k < len(rec) else None)
        _put(sd, f"D{29 + k}", desp[k] if k < len(desp) else None)
    novos[abas["Contas e Cadastro"]] = F._bytes(ws)

    # C.Crédito
    ws = F._xml(zin.read(abas["C.Crédito"]))
    sd = ws.find(F._X + "sheetData")
    for k in range(MAX_CARTAO):
        r = 17 + k
        c = d["cartao"][k] if k < len(d["cartao"]) else None
        _put(sd, f"E{r}", c["cartao"] if c else None)
        _put(sd, f"F{r}", c["descricao"] if c else None)
        _put(sd, f"G{r}", _num_ou_vazio(c["valor_total"]) if c else None)
        _put(sd, f"H{r}", c["parcelas"] if c else None)
        for mi in range(12):
            _put(sd, f"{_col(9 + mi)}{r}", _num_ou_vazio(c["meses"][mi]) if c else None)
    novos[abas["C.Crédito"]] = F._bytes(ws)

    # recalcular ao abrir (os valores em cache das fórmulas estão zerados)
    wb = F._xml(zin.read("xl/workbook.xml"))
    calc = wb.find(F._X + "calcPr")
    if calc is not None:
        calc.set("fullCalcOnLoad", "1")
    novos["xl/workbook.xml"] = F._bytes(wb)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            dados = novos.pop(item.filename, None)
            zout.writestr(item, dados if dados is not None else zin.read(item.filename))
    return out.getvalue()


def exportar(ano, versao: str):
    ano = _ano(ano)
    d = carregar(ano)
    base, _ = F.gerar(versao)
    sufixo = "Aprimorado" if versao == "aprimorada" else "Recriado"
    return preencher(base, d), f"ControleFinanceiro_{ano}_{sufixo}.xlsx"


# ---------------------------------------------------------------------------
# análise pela IA local
# ---------------------------------------------------------------------------

def _brl(x: float) -> str:
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-R$ " if x < 0 else "R$ ") + s


def prompt_analise(ano) -> str:
    ano = _ano(ano)
    d = carregar(ano)
    c = calcular(d)
    ativos = [i for i, m in enumerate(d["meses"]) if m["entradas"] or m["saidas"] or m["investimento"]]
    if not ativos:
        raise ValueError(f"{ano}: ainda não há lançamentos para analisar")
    L = [f"Analise as minhas finanças pessoais de {ano} como um consultor financeiro. "
         "Use SOMENTE os números abaixo (não invente valores). Responda em português, com: "
         "1) visão geral do ano; 2) padrões e meses fora da curva; 3) alertas (saldo negativo, "
         "contas a pagar, cartão); 4) três sugestões práticas e concretas.", "",
         f"## Resumo do ano {ano}",
         f"- Entradas: {_brl(c['totais']['entradas'])} · Saídas: {_brl(c['totais']['saidas'])} · "
         f"Líquido: {_brl(c['totais']['diferenca'])}",
         f"- Investido no ano: {_brl(c['totais']['investimento'])} · Saldo final (Dez): {_brl(c['saldo_final'])}",
         f"- Saldo inicial (Jan): {_brl(d['meses'][0]['saldo_inicial'])}", "",
         "## Mês a mês", "| Mês | Entradas | Saídas | Diferença | Investido | Saldo |", "|---|---|---|---|---|---|"]
    for i in ativos:
        m = c["meses"][i]
        L.append(f"| {MESES_NOME[i]} | {_brl(m['entradas'])} | {_brl(m['saidas'])} | "
                 f"{_brl(m['diferenca'])} | {_brl(m['investimento'])} | {_brl(m['saldo_global'])} |")
    for titulo, lado in (("Saídas por tipo (ano)", "saidas"), ("Entradas por tipo (ano)", "entradas")):
        por = {}
        for m in d["meses"]:
            for l in m[lado]:
                por[l["tipo"] or "(sem tipo)"] = por.get(l["tipo"] or "(sem tipo)", 0) + l["valor"]
        if por:
            tot = sum(por.values()) or 1
            L += ["", f"## {titulo}"] + [f"- {k}: {_brl(v)} ({v / tot:.0%})"
                                         for k, v in sorted(por.items(), key=lambda kv: -kv[1])[:10]]
    pend = [(MESES_NOME[i], l) for i, m in enumerate(d["meses"]) for l in m["saidas"] if l["pago"] == "Não"]
    if pend:
        L += ["", f"## Contas marcadas como NÃO pagas ({len(pend)})"] + \
             [f"- {mes}: {l['descricao'] or l['tipo'] or '—'} {_brl(l['valor'])}" for mes, l in pend[:12]]
    if d["cartao"]:
        L += ["", "## Cartão de crédito",
              f"- Total comprometido no ano: {_brl(c['cartao']['total'])}",
              "- Por mês: " + ", ".join(f"{MESES[k]} {_brl(v)}" for k, v in enumerate(c["cartao"]["meses"]) if v)]
        if c["cartao"]["divergentes"]:
            L.append(f"- {c['cartao']['divergentes']} compra(s) com Valor Total diferente da soma das parcelas")
    neg = [MESES_NOME[i] for i, m in enumerate(c["meses"]) if m["saldo_global"] < 0]
    if neg:
        L += ["", "## Saldo negativo em: " + ", ".join(neg)]
    return "\n".join(L)
