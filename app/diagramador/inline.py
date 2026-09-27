"""Tokenização compartilhada pelas duas saídas."""
import re

_TOKEN_RE = re.compile(
    r"\*\*\*(.+?)\*\*\*"                                   # 1 negrito+itálico
    r"|___(.+?)___"                                        # 2 negrito+itálico
    r"|\*\*(.+?)\*\*"                                      # 3 negrito
    r"|__(.+?)__"                                          # 4 negrito
    r"|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"          # 5 itálico (*)
    r"|(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])"            # 6 itálico (_) sem quebrar snake_case
    r"|`([^`]+?)`"                                         # 7 código
    r"|!\[([^\]]*)\]\(([^)]+)\)"                           # 8 alt, 9 src (imagem)
    r"|\[([^\]]+)\]\(([^)]+)\)"                            # 10 texto, 11 href (link)
)


def tokenizar_inline(texto: str) -> list:
    """Divide o texto em tuplas: (tipo, conteudo[, extra])."""
    tokens, pos = [], 0
    for m in _TOKEN_RE.finditer(texto):
        if m.start() > pos:
            tokens.append(("text", texto[pos:m.start()]))
        if m.group(1) is not None or m.group(2) is not None:
            tokens.append(("bolditalic", m.group(1) or m.group(2)))
        elif m.group(3) is not None or m.group(4) is not None:
            tokens.append(("bold", m.group(3) or m.group(4)))
        elif m.group(5) is not None or m.group(6) is not None:
            tokens.append(("italic", m.group(5) or m.group(6)))
        elif m.group(7) is not None:
            tokens.append(("code", m.group(7)))
        elif m.group(9) is not None:                       # imagem
            tokens.append(("image", m.group(9).strip(), m.group(8)))
        elif m.group(11) is not None:                      # link
            tokens.append(("link", m.group(10), m.group(11).strip()))
        pos = m.end()
    if pos < len(texto):
        tokens.append(("text", texto[pos:]))
    return tokens

