#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: planejador determinístico (V0.9).

Dado um gênero e uma meta de tamanho, distribui o alvo em capítulos com
orçamento de palavras, e acompanha o progresso (palavras escritas vs meta).
Nenhuma IA aqui — só aritmética e leitura de arquivos.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

# Faixas de palavras por gênero (mín, máx). Base: médias informadas pelo autor.
GENRE_TARGETS = {
    # Ficção (voz de ficção — cena viva)
    "novela":            (20000, 50000),
    "romance_curto":     (50000, 70000),
    "romance_padrao":    (70000, 100000),
    "romance_longo":     (100000, 130000),
    "fantasia":          (90000, 130000),
    "ficcao_historica":  (90000, 130000),
    "contos":            (20000, 60000),
    "suspense":          (70000, 110000),
    "terror":            (60000, 100000),
    "distopia":          (80000, 120000),
    "biografia":         (70000, 120000),   # não-ficção narrativa → voz de ficção
    # Técnico / não-ficção expositiva (voz técnica)
    "tecnico_guia":         (20000, 35000),
    "tecnico_curto":        (35000, 50000),
    "tecnico_padrao":       (50000, 80000),
    "tecnico_aprofundado":  (80000, 110000),
    "tecnico_referencia":   (110000, 150000),
    "autoajuda":            (30000, 60000),
    "academico":            (50000, 120000),
}

FICTION = {"novela", "romance_curto", "romance_padrao", "romance_longo",
           "fantasia", "ficcao_historica", "contos",
           "suspense", "terror", "distopia", "biografia"}

DEFAULT_WPC = {  # palavras por capítulo sugeridas por família
    "ficcao": 3000,
    "tecnico": 4000,
}


def is_fiction(genre: str) -> bool:
    return genre in FICTION


def target_words(genre: str, choice: str = "medio") -> int:
    lo, hi = GENRE_TARGETS[genre]
    if choice == "min":
        return lo
    if choice == "max":
        return hi
    return (lo + hi) // 2


def plan_chapters(genre: str, total_words: int | None = None,
                  words_per_chapter: int | None = None,
                  choice: str = "medio") -> dict:
    if genre not in GENRE_TARGETS:
        raise ValueError(f"Gênero desconhecido: {genre}. "
                         f"Use um de: {', '.join(sorted(GENRE_TARGETS))}")
    total = int(total_words or target_words(genre, choice))
    wpc = int(words_per_chapter or
              (DEFAULT_WPC["ficcao"] if is_fiction(genre) else DEFAULT_WPC["tecnico"]))
    n = max(1, round(total / wpc))
    base = total // n
    chapters = []
    acc = 0
    for i in range(1, n + 1):
        # último capítulo absorve o resto para fechar exatamente na meta
        budget = base if i < n else (total - acc)
        chapters.append({"n": i, "budget_words": budget})
        acc += budget
    return {
        "genre": genre,
        "family": "ficcao" if is_fiction(genre) else "tecnico",
        "target_words": total,
        "range": GENRE_TARGETS[genre],
        "words_per_chapter": wpc,
        "n_chapters": n,
        "chapters": chapters,
    }


def render_plan_md(plan: dict, titulo: str = "") -> str:
    lo, hi = plan["range"]
    lines = [
        f"# PLANO DE CAPÍTULOS — {titulo or plan['genre']}",
        "",
        f"- Gênero: `{plan['genre']}` (família: {plan['family']})",
        f"- Faixa do gênero: {lo:,}–{hi:,} palavras".replace(",", "."),
        f"- Meta adotada: **{plan['target_words']:,} palavras**".replace(",", "."),
        f"- Orçamento por capítulo (alvo): ~{plan['words_per_chapter']:,}".replace(",", "."),
        f"- Nº de capítulos: **{plan['n_chapters']}**",
        "",
        "| Cap. | Orçamento (palavras) | Escritas | Status | Título de trabalho |",
        "|---|---|---|---|---|",
    ]
    for c in plan["chapters"]:
        b = f"{c['budget_words']:,}".replace(",", ".")
        lines.append(f"| {c['n']:02d} | {b} | 0 | ⬜ pendente | — |")
    lines += [
        "",
        "> Atualize 'Escritas' e 'Status' conforme avança. `progresso` calcula o",
        "> total real a partir de `04_CAPITULOS/cap_*.md`.",
    ]
    return "\n".join(lines) + "\n"


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÿ][\wÀ-ÿ'-]*\b", text, flags=re.UNICODE))


def progress(book_dir: Path) -> dict:
    book_dir = Path(book_dir)
    caps_dir = book_dir / "04_CAPITULOS"
    written = 0
    per_cap = []
    if caps_dir.exists():
        for p in sorted(caps_dir.glob("cap_*.md")):
            try:
                w = _count_words(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                w = 0
            per_cap.append({"file": p.name, "words": w})
            written += w
    return {"written_words": written, "chapters_found": len(per_cap), "per_chapter": per_cap}


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Planejador do Escritor 360°.")
    sub = ap.add_subparsers(dest="cmd")
    pp = sub.add_parser("plan", help="gera um plano de capítulos")
    pp.add_argument("--genero", required=True)
    pp.add_argument("--total", type=int, default=None)
    pp.add_argument("--wpc", type=int, default=None)
    pp.add_argument("--escolha", default="medio", choices=["min", "medio", "max"])
    pp.add_argument("--titulo", default="")
    pr = sub.add_parser("progresso", help="mede progresso de um livro")
    pr.add_argument("--dir", required=True)
    pg = sub.add_parser("generos", help="lista gêneros e faixas")
    args = ap.parse_args()

    if args.cmd == "plan":
        plan = plan_chapters(args.genero, args.total, args.wpc, args.escolha)
        print(render_plan_md(plan, args.titulo))
    elif args.cmd == "progresso":
        pr = progress(Path(args.dir))
        print(f"Capítulos: {pr['chapters_found']} | palavras escritas: {pr['written_words']:,}".replace(",", "."))
        for c in pr["per_chapter"]:
            print(f"  - {c['file']}: {c['words']:,}".replace(",", "."))
    elif args.cmd == "generos":
        for g in sorted(GENRE_TARGETS):
            lo, hi = GENRE_TARGETS[g]
            fam = "ficção" if is_fiction(g) else "técnico"
            print(f"{g:22} {fam:8} {lo:>7,}–{hi:<7,}".replace(",", "."))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
