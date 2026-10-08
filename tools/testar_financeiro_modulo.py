#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testar_financeiro_modulo.py — confere o módulo Financeiro (fase B) contra o Excel.

Monta um ano fictício completo (lançamentos nos 12 meses, investimentos, cartão
com parcelas, contas), exporta para as versões fiel e aprimorada, abre cada uma
NO EXCEL (tools/excel_ler.ps1) e compara célula a célula com
financeiro_dados.calcular(): resumo U5–U10 dos 12 meses, Evolução, cartão (U e
totais), contas (Líquido dos 12 meses). Também testa herança de ano, limites e
o prompt da IA. Não toca em workspace/financeiro (usa pasta temporária).

Requer Windows + Excel. Uso: runtime\\python\\python.exe tools\\testar_financeiro_modulo.py
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import financeiro_dados as FD  # noqa: E402

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

ok_total, falhas = 0, []


def check(nome, cond, det=""):
    global ok_total
    if cond:
        ok_total += 1
        print(f"[OK   ] {nome}")
    else:
        falhas.append(nome)
        print(f"[FALHA] {nome} — {det}")


def ano_ficticio(ano: int) -> dict:
    rnd = random.Random(42)
    d = FD.vazio(ano)
    d["cadastro"]["despesas"].append("Assinaturas")
    d["meses"][0]["saldo_inicial"] = 2500.0
    for i in range(12):
        m = d["meses"][i]
        m["entradas"] = [{"descricao": "Salário", "tipo": "Salário", "valor": 6200.0, "dia": 5, "recebido": "Sim"},
                         {"descricao": "Freela", "tipo": "Outros", "valor": round(rnd.uniform(0, 1800), 2),
                          "dia": 20, "recebido": "Não" if i % 3 == 0 else "Sim"}]
        m["saidas"] = [{"descricao": "Aluguel", "tipo": "Moradia", "valor": 2100.0, "dia": 10, "pago": "Sim"},
                       {"descricao": "Mercado", "tipo": "Alimentação", "valor": round(rnd.uniform(900, 1700), 2),
                        "dia": 15, "pago": "Sim"},
                       {"descricao": "Streaming", "tipo": "Assinaturas", "valor": 55.9, "dia": 1,
                        "pago": "Não" if i == 11 else "Sim"}]
        if i == 6:   # mês negativo
            m["saidas"].append({"descricao": "Conserto carro", "tipo": "Transporte", "valor": 40000.0,
                                "dia": 3, "pago": "Sim"})
        m["investimento"] = 500.0 if i % 2 == 0 else 0.0
    d["cartao"] = [
        {"cartao": "Visa", "descricao": "Geladeira", "valor_total": 3600.0, "parcelas": 6,
         "meses": [0, 0, 600, 600, 600, 600, 600, 600, 0, 0, 0, 0]},
        {"cartao": "Master", "descricao": "Curso", "valor_total": 1000.0, "parcelas": 3,
         "meses": [300, 300, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0]},          # diverge (900 ≠ 1000)
    ]
    d["contas"] = [{"nome": "Banco A", "saldo_inicial": 1000.0,
                    "meses": [{"entrada": 6200.0, "saida": 5000.0 + 37 * k} for k in range(12)]},
                   {"nome": "Poupança", "saldo_inicial": 8000.0,
                    "meses": [{"entrada": 500.0 if k % 2 == 0 else 0.0, "saida": 0.0} for k in range(12)]}]
    return d


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="fin_mod_"))
    FD.DIR = tmp / "financeiro"              # isola do workspace real
    ano = 2031
    salvo = FD.salvar(ano, ano_ficticio(ano))
    calc = FD.calcular(salvo)

    # ---- unidade: normalização, limites, herança, prompt ----
    check("normalizar: texto pt-BR '1.234,56' vira número", FD._num("R$ 1.234,56") == 1234.56)
    try:
        FD.salvar(ano, {"meses": [{"entradas": [{"valor": 1}] * 51}]})
        check("limite de 50 linhas por mês recusa a 51ª", False, "aceitou")
    except ValueError:
        check("limite de 50 linhas por mês recusa a 51ª", True)
    prox = FD.carregar(ano + 1)
    check("ano novo herda saldo final, contas e cadastro",
          prox["novo"] and prox["meses"][0]["saldo_inicial"] == calc["saldo_final"]
          and [c["saldo_inicial"] for c in prox["contas"]] == [l[11]["liquido"] for l in calc["contas"]]
          and "Assinaturas" in prox["cadastro"]["despesas"],
          json.dumps(prox["meses"][0]["saldo_inicial"]))
    p = FD.prompt_analise(ano)
    check("prompt da IA tem resumo, mês a mês, pendências e cartão",
          all(x in p for x in ("Resumo do ano", "| Julho |", "NÃO pagas", "Cartão de crédito", "Saldo negativo em: Julho")))
    check("cálculo: Julho negativo e cartão com 1 divergência",
          calc["meses"][6]["saldo_global"] < 0 and calc["cartao"]["divergentes"] == 1)

    # ---- Excel: célula a célula ----
    refs, esperado = [], {}
    for i, mes in enumerate(FD.MESES):
        m = calc["meses"][i]
        for cel, k in (("U5", "entradas"), ("U6", "saidas"), ("U7", "diferenca"), ("U8", "investimento"),
                       ("U9", "saldo_anterior"), ("U10", "saldo_global")):
            esperado[f"{mes}!{cel}"] = m[k]
        esperado[f"{mes}!I6"] = m["pct_entradas"][0]
        col = FD._col(5 + i)                                      # Evolução E..P
        esperado[f"Evolução!{col}39"] = m["entradas"]
        esperado[f"Evolução!{col}40"] = m["saidas"]
        esperado[f"Evolução!{col}41"] = m["diferenca"]
        esperado[f"Evolução!{col}42"] = m["investido_acumulado"]
        esperado[f"Evolução!{col}43"] = m["saldo_global"]
        esperado[f"C.Crédito!{FD._col(9 + i)}117"] = calc["cartao"]["meses"][i]
        for k, linhas in enumerate(calc["contas"]):
            esperado[f"Contas e Cadastro!{FD._col(5 + 4 * i + 3)}{4 + k}"] = linhas[i]["liquido"]
    # o ORIGINAL não tem fórmula em AZ5:AZ10 (Líquido de dezembro das contas 2–7):
    # na versão fiel o Excel mostra vazio; a aprimorada corrige (melhoria 6)
    az_original = {f"Contas e Cadastro!AZ{4 + k}" for k in range(1, len(calc["contas"]))}
    esperado["Evolução!S39"] = calc["totais"]["entradas"]
    esperado["Evolução!S40"] = calc["totais"]["saidas"]
    esperado["Evolução!S41"] = calc["totais"]["diferenca"]
    for k, l in enumerate(calc["cartao"]["linhas"]):
        esperado[f"C.Crédito!U{17 + k}"] = l["total"]
    esperado["C.Crédito!U117"] = calc["cartao"]["total"]
    refs = list(esperado)
    (tmp / "refs.json").write_text(json.dumps(refs, ensure_ascii=False), encoding="utf-8")

    FD_exportar_base = FD.exportar
    for versao in ("fiel", "aprimorada"):
        dados, nome = FD_exportar_base(ano, versao)
        xlsx = tmp / nome
        xlsx.write_bytes(dados)
        out = tmp / f"{versao}.json"
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(ROOT / "tools" / "excel_ler.ps1"), "-Arquivo", str(xlsx),
                        "-Celulas", str(tmp / "refs.json"), "-Saida", str(out)], timeout=600)
        r = json.loads(out.read_text(encoding="utf-8-sig"))
        if r.get("excecao"):
            check(f"{versao}: Excel abriu o arquivo", False, r["excecao"])
            continue
        dif = []
        for ref, esp in esperado.items():
            got = r["valores"].get(ref)
            if versao == "fiel" and ref in az_original:
                esp = 0.0                        # erro do original reproduzido
            if esp is None:                      # % de total zerado: IFERROR -> ""
                bate = got in (None, "")
            else:                                # célula de digitação vazia = 0
                got = 0.0 if got in (None, "") else got
                bate = isinstance(got, (int, float)) and abs(got - esp) < 0.005
            if not bate:
                dif.append(f"{ref}: módulo={esp} Excel={got}")
        check(f"{versao}: {len(esperado)} células do Excel = cálculo do módulo", not dif, "; ".join(dif[:6]))
        check(f"{versao}: nenhum erro de fórmula no Excel", r["erros"] == 0, str(r["erros"]))

    print(f"\n{ok_total} aprovado(s), {len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
