"""Leitores e composição de capítulos e pré-textuais."""
import os
import re
import warnings
from docx import Document
from docx.oxml.ns import qn
from .modelo import Bloco, Livro
from .caminhos import _resolver_caminho
from .config import EXTS_DOC

RE_CAPITULO_TXT = re.compile(
    r"^\s*(cap[íi]tulo\s+[\divxlc]+|pr[óo]logo|ep[íi]logo|pref[áa]cio|"
    r"introdu[çc][ãa]o|conclus[ãa]o|ap[êe]ndice.*|parte\s+[\divxlc]+)\s*[:.\-–—]?\s*(.*)$",
    re.IGNORECASE)


_RE_QUEBRA_PARAGRAFO = re.compile(r"^(#{1,6}\s|>|```|[-*+]\s|\d+[.)]\s|\||!?\[)")


_RE_CENA = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")


_RE_IMAGEM_BLOCO = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")


_RE_TABELA_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")


def _celulas(linha: str) -> list:
    """Divide uma linha de tabela Markdown em células."""
    linha = linha.strip()
    if linha.startswith("|"):
        linha = linha[1:]
    if linha.endswith("|"):
        linha = linha[:-1]
    return [c.strip() for c in linha.split("|")]


def ler_markdown(caminho: str) -> Livro:
    livro = Livro(base_dir=os.path.dirname(os.path.abspath(caminho)))
    with open(caminho, encoding="utf-8-sig") as f:   # utf-8-sig: ignora BOM
        linhas = f.read().splitlines()

    i, em_codigo, buffer_codigo = 0, False, []
    while i < len(linhas):
        ln = linhas[i]

        # Blocos de código cercados ```
        if ln.strip().startswith("```"):
            if em_codigo:
                livro.blocos.append(Bloco("code", "\n".join(buffer_codigo)))
                buffer_codigo, em_codigo = [], False
            else:
                em_codigo = True
            i += 1
            continue
        if em_codigo:
            buffer_codigo.append(ln)
            i += 1
            continue

        s = ln.strip()
        if not s:
            i += 1
            continue

        # Quebra de cena / divisória (antes de listas, pois --- casaria com lista)
        if _RE_CENA.match(s):
            livro.blocos.append(Bloco("hr", ""))
            i += 1
            continue

        # Títulos ATX de 1 a 6 (# .. ######); nível interno é limitado a h3
        m_head = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m_head:
            nivel = len(m_head.group(1))
            texto = m_head.group(2).strip().rstrip("#").strip()
            if nivel == 1:
                if livro.titulo == "Sem título" and not any(
                        b.tipo == "h1" for b in livro.blocos):
                    livro.titulo = texto            # 1º H1 = título do livro
                else:
                    livro.blocos.append(Bloco("h1", texto))
            elif nivel == 2:
                livro.blocos.append(Bloco("h2", texto))
            else:                                    # h3..h6 → h3
                livro.blocos.append(Bloco("h3", texto))
            i += 1
            continue

        # Imagem em bloco (linha inteira)
        m_img = _RE_IMAGEM_BLOCO.match(s)
        if m_img:
            alt, src = m_img.group(1), m_img.group(2).strip()
            livro.blocos.append(
                Bloco("image", _resolver_caminho(livro.base_dir, src), extra=alt))
            i += 1
            continue

        # Tabela: linha com | seguida por linha separadora |---|---|
        if "|" in s and i + 1 < len(linhas) and _RE_TABELA_SEP.match(linhas[i + 1]):
            linhas_tab = [_celulas(s)]
            i += 2  # pula cabeçalho + separador
            while i < len(linhas) and "|" in linhas[i] and linhas[i].strip():
                linhas_tab.append(_celulas(linhas[i]))
                i += 1
            livro.blocos.append(Bloco("table", "", itens=linhas_tab))
            continue

        if s.startswith(">"):
            livro.blocos.append(Bloco("quote", s.lstrip("> ").strip()))
        # Lista NÃO-ordenada
        elif re.match(r"^[-*+]\s+", s):
            itens = []
            while i < len(linhas) and re.match(r"^\s*[-*+]\s+", linhas[i]):
                itens.append(re.sub(r"^\s*[-*+]\s+", "", linhas[i]).strip())
                i += 1
            livro.blocos.append(Bloco("list", "", itens, ordenada=False))
            continue
        # Lista ORDENADA (1. 2. 3.  ou  1) 2) 3))
        elif re.match(r"^\d+[.)]\s+", s):
            itens = []
            while i < len(linhas) and re.match(r"^\s*\d+[.)]\s+", linhas[i]):
                itens.append(re.sub(r"^\s*\d+[.)]\s+", "", linhas[i]).strip())
                i += 1
            livro.blocos.append(Bloco("list", "", itens, ordenada=True))
            continue
        else:
            # Junta linhas contíguas num mesmo parágrafo
            par = [s]
            while (i + 1 < len(linhas) and linhas[i + 1].strip()
                   and not _RE_QUEBRA_PARAGRAFO.match(linhas[i + 1].strip())):
                i += 1
                par.append(linhas[i].strip())
            livro.blocos.append(Bloco("p", " ".join(par)))
        i += 1

    if em_codigo:
        livro.blocos.append(Bloco("code", "\n".join(buffer_codigo)))
        warnings.warn(f"{caminho}: bloco de código sem fechamento; conteúdo preservado.")

    # Se não houve nenhum H1 no corpo, promove H2→capítulos
    if not any(b.tipo == "h1" for b in livro.blocos):
        for b in livro.blocos:
            if b.tipo == "h2":
                b.tipo = "h1"
            elif b.tipo == "h3":
                b.tipo = "h2"
    return _atribuir_origem(livro)


