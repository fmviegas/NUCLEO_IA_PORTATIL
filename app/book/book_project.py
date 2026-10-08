#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: scaffolder de projeto de livro (V0.9).

Cria a estrutura de pastas 00–08 (universal, adaptada por gênero), pré-preenche
os templates .md (com as regras de humanização embutidas) e copia a persona do
gênero + o módulo de humanização para 00_GOVERNANCA (livro autocontido).

Offline; não toca no motor. Uso:
  python app/book/book_project.py criar --slug meu-livro --genero romance_padrao \
        --titulo "Título" --autor "Autor"
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent          # app/book
ROOT = APP_DIR.parent.parent                        # raiz do projeto
sys.path.insert(0, str(APP_DIR))
import planner  # noqa: E402

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

PERSONAS_DIR = ROOT / "config" / "personas"
BOOKS_DIR = ROOT / "workspace" / "livros"

FOLDERS = [
    "00_GOVERNANCA", "01_FUNDACAO", "02_ARQUITETURA", "03_CONHECIMENTO",
    "04_CAPITULOS", "05_PROJETO_PRATICO", "06_EXERCICIOS", "07_REVISAO",
    "08_PUBLICACAO",
]

HUMANIZ_BLOCK = """\
REGRAS DE HUMANIZAÇÃO DA PROSA (aplicar na escrita, auditar na revisão)

1. Ritmo assimétrico obrigatório. Alternar períodos longos e fragmentos.
   Nunca três frases seguidas de comprimento parecido.
2. Negar-e-reafirmar ("Não era X. Era Y."): máx. 1 a cada 3.000 palavras.
   Só se o leitor de fato suporia X.
3. Não nomear a emoção depois do gesto. Se o gesto não basta, refazer o gesto.
4. Proibido o tricolon reflexo. Preferir dois ou cinco itens; desbalancear listas.
5. "Como se" / "uma espécie de" / "algo como": teto por capítulo (definir nº).
6. Uma metáfora central por capítulo. Deixá-la levemente imperfeita.
7. Especificidade concreta e idiossincrática > número exato como enfeite.
8. Léxico: concreto e comum vence abstrato e grandioso. Consultar banidos.
9. Narrador/autor com viés/posição. Sem "neutro e de bom gosto".
10. Aberturas de capítulo: nenhuma se repete em molde. Registrar as usadas.
11. Evitar frases de enchimento, conclusões previsíveis e excesso de listas.
12. Cavar fundo em algo por capítulo (evitar profundidade horizontal).
13. Sem redundância entre capítulos (conceito não volta como novo).
"""

CORRECAO_BLOCK = """\
PADRÃO DE CORREÇÃO (norma na narração; diálogo/voz seguem o personagem/autor)
- Norma de referência: Acordo Ortográfico vigente + norma culta PB.
- A correção fina (crase, concordância, regência) é o PASSE DE CÓPIA, no fim —
  não trave a escrita perseguindo vírgula; mas não produza texto desleixado.
- NÃO corrigir o que é voz/aspereza registrada no STYLE_SHEET_ANTITIQUE.
"""


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", str(s), flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", s) or "livro"


