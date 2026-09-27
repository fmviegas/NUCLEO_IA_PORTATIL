"""Limpeza de texto com preservação da sintaxe de Markdown e HTML."""
import os
import re
import tempfile
import unicodedata
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Tabelas de caracteres
# ---------------------------------------------------------------------------

# Caracteres invisiveis / de controle de formatacao que devem sumir do texto.
INVISIVEIS = {
    "\u200B": "ZERO WIDTH SPACE",
    "\u200C": "ZERO WIDTH NON-JOINER",
    "\u200D": "ZERO WIDTH JOINER",
    "\u2060": "WORD JOINER",
    "\uFEFF": "ZERO WIDTH NO-BREAK SPACE / BOM",
    "\u00AD": "SOFT HYPHEN",
    "\u180E": "MONGOLIAN VOWEL SEPARATOR",
    "\u200E": "LEFT-TO-RIGHT MARK",
    "\u200F": "RIGHT-TO-LEFT MARK",
    "\u202A": "LEFT-TO-RIGHT EMBEDDING",
    "\u202B": "RIGHT-TO-LEFT EMBEDDING",
    "\u202C": "POP DIRECTIONAL FORMATTING",
    "\u202D": "LEFT-TO-RIGHT OVERRIDE",
    "\u202E": "RIGHT-TO-LEFT OVERRIDE",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\u2066": "LEFT-TO-RIGHT ISOLATE",
    "\u2067": "RIGHT-TO-LEFT ISOLATE",
    "\u2068": "FIRST STRONG ISOLATE",
    "\u2069": "POP DIRECTIONAL ISOLATE",
}

# Espacos "exoticos" que viram espaco comum (U+0020).
ESPACOS = {
    "\u00A0": "NO-BREAK SPACE",
    "\u2000": "EN QUAD",
    "\u2001": "EM QUAD",
    "\u2002": "EN SPACE",
    "\u2003": "EM SPACE",
    "\u2004": "THREE-PER-EM SPACE",
    "\u2005": "FOUR-PER-EM SPACE",
    "\u2006": "SIX-PER-EM SPACE",
    "\u2007": "FIGURE SPACE",
    "\u2008": "PUNCTUATION SPACE",
    "\u2009": "THIN SPACE",
    "\u200A": "HAIR SPACE",
    "\u202F": "NARROW NO-BREAK SPACE",
    "\u205F": "MEDIUM MATHEMATICAL SPACE",
    "\u3000": "IDEOGRAPHIC SPACE",
}

# Homoglifos (letras cirilicas/gregas identicas a latinas). So aplicado com
# --homoglifos, porque em texto genuinamente multilingue corromperia o conteudo.
HOMOGLIFOS = {
    "\u0430": "a", "\u0435": "e", "\u043E": "o", "\u0440": "p", "\u0441": "c",
    "\u0443": "y", "\u0445": "x", "\u0456": "i", "\u0458": "j",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041A": "K", "\u041C": "M",
    "\u041D": "H", "\u041E": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T",
    "\u0423": "Y", "\u0425": "X", "\u0406": "I",
    "\u03BF": "o", "\u03B1": "a", "\u03B5": "e", "\u0391": "A", "\u0392": "B",
    "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I", "\u039A": "K",
    "\u039C": "M", "\u039D": "N", "\u039F": "O", "\u03A1": "P", "\u03A4": "T",
    "\u03A5": "Y", "\u03A7": "X",
}


# ---------------------------------------------------------------------------
# Limpeza
# ---------------------------------------------------------------------------

