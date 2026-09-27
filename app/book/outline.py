#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: geração de OUTLINE via LLM (V0.9 fatia 2).

Monta um prompt COMPACTO (cabível em 4096 de contexto) a partir da bíblia
(01_FUNDACAO) + gênero + plano (02_ARQUITETURA), com um brief destilado do
gênero e as regras curtas de humanização, e pede ao motor do NÚCLEO um outline
estruturado. Grava em 02_ARQUITETURA/OUTLINE_GERADO.md.

A persona completa (config/personas) NÃO entra no prompt (não cabe em 4096);
ela orienta o autor e a revisão. Aqui usamos um brief.

Uso:
  python app/book/outline.py gerar --dir workspace/livros/<slug> [--modo auto|fast|quality]
  python app/book/outline.py prompt --dir workspace/livros/<slug>   # só escreve o prompt
  python app/book/outline.py aplicar --dir workspace/livros/<slug>  # leva títulos ao PLANO
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

APP_BOOK = Path(__file__).resolve().parent          # app/book
APP_DIR = APP_BOOK.parent                            # app
ROOT = APP_DIR.parent                                # raiz
sys.path.insert(0, str(APP_BOOK))
sys.path.insert(0, str(APP_DIR))
import planner  # noqa: E402

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

MAX_BIBLE_CHARS = 2600

HUMANIZ_BRIEF = (
    "Evite marcas de escrita-IA: negar-e-reafirmar (\"Não é X, é Y\"), frases de "
    "enchimento (\"é importante destacar\", \"no mundo atual\"), conclusões clichê "
    "(\"em resumo\", \"portanto\"), excesso de listas, exemplos genéricos e ritmo "
    "uniforme. Seja concreto, tome posição, varie o ritmo."
)

BRIEF_FICCAO = (
    "Você é um editor de desenvolvimento de ficção. Gênero é contrato: cumpra a "
    "promessa do subgênero. Estrutura antes de prosa. Todo capítulo precisa de "
    "conflito e mudança; entrar tarde, sair cedo."
)

BRIEF_TECNICO = (
    "Você é um editor de desenvolvimento de livro técnico. O leitor precisa SABER "
    "FAZER algo. Intuição antes da fórmula. Conteúdo técnico é um grafo de "
    "pré-requisitos: nenhum conceito antes do que ele exige. Cada seção tem um "
    "único tipo (tutorial/explicação/receita/referência)."
)

FORMAT_FICCAO = """\
Responda SOMENTE em Markdown, em português do Brasil, NESTE formato e nada mais:

## PREMISSA
<uma frase>

## ESTRUTURA
- Começo: <1 linha>
- Virada central: <1 linha>
- Clímax: <1 linha>

## ARCO DO PROTAGONISTA
<1 linha: desejo x necessidade, o que muda>

## CAPÍTULOS ({n} capítulos)
1. <título de trabalho> — <o que acontece, 1 linha, concreto>
(continue até {n}; UMA linha por capítulo)
"""

