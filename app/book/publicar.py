#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
publicar.py — Etapa PUBLICAR do Escritor de Livros 360° (NÚCLEO IA PORTÁTIL).

Diagrama os capítulos de um livro em .docx (e .epub) profissional usando o
pacote `diagramador` vendorado em app/diagramador. É o capstone do pipeline:

    CRIAR_LIVRO -> OUTLINE -> ESCREVER -> REVISAR -> PUBLICAR

Lê 04_CAPITULOS/cap_*.md na ordem (+ pré-textuais capa/homenagens/prefácio, se
existirem na pasta de capítulos) e grava em 08_PUBLICACAO/<slug>.docx (+ .epub).
O gênero do diagramador é mapeado da família do livro (tecnico/ficcao),
detectada no PLANO_DE_CAPITULOS.md; o título vem do PLANO/LEIA-ME ou de --titulo.

Uso:
    python app/book/publicar.py --dir workspace/livros/<slug>
    python app/book/publicar.py --dir <livro> --genero tecnico --formato 16x23
    python app/book/publicar.py --dir <livro> --sem-epub --autor "Fulano"

Requer python-docx (.docx) e ebooklib (.epub) instalados no runtime portátil.
"""
import argparse
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

# app/ no sys.path para importar o pacote `diagramador`
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from diagramador.config import GENEROS, FORMATOS          # noqa: E402
from diagramador.leitura import carregar_multiplos          # noqa: E402
from diagramador.exportar_docx import diagramar_docx        # noqa: E402
from diagramador.exportar_epub import exportar_epub         # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fences                                               # noqa: E402

# Família do Escritor 360° -> gênero do diagramador / formato de miolo padrão
FAMILIA_PARA_GENERO = {"tecnico": "tecnico", "ficcao": "romance"}
FORMATO_PADRAO = {"tecnico": "16x23", "ficcao": "14x21"}

# Gênero específico do escritor -> preset tipográfico do diagramador.
# (o diagramador tem tipografia própria para vários gêneros; casamos aqui.)
GENERO_ESCRITOR_PARA_DIAGRAMADOR = {
    "novela": "romance", "romance_curto": "romance", "romance_padrao": "romance",
    "romance_longo": "romance", "ficcao_historica": "romance", "contos": "romance",
    "fantasia": "suspense", "suspense": "suspense",
    "terror": "terror", "distopia": "distopia", "biografia": "biografia",
    "tecnico_guia": "tecnico", "tecnico_curto": "tecnico", "tecnico_padrao": "tecnico",
    "tecnico_aprofundado": "tecnico", "tecnico_referencia": "tecnico",
    "autoajuda": "autoajuda", "academico": "academico",
}


def _slug(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "_", s) or "livro"


def _detectar_meta(book_dir: Path):
    """Extrai (familia, genero_escritor, titulo, autor) do PLANO/LEIA-ME/BIBLIA."""
    familia = genero_escritor = titulo = autor = None
    # LEIA-ME primeiro: seu 1º "# " é o título limpo do livro. O PLANO tem o
    # campo "família:" e um cabeçalho poluído ("PLANO DE CAPÍTULOS — ...").
    for rel in ("LEIA-ME.md", "02_ARQUITETURA/PLANO_DE_CAPITULOS.md"):
        f = book_dir / rel
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if titulo is None:
            m = re.search(r"^#\s+(.+)$", t, re.MULTILINE)
            if m:
                titulo = m.group(1).strip()
        if familia is None:
            m = re.search(r"fam[íi]lia:\s*`?(\w+)`?", t)
            if m:
                familia = m.group(1).strip().lower()
        if genero_escritor is None:
            m = re.search(r"[Gg][êe]nero:\s*`?([\w]+)`?", t)
            if m:
                genero_escritor = m.group(1).strip()
    # Autor e título (provisório) vêm da BÍBLIA (01_FUNDACAO/BIBLIA.md)
    biblia = book_dir / "01_FUNDACAO" / "BIBLIA.md"
    if biblia.exists():
        b = biblia.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^Autor:\s*(.+)$", b, re.MULTILINE)
        if m:
            cand = m.group(1).strip()
            if cand and cand not in ("[nome]", "[...]"):
                autor = cand
        if titulo is None:
            m = re.search(r"^T[íi]tulo[^:]*:\s*(.+)$", b, re.MULTILINE)
            if m:
                cand = m.group(1).strip()
                if cand and cand not in ("[...]",):
                    titulo = cand
    return familia, genero_escritor, titulo, autor


def _coletar_fontes(book_dir: Path):
    """Lista ordenada: pré-textuais reconhecidos + cap_*.md (nunca LEIA-ME).
    Pré-textuais (capa/dedicatória/prefácio) são lidos de 08_PUBLICACAO/PRETEXTUAIS/
    (local recomendado) e, por retrocompatibilidade, também de 04_CAPITULOS/."""
    caps = book_dir / "04_CAPITULOS"
    if not caps.is_dir():
        raise FileNotFoundError(f"pasta de capítulos ausente: {caps}")
    padroes = ("capa.*", "cover.*", "00-capa.*",
               "homenagens.md", "homenagem.md", "00-homenagens.md",
               "dedicatoria.md", "dedicatória.md", "agradecimentos.md",
               "prefacio.md", "prefácio.md", "00-prefacio.md", "apresentacao.md")
    pretextuais = []
    for base in (book_dir / "08_PUBLICACAO" / "PRETEXTUAIS", caps):
        if base.is_dir():
            for pat in padroes:
                pretextuais += sorted(str(p) for p in base.glob(pat))
    capitulos = sorted(str(p) for p in caps.glob("cap_*.md"))
    if not capitulos:
        raise FileNotFoundError(f"nenhum cap_*.md em {caps}")
    return pretextuais + capitulos, capitulos


def _sanear_capitulos(fontes, capitulos, tmp: Path, fiction: bool):
    """Troca cada cap_*.md em `fontes` por uma cópia com as cercas ``` saneadas
    (só quando há o que corrigir). Devolve (fontes, n_correcoes)."""
    caps, novas, total = set(capitulos), [], 0
    for f in fontes:
        if f in caps:
            txt = Path(f).read_text(encoding="utf-8", errors="replace")
            limpo, n = fences.sanear(txt, fiction)
            if n:
                destino = tmp / Path(f).name
                destino.write_text(limpo, encoding="utf-8")
                f, total = str(destino), total + n
        novas.append(f)
    return novas, total


def _limpar_comentarios(livro):
    """Remove parágrafos que são só comentários HTML (ex.: <!-- rascunho -->)."""
    antes = len(livro.blocos)
    livro.blocos = [b for b in livro.blocos
                    if not (b.tipo == "p" and b.texto.strip().startswith("<!--"))]
    return antes - len(livro.blocos)


def _tokens(s: str):
    s = re.sub(r"[*_`#]", "", s)
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _titulo_duplicado(paragrafo: str, titulo_h1: str) -> bool:
    """True se o parágrafo é uma linha-título (negrito ou 'Capítulo ...') que
    repete o cabeçalho H1 — artefato do escritor (ex.: **Capítulo 3: ...**)."""
    txt = paragrafo.strip()
    if len(txt) > 140:
        return False
    parece_titulo = ((txt.startswith("**") and txt.endswith("**"))
                     or re.match(r"^\**\s*cap[íi]tulo\b", txt, re.IGNORECASE))
    if not parece_titulo:
        return False
    a, h = _tokens(txt), _tokens(titulo_h1)
    if not a or not h:
        return False
    return len(a & h) / len(a | h) >= 0.6


