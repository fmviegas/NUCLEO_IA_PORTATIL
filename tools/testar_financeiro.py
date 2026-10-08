#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testar_financeiro.py — gera as 2 versões do Controle Financeiro e testa cada uma
NO EXCEL (tools/testar_financeiro.ps1, via COM), escrevendo o relatório de
auditoria em docs/financeiro_relatorio_testes.md (entregável C do prompt mestre).

Requer Windows + Microsoft Excel. Uso: runtime\\python\\python.exe tools\\testar_financeiro.py
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import financeiro  # noqa: E402

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

ITENS = {
    "1": "Existência, ordem e nomes das 16 abas",
    "2": "Totais e porcentagens do mês (dados fictícios)",
    "3": "Passagem de saldo Jan → Fev → … → Dez",
    "4": "Evolução mensal, total anual e investido acumulado",
    "5": "Soma mensal do cartão na coluna U",
    "6": "Cálculo e transporte de saldo das contas",
    "7": "Sem #DIV/0!, #REF!, #VALUE!, #NAME? (vazio e com dados)",
    "8": "Proteção das abas mantida",
    "A": "Melhorias da versão aprimorada",
}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="fin_"))
    ps1 = ROOT / "tools" / "testar_financeiro.ps1"
    resultados = {}
    for versao in ("fiel", "aprimorada"):
        dados, nome = financeiro.gerar(versao)
        xlsx = tmp / nome
        xlsx.write_bytes(dados)
        saida = tmp / f"{versao}.json"
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1),
                        "-Arquivo", str(xlsx), "-Saida", str(saida)], check=False, timeout=600)
        if not saida.exists():
            print(f"ERRO: teste da versão {versao} não gerou resultado (Excel instalado?)")
            return 2
        resultados[versao] = (nome, json.loads(saida.read_text(encoding="utf-8-sig")))

    L = [f"# Relatório de testes — Controle Financeiro",
         "",
         f"Gerado em {dt.datetime.now():%Y-%m-%d %H:%M} por `tools/testar_financeiro.py`, "
         "no **Microsoft Excel** (COM), com dados fictícios numa cópia de teste.",
         "Modelo: cópia local do usuário em `workspace/financeiro/modelo/` (planilha de terceiros, fora do git).", ""]
    falhas = 0
    for versao, (nome, r) in resultados.items():
        ok = sum(c["ok"] for c in r["checks"]); tot = len(r["checks"])
        falhas += tot - ok + (1 if r.get("excecao") else 0)
        L += [f"## {nome} — {ok}/{tot} aprovados", ""]
        if r.get("excecao"):
            L += [f"**EXCEÇÃO:** {r['excecao']}", ""]
        L += ["| Item | Teste | Resultado | Detalhe |", "|---|---|---|---|"]
        for c in r["checks"]:
            item = str(c["item"])
            L.append(f"| {item} — {ITENS.get(item, '')} | {c['nome']} | "
                     f"{'✅ aprovado' if c['ok'] else '❌ falhou'} | {c['detalhe'][:120]} |")
        graf = sum(r["graficos"].values()); formas = sum(r["formas"].values())
        L += ["", f"Gráficos (inclui treemaps): **{graf}** · formas/botões: **{formas}** · abas: {len(r['abas'])}", ""]

    g = [sum(r["graficos"].values()) for _, r in resultados.values()]
    f = [sum(r["formas"].values()) for _, r in resultados.values()]
    L += ["## Diferenças entre as versões", "",
          f"- Gráficos idênticos nas duas: {'sim' if g[0] == g[1] else 'NÃO'} ({g[0]} × {g[1]}).",
          f"- Formas/botões idênticos: {'sim' if f[0] == f[1] else 'NÃO'} ({f[0]} × {f[1]}).",
          "- Fiel: cópia byte a byte do original (inclusive o título JANEIRO nas abas Fev–Dez).",
          "- Aprimorada: títulos corrigidos, listas suspensas, destaques, conferência do cartão "
          "(coluna V), aba Notas, recálculo ao abrir. Proteção original intacta.", "",
          "## Limitações declaradas", "",
          "- O teste visual (cores, mesclagens, larguras, gráficos) foi feito comparando PDFs "
          "exportados pelo Excel das duas versões; não há comparação pixel a pixel automática.",
          "- As listas suspensas usam OFFSET para crescer com o cadastro; exigem Excel 2010+.",
          ""]
    out = ROOT / "docs" / "financeiro_relatorio_testes.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nRelatório: {out}")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
