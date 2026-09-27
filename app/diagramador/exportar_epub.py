"""Renderização EPUB, imagens e CSS."""
import os
import re
import html
import uuid
from .config import PresetGenero, resolver_corpo
from .modelo import Livro
from .inline import tokenizar_inline
from .caminhos import _resolver_caminho
from .arquivos import _gravar_atomico

def _pilha_fontes(fontes: list) -> str:
    return ", ".join(f'"{f}"' for f in fontes) + ", serif"


def _mime_imagem(nome: str) -> str:
    ext = os.path.splitext(nome)[1].lower()
    return {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
    }.get(ext, "image/png")


def _md_inline_para_html(texto: str, mapa=None, base_dir: str = "") -> str:
    """Converte Markdown inline em HTML usando o mesmo tokenizador do DOCX."""
    out = []
    for tok in tokenizar_inline(texto):
        t = tok[0]
        if t == "text":
            out.append(html.escape(tok[1]))
        elif t == "bold":
            out.append(f"<strong>{html.escape(tok[1])}</strong>")
        elif t == "italic":
            out.append(f"<em>{html.escape(tok[1])}</em>")
        elif t == "bolditalic":
            out.append(f"<strong><em>{html.escape(tok[1])}</em></strong>")
        elif t == "code":
            out.append(f"<code>{html.escape(tok[1])}</code>")
        elif t == "link":
            out.append(f'<a href="{html.escape(tok[2], quote=True)}">'
                       f"{html.escape(tok[1])}</a>")
        elif t == "image":
            src = _resolver_caminho(base_dir, tok[1])
            href = (mapa or {}).get(src)
            if href:
                out.append(f'<img src="{html.escape(href, quote=True)}" '
                           f'alt="{html.escape(tok[2], quote=True)}"/>')
            else:
                out.append(html.escape(f"[{tok[2] or 'imagem'}]"))
    return "".join(out)


def _registrar_imagens(ebook, livro):
    """Adiciona ao EPUB todas as imagens referenciadas; retorna mapa src→href."""
    from ebooklib import epub
    mapa = {}

    def add(src):
        if not src or src in mapa:
            return mapa.get(src)
        if isinstance(src, bytes):
            from docx.image.image import Image
            img = Image.from_blob(src)
            href = f"images/img{len(mapa):02d}.{img.ext}"
            ebook.add_item(epub.EpubImage(uid=f"img{len(mapa):02d}",
                file_name=href, media_type=img.content_type, content=src))
            mapa[src] = href
            return href
        if re.match(r"^[a-z]+://", src):     # URL externa: mantém como está
            mapa[src] = src
            return src
        if not os.path.isfile(src):
            mapa[src] = None
            return None
        href = f"images/img{len(mapa):02d}_{os.path.basename(src)}"
        with open(src, "rb") as f:
            dados = f.read()
        ebook.add_item(epub.EpubImage(
            uid=f"img{len(mapa):02d}", file_name=href,
            media_type=_mime_imagem(src), content=dados))
        mapa[src] = href
        return href

    for b in list(livro.blocos) + list(livro.homenagens) + list(livro.prefacio):
        if b.tipo == "image":
            add(b.texto)
        else:
            textos = [b.texto] if isinstance(b.texto, str) else []
            if b.tipo == "list":
                textos.extend(b.itens)
            elif b.tipo == "table":
                textos.extend(cel for linha in b.itens for cel in linha)
            for tok in (tok for texto in textos for tok in tokenizar_inline(texto)):
                if tok[0] == "image":
                    add(_resolver_caminho(b.base_dir or livro.base_dir, tok[1]))
    return mapa


