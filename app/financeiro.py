#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
financeiro.py — menu FINANCEIRO: entrega o Controle Financeiro Pessoal (.xlsx).

Spec: config/templates/financeiro/Prompt_Mestre_Recriar_ControleFinanceiro.md
Modelo: workspace/financeiro/modelo/ControleFinanceiro.xlsx — a CÓPIA DO USUÁRIO de
uma planilha de TERCEIROS (não é criação dele): fica só na máquina dele (workspace/
é ignorado pelo git e não vai na cópia portátil). O NÚCLEO não distribui o modelo nem
oferece download em branco; só preenche a cópia que o usuário já tem. Sem o arquivo,
a exportação .xlsx fica indisponível (o módulo do painel funciona normalmente).
Anatomia: 16 abas, 26 gráficos, 12 treemaps, 37 botões de navegação, abas
protegidas com senha.

Duas versões:
  * FIEL      — cópia byte a byte do original (fidelidade 100%: treemaps, botões,
                proteção e o erro do título "JANEIRO" nas abas Fev–Dez).
  * APRIMORADA — melhorias aplicadas DIRETO no XML do pacote, sem abrir/salvar
                pelo openpyxl (que descartaria treemaps e formas — o próprio
                arquivo avisa: "salvar em outro formato quebrará o gráfico").
                A proteção original (com a senha do autor) é mantida intacta;
                tudo o que é adicionado é validação/formatação condicional/
                fórmula em células já bloqueadas, então não exige desproteger.

Melhorias (todas marcadas como MELHORIA na aba "Notas"):
  1. Títulos D2 de Fev–Dez corrigidos (FEVEREIRO…DEZEMBRO).
  2. Listas suspensas nos meses: Tipo de entrada/saída (cadastros, dinâmicas até
     a linha livre do cadastro) e Rec.?/Pago? (Sim/Não). Estilo "aviso": não
     impede digitar outro valor, como no original.
  3. Destaques: saldo/diferença negativos (meses, Evolução, Contas); saída com
     "Pago? = Não" (a pagar) e entrada com "Rec.? = Não" (a receber) — só na
     fonte, mantendo as cores originais de digitação.
  4. C.Crédito: coluna V "Confere?" compara Valor Total (G) com a soma dos meses
     (U) — "OK" / "Difere R$ x" — e V117 resume as divergências.
  5. Aba "Notas": documenta U8/U9/U10 e a política de investimentos (sem mudar
     a semântica original).
  6. Recalcular ao abrir (fullCalcOnLoad).
  7. Contas: fórmula do Líquido de dezembro nas contas 2–7 (AZ5:AZ10 vazias no original).

API:
    info() -> dict
    gerar(versao) -> (bytes, filename)      versao: "fiel" | "aprimorada"
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "workspace" / "financeiro" / "modelo" / "ControleFinanceiro.xlsx"
MSG_SEM_MODELO = ("Exportação .xlsx indisponível: coloque a SUA cópia do ControleFinanceiro.xlsx "
                  "(em branco) em workspace/financeiro/modelo/. O arquivo fica só neste computador.")

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
_X = "{%s}" % NS

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_EXT = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO",
             "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

CAD = "'Contas e Cadastro'"
# listas dinâmicas: crescem conforme o usuário preenche o cadastro (áreas livres)
LISTA_RECEITAS = f"OFFSET({CAD}!$D$14,0,0,MAX(1,COUNTA({CAD}!$D$14:$D$26)),1)"
LISTA_DESPESAS = f"OFFSET({CAD}!$D$29,0,0,MAX(1,COUNTA({CAD}!$D$29:$D$41)),1)"
LISTA_RECEBIDO = f"{CAD}!$F$14:$F$15"
LISTA_PAGO = f"{CAD}!$F$20:$F$21"

# ordem dos elementos em CT_Worksheet a partir de mergeCells (ECMA-376)
_ORDEM_POS = ["phoneticPr", "conditionalFormatting", "dataValidations", "hyperlinks",
              "printOptions", "pageMargins", "pageSetup", "headerFooter", "rowBreaks",
              "colBreaks", "customProperties", "cellWatches", "ignoredErrors",
              "smartTags", "drawing", "legacyDrawing", "legacyDrawingHF",
              "drawingHF", "picture", "oleObjects", "controls", "webPublishItems",
              "tableParts", "extLst"]