def _remover_titulos_duplicados(livro):
    """Descarta o 1º parágrafo após cada H1 quando ele duplica o título."""
    novos, prev_h1, n = [], False, 0
    for b in livro.blocos:
        if b.tipo == "h1":
            novos.append(b)
            prev_h1 = True
            continue
        if prev_h1 and b.tipo == "p" and _titulo_duplicado(b.texto, novos[-1].texto):
            n += 1
            prev_h1 = False
            continue
        prev_h1 = False
        novos.append(b)
    livro.blocos = novos
    return n


def publicar(book_dir: Path, genero=None, formato=None, autor=None, titulo=None,
             subtitulo="", ano="", fazer_epub=True, sumario=True,
             capa_no_miolo=True):
    book_dir = Path(book_dir).resolve()
    familia, genero_escritor, titulo_detectado, autor_detectado = _detectar_meta(book_dir)

    # Gênero do diagramador: casa o gênero específico do escritor com o preset
    # tipográfico correspondente; se não houver, cai no mapa por família.
    if not genero:
        genero = (GENERO_ESCRITOR_PARA_DIAGRAMADOR.get((genero_escritor or "").lower())
                  or FAMILIA_PARA_GENERO.get(familia or "", "romance"))
    if genero not in GENEROS:
        raise ValueError(f"gênero do diagramador inválido: {genero} "
                         f"(use um de: {', '.join(GENEROS)})")
    # Formato de miolo
    if not formato:
        formato = FORMATO_PADRAO.get(familia or "", "16x23")
    if formato not in FORMATOS:
        raise ValueError(f"formato inválido: {formato} "
                         f"(use um de: {', '.join(FORMATOS)})")

    fontes, capitulos = _coletar_fontes(book_dir)
    print(f"Livro     : {book_dir.name}")
    print(f"Família    : {familia or '(indefinida)'}  ->  gênero diagramador: {genero}")
    print(f"Formato    : {formato}  ({FORMATOS[formato].nome})")
    print(f"Capítulos  : {len(capitulos)} arquivo(s)")

    # Capítulos com ``` aberto (artefato do modelo) virariam bloco de código até o
    # fim do arquivo. Lê cópias saneadas (mesmo nome) — os originais não mudam.
    with tempfile.TemporaryDirectory(prefix="nucleo_pub_") as tmp:
        fontes, corrigidas = _sanear_capitulos(fontes, capitulos, Path(tmp),
                                               fiction=(familia == "ficcao"))
        if corrigidas:
            print(f"           (corrigida(s) {corrigidas} cerca(s) ``` solta(s) nos capítulos)")
        livro = carregar_multiplos(fontes)

    # A leitura consome o 1º H1 do 1º capítulo como "título do livro" e, como o
    # corpo do cap 1 fica sem H1, dá a ele um cabeçalho derivado do nome do
    # arquivo (ex.: "Cap 01"). Renomeia esse 1º H1 de volta para o título real
    # consumido — em vez de reinserir (que criaria um capítulo duplicado).
    cabecalho_cap1 = livro.titulo
    if cabecalho_cap1 and cabecalho_cap1 != "Sem título":
        for b in livro.blocos:
            if b.tipo == "h1":
                b.texto = cabecalho_cap1
                break

    titulo_final = titulo or titulo_detectado or book_dir.name
    livro.titulo = titulo_final
    if subtitulo:
        livro.subtitulo = subtitulo
    # Autor: --autor > BÍBLIA > o que a leitura trouxer. Ano: --ano > ano atual.
    autor_final = autor or autor_detectado
    if autor_final:
        livro.autor = autor_final
    from datetime import datetime as _dt
    livro.ano = ano or livro.ano or str(_dt.now().year)

    removidos = _limpar_comentarios(livro)
    if removidos:
        print(f"           (removidos {removidos} comentário(s) HTML do rascunho)")
    dup = _remover_titulos_duplicados(livro)
    if dup:
        print(f"           (removida(s) {dup} linha(s) de título duplicado)")

    n_caps = sum(1 for b in livro.blocos if b.tipo == "h1")
    preset = GENEROS[genero]
    fmt = FORMATOS[formato]
    print(f"Título     : {livro.titulo}")
    print(f"Autor      : {livro.autor}")
    print(f"Fonte/corpo: {preset.fonte_corpo} {preset.tam_corpo}pt · capítulos: {n_caps}")

    pub = book_dir / "08_PUBLICACAO"
    pub.mkdir(parents=True, exist_ok=True)
    slug = _slug(titulo_final)
    saida_docx = pub / f"{slug}.docx"
    diagramar_docx(livro, preset, fmt, str(saida_docx),
                   incluir_sumario=sumario, capa_no_miolo=capa_no_miolo)
    print(f"OK DOCX    : {saida_docx}")

    saida_epub = None
    if fazer_epub:
        saida_epub = pub / f"{slug}.epub"
        exportar_epub(livro, preset, str(saida_epub))
        print(f"OK EPUB    : {saida_epub}")
    return saida_docx, saida_epub