def _blocos_para_html(blocos, mapa, base_dir):
    """Renderiza uma lista de blocos (dentro de um capítulo) para HTML."""
    corpo = []
    for b in blocos:
        origem = b.base_dir or base_dir
        if b.tipo == "h2":
            corpo.append(f"<h2>{_md_inline_para_html(b.texto, mapa, origem)}</h2>")
        elif b.tipo == "h3":
            corpo.append(f"<h3>{_md_inline_para_html(b.texto, mapa, origem)}</h3>")
        elif b.tipo == "code":
            corpo.append(f"<pre><code>{html.escape(b.texto)}</code></pre>")
        elif b.tipo == "quote":
            corpo.append(f"<blockquote>"
                         f"{_md_inline_para_html(b.texto, mapa, origem)}</blockquote>")
        elif b.tipo == "hr":
            corpo.append('<p class="cena">* * *</p>')
        elif b.tipo == "image":
            href = mapa.get(b.texto)
            if href:
                leg = f"<figcaption>{html.escape(b.extra)}</figcaption>" if b.extra else ""
                corpo.append(f'<figure><img src="{html.escape(href, quote=True)}" '
                             f'alt="{html.escape(b.extra, quote=True)}"/>{leg}</figure>')
            else:
                corpo.append(f"<p>[imagem não encontrada: "
                             f"{html.escape(b.extra or b.texto)}]</p>")
        elif b.tipo == "table":
            linhas_html = []
            for r_idx, linha in enumerate(b.itens):
                tag = "th" if r_idx == 0 else "td"
                cels = "".join(
                    f"<{tag}>{_md_inline_para_html(c, mapa, origem)}</{tag}>"
                    for c in linha)
                linhas_html.append(f"<tr>{cels}</tr>")
            corpo.append(f"<table>{''.join(linhas_html)}</table>")
        elif b.tipo == "list":
            tag = "ol" if b.ordenada else "ul"
            lis = "".join(f"<li>{_md_inline_para_html(i, mapa, origem)}</li>"
                          for i in b.itens)
            corpo.append(f"<{tag}>{lis}</{tag}>")
        else:
            corpo.append(f"<p>{_md_inline_para_html(b.texto, mapa, origem)}</p>")
    return "".join(corpo)