# dxfs acrescentados ao styles.xml (índices 0..3 — o original tem count="0")
DXFS = [
    '<dxf><font><b/><color rgb="FFC00000"/></font></dxf>',                        # 0 negativo (fundo claro)
    '<dxf><font><b/><color rgb="FFFFFFFF"/></font>'
    '<fill><patternFill><bgColor rgb="FFC00000"/></patternFill></fill></dxf>',    # 1 negativo (fundo escuro)
    '<dxf><font><b/><color rgb="FFC55A11"/></font></dxf>',                        # 2 a pagar
    '<dxf><font><i/><color rgb="FF7F7F7F"/></font></dxf>',                        # 3 a receber
]

NOTAS = [
    ("NOTAS — VERSÃO APRIMORADA", "t"),
    ("Esta aba e os itens abaixo são MELHORIAS sobre o arquivo original; não existiam nele.", ""),
    ("", ""),
    ("COMO O SALDO FUNCIONA (semântica original, não alterada)", "h"),
    ("U5 Entradas = total das entradas do mês (G56).", ""),
    ("U6 Saídas = total das saídas do mês (O56).", ""),
    ("U7 Diferença = U5 − U6.", ""),
    ("U8 Investimentos = valor que você TIROU da conta corrente e aplicou no mês (digitado).", ""),
    ("U9 Saldo Mês Anterior = em Janeiro, digite o saldo inicial; de Fev a Dez vem do U10 do mês anterior.", ""),
    ("U10 Saldo Global = (U7 + U9) − U8 → saldo da conta corrente no fim do mês.", ""),
    ("", ""),
    ("POLÍTICA PARA INVESTIMENTOS (evitar dupla contagem)", "h"),
    ("Lance o valor aplicado SOMENTE em U8. Não lance o mesmo valor também como saída (O6:O55):", ""),
    ("ele seria descontado duas vezes do saldo.", ""),
    ("A linha 'Valor Investido' da Evolução acumula os U8 de Jan a Dez.", ""),
    ("Rendimento ou resgate que volta para a conta: lance como ENTRADA (tipo Investimentos ou Juros).", ""),
    ("", ""),
    ("MELHORIAS DESTA VERSÃO", "h"),
    ("1. Títulos das abas Fev–Dez corrigidos (no original todas mostram JANEIRO).", ""),
    ("2. Listas suspensas em Tipo, Rec.? e Pago? — vêm do cadastro em 'Contas e Cadastro'.", ""),
    ("   Novos tipos: preencha D18:D26 (receitas) ou D38:D41 (despesas); a lista cresce sozinha.", ""),
    ("   O aviso não bloqueia: dá para digitar um valor fora da lista, como no original.", ""),
    ("3. Destaques: valores negativos em vermelho; saída com Pago? = Não em laranja (a pagar);", ""),
    ("   entrada com Rec.? = Não em cinza itálico (a receber). As cores de digitação foram mantidas.", ""),
    ("4. C.Crédito, coluna V 'Confere?': compara o Valor Total (G) com a soma dos meses (U).", ""),
    ("   'OK' quando batem; 'Difere R$ x' quando não. V117 resume quantas linhas diferem.", ""),
    ("5. A planilha recalcula ao abrir.", ""),
    ("6. Contas e Cadastro: o Líquido de DEZEMBRO das contas 2 a 7 (AZ5:AZ10) não tinha fórmula", ""),
    ("   no original — o saldo de dezembro dessas contas não aparecia. Fórmula acrescentada.", ""),
    ("", ""),
    ("Proteção: as abas continuam protegidas exatamente como no original (mesma senha do autor).", ""),
]


def _nome_fiel():
    return "ControleFinanceiro_Recriado.xlsx"