def _cli():
    ap = argparse.ArgumentParser(description="PUBLICAR — diagrama o livro em .docx/.epub.")
    ap.add_argument("--dir", required=True, help="pasta do livro (workspace/livros/<slug>)")
    ap.add_argument("--genero", choices=list(GENEROS), help="gênero do diagramador (senão, mapeado da família)")
    ap.add_argument("--formato", choices=list(FORMATOS), help="formato de miolo (senão, padrão da família)")
    ap.add_argument("--titulo", help="título do livro (senão, detectado do PLANO/LEIA-ME)")
    ap.add_argument("--subtitulo", default="")
    ap.add_argument("--autor", help="nome do autor")
    ap.add_argument("--ano", default="")
    ap.add_argument("--sem-epub", action="store_true", help="não gera o .epub")
    ap.add_argument("--sem-sumario", action="store_true")
    ap.add_argument("--sem-capa-no-miolo", action="store_true")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        print(f"Livro não encontrado: {d}")
        return 2
    try:
        publicar(d, genero=args.genero, formato=args.formato, autor=args.autor,
                 titulo=args.titulo, subtitulo=args.subtitulo, ano=args.ano,
                 fazer_epub=not args.sem_epub, sumario=not args.sem_sumario,
                 capa_no_miolo=not args.sem_capa_no_miolo)
        return 0
    except Exception as exc:
        print(f"Falha: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
