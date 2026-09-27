"""Renderização DOCX e campos XML do Word."""
import io
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from .config import PresetGenero, Formato, resolver_corpo
from .modelo import Livro
from .inline import tokenizar_inline
from .caminhos import _resolver_caminho
from .arquivos import _gravar_atomico

def _campo(paragrafo, instrucao: str, texto_provisorio: str = ""):
    """Insere um campo dinâmico do Word (TOC, PAGE...)."""
    r1 = paragrafo.add_run()
    fld = OxmlElement("w:fldChar"); fld.set(qn("w:fldCharType"), "begin")
    r1._r.append(fld)

    r2 = paragrafo.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instrucao
    r2._r.append(instr)

    r3 = paragrafo.add_run()
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    r3._r.append(sep)

    if texto_provisorio:
        paragrafo.add_run(texto_provisorio)

    r4 = paragrafo.add_run()
    fim = OxmlElement("w:fldChar"); fim.set(qn("w:fldCharType"), "end")
    r4._r.append(fim)


def _sombrear(paragrafo, cor_hex: str):
    """Fundo cinza para blocos de código."""
    pPr = paragrafo._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), cor_hex)
    pPr.append(shd)


def _habilitar_hifenizacao(doc):
    """Liga a hifenização automática do Word (essencial em texto justificado)."""
    settings = doc.settings.element
    auto = OxmlElement("w:autoHyphenation"); auto.set(qn("w:val"), "true")
    lim = OxmlElement("w:consecutiveHyphenLimit"); lim.set(qn("w:val"), "2")
    zona = OxmlElement("w:hyphenationZone"); zona.set(qn("w:val"), "360")  # ~0,25"
    settings.append(auto)
    settings.append(lim)
    settings.append(zona)


def _atualizar_campos_ao_abrir(doc):
    """Faz o Word oferecer a atualização de campos (ex.: sumário) ao abrir."""
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields"); upd.set(qn("w:val"), "true")
    settings.append(upd)


def _definir_idioma_estilo(estilo, lang="pt-BR"):
    """Define o idioma do estilo (para hifenização e correção usarem pt-BR)."""
    rPr = estilo.element.get_or_add_rPr()
    el = rPr.find(qn("w:lang"))
    if el is None:
        el = OxmlElement("w:lang")
        rPr.append(el)
    el.set(qn("w:val"), lang)