FORMAT_TECNICO = """\
Responda SOMENTE em Markdown, em português do Brasil, NESTE formato e nada mais:

## OBJETIVO
<o que o leitor saberá FAZER ao final, 1 frase>

## PRÉ-REQUISITOS
<1 linha>

## SUMÁRIO ({n} capítulos)
1. <título> — <objetivo do capítulo em 1 linha> [tipo: tutorial|explicação|receita|referência]
(continue até {n}; UMA linha por capítulo)

## MAPA DE DEPENDÊNCIAS
<liste 4–8 relações no formato: conceito_A -> conceito_B>
"""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _detect_genre(book_dir: Path) -> str:
    biblia = _read(book_dir / "01_FUNDACAO" / "BIBLIA.md")
    m = re.search(r"(?im)^\s*G[êe]nero\s*:\s*([a-z0-9_]+)", biblia)
    if m and m.group(1).strip() in planner.GENRE_TARGETS:
        return m.group(1).strip()
    # fallback: procurar no PLANO
    plano = _read(book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md")
    m = re.search(r"`([a-z0-9_]+)`", plano)
    if m and m.group(1) in planner.GENRE_TARGETS:
        return m.group(1)
    raise ValueError("Não consegui detectar o gênero na bíblia/plano. "
                     "Preencha 'Gênero: <chave>' em 01_FUNDACAO/BIBLIA.md.")


def _plan_summary(book_dir: Path, genre: str) -> dict:
    plano = _read(book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md")
    n = None
    m = re.search(r"N[úu]mero de cap[íi]tulos:\s*\*\*(\d+)\*\*", plano)
    if m:
        n = int(m.group(1))
    tw = None
    m = re.search(r"Meta adotada:\s*\*\*([\d.]+)", plano)
    if m:
        tw = int(m.group(1).replace(".", ""))
    if not n:
        p = planner.plan_chapters(genre)
        n, tw = p["n_chapters"], p["target_words"]
    return {"n_chapters": n, "target_words": tw}


def build_user_message(book_dir: Path) -> str:
    book_dir = Path(book_dir)
    genre = _detect_genre(book_dir)
    fiction = planner.is_fiction(genre)
    biblia = _read(book_dir / "01_FUNDACAO" / "BIBLIA.md").strip()
    if len(biblia) > MAX_BIBLE_CHARS:
        biblia = biblia[:MAX_BIBLE_CHARS] + "\n[...bíblia truncada para caber no contexto...]"
    ps = _plan_summary(book_dir, genre)
    n = ps["n_chapters"]
    brief = BRIEF_FICCAO if fiction else BRIEF_TECNICO
    fmt = (FORMAT_FICCAO if fiction else FORMAT_TECNICO).format(n=n)
    partes = [
        brief,
        HUMANIZ_BRIEF,
        f"Gênero: {genre} | meta ~{ps['target_words']} palavras | {n} capítulos.",
        "BÍBLIA DA OBRA (fonte da verdade; não invente fatos que a contradigam):",
        biblia or "[bíblia ainda vazia — proponha um outline plausível e marque suposições]",
        f"TAREFA: proponha o outline com EXATAMENTE {n} capítulos.",
        fmt,
    ]
    return "\n\n".join(partes)


def _header_message(book_dir: Path) -> str:
    """Prompt curto só para PREMISSA/ESTRUTURA/ARCO (ficção) ou OBJETIVO/
    PRÉ-REQUISITOS (técnico). Sem capítulos — evita loop do modelo pequeno."""
    genre = _detect_genre(book_dir)
    fiction = planner.is_fiction(genre)
    biblia = _read(book_dir / "01_FUNDACAO" / "BIBLIA.md").strip()
    if len(biblia) > MAX_BIBLE_CHARS:
        biblia = biblia[:MAX_BIBLE_CHARS] + "\n[...truncada...]"
    brief = BRIEF_FICCAO if fiction else BRIEF_TECNICO
    if fiction:
        fmt = ("Responda SOMENTE em Markdown, PT-BR, neste formato:\n"
               "## PREMISSA\n<1 frase>\n\n## ESTRUTURA\n- Começo: <1 linha>\n"
               "- Virada central: <1 linha>\n- Clímax: <1 linha>\n\n"
               "## ARCO DO PROTAGONISTA\n<1 linha>")
    else:
        fmt = ("Responda SOMENTE em Markdown, PT-BR, neste formato:\n"
               "## OBJETIVO\n<o que o leitor saberá FAZER, 1 frase>\n\n"
               "## PRÉ-REQUISITOS\n<1 linha>")
    return "\n\n".join([
        brief, HUMANIZ_BRIEF,
        "BÍBLIA (fonte da verdade; não contradiga):", biblia or "[vazia — proponha algo plausível]",
        "TAREFA: gere APENAS as seções pedidas. NÃO liste capítulos agora.", fmt,
    ])


def _ritmo_por_ato(i: int, j: int, n: int, fiction: bool) -> str:
    """Instrução de pacing conforme a posição do lote no livro inteiro —
    evita que um lote 'feche' a história antes do fim."""
    frac = j / max(1, n)
    if fiction:
        if frac <= 0.30:
            fase = ("ATO 1 (MONTAGEM): apresente protagonista, mundo e o conflito; "
                    "plante mistérios. NÃO revele a grande virada nem resolva nada central.")
        elif frac <= 0.70:
            fase = ("ATO 2 (DESENVOLVIMENTO): complicações crescentes, reviravoltas e "
                    "custos; aprofunde relações. O CLÍMAX AINDA NÃO ACONTECEU.")
        elif frac < 0.90:
            fase = ("FIM DO ATO 2 / PRÉ-CLÍMAX: aperto máximo, 'tudo está perdido'. "
                    "Ainda NÃO resolva — prepare o confronto final.")
        else:
            fase = ("ATO 3 (CLÍMAX E RESOLUÇÃO): o confronto decisivo e o desfecho "
                    "acontecem AQUI, nos últimos capítulos.")
    else:
        if frac <= 0.30:
            fase = "PARTE INICIAL: fundamentos e pré-requisitos; do básico ao intermediário."
        elif frac <= 0.75:
            fase = "PARTE CENTRAL: aprofundamento e aplicação; um conceito por vez, sobre os anteriores."
        else:
            fase = "PARTE FINAL: tópicos avançados, integração e projeto/síntese."
    return fase


def _batch_message(book_dir: Path, header_text: str, i: int, j: int, n: int,
                   done_titles: list[str]) -> str:
    genre = _detect_genre(book_dir)
    fiction = planner.is_fiction(genre)
    ja = "; ".join(done_titles[-30:]) if done_titles else "(nenhum ainda)"
    tipo = ("cada linha: 'N. Título — o que ACONTECE (evento concreto que avança a trama)'"
            if fiction else
            "cada linha: 'N. Título — objetivo do capítulo [tipo: tutorial|explicação|receita|referência]'")
    fase = _ritmo_por_ato(i, j, n, fiction)
    return "\n\n".join([
        (BRIEF_FICCAO if fiction else BRIEF_TECNICO), HUMANIZ_BRIEF,
        "CONTEXTO (não repita, apenas continue):", header_text.strip()[:1200],
        f"POSIÇÃO NO LIVRO: livro de {n} capítulos; você gera os capítulos {i}–{j}. "
        f"{fase} NÃO conclua a história antes do capítulo {n}.",
        f"CAPÍTULOS JÁ DEFINIDOS (NÃO repita título nem evento): {ja}",
        f"TAREFA: gere SOMENTE os capítulos {i} a {j} (inclusive), um por linha, "
        f"numerados de {i} a {j}. {tipo}. Cada capítulo deve AVANÇAR a história com "
        "algo NOVO — proibido repetir eventos anteriores. Escreva só as linhas dos "
        "capítulos, sem o prefixo 'Capítulo'.",
    ])


def _run_engine(eng, msg: str, max_tokens: int):
    partes, truncated = [], False
    for ev in eng.stream_chat([{"role": "user", "content": msg}], max_tokens=max_tokens):
        if ev.get("type") == "delta":
            partes.append(ev.get("text", ""))
        elif ev.get("type") == "done":
            truncated = bool(ev.get("truncated"))
    return "".join(partes).strip(), truncated


def _parse_chapter_lines(text: str):
    out = []
    for m in re.finditer(r"(?m)^\s*\d+\.\s+(.+?)\s*$", text):
        line = m.group(1).strip()
        # remove prefixo redundante "Capítulo N —/:/-" que alguns lotes emitem
        line = re.sub(r"(?i)^cap[íi]tulo\s*\d+\s*[—:\-]\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def _norm_title(line: str) -> str:
    t = re.split(r"\s+[—-]\s+", line, maxsplit=1)[0].strip().lower()
    return re.sub(r"[^\wà-ÿ ]", "", t)


def gerar(book_dir: Path, modo: str = "advanced", lote: int = 8,
          max_tokens: int = 1200) -> Path:
    """Gera o outline em LOTES: cabeçalho + capítulos em blocos de `lote`,
    passando os títulos já usados para evitar repetição (fix do loop do 4B).
    Renumera no cliente (1..N contíguos) e marca possíveis repetições."""
    book_dir = Path(book_dir)
    genre = _detect_genre(book_dir)
    ps = _plan_summary(book_dir, genre)
    n = int(ps["n_chapters"])

    sys.path.insert(0, str(APP_DIR))
    import engine_manager  # noqa: E402
    eng = engine_manager.EngineManager()
    if not eng.has_profile():
        raise RuntimeError("Máquina sem perfil calibrado. Calibre o NÚCLEO antes de gerar.")

    header_text = ""
    chapters: list[str] = []       # descrição sem número
    done_titles: list[str] = []
    truncated_any = False
    try:
        eng.start(modo)
        # 1) cabeçalho (premissa/estrutura/arco ou objetivo/pré-req)
        header_text, tr = _run_engine(eng, _header_message(book_dir), max_tokens)
        truncated_any = truncated_any or tr
        # 2) capítulos em lotes
        i = 1
        guard = 0
        while i <= n and guard < n + 8:
            guard += 1
            j = min(n, i + lote - 1)
            txt, tr = _run_engine(eng, _batch_message(book_dir, header_text, i, j, n, done_titles), max_tokens)
            truncated_any = truncated_any or tr
            novos = _parse_chapter_lines(txt)
            if not novos:
                break
            for line in novos:
                if len(chapters) >= n:
                    break
                chapters.append(line)
                done_titles.append(_norm_title(line))
            i = len(chapters) + 1
    finally:
        try:
            eng.stop()
        except Exception:
            pass

    if not header_text and not chapters:
        raise RuntimeError("O motor não retornou conteúdo.")

    # renumeração + marcação de repetições
    seen = set()
    linhas = []
    dups = 0
    for idx, line in enumerate(chapters, 1):
        key = _norm_title(line)
        flag = ""
        if key in seen:
            flag = "  ⚠(possível repetição — revise)"
            dups += 1
        seen.add(key)
        linhas.append(f"{idx}. {line}{flag}")

    avisos = []
    if len(chapters) < n:
        avisos.append(f"gerados {len(chapters)}/{n} capítulos (rode de novo para completar)")
    if dups:
        avisos.append(f"{dups} possível(is) repetição(ões) marcada(s)")
    if truncated_any:
        avisos.append("algum lote truncou por contexto")
    aviso_txt = ("⚠ " + "; ".join(avisos)) if avisos else "gerado em lotes; renumerado."

    out = book_dir / "02_ARQUITETURA" / "OUTLINE_GERADO.md"
    corpo = (f"# OUTLINE GERADO (rascunho — revise!)\n\n> {aviso_txt}\n"
             f"> Modo: {modo} | lote: {lote}. Dica: --modo advanced (30B-A3B) dá a melhor coerência; fast/quality são mais leves.\n\n"
             f"{header_text.strip()}\n\n## CAPÍTULOS ({len(chapters)} de {n})\n"
             + "\n".join(linhas) + "\n")
    out.write_text(corpo, encoding="utf-8")
    return out


def escrever_prompt(book_dir: Path) -> Path:
    book_dir = Path(book_dir)
    msg = build_user_message(book_dir)
    out = book_dir / "02_ARQUITETURA" / "OUTLINE_PROMPT.md"
    out.write_text(
        "# PROMPT DE OUTLINE (cole no chat do NÚCLEO se preferir gerar manualmente)\n\n"
        + msg + "\n", encoding="utf-8")
    return out


def aplicar(book_dir: Path) -> int:
    """Extrai 'N. título — desc' do OUTLINE_GERADO e preenche os títulos de
    trabalho no PLANO_DE_CAPITULOS.md."""
    book_dir = Path(book_dir)
    outline = _read(book_dir / "02_ARQUITETURA" / "OUTLINE_GERADO.md")
    titles = {}
    for m in re.finditer(r"(?m)^\s*(\d+)\.\s+(.+?)(?:\s+[—-]\s+.*)?$", outline):
        num = int(m.group(1))
        title = m.group(2).strip()
        if title and num not in titles:
            titles[num] = title[:80]
    if not titles:
        print("Nenhum capítulo reconhecido em OUTLINE_GERADO.md (rode 'gerar' antes).")
        return 1
    plano_path = book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md"
    plano = _read(plano_path)
    def repl(line):
        m = re.match(r"^\| (\d+) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", line)
        if not m:
            return line
        n = int(m.group(1))
        t = titles.get(n)
        if not t:
            return line
        return f"| {m.group(1)} | {m.group(2)} | {m.group(3)} | {m.group(4)} | {t} |"
    novo = "\n".join(repl(ln) for ln in plano.splitlines())
    plano_path.write_text(novo + ("\n" if not novo.endswith("\n") else ""), encoding="utf-8")
    print(f"Aplicados {len(titles)} títulos de trabalho ao PLANO_DE_CAPITULOS.md.")
    return 0


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Outline via LLM — Escritor 360°.")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("gerar", "prompt", "aplicar"):
        sp = sub.add_parser(name)
        sp.add_argument("--dir", required=True)
        if name == "gerar":
            sp.add_argument("--modo", default="advanced", choices=["auto", "fast", "quality", "advanced"])
            sp.add_argument("--lote", type=int, default=8)
            sp.add_argument("--max-tokens", type=int, default=1200)
    args = ap.parse_args()
    d = Path(args.dir)
    if not d.exists():
        print(f"Livro não encontrado: {d}")
        return 2
    if args.cmd == "gerar":
        try:
            out = gerar(d, args.modo, args.lote, args.max_tokens)
            print(f"Outline gerado: {out}")
            print("Revise e rode 'aplicar' para levar os títulos ao plano.")
        except Exception as exc:
            print(f"Falha ao gerar via motor: {exc}")
            p = escrever_prompt(d)
            print(f"Escrevi o prompt para uso manual no chat do NÚCLEO: {p}")
            return 1
        return 0
    if args.cmd == "prompt":
        print(f"Prompt escrito: {escrever_prompt(d)}")
        return 0
    if args.cmd == "aplicar":
        return aplicar(d)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