def exportar_epub(livro: Livro, preset: PresetGenero, saida: str):
    from ebooklib import epub

    tipografia = resolver_corpo(preset)
    ebook = epub.EpubBook()
    ebook.set_identifier("urn:uuid:" + str(uuid.uuid4()))   # id único e estável
    ebook.set_title(livro.titulo)
    ebook.set_language("pt-BR")
    ebook.add_author(livro.autor)

    # ---- CSS a partir do preset (mesma identidade do DOCX) --------------
    corpo_stack = _pilha_fontes([preset.fonte_corpo] + preset.fontes_alternativas)
    tit_stack = _pilha_fontes([preset.fonte_titulos])
    caixa = ("text-transform: uppercase; "
             f"letter-spacing: {preset.espacamento_titulo}px;"
             if preset.capitulo_caixa_alta else "")
    css = epub.EpubItem(
        uid="style", file_name="style/main.css", media_type="text/css",
        content=f"""
        body {{ font-family: {corpo_stack}; line-height: {tipografia.entrelinha};
               margin: 0 5%; }}
        h1, h2, h3 {{ font-family: {tit_stack}; color: #{preset.cor_titulos}; }}
        h1 {{ text-align: center; page-break-before: always;
              margin: 2em 0 1.5em; {caixa} }}
        h2 {{ margin-top: 1.5em; }}
        p  {{ text-indent: {tipografia.recuo}cm;
              margin: {tipografia.antes}pt 0 {tipografia.depois}pt;
              text-align: {'justify' if preset.justificado else 'left'}; }}
        h1 + p, h2 + p, h3 + p, blockquote + p, .cena + p {{ text-indent: 0; }}
        .cena {{ text-align: center; text-indent: 0; margin: 1.5em 0;
                 letter-spacing: .4em; }}
        pre {{ background: #f2f2f2; padding: .6em; font-size: .85em;
               overflow-x: auto; white-space: pre-wrap; }}
        code {{ font-family: "{preset.fonte_codigo}", monospace; }}
        blockquote {{ font-style: italic; margin: 1em 2em; }}
        figure {{ text-align: center; margin: 1.5em 0; }}
        figure img {{ max-width: 100%; }}
        figcaption {{ font-style: italic; font-size: .9em; margin-top: .4em; }}
        table {{ border-collapse: collapse; margin: 1em auto; }}
        th, td {{ border: 1px solid #999; padding: .3em .6em; text-align: left; }}
        th {{ background: #f2f2f2; }}
        .rosto {{ text-align: center; margin-top: 30%; }}
        .rosto .titulo {{ font-size: 2em; font-weight: bold;
                          font-family: {tit_stack}; color: #{preset.cor_titulos}; }}
        .rosto .subtitulo {{ font-style: italic; font-size: 1.2em; margin-top: .5em; }}
        .rosto .autor {{ margin-top: 3em; font-size: 1.1em; }}
        .dedicatoria {{ text-align: center; font-style: italic; margin-top: 20%; }}
        .dedicatoria p {{ text-indent: 0; }}
        .dedicatoria .ded-titulo {{ font-weight: bold; font-style: normal;
                                    font-family: {tit_stack}; color: #{preset.cor_titulos};
                                    margin-bottom: 1.5em; }}
        .creditos {{ font-size: .8em; color: #595959; text-align: center;
                     margin-top: 40%; }}
        """.encode())
    ebook.add_item(css)

    # ---- Registra imagens referenciadas --------------------------------
    mapa_img = _registrar_imagens(ebook, livro)

    # ---- Capa real (metadado cover) OU página de rosto em texto ---------
    tem_capa = bool(livro.capa and os.path.isfile(livro.capa))
    rosto = None
    if tem_capa:
        ext = os.path.splitext(livro.capa)[1].lower()
        with open(livro.capa, "rb") as f:
            # set_cover cria a imagem de capa + a página de capa + o metadado
            ebook.set_cover("cover" + ext, f.read())
    else:
        sub = (f'<p class="subtitulo">{html.escape(livro.subtitulo)}</p>'
               if livro.subtitulo else "")
        rosto = epub.EpubHtml(title=livro.titulo, file_name="rosto.xhtml", lang="pt-BR")
        rosto.content = (
            f'<div class="rosto"><p class="titulo">{html.escape(livro.titulo)}</p>'
            f'{sub}<p class="autor">{html.escape(livro.autor)}</p></div>')
        rosto.add_item(css)
        ebook.add_item(rosto)

    # ---- Página de créditos --------------------------------------------
    creditos = epub.EpubHtml(title="Créditos", file_name="creditos.xhtml",
                             lang="pt-BR")
    creditos.content = (
        '<div class="creditos">'
        f"<p>© {html.escape(livro.ano or '')} {html.escape(livro.autor)}</p>"
        "<p>Todos os direitos reservados.</p>"
        "<p>Nenhuma parte desta obra pode ser reproduzida sem autorização "
        "prévia do autor.</p></div>")
    creditos.add_item(css)
    ebook.add_item(creditos)

    # ---- Homenagens / dedicatória --------------------------------------
    homenagens_item = None
    if livro.homenagens:
        tit_h = (f'<p class="ded-titulo">{html.escape(livro.homenagens_titulo)}</p>'
                 if livro.homenagens_titulo else "")
        corpo_h = _blocos_para_html(livro.homenagens, mapa_img, livro.base_dir)
        homenagens_item = epub.EpubHtml(
            title=livro.homenagens_titulo or "Dedicatória",
            file_name="homenagens.xhtml", lang="pt-BR")
        homenagens_item.content = f'<div class="dedicatoria">{tit_h}{corpo_h}</div>'
        homenagens_item.add_item(css)
        ebook.add_item(homenagens_item)

    # ---- Prefácio ------------------------------------------------------
    prefacio_item = None
    if livro.prefacio:
        corpo_p = (f"<h1>{html.escape(livro.prefacio_titulo or 'Prefácio')}</h1>"
                   + _blocos_para_html(livro.prefacio, mapa_img, livro.base_dir))
        prefacio_item = epub.EpubHtml(
            title=livro.prefacio_titulo or "Prefácio",
            file_name="prefacio.xhtml", lang="pt-BR")
        prefacio_item.content = corpo_p
        prefacio_item.add_item(css)
        ebook.add_item(prefacio_item)

    # ---- Divide blocos em capítulos ------------------------------------
    capitulos, atual, titulo_atual = [], [], livro.titulo
    origem_titulo = livro.base_dir
    for b in livro.blocos:
        if b.tipo == "h1":
            if atual:
                capitulos.append((titulo_atual, atual, origem_titulo))
            titulo_atual, atual = b.texto, []
            origem_titulo = b.base_dir or livro.base_dir
        else:
            atual.append(b)
    if atual:
        capitulos.append((titulo_atual, atual, origem_titulo))

    itens = []
    for idx, (titulo, blocos, origem_titulo) in enumerate(capitulos, 1):
        corpo = (f"<h1>{_md_inline_para_html(titulo, mapa_img, origem_titulo)}</h1>"
                 + _blocos_para_html(blocos, mapa_img, livro.base_dir))
        cap = epub.EpubHtml(title=titulo, file_name=f"cap{idx:02d}.xhtml",
                            lang="pt-BR")
        cap.content = corpo
        cap.add_item(css)
        ebook.add_item(cap)
        itens.append(cap)

    # Sumário (nav) lista prefácio + capítulos; dedicatória fica fora, como no DOCX
    ebook.toc = ([prefacio_item] if prefacio_item else []) + itens
    # Ordem: capa → créditos → homenagens → sumário(nav) → prefácio → capítulos
    spine = (["cover"] if tem_capa else [rosto]) + [creditos]
    if homenagens_item:
        spine.append(homenagens_item)
    spine.append("nav")
    if prefacio_item:
        spine.append(prefacio_item)
    ebook.spine = spine + itens
    ebook.add_item(epub.EpubNcx())
    ebook.add_item(epub.EpubNav())
    _gravar_atomico(saida, lambda destino: epub.write_epub(destino, ebook))
    return saida