_PALAVRAS_MINUSCULAS = {
    "a", "o", "as", "os", "e", "de", "da", "do", "das", "dos", "em", "no",
    "na", "nos", "nas", "um", "uma", "por", "para", "com", "sem", "sob",
    "ao", "aos", "à", "às", "que", "se", "ou", "the", "of", "and", "in",
}


def titulo_ptbr(s: str) -> str:
    """Title-case que respeita preposições/artigos do português."""
    palavras = s.lower().split()
    saida = []
    for idx, p in enumerate(palavras):
        if idx != 0 and p in _PALAVRAS_MINUSCULAS:
            saida.append(p)
        else:
            saida.append(p[:1].upper() + p[1:])
    return " ".join(saida)


def ler_txt(caminho: str) -> Livro:
    """TXT simples: detecta capítulos por heurística."""
    livro = Livro(base_dir=os.path.dirname(os.path.abspath(caminho)))
    with open(caminho, encoding="utf-8-sig") as f:
        linhas = f.read().splitlines()

    par = []
    def fecha_paragrafo():
        if par:
            livro.blocos.append(Bloco("p", " ".join(par)))
            par.clear()

    for ln in linhas:
        s = ln.strip()
        if not s:
            fecha_paragrafo()
            continue
        m = RE_CAPITULO_TXT.match(s)
        # Linha curta toda em caixa-alta também vira capítulo
        caixa_alta = (s.isupper() and 3 < len(s) < 60 and not s.endswith((".", ",", ";")))
        if m or caixa_alta:
            fecha_paragrafo()
            livro.blocos.append(Bloco("h1", titulo_ptbr(s) if s.isupper() else s))
        else:
            par.append(s)
    fecha_paragrafo()
    return _atribuir_origem(livro)