def _add_hyperlink(paragrafo, texto, url):
    """Insere um hyperlink real (clicável) no parágrafo do Word."""
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    r_id = paragrafo.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    cor = OxmlElement("w:color"); cor.set(qn("w:val"), "0563C1"); rPr.append(cor)
    sub = OxmlElement("w:u"); sub.set(qn("w:val"), "single"); rPr.append(sub)
    run.append(rPr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = texto
    run.append(t)
    link.append(run)
    paragrafo._p.append(link)


def escrever_runs(paragrafo, texto: str, preset, base_dir: str = ""):
    """Escreve runs formatados no parágrafo a partir do Markdown inline."""
    for tok in tokenizar_inline(texto):
        tipo = tok[0]
        if tipo == "text":
            paragrafo.add_run(tok[1])
        elif tipo == "bold":
            paragrafo.add_run(tok[1]).bold = True
        elif tipo == "italic":
            paragrafo.add_run(tok[1]).italic = True
        elif tipo == "bolditalic":
            r = paragrafo.add_run(tok[1]); r.bold = True; r.italic = True
        elif tipo == "code":
            r = paragrafo.add_run(tok[1])
            r.font.name = preset.fonte_codigo
            r.font.size = Pt(10)
        elif tipo == "link":
            _add_hyperlink(paragrafo, tok[1], tok[2])
        elif tipo == "image":
            caminho = _resolver_caminho(base_dir, tok[1])
            try:
                paragrafo.add_run().add_picture(caminho, width=Cm(4))
            except Exception:
                paragrafo.add_run(f"[{tok[2] or 'imagem'}]")


def _config_estilo(st, fonte, tam, negrito=False, cor=None,
                   entrelinha=None, antes=0, depois=0, recuo=0,
                   justificado=False, centralizado=False, caixa_alta=False):
    st.font.name = fonte
    st.font.size = Pt(tam)
    st.font.bold = negrito
    st.font.all_caps = caixa_alta
    # Garante a fonte também para caracteres complexos/east-asia
    rPr = st.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rFonts.set(qn(attr), fonte)
    if rFonts.getparent() is None:
        rPr.append(rFonts)
    if cor:
        st.font.color.rgb = RGBColor.from_string(cor)
    pf = st.paragraph_format
    if entrelinha:
        pf.line_spacing = entrelinha
    pf.space_before = Pt(antes)
    pf.space_after = Pt(depois)
    if recuo:
        pf.first_line_indent = Cm(recuo)
    if centralizado:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif justificado:
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    else:
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.widow_control = True


def _emitir_bloco_pretextual(doc, b, preset, fmt, base_dir,
                             centralizar=False, italico=False, apos_titulo=False):
    """Renderiza um bloco de pré-textual (homenagens/prefácio) no DOCX.
    Espelha o rendering do miolo, com opção de centralizar/italizar (dedicatória)."""
    base_dir = b.base_dir or base_dir
    corpo = resolver_corpo(preset)
    if b.tipo == "table":
        if b.itens:
            tabela = doc.add_table(rows=0, cols=max(len(linha) for linha in b.itens))
            tabela.style = "Table Grid"
            for idx, linha in enumerate(b.itens):
                cels = tabela.add_row().cells
                for col, texto in enumerate(linha):
                    escrever_runs(cels[col].paragraphs[0], texto, preset, base_dir)
                    if idx == 0:
                        for run in cels[col].paragraphs[0].runs:
                            run.bold = True
        return
    if b.tipo == "code":
        for linha in b.texto.split("\n"):
            p = doc.add_paragraph()
            run = p.add_run(linha or " ")
            run.font.name = preset.fonte_codigo
            run.font.size = Pt(9.5)
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_after = Pt(0)
            _sombrear(p, "F2F2F2")
        return
    if b.tipo in ("h2", "h3"):
        h = doc.add_paragraph(style="Heading 2" if b.tipo == "h2" else "Heading 3")
        escrever_runs(h, b.texto, preset, base_dir)
        return
    if b.tipo == "quote":
        p = doc.add_paragraph()
        escrever_runs(p, b.texto, preset, base_dir)
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0); pf.right_indent = Cm(1.0)
        pf.first_line_indent = Cm(0)
        for r in p.runs:
            r.italic = True
        return
    if b.tipo == "hr":
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run("* * *")
        r.font.name = preset.fonte_titulos
        return
    if b.tipo == "list":
        estilo = "List Number" if b.ordenada else "List Bullet"
        for item in b.itens:
            p = doc.add_paragraph(style=estilo)
            escrever_runs(p, item, preset, base_dir)
            p.paragraph_format.first_line_indent = Cm(0)
        return
    if b.tipo == "image":
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        try:
            larg = fmt.largura_cm - fmt.margem_int - fmt.margem_ext - fmt.medianiz
            p.add_run().add_picture(io.BytesIO(b.texto) if isinstance(b.texto, bytes) else b.texto, width=Cm(larg))
        except Exception:
            p.add_run(f"[imagem não encontrada: {b.extra or b.texto}]").italic = True
        return
    # parágrafo comum (e fallback)
    p = doc.add_paragraph()
    escrever_runs(p, b.texto, preset, base_dir)
    pf = p.paragraph_format
    if centralizar:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Cm(0)
    elif apos_titulo and corpo.recuo:
        pf.first_line_indent = Cm(0)
    if italico:
        for r in p.runs:
            r.italic = True