def limpar(texto, forma="NFC", manter_nbsp=False, colapsar_espacos=False,
           tratar_homoglifos=False, aparar_linhas=True,
           colapsar_linhas_branco=True, remover_invisiveis=False):
    """Retorna (texto_limpo, relatorio_dict)."""
    rel = {}

    def conta(chave, n):
        if n:
            rel[chave] = rel.get(chave, 0) + n

    # 1. Invisiveis -> removidos
    for ch, nome in INVISIVEIS.items():
        if not remover_invisiveis and ch not in ("\u200b", "\ufeff", "\u00ad"):
            continue
        n = texto.count(ch)
        if n:
            texto = texto.replace(ch, "")
            conta(f"invisivel removido: {nome}", n)

    # 2. Espacos exoticos -> espaco comum (nbsp opcionalmente preservado)
    for ch, nome in ESPACOS.items():
        if ch == "\u00A0" and manter_nbsp:
            continue
        n = texto.count(ch)
        if n:
            texto = texto.replace(ch, " ")
            conta(f"espaco normalizado: {nome}", n)

    # 3. Homoglifos (opcional)
    if tratar_homoglifos:
        for ch, sub in HOMOGLIFOS.items():
            n = texto.count(ch)
            if n:
                texto = texto.replace(ch, sub)
                conta(f"homoglifo corrigido: {ch!r} -> {sub!r}", n)

    # 4. Normalizacao Unicode canonica
    antes = texto
    texto = unicodedata.normalize(forma, texto)
    if texto != antes:
        conta(f"normalizacao Unicode ({forma})", 1)

    # 5. Fim de linha -> LF
    n_crlf = texto.count("\r\n")
    texto = texto.replace("\r\n", "\n")
    n_cr = texto.count("\r")
    texto = texto.replace("\r", "\n")
    conta("fim de linha CRLF -> LF", n_crlf)
    conta("fim de linha CR -> LF", n_cr)

    # 6. Divide em linhas (base para os passos seguintes)
    linhas = texto.split("\n")

    # 6a. Espaco em branco no fim de cada linha (opcional)
    if aparar_linhas:
        n_trailing = sum(1 for l in linhas if l != l.rstrip())
        linhas = [l.rstrip() for l in linhas]
        conta("linhas com espaco final aparado", n_trailing)

    # 7. Espacos internos duplicados -> um (opcional)
    if colapsar_espacos:
        novas = []
        n_col = 0
        for l in linhas:
            while "  " in l:
                l = l.replace("  ", " ")
                n_col += 1
            novas.append(l)
        linhas = novas
        if n_col:
            conta("sequencias de espacos colapsadas", n_col)

    texto = "\n".join(linhas)

    # 8. Colapsa 3+ linhas em branco seguidas em 1 linha em branco (opcional)
    if colapsar_linhas_branco:
        import re
        n_blocos = len(re.findall(r"\n{3,}", texto))
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        conta("blocos de linhas em branco colapsados", n_blocos)

    # Detecta OUTROS caracteres de formatacao (Cf) que nao estao na nossa lista,
    # so pra reportar (nao remove automaticamente).
    outros = {}
    for c in texto:
        if unicodedata.category(c) == "Cf":
            nome = unicodedata.name(c, f"U+{ord(c):04X}")
            outros[nome] = outros.get(nome, 0) + 1
    for nome, n in outros.items():
        conta(f"[ATENCAO] formatacao invisivel ainda presente: {nome}", n)

    return texto, rel


def limpar_formato(texto, extensao, **opts):
    """Limpa prosa sem modificar a sintaxe ou trechos pré-formatados."""
    relatorio = {}

    def trecho(s):
        resultado, rel = limpar(s, **opts)
        for chave, n in rel.items():
            relatorio[chave] = relatorio.get(chave, 0) + n
        return resultado

    if extensao.lower() in {".html", ".htm", ".xhtml"}:
        # O parser localiza apenas nós de texto; o markup original é copiado
        # literalmente, inclusive entidades, atributos e declarações XML.
        linhas = texto.splitlines(keepends=True)
        offsets = [0]
        for linha in linhas:
            offsets.append(offsets[-1] + len(linha))
        edits = []

        class Prosa(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=False)
                self.protegidos = []

            def handle_starttag(self, tag, attrs):
                if tag in {"pre", "code", "script", "style", "textarea", "svg", "math"}:
                    self.protegidos.append(tag)

            def handle_endtag(self, tag):
                if self.protegidos and tag == self.protegidos[-1]:
                    self.protegidos.pop()

            def handle_startendtag(self, tag, attrs):
                pass

            def handle_data(self, data):
                if not self.protegidos:
                    linha, coluna = self.getpos()
                    inicio = offsets[linha - 1] + coluna
                    edits.append((inicio, inicio + len(data), trecho(data)))

        # Espaços nas bordas dos nós separam palavras junto a tags inline.
        opts = dict(opts, aparar_linhas=False, colapsar_linhas_branco=False)
        parser = Prosa()
        parser.feed(texto)
        parser.close()
        for inicio, fim, novo in reversed(edits):
            texto = texto[:inicio] + novo + texto[fim:]
        return texto, relatorio

    if extensao.lower() in {".md", ".markdown"}:
        saida, cerca = [], None
        for linha in texto.splitlines(keepends=True):
            m = re.match(r"^\s*(`{3,}|~{3,})", linha)
            if cerca:
                saida.append(linha)
                if re.match(r"^\s*" + re.escape(cerca[0]) + "{" + str(len(cerca)) + r",}\s*$", linha):
                    cerca = None
                continue
            if m:
                cerca = m.group(1)
                saida.append(linha)
                continue
            if linha.startswith(("    ", "\t")):
                saida.append(linha)
                continue
            # Preserva indentação, hard breaks, código inline e destinos de links.
            opts = dict(opts, aparar_linhas=False, colapsar_linhas_branco=False,
                        colapsar_espacos=False)
            partes = re.split(r"(`+[^`]*`+|!?\[[^\]]*\]\([^)]*\)|<[^>]*>)", linha)
            saida.append("".join(p if i % 2 else trecho(p)
                                 for i, p in enumerate(partes)))
        return "".join(saida), relatorio
    return limpar(texto, **opts)


def gravar_texto_atomico(destino, texto):
    destino = os.path.abspath(destino)
    fd, temp = tempfile.mkstemp(prefix=".limpeza-", dir=os.path.dirname(destino))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        os.replace(temp, destino)
    finally:
        if os.path.exists(temp):
            os.remove(temp)