def ler_docx(caminho: str) -> Livro:
    """Lê .docx existente mapeando estilos de título → capítulos/seções."""
    livro = Livro(base_dir=os.path.dirname(os.path.abspath(caminho)))
    doc = Document(caminho)
    props = doc.core_properties
    if props.title:
        livro.titulo = props.title
    if props.author:
        livro.autor = props.author

    from docx.text.paragraph import Paragraph
    from docx.table import Table
    from docx.text.run import Run

    def texto_formatado(elemento, parent):
        partes = []
        for node in elemento:
            if node.tag == qn("w:r"):
                run = Run(node, parent)
                s = run.text
                if s and run.bold and run.italic:
                    s = f"***{s}***"
                elif s and run.bold:
                    s = f"**{s}**"
                elif s and run.italic:
                    s = f"*{s}*"
                partes.append(s)
            elif node.tag == qn("w:hyperlink"):
                label = texto_formatado(node, parent)
                rid = node.get(qn("r:id"))
                url = doc.part.rels[rid].target_ref if rid else "#" + node.get(qn("w:anchor"), "")
                partes.append(f"[{label}]({url})")
        return "".join(partes)

    for elemento in doc.element.body:
        if elemento.tag == qn("w:tbl"):
            tabela = Table(elemento, doc)
            linhas = [["\n".join(texto_formatado(p._p, p) for p in cel.paragraphs)
                       for cel in row.cells] for row in tabela.rows]
            livro.blocos.append(Bloco("table", "", itens=linhas))
            for blip in elemento.iter(qn("a:blip")):
                rid = blip.get(qn("r:embed"))
                if rid:
                    livro.blocos.append(Bloco("image", doc.part.related_parts[rid].blob))
            continue
        if elemento.tag != qn("w:p"):
            continue
        p = Paragraph(elemento, doc)
        txt = texto_formatado(elemento, p).strip()
        imagens = []
        for blip in elemento.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if rid:
                imagens.append(Bloco("image", doc.part.related_parts[rid].blob))
        if not txt:
            livro.blocos.extend(imagens)
            continue
        estilo = (p.style.name or "").lower()
        if "heading 1" in estilo or "título 1" in estilo or estilo == "title":
            livro.blocos.append(Bloco("h1", txt))
        elif "heading 2" in estilo or "título 2" in estilo:
            livro.blocos.append(Bloco("h2", txt))
        elif "heading 3" in estilo or "título 3" in estilo:
            livro.blocos.append(Bloco("h3", txt))
        elif "quote" in estilo or "citação" in estilo:
            livro.blocos.append(Bloco("quote", txt))
        elif "list" in estilo or "lista" in estilo:
            ordenada = ("number" in estilo or "número" in estilo
                        or "numero" in estilo)
            if (livro.blocos and livro.blocos[-1].tipo == "list"
                    and livro.blocos[-1].ordenada == ordenada):
                livro.blocos[-1].itens.append(txt)
            else:
                livro.blocos.append(Bloco("list", "", [txt], ordenada=ordenada))
        else:
            # Heurística extra: docx sem estilos de título
            m = RE_CAPITULO_TXT.match(txt)
            if m and len(txt) < 60:
                livro.blocos.append(Bloco("h1", txt))
            else:
                livro.blocos.append(Bloco("p", txt))
        livro.blocos.extend(imagens)
    return _atribuir_origem(livro)


def carregar(caminho: str) -> Livro:
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".md":
        return ler_markdown(caminho)
    if ext == ".txt":
        return ler_txt(caminho)
    if ext == ".docx":
        return ler_docx(caminho)
    raise ValueError(f"Formato não suportado: {ext} (use .md, .txt ou .docx)")


_EXTS_DOC = EXTS_DOC


_EXTS_IMAGEM = (".jpg", ".jpeg", ".png", ".webp", ".gif")


_FM_CAPA = {"capa", "cover"}


_FM_HOMENAGENS = {"homenagens", "homenagem", "dedicatoria", "agradecimentos"}


_FM_PREFACIO = {"prefacio", "apresentacao"}


def _stem_reservado(caminho: str) -> str:
    """Nome-base: sem extensão, sem prefixo numérico, sem acento, minúsculo."""
    import unicodedata
    stem = os.path.splitext(os.path.basename(caminho))[0]
    stem = re.sub(r"^\d+[\s._-]*", "", stem).strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", stem)
                   if unicodedata.category(c) != "Mn")


def _classe_pre_textual(caminho: str):
    """'capa' | 'homenagens' | 'prefacio' se for pré-textual; senão None."""
    stem = _stem_reservado(caminho)
    ext = os.path.splitext(caminho)[1].lower()
    if stem in _FM_CAPA and ext in _EXTS_IMAGEM:
        return "capa"
    if stem in _FM_HOMENAGENS and ext in _EXTS_DOC:
        return "homenagens"
    if stem in _FM_PREFACIO and ext in _EXTS_DOC:
        return "prefacio"
    return None