def info() -> dict:
    ok = TEMPLATE.exists()
    return {
        "modelo_presente": ok,
        "modelo": str(TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
        "versoes": [
            {"id": "fiel", "nome": "Versão fiel",
             "arquivo": _nome_fiel(),
             "descricao": "Cópia exata do seu Controle Financeiro original: 16 abas, gráficos, "
                          "treemaps, botões de navegação e proteção — idêntico byte a byte."},
            {"id": "aprimorada", "nome": "Versão aprimorada",
             "arquivo": "ControleFinanceiro_Aprimorado.xlsx",
             "descricao": "O mesmo arquivo + títulos dos meses corrigidos, listas suspensas "
                          "(Tipo, Rec.?, Pago?), destaque de saldo negativo e contas a pagar/"
                          "receber, conferência do cartão (Valor Total × meses) e aba Notas."},
        ],
    }


# ---------------------------------------------------------------------------
# helpers XML
# ---------------------------------------------------------------------------

def _xml(b: bytes):
    return etree.fromstring(b, etree.XMLParser(remove_blank_text=False))


def _bytes(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _col_num(letras: str) -> int:
    n = 0
    for ch in letras:
        n = n * 26 + (ord(ch) - 64)
    return n


def _ref_col(ref: str) -> int:
    return _col_num(re.match(r"[A-Z]+", ref).group(0))


def _insere_ordenado(ws, elem):
    """Insere `elem` (filho de worksheet) na posição exigida pelo schema."""
    nome = etree.QName(elem).localname
    depois = _ORDEM_POS[_ORDEM_POS.index(nome) + 1:]
    for filho in ws:
        if etree.QName(filho).localname in depois:
            filho.addprevious(elem)
            return
    ws.append(elem)


def _row(sheet_data, r: int, criar: bool = False):
    for row in sheet_data.iter(_X + "row"):
        n = int(row.get("r"))
        if n == r:
            return row
        if criar and n > r:
            novo = etree.Element(_X + "row", r=str(r))
            row.addprevious(novo)
            return novo
    if criar:
        return etree.SubElement(sheet_data, _X + "row", r=str(r))
    raise KeyError(f"linha {r} ausente")


def _set_cell(row, ref: str, *, s=None, formula=None, texto=None, numero=None):
    """Cria/substitui a célula `ref` na linha, mantendo a ordem das colunas."""
    alvo = _ref_col(ref)
    existente = None
    for c in row.iter(_X + "c"):
        if c.get("r") == ref:
            existente = c
            break
    novo = etree.Element(_X + "c", r=ref)
    estilo = s if s is not None else (existente.get("s") if existente is not None else None)
    if estilo is not None:
        novo.set("s", str(estilo))
    if formula is not None:
        novo.set("t", "str")
        etree.SubElement(novo, _X + "f").text = formula
    elif numero is not None:
        etree.SubElement(novo, _X + "v").text = repr(float(numero)) if not float(numero).is_integer() \
            else str(int(numero))
    elif texto is not None:
        novo.set("t", "inlineStr")
        is_ = etree.SubElement(novo, _X + "is")
        t = etree.SubElement(is_, _X + "t")
        t.text = texto
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    if existente is not None:
        existente.addprevious(novo)
        row.remove(existente)
        return
    for c in row.iter(_X + "c"):
        if _ref_col(c.get("r")) > alvo:
            c.addprevious(novo)
            return
    row.append(novo)
    spans = row.get("spans")
    if spans:
        a, b = spans.split(":")
        row.set("spans", f"{a}:{max(int(b), alvo)}")


def _cf(sqref: str, regras):
    """regras: [(tipo, dxf, operador|None, formula)]"""
    cf = etree.Element(_X + "conditionalFormatting", sqref=sqref)
    for tipo, dxf, op, f in regras:
        rule = etree.SubElement(cf, _X + "cfRule", type=tipo, dxfId=str(dxf), priority="1")
        if op:
            rule.set("operator", op)
        etree.SubElement(rule, _X + "formula").text = f
    return cf


def _dv_lista(sqref: str, formula: str, titulo: str):
    dv = etree.Element(_X + "dataValidation", type="list", errorStyle="warning",
                       allowBlank="1", showInputMessage="1", showErrorMessage="1",
                       sqref=sqref, errorTitle=titulo,
                       error="Valor fora do cadastro. Clique em Sim para manter mesmo assim.")
    etree.SubElement(dv, _X + "formula1").text = formula
    return dv


def _prioridades(ws):
    """Prioridade única e crescente para todos os cfRule da aba."""
    for i, rule in enumerate(ws.iter(_X + "cfRule"), start=1):
        rule.set("priority", str(i))


# ---------------------------------------------------------------------------
# mapa de abas -> arquivos
# ---------------------------------------------------------------------------

def _mapa_abas(zf) -> dict:
    wb = _xml(zf.read("xl/workbook.xml"))
    rels = _xml(zf.read("xl/_rels/workbook.xml.rels"))
    alvo = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for s in wb.iter(_X + "sheet"):
        t = alvo[s.get("{%s}id" % NS_R)].lstrip("/")
        out[s.get("name")] = t if t.startswith("xl/") else "xl/" + t
    return out


# ---------------------------------------------------------------------------
# melhorias
# ---------------------------------------------------------------------------

def _mes(xml: bytes, idx: int) -> bytes:
    ws = _xml(xml)
    sd = ws.find(_X + "sheetData")
    if idx > 0:                                  # 1. título D2 (o original diz JANEIRO em todas)
        _set_cell(_row(sd, 2), "D2", texto=MESES_EXT[idx])
    # 3. destaques
    for el in (
        _cf("U5:U7 U9", [("cellIs", 0, "lessThan", "0")]),
        _cf("U10", [("cellIs", 1, "lessThan", "0")]),
        _cf("M6:R55", [("expression", 2, None, 'AND($O6<>"",$R6="Não")')]),
        _cf("E6:J55", [("expression", 3, None, 'AND($G6<>"",$J6="Não")')]),
    ):
        _insere_ordenado(ws, el)
    _prioridades(ws)
    # 2. listas suspensas
    dvs = etree.Element(_X + "dataValidations", count="4")
    dvs.append(_dv_lista("F6:F55", LISTA_RECEITAS, "Tipo de receita"))
    dvs.append(_dv_lista("N6:N55", LISTA_DESPESAS, "Tipo de despesa"))
    dvs.append(_dv_lista("J6:J55", LISTA_RECEBIDO, "Recebido?"))
    dvs.append(_dv_lista("R6:R55", LISTA_PAGO, "Pago?"))
    _insere_ordenado(ws, dvs)
    return _bytes(ws)


def _evolucao(xml: bytes) -> bytes:
    ws = _xml(xml)
    _insere_ordenado(ws, _cf("E41:S41 E43:P43", [("cellIs", 0, "lessThan", "0")]))
    _prioridades(ws)
    return _bytes(ws)


def _contas(xml: bytes) -> bytes:
    ws = _xml(xml)
    sd = ws.find(_X + "sheetData")
    # 7. o original só tem a fórmula do Líquido de dezembro na 1ª conta (AZ4);
    #    AZ5:AZ10 estão vazias -> o saldo de dezembro das contas 2–7 nunca aparece
    s_az4 = next((c.get("s") for c in _row(sd, 4).iter(_X + "c") if c.get("r") == "AZ4"), None)
    for r in range(5, 11):
        row = _row(sd, r)
        if not any(c.get("r") == f"AZ{r}" and c.find(_X + "f") is not None for c in row.iter(_X + "c")):
            _set_cell(row, f"AZ{r}", s=s_az4, formula=f"(AW{r}+AX{r})-AY{r}")
    _insere_ordenado(ws, _cf("E4:AZ10", [("cellIs", 0, "lessThan", "0")]))
    _prioridades(ws)
    return _bytes(ws)


def _cartao(xml: bytes) -> bytes:
    ws = _xml(xml)
    sd = ws.find(_X + "sheetData")
    # estilos de referência: cabeçalho U16, célula calculada U17, total U117
    def estilo(r, ref):
        for c in _row(sd, r).iter(_X + "c"):
            if c.get("r") == ref:
                return c.get("s")
    s_cab, s_cel, s_tot = estilo(16, "U16"), estilo(17, "U17"), estilo(117, "U117")
    _set_cell(_row(sd, 16), "V16", s=s_cab, texto="Confere?")
    for r in range(17, 117):
        _set_cell(_row(sd, r), f"V{r}", s=s_cel,
                  formula=f'IF(G{r}="","",IF(ABS(G{r}-U{r})<0.005,"OK",'
                          f'"Difere R$ "&FIXED(G{r}-U{r},2)))')   # FIXED usa a pontuação do idioma (TEXT não)
    _set_cell(_row(sd, 117), "V117", s=s_tot,
              formula='IF(COUNTIF(V17:V116,"Difere*")=0,"OK",'
                      'COUNTIF(V17:V116,"Difere*")&" difere(m)")')
    # largura da coluna V para caber "Difere R$ 1.234,56"
    # (no original V faz parte de um bloco <col min=22 max=34>: separa a V do bloco)
    cols = ws.find(_X + "cols")
    if cols is not None:
        for col in list(cols):
            a, b = int(col.get("min")), int(col.get("max"))
            if a <= 22 <= b:
                partes = []
                if a < 22:
                    partes.append((a, 21, {}))
                partes.append((22, 22, {"width": "18.7109375", "customWidth": "1"}))
                if b > 22:
                    partes.append((23, b, {}))
                for ini, fim, extra in partes:
                    novo = etree.Element(_X + "col", dict(col.attrib))
                    novo.set("min", str(ini)); novo.set("max", str(fim))
                    novo.attrib.pop("bestFit", None) if extra else None
                    for k, v in extra.items():
                        novo.set(k, v)
                    col.addprevious(novo)
                cols.remove(col)
                break
        else:
            etree.SubElement(cols, _X + "col", min="22", max="22",
                             width="18.7109375", customWidth="1")
            ordenadas = sorted(cols, key=lambda c: int(c.get("min")))
            for c in list(cols):
                cols.remove(c)
            for c in ordenadas:
                cols.append(c)
    _insere_ordenado(ws, _cf("V17:V117", [("expression", 1, None, 'LEFT(V17,6)="Difere"')]))
    _prioridades(ws)
    return _bytes(ws)


def _styles(xml: bytes) -> bytes:
    txt = xml.decode("utf-8")
    novo = f'<dxfs count="{len(DXFS)}">' + "".join(DXFS) + "</dxfs>"
    if '<dxfs count="0"/>' in txt:
        txt = txt.replace('<dxfs count="0"/>', novo, 1)
    elif "<dxfs" not in txt:
        txt = txt.replace("</cellStyles>", "</cellStyles>" + novo, 1)
    else:
        raise RuntimeError("styles.xml já tem dxfs — índices das regras precisariam ser deslocados")
    return txt.encode("utf-8")


def _workbook(xml: bytes, rid_notas: str, sheet_id: int) -> bytes:
    wb = _xml(xml)
    calc = wb.find(_X + "calcPr")
    if calc is not None:
        calc.set("fullCalcOnLoad", "1")
    # área de impressão do C.Crédito passa a incluir a coluna V (Confere?)
    for dn in wb.iter(_X + "definedName"):
        if dn.get("name") == "_xlnm.Print_Area" and "C.Crédito" in (dn.text or ""):
            dn.text = dn.text.replace("$U$117", "$V$117")
    sheets = wb.find(_X + "sheets")
    s = etree.SubElement(sheets, _X + "sheet", name="Notas", sheetId=str(sheet_id))
    s.set("{%s}id" % NS_R, rid_notas)
    return _bytes(wb)


def _aba_notas() -> bytes:
    linhas = []
    for i, (txt, kind) in enumerate(NOTAS, start=2):
        if not txt:
            continue
        # estilos inline mínimos não existem sem tocar o styles.xml: usa negrito
        # via rich text (<r><rPr><b/>) para títulos — sem depender de cellXfs.
        esc = (txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        if kind in ("t", "h"):
            tam = "14" if kind == "t" else "11"
            cor = "FF252E40"
            run = (f'<r><rPr><b/><sz val="{tam}"/><color rgb="{cor}"/><rFont val="Calibri"/></rPr>'
                   f'<t xml:space="preserve">{esc}</t></r>')
        else:
            run = f'<t xml:space="preserve">{esc}</t>'
        linhas.append(f'<row r="{i}"><c r="B{i}" t="inlineStr"><is>{run}</is></c></row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS}" xmlns:r="{NS_R}">'
        '<sheetPr><tabColor rgb="FF04B891"/></sheetPr>'
        '<sheetViews><sheetView workbookViewId="0" showGridLines="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        '<cols><col min="1" max="1" width="3" customWidth="1"/>'
        '<col min="2" max="2" width="110" customWidth="1"/></cols>'
        f'<sheetData>{"".join(linhas)}</sheetData>'
        '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
        '</worksheet>'
    ).encode("utf-8")


def _aprimorar(original: bytes) -> bytes:
    zin = zipfile.ZipFile(io.BytesIO(original))
    abas = _mapa_abas(zin)
    novos = {}
    for i, mes in enumerate(MESES):
        novos[abas[mes]] = _mes(zin.read(abas[mes]), i)
    novos[abas["Evolução"]] = _evolucao(zin.read(abas["Evolução"]))
    novos[abas["Contas e Cadastro"]] = _contas(zin.read(abas["Contas e Cadastro"]))
    novos[abas["C.Crédito"]] = _cartao(zin.read(abas["C.Crédito"]))
    novos["xl/styles.xml"] = _styles(zin.read("xl/styles.xml"))

    # aba Notas (nova parte + relacionamento + content type)
    n_sheet = 1 + max(int(m) for m in (re.search(r"sheet(\d+)\.xml$", p).group(1)
                                       for p in zin.namelist() if re.search(r"worksheets/sheet\d+\.xml$", p)))
    parte = f"xl/worksheets/sheet{n_sheet}.xml"
    rels = _xml(zin.read("xl/_rels/workbook.xml.rels"))
    rids = [int(re.sub(r"\D", "", r.get("Id")) or 0) for r in rels]
    rid = f"rId{max(rids) + 1}"
    etree.SubElement(rels, "{%s}Relationship" % NS_PKG, Id=rid,
                     Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                     Target=f"worksheets/sheet{n_sheet}.xml")
    novos["xl/_rels/workbook.xml.rels"] = _bytes(rels)
    wbx = _xml(zin.read("xl/workbook.xml"))
    sheet_id = 1 + max(int(s.get("sheetId")) for s in wbx.iter(_X + "sheet"))
    novos["xl/workbook.xml"] = _workbook(zin.read("xl/workbook.xml"), rid, sheet_id)
    ct = _xml(zin.read("[Content_Types].xml"))
    etree.SubElement(ct, "{%s}Override" % NS_CT, PartName="/" + parte,
                     ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml")
    novos["[Content_Types].xml"] = _bytes(ct)
    novos[parte] = _aba_notas()

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            dados = novos.pop(item.filename, None)
            zout.writestr(item, dados if dados is not None else zin.read(item.filename))
        for nome, dados in novos.items():             # partes novas (aba Notas)
            zout.writestr(nome, dados)
    return out.getvalue()


def gerar(versao: str):
    if not TEMPLATE.exists():
        raise FileNotFoundError(MSG_SEM_MODELO)
    original = TEMPLATE.read_bytes()
    if versao == "fiel":
        return original, _nome_fiel()
    if versao == "aprimorada":
        return _aprimorar(original), "ControleFinanceiro_Aprimorado.xlsx"
    raise ValueError("versão inválida (use 'fiel' ou 'aprimorada')")


if __name__ == "__main__":   # uso: python app/financeiro.py <fiel|aprimorada> <saida.xlsx>
    import sys
    dados, nome = gerar(sys.argv[1])
    Path(sys.argv[2] if len(sys.argv) > 2 else nome).write_bytes(dados)
    print("ok", nome, len(dados), "bytes")