def diagramar_docx(livro: Livro, preset: PresetGenero, fmt: Formato,
                   saida: str, incluir_sumario=True, capa_no_miolo=True):
    corpo = resolver_corpo(preset)
    doc = Document()

    # ---- Página e margens espelhadas -------------------------------
    sec = doc.sections[0]
    sec.page_width = Cm(fmt.largura_cm)
    sec.page_height = Cm(fmt.altura_cm)
    sec.top_margin = Cm(fmt.margem_sup)
    sec.bottom_margin = Cm(fmt.margem_inf)
    sec.left_margin = Cm(fmt.margem_int)
    sec.right_margin = Cm(fmt.margem_ext)
    sec.gutter = Cm(fmt.medianiz)
    # mirrorMargins (margens espelhadas para impressão frente/verso)
    sectPr = sec._sectPr
    if sectPr.find(qn("w:mirrorMargins")) is None:
        sectPr.append(OxmlElement("w:mirrorMargins"))

    # ---- Idioma + hifenização (tipografia) --------------------------
    _definir_idioma_estilo(doc.styles["Normal"], "pt-BR")
    if preset.justificado:
        # Hifenização só faz sentido/ajuda de fato em texto justificado.
        _habilitar_hifenizacao(doc)

    # ---- Estilos ----------------------------------------------------
    est = doc.styles
    # Corpo de texto usa o ajuste fino GLOBAL (recuo/espaçamento/entrelinha),
    # sobrepondo os valores do preset. Do preset ficam só fonte, tamanho e
    # justificação, que continuam variando por gênero.
    _config_estilo(est["Normal"], preset.fonte_corpo, preset.tam_corpo,
                   entrelinha=corpo.entrelinha,
                   antes=corpo.antes,
                   depois=corpo.depois,
                   recuo=corpo.recuo,
                   justificado=preset.justificado)
    # antes=36: "respiro" do capítulo controlado pelo estilo (mais robusto que
    # inserir parágrafos vazios, que podem escorregar para o topo da página).
    _config_estilo(est["Heading 1"], preset.fonte_titulos, preset.tam_capitulo,
                   negrito=True, cor=preset.cor_titulos,
                   antes=36, depois=24, centralizado=True,
                   caixa_alta=preset.capitulo_caixa_alta)
    if preset.espacamento_titulo:
        rPr = est["Heading 1"].element.get_or_add_rPr()
        esp = OxmlElement("w:spacing")
        esp.set(qn("w:val"), str(int(preset.espacamento_titulo * 20)))  # 20 = pt→twips
        rPr.append(esp)
    est["Heading 1"].paragraph_format.page_break_before = False  # controlamos manualmente
    _config_estilo(est["Heading 2"], preset.fonte_titulos, preset.tam_secao,
                   negrito=True, cor=preset.cor_titulos, antes=18, depois=8)
    _config_estilo(est["Heading 3"], preset.fonte_titulos,
                   max(preset.tam_corpo + 1, preset.tam_secao - 2),
                   negrito=True, cor=preset.cor_titulos, antes=12, depois=6)

    # ---- Capa (imagem) ou página de rosto (texto) -------------------
    capa_ok = False
    if livro.capa and capa_no_miolo:
        try:
            avail_w = Cm(fmt.largura_cm - fmt.margem_int - fmt.margem_ext - fmt.medianiz)
            avail_h = Cm(fmt.altura_cm - fmt.margem_sup - fmt.margem_inf)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(0)
            pic = p.add_run().add_picture(livro.capa, width=avail_w)
            if pic.height > avail_h:                 # não estourar a altura da página
                fator = avail_h / pic.height
                pic.height = int(pic.height * fator)
                pic.width = int(pic.width * fator)
            doc.add_page_break()
            capa_ok = True
        except Exception as e:
            print(f"   ⚠ não consegui inserir a capa no miolo ({e}); "
                  f"caindo para a página de rosto em texto.")

    if not capa_ok:
        # Página de rosto em texto: fallback sem imagem de capa, ou quando
        # --sem-capa-no-miolo é usado para gerar o miolo de KDP print.
        for _ in range(6):
            doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(livro.titulo)
        r.font.name = preset.fonte_titulos
        r.font.size = Pt(min(preset.tam_capitulo + 8, 36))
        r.bold = True
        r.font.color.rgb = RGBColor.from_string(preset.cor_titulos)
        if livro.subtitulo:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(livro.subtitulo)
            r.font.name = preset.fonte_titulos
            r.font.size = Pt(preset.tam_secao + 2)
            r.italic = True
        for _ in range(4):
            doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(livro.autor)
        r.font.name = preset.fonte_titulos
        r.font.size = Pt(preset.tam_secao + 2)
        doc.add_page_break()

    # ---- Página de créditos ------------------------------------------
    for _ in range(14):
        doc.add_paragraph()
    for linha in (f"© {livro.ano or ''} {livro.autor}".strip(),
                  "Todos os direitos reservados.",
                  "Nenhuma parte desta obra pode ser reproduzida",
                  "sem autorização prévia do autor.",
                  "",
                  f"Diagramação: preset “{preset.nome}” · fonte {preset.fonte_corpo}"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(linha)
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string("595959")
    doc.add_page_break()

    # ---- Homenagens / dedicatória -----------------------------------
    if livro.homenagens:
        for _ in range(6):
            doc.add_paragraph()
        if livro.homenagens_titulo:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            r = p.add_run(livro.homenagens_titulo)
            r.font.name = preset.fonte_titulos
            r.font.size = Pt(preset.tam_secao + 2)
            r.bold = True
            r.font.color.rgb = RGBColor.from_string(preset.cor_titulos)
            p.paragraph_format.space_after = Pt(18)
        for b in livro.homenagens:
            _emitir_bloco_pretextual(doc, b, preset, fmt, livro.base_dir,
                                     centralizar=True, italico=True)
        doc.add_page_break()

    # ---- Sumário (campo TOC nativo) ----------------------------------
    if incluir_sumario:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("Sumário")
        r.font.name = preset.fonte_titulos
        r.font.size = Pt(preset.tam_capitulo - 2)
        r.bold = True
        r.font.color.rgb = RGBColor.from_string(preset.cor_titulos)
        p.paragraph_format.space_after = Pt(20)
        p_toc = doc.add_paragraph()
        _campo(p_toc, r'TOC \o "1-2" \h \z \u',
               "Sumário automático — clique com o botão direito → "
               "“Atualizar campo” no Word para preencher.")
        _atualizar_campos_ao_abrir(doc)  # Word oferece atualizar o TOC ao abrir
        doc.add_page_break()

    # ---- Prefácio ---------------------------------------------------
    if livro.prefacio:
        h = doc.add_paragraph(style="Heading 1")   # Heading 1 → entra no sumário
        escrever_runs(h, livro.prefacio_titulo or "Prefácio", preset, livro.base_dir)
        apos = True
        for b in livro.prefacio:
            _emitir_bloco_pretextual(doc, b, preset, fmt, livro.base_dir,
                                     apos_titulo=apos)
            apos = False
        doc.add_page_break()

    # ---- Conteúdo -----------------------------------------------------
    primeiro_cap = True
    apos_titulo = False
    for b in livro.blocos:
        base_dir = b.base_dir or livro.base_dir
        if b.tipo == "h1":
            if not primeiro_cap:
                doc.add_page_break()
            primeiro_cap = False
            # "respiro" vem do space_before=36 do estilo Heading 1
            h = doc.add_paragraph(style="Heading 1")
            escrever_runs(h, b.texto, preset, base_dir)
            apos_titulo = True
        elif b.tipo == "h2":
            h = doc.add_paragraph(style="Heading 2")
            escrever_runs(h, b.texto, preset, base_dir)
            apos_titulo = True
        elif b.tipo == "h3":
            h = doc.add_paragraph(style="Heading 3")
            escrever_runs(h, b.texto, preset, base_dir)
            apos_titulo = True
        elif b.tipo == "code":
            for ln in b.texto.split("\n"):
                p = doc.add_paragraph()
                r = p.add_run(ln if ln else " ")
                r.font.name = preset.fonte_codigo
                r.font.size = Pt(9.5)
                pf = p.paragraph_format
                pf.space_after = Pt(0)
                pf.first_line_indent = Cm(0)
                pf.left_indent = Cm(0.4)
                pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
                _sombrear(p, "F2F2F2")
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        elif b.tipo == "quote":
            p = doc.add_paragraph()
            escrever_runs(p, b.texto, preset, base_dir)
            pf = p.paragraph_format
            pf.left_indent = Cm(1.0)
            pf.right_indent = Cm(1.0)
            pf.first_line_indent = Cm(0)
            pf.space_before = Pt(6)
            pf.space_after = Pt(6)
            for r in p.runs:
                r.italic = True
        elif b.tipo == "hr":
            # Quebra de cena: dínkus centralizado (convenção editorial)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.space_before = Pt(12)
            pf.space_after = Pt(12)
            r = p.add_run("* * *")
            r.font.name = preset.fonte_titulos
        elif b.tipo == "image":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            try:
                # largura máxima = área útil da página
                larg = fmt.largura_cm - fmt.margem_int - fmt.margem_ext - fmt.medianiz
                p.add_run().add_picture(io.BytesIO(b.texto) if isinstance(b.texto, bytes) else b.texto, width=Cm(larg))
            except Exception:
                p.add_run(f"[imagem não encontrada: {b.extra or b.texto}]").italic = True
            if b.extra:  # legenda a partir do alt
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.paragraph_format.first_line_indent = Cm(0)
                rc = cap.add_run(b.extra)
                rc.italic = True
                rc.font.size = Pt(max(preset.tam_corpo - 2, 8))
        elif b.tipo == "table":
            if b.itens:
                n_col = max(len(l) for l in b.itens)
                tabela = doc.add_table(rows=0, cols=n_col)
                tabela.style = "Table Grid"
                for r_idx, linha in enumerate(b.itens):
                    cels = tabela.add_row().cells
                    for c_idx in range(n_col):
                        txt = linha[c_idx] if c_idx < len(linha) else ""
                        celula = cels[c_idx]
                        celula.paragraphs[0].text = ""
                        escrever_runs(celula.paragraphs[0], txt, preset, base_dir)
                        for run_cel in celula.paragraphs[0].runs:
                            run_cel.font.name = preset.fonte_corpo
                            run_cel.font.size = Pt(max(preset.tam_corpo - 1, 9))
                            if r_idx == 0:
                                run_cel.bold = True
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        elif b.tipo == "list":
            estilo = "List Number" if b.ordenada else "List Bullet"
            for item in b.itens:
                p = doc.add_paragraph(style=estilo)
                escrever_runs(p, item, preset, base_dir)
                p.paragraph_format.first_line_indent = Cm(0)
        else:  # parágrafo comum
            p = doc.add_paragraph()
            escrever_runs(p, b.texto, preset, base_dir)
            # 1º parágrafo após um título: sem recuo (convenção editorial)
            if apos_titulo and corpo.recuo:
                p.paragraph_format.first_line_indent = Cm(0)
            apos_titulo = False

    # ---- Rodapé com número de página ----------------------------------
    rodape = sec.footer.paragraphs[0]
    rodape.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _campo(rodape, "PAGE")
    for r in rodape.runs:
        r.font.size = Pt(9)
        r.font.name = preset.fonte_corpo

    # ---- Metadados ------------------------------------------------------
    doc.core_properties.title = livro.titulo
    doc.core_properties.author = livro.autor

    _gravar_atomico(saida, doc.save)
    return saida