def _carregar_pre_textual(caminho: str):
    """Lê um arquivo pré-textual → (titulo_ou_None, blocos)."""
    livro = carregar(caminho)
    titulo = livro.titulo if livro.titulo != "Sem título" else None
    return titulo, livro.blocos


def carregar_multiplos(caminhos: list) -> Livro:
    """
    Une vários arquivos (ou uma pasta) em um único Livro.
    - Pastas são expandidas para todos os .md/.txt/.docx em ordem alfabética
      (por isso vale nomear os capítulos como 01_intro.md, 02_medias.md...).
    - Arquivos pré-textuais (capa/homenagens/prefácio) são reconhecidos pelo
      NOME e retirados do fluxo de capítulos (ver _classe_pre_textual).
    - O título do livro vem do 1º H1 do 1º capítulo (ou de --titulo).
    - Nos demais arquivos, o 1º H1 é mantido como título de capítulo.
    - Arquivo sem nenhum H1 ganha um capítulo com o nome do próprio arquivo.
    """
    # Expande pastas → arquivos (docs E imagens, para encontrar a capa)
    todos = []
    for c in caminhos:
        if os.path.isdir(c):
            todos += sorted(
                os.path.join(c, f) for f in os.listdir(c)
                if f.lower().endswith(_EXTS_DOC + _EXTS_IMAGEM)
                and not f.startswith(("~$", ".")))
        else:
            todos.append(c)

    # Separa os pré-textuais do fluxo de capítulos
    capa = ""
    homenagens_tit, homenagens = None, None
    prefacio_tit, prefacio = None, None
    arquivos = []
    for arq in todos:
        classe = _classe_pre_textual(arq)
        if classe == "capa":
            capa = arq
            print(f"   ★ capa       : {os.path.basename(arq)}")
        elif classe == "homenagens":
            homenagens_tit, homenagens = _carregar_pre_textual(arq)
            print(f"   ★ homenagens : {os.path.basename(arq)}")
        elif classe == "prefacio":
            prefacio_tit, prefacio = _carregar_pre_textual(arq)
            print(f"   ★ prefácio   : {os.path.basename(arq)}")
        elif arq.lower().endswith(_EXTS_DOC):
            arquivos.append(arq)
        # imagens não-capa entram no texto via ![](...); aqui são ignoradas

    if not arquivos:
        raise ValueError("Nenhum arquivo .md/.txt/.docx de capítulo encontrado.")

    # Monta o miolo a partir dos capítulos
    if len(arquivos) == 1:
        final = carregar(arquivos[0])
    else:
        final = Livro(base_dir=os.path.dirname(os.path.abspath(arquivos[0])))
        for idx, arq in enumerate(arquivos):
            parcial = carregar(arq)
            blocos = list(parcial.blocos)
            if idx == 0:
                # 1º capítulo define título/autor do livro
                final.titulo = parcial.titulo
                final.autor = parcial.autor
            elif parcial.titulo != "Sem título":
                # Nos demais, o H1 "consumido" como título volta a ser capítulo
                blocos.insert(0, Bloco("h1", parcial.titulo, base_dir=parcial.base_dir))
            # Arquivo sem nenhum capítulo → usa o nome do arquivo como capítulo
            if not any(b.tipo == "h1" for b in blocos):
                nome = os.path.splitext(os.path.basename(arq))[0]
                nome = re.sub(r"^\d+[\s._-]*", "", nome).replace("_", " ").replace("-", " ").strip()
                blocos.insert(0, Bloco("h1", nome.title() or f"Capítulo {idx + 1}", base_dir=parcial.base_dir))
            final.blocos.extend(blocos)
            print(f"   + {os.path.basename(arq)} "
                  f"({sum(1 for b in blocos if b.tipo == 'h1')} capítulo(s))")

    # Anexa os pré-textuais ao Livro
    if capa:
        final.capa = capa if os.path.isabs(capa) else os.path.abspath(capa)
    if homenagens is not None:
        final.homenagens = homenagens
        final.homenagens_titulo = homenagens_tit or ""
    if prefacio is not None:
        final.prefacio = prefacio
        final.prefacio_titulo = prefacio_tit or "Prefácio"
    return final


def _atribuir_origem(livro):
    for bloco in livro.blocos:
        bloco.base_dir = livro.base_dir
    return livro