def _w(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _estilo_e_voz(fiction: bool, meta=None) -> str:
    meta = meta or {}
    tipo = "narração/POV" if fiction else "registro técnico"
    pov = _campo(meta, "pov", f"[definir — {tipo}]")
    tom = _campo(meta, "tom", "[seco/lírico/caloroso/divulgativo]")
    vies = _campo(meta, "voz_narrador", "[implicância / humor / julgamento recorrente]")
    tique = _campo(meta, "voz_tique", "[uma construção que só esta voz usa]")
    return f"""# ESTILO E VOZ

- Ponto de vista / registro: {pov}
- Tom: {tom}  ·  Idioma da obra: português do Brasil

## FICHA DE VOZ
- Viés do narrador/autor: {vies}
- Tique verbal / palavra-assinatura: {tique}
- Grau de imperfeição-alvo: [seco e áspero / polido / oral e digressivo]

## {HUMANIZ_BLOCK}

## {CORRECAO_BLOCK}
"""


def _style_sheet(meta=None) -> str:
    meta = meta or {}
    banidos = _campo(meta, "banidos",
                     '[ex.: "inabalável", "de alguma forma", "havia algo em", "no mundo atual"]')
    tetos = _campo(meta, "tetos", '"como se": máx. [n] por capítulo · negar-e-reafirmar: máx. [n] no livro')
    return f"""# STYLE SHEET ANTI-TIQUE

BANIDOS (palavras/construções que esta obra não usa):
- {banidos}

TETOS (limites numéricos):
- {tetos}

ABERTURAS JÁ USADAS (para não repetir molde):
- Cap. 1: [tipo de entrada]

PONTAS SOLTAS INTENCIONAIS:
- [o que fica sem resposta e por quê]

ASPEREZAS AUTORAIS (imperfeição que é assinatura, não descuido):
- [ex.: parágrafos que começam com "E"; frases-fragmento em momentos de choque]
"""


def _campo(meta, key, fallback="[...]"):
    """Valor do questionário (meta) ou o placeholder padrão da bíblia."""
    v = (meta or {}).get(key)
    return v.strip() if isinstance(v, str) and v.strip() else fallback


def _biblia(fiction: bool, titulo: str, autor: str, genero: str, meta=None) -> str:
    meta = meta or {}
    # bloco de voz/estilo comum às duas famílias — a IA lê a bíblia, então isto
    # molda a prosa (viés, tique, palavras banidas e tetos de humanização).
    voz = (
        f"Viés / posição do narrador-autor: {_campo(meta, 'voz_narrador')}\n"
        f"Tique verbal / palavra-assinatura: {_campo(meta, 'voz_tique')}\n"
        f"NÃO usar (palavras/construções banidas): {_campo(meta, 'banidos')}\n"
        f"Tetos de humanização (ex.: \"como se\" por capítulo): {_campo(meta, 'tetos')}"
    )
    if fiction:
        campos = (
            f"Gênero e subgênero: {_campo(meta, 'subgenero', genero)}\n"
            f"Promessa central (o que o leitor vai sentir/viver): {_campo(meta, 'promessa')}\n"
            f"Público-alvo: {_campo(meta, 'publico')}\n"
            f"Época / ambientação: {_campo(meta, 'epoca')}\n"
            f"Ponto de vista e tempo verbal: {_campo(meta, 'pov')}\n"
            f"Premissa (uma frase): {_campo(meta, 'premissa')}\n"
            f"Estrutura pretendida (começo→virada→clímax): {_campo(meta, 'estrutura')}\n"
            f"Protagonista (desejo/necessidade): {_campo(meta, 'protagonista')}\n"
            f"Conflito central: {_campo(meta, 'conflito')}\n"
            f"Personagens-chave (nome — desejo/necessidade): {_campo(meta, 'personagens_chave')}\n"
            f"Personagens secundários: {_campo(meta, 'personagens')}\n"
            f"Tema profundo: {_campo(meta, 'tema')}\n"
            f"Tom / voz: {_campo(meta, 'tom')}\n"
            f"{voz}"
        )
    else:
        campos = (
            f"Tipo de livro: {_campo(meta, 'tipo', '[didático / aplicado / receita / referência / divulgação]')}\n"
            f"Área/assunto: {_campo(meta, 'assunto')}\n"
            f"Promessa pedagógica (o que o leitor saberá FAZER ao final): {_campo(meta, 'promessa')}\n"
            f"Público-alvo (o que já sabe / o que NÃO sabe): {_campo(meta, 'publico')}\n"
            f"Nível matemático/técnico: {_campo(meta, 'nivel', '[intuição-primeiro / com cálculo / com demonstrações]')}\n"
            f"Ferramenta dos exemplos: {_campo(meta, 'ferramenta', '[Python / R / planilha / sem código / ...]')}\n"
            f"Estrutura / sumário pretendido (objetivo→tópicos): {_campo(meta, 'estrutura')}\n"
            f"Tese/mensagem central: {_campo(meta, 'tema')}\n"
            f"Tom / voz: {_campo(meta, 'tom')}\n"
            f"{voz}\n"
            f"Fontes do assunto: ver 03_CONHECIMENTO/FONTES/"
        )
    return f"""# BÍBLIA DA OBRA

Autor: {autor or '[nome]'}
Título (provisório): {titulo or '[...]'}
Gênero: {genero}
Estágio atual: concepção

{campos}

> Não preencher tudo no dia zero. O essencial destrava o começo; o resto cresce.
> O que faltar vira item em 00_GOVERNANCA/DECISOES_PENDENTES.md.
"""


def _estrutura(fiction: bool) -> str:
    if fiction:
        corpo = """## Beats / arcos
- Começo (estado inicial): [...]
- Virada central: [...]
- Clímax: [...]
- Arco do protagonista (início → mudança → fim): [...]
- Subtramas: [...]
"""
    else:
        corpo = """## Mapa de dependências de conceitos (o que precede o quê)
```mermaid
graph TD
  A[conceito base] --> B[conceito seguinte]
```
## Sumário (ordenado a partir do grafo; nenhum conceito antes do pré-requisito)
- [...]
"""
    return "# ESTRUTURA\n\n" + corpo


def criar_livro(slug: str, genero: str, titulo: str = "", autor: str = "",
                total: int | None = None, wpc: int | None = None,
                base_dir: Path | None = None, meta: dict | None = None) -> Path:
    meta = meta or {}
    if genero not in planner.GENRE_TARGETS:
        raise ValueError(f"Gênero desconhecido: {genero}. "
                         f"Veja: python app/book/planner.py generos")
    fiction = planner.is_fiction(genero)
    base = Path(base_dir) if base_dir else BOOKS_DIR
    slug = slugify(slug or titulo or genero)
    book = base / slug
    if book.exists():
        raise FileExistsError(f"Já existe: {book}")

    for f in FOLDERS:
        (book / f).mkdir(parents=True, exist_ok=True)

    # 00_GOVERNANCA — persona + humanização + voz + style sheet + decisões
    gov = book / "00_GOVERNANCA"
    persona_src = PERSONAS_DIR / ("ficcao_360.md" if fiction else "tecnico_360.md")
    if persona_src.exists():
        shutil.copyfile(persona_src, gov / "PERSONA.md")
    hum_src = PERSONAS_DIR / "humanizacao.md"
    if hum_src.exists():
        shutil.copyfile(hum_src, gov / "HUMANIZACAO.md")
    _w(gov / "ESTILO_E_VOZ.md", _estilo_e_voz(fiction, meta))
    _w(gov / "STYLE_SHEET_ANTITIQUE.md", _style_sheet(meta))
    _w(gov / "DECISOES_PENDENTES.md",
       "# DECISÕES PENDENTES\n\n- [ ] Preencher a bíblia (01_FUNDACAO)\n"
       "- [ ] Fixar voz e tetos de humanização (00_GOVERNANCA/ESTILO_E_VOZ.md)\n")

    # 01_FUNDACAO
    _w(book / "01_FUNDACAO" / "BIBLIA.md", _biblia(fiction, titulo, autor, genero, meta))

    # 02_ARQUITETURA — estrutura + plano de capítulos
    _est = _estrutura(fiction)
    _semente = _campo(meta, "estrutura", "")
    if _semente and _semente != "[...]":
        _est += f"\n## SEMENTE (do autor, no dia zero)\n{_semente}\n"
    _w(book / "02_ARQUITETURA" / "ESTRUTURA.md", _est)
    # tamanho na faixa do gênero (curto/médio/longo) quando não veio total explícito
    _tam = str((meta or {}).get("tamanho") or "").strip().lower()
    _choice = {"curto": "min", "medio": "medio", "médio": "medio",
               "padrao": "medio", "padrão": "medio", "longo": "max"}.get(_tam, "medio")
    plan = planner.plan_chapters(genero, total, wpc, choice=_choice)
    _w(book / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md",
       planner.render_plan_md(plan, titulo))

    # 03_CONHECIMENTO — difere por gênero
    con = book / "03_CONHECIMENTO"
    _w(con / "GLOSSARIO.md", "# GLOSSÁRIO\n\n- termo: definição\n")
    if fiction:
        (con / "PERSONAGENS").mkdir(exist_ok=True)
        _w(con / "PERSONAGENS" / "_MODELO.md",
           "# PERSONAGEM — [nome]\n\n- Desejo (want): \n- Necessidade (need): \n"
           "- Ferida / mentira que acredita: \n- Falha e qualidade: \n- Voz/tique: \n"
           "- Contradição (quer duas coisas incompatíveis): \n")
        _amb = _campo(meta, "epoca", "[...]")
        _w(con / "AMBIENTACAO.md", f"# AMBIENTAÇÃO / MUNDO\n\nÉpoca / lugar: {_amb}\n\n[detalhar: clima, regras do mundo, atmosfera]\n")
        _w(con / "CRONOLOGIA.md", "# CRONOLOGIA INTERNA\n\n- [quando] — [o quê]\n")
        prot = _campo(meta, "protagonista", "")
        if prot and prot != "[...]":
            _w(con / "PERSONAGENS" / "protagonista.md",
               f"# PERSONAGEM — Protagonista\n\n- Desejo/necessidade: {prot}\n"
               f"- Conflito: {_campo(meta, 'conflito', '')}\n"
               "- Ferida / mentira que acredita: \n- Voz/tique: \n")
        # personagens-chave (1–2+): "Nome — desejo/necessidade", separados por ; ou linha
        chave = (meta or {}).get("personagens_chave") or ""
        if isinstance(chave, str) and chave.strip():
            idx = 0
            for item in re.split(r"[;\n]+", chave):
                item = item.strip()
                if not item or idx >= 6:
                    continue
                idx += 1
                partes_p = re.split(r"\s*[—:–-]\s*", item, maxsplit=1)
                nome = partes_p[0].strip() or f"personagem {idx}"
                desejo = partes_p[1].strip() if len(partes_p) > 1 else ""
                fn = slugify(nome) or f"personagem-{idx}"
                if fn == "protagonista":
                    fn = f"protagonista-{idx}"
                _w(con / "PERSONAGENS" / f"{fn}.md",
                   f"# PERSONAGEM — {nome}\n\n- Desejo/necessidade: {desejo}\n"
                   "- Ferida / mentira que acredita: \n- Falha e qualidade: \n- Voz/tique: \n")
    else:
        (con / "FONTES").mkdir(exist_ok=True)
        _w(con / "FONTES" / "LEIA-ME.md",
           "# FONTES DO ASSUNTO\n\nColoque aqui o(s) arquivo(s) técnico(s) do assunto "
           "(a fonte da verdade). Nenhuma afirmação técnica/nº entra no livro sem lastro aqui.\n")
        (con / "DATASETS").mkdir(exist_ok=True)
        _w(con / "DATASETS" / "LEIA-ME.md", "# DATASETS-FIO\n\nOrigem, licença e descrição de cada conjunto.\n")
        _w(con / "NOTACAO.md", "# NOTAÇÃO\n\nUm símbolo, um significado — do início ao fim.\n")

    # 04_CAPITULOS + RESUMOS
    caps = book / "04_CAPITULOS"
    (caps / "RESUMOS").mkdir(exist_ok=True)
    _w(caps / "LEIA-ME.md",
       "# CAPÍTULOS\n\nUm arquivo por capítulo: `cap_01.md`, `cap_02.md`, ...\n"
       "Para cada capítulo escrito, gerar um resumo de 5–10 linhas em "
       "`RESUMOS/cap_NN.md` (alimenta o contexto do capítulo seguinte).\n")

    # 05 / 06 — universais; conteúdo por gênero
    p5 = book / "05_PROJETO_PRATICO"
    p6 = book / "06_EXERCICIOS"
    if fiction:
        _w(p5 / "LEIA-ME.md", "# PROJETO PRÁTICO (opcional na ficção)\n\n"
           "Use para dossiê, mapas, linha do tempo visual, moodboard.\n")
        _w(p6 / "LEIA-ME.md", "# EXTRAS (opcional na ficção)\n\n"
           "Material bônus, apêndices, contos-satélite.\n")
    else:
        (p5 / "CODIGO").mkdir(exist_ok=True)
        _w(p5 / "CODIGO" / "LEIA-ME.md", "# CÓDIGO (reprodutibilidade)\n\n"
           "Todo número/figura do livro nasce de código versionado aqui.\n")
        _w(p6 / "EXERCICIOS.md", "# EXERCÍCIOS\n\nGraduados por dificuldade; soluções verificadas.\n")

    # 07_REVISAO
    rev = book / "07_REVISAO"
    _w(rev / "REVISAO.md", "# REVISÃO\n\nProblemas e decisões dos passes.\n")
    _w(rev / "PASSE_HUMANIZACAO.md",
       "# PASSE DE HUMANIZAÇÃO\n\nRodar: `python app/book/humanizar.py "
       f"workspace/livros/{slug}/04_CAPITULOS`\nColar aqui o relatório e as decisões.\n")

    # 08_PUBLICACAO
    pub = book / "08_PUBLICACAO"
    _w(pub / "METADADOS.md", "# METADADOS\n\nTítulo, subtítulo, categorias, palavras-chave.\n")
    _w(pub / "BLURB.md", "# BLURB (100–200 palavras)\n\nVende a promessa sem entregar o final.\n")
    # Pré-textuais opcionais: crie os arquivos abaixo AQUI para entrarem no
    # publish (.docx/.epub). Só entram os que você realmente criar.
    _w(pub / "PRETEXTUAIS" / "LEIA-ME.md",
       "# PRÉ-TEXTUAIS (páginas de abertura do livro)\n\n"
       "Crie nesta pasta os arquivos abaixo (nomes exatos) para o PUBLICAR "
       "incluí-los antes dos capítulos. O que não existir é simplesmente omitido.\n\n"
       "- `capa.jpg` (ou .png) — imagem de capa; vira a capa do miolo/epub.\n"
       "- `dedicatoria.md` — dedicatória (página centralizada em itálico). O 1º "
       "`# Título` vira o título da página.\n"
       "- `epigrafe.md` — epígrafe (página própria, depois da dedicatória): a citação em "
       "itálico, recuada à direita no terço inferior da página; numa linha separada, "
       "a autoria começando com travessão. Exemplo:\n\n"
       "      O que a gente não sabe, a gente não sabe.\n\n"
       "      — Guimarães Rosa, *Grande Sertão: Veredas*\n\n"
       "  Mais de uma epígrafe: separe com uma linha `* * *`.\n"
       "- `prefacio.md` — prefácio/apresentação (entra no sumário). 1º `# Título` = título da página.\n\n"
       "A **folha de rosto** (título/subtítulo/autor), a **página de créditos** "
       "(© ano autor) e o **sumário** são gerados automaticamente — autor e ano "
       "saem da BÍBLIA e da data atual.\n")

    # LEIA-ME raiz do livro
    _w(book / "LEIA-ME.md",
       f"# {titulo or slug}\n\nGênero: `{genero}` · Meta: {plan['target_words']} palavras "
       f"em ~{plan['n_chapters']} capítulos.\n\nEstrutura 00–08 do Escritor 360° "
       "(NÚCLEO IA PORTÁTIL). Comece pela bíblia (01) e pela voz (00).\n")

    return book


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Scaffolder do Escritor 360°.")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("criar", help="cria um novo projeto de livro")
    c.add_argument("--slug", default="")
    c.add_argument("--genero", required=True)
    c.add_argument("--titulo", default="")
    c.add_argument("--autor", default="")
    c.add_argument("--total", type=int, default=None)
    c.add_argument("--wpc", type=int, default=None)
    c.add_argument("--dir", default=None, help="base (padrão: workspace/livros)")
    args = ap.parse_args()
    if args.cmd == "criar":
        book = criar_livro(args.slug, args.genero, args.titulo, args.autor,
                           args.total, args.wpc,
                           Path(args.dir) if args.dir else None)
        print(f"Livro criado em: {book}")
        print("Estrutura 00–08 pronta. Persona e humanização copiadas para 00_GOVERNANCA.")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
