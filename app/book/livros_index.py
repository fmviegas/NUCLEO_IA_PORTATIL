#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
livros_index.py — Índice READ-ONLY dos livros do Escritor 360° (para a UI).

Lê workspace/livros/<slug> e devolve, por livro: título, gênero/família,
capítulos escritos, palavras escritas vs meta, e se já há .docx/.epub em
08_PUBLICACAO. Não escreve nada — só lista, para a aba "Escrever Livros".
"""
from __future__ import annotations
import re
from pathlib import Path

_WORD = re.compile(r"\b[\wÀ-ÿ][\wÀ-ÿ'-]*\b", re.UNICODE)


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _count_words(text: str) -> int:
    return len(_WORD.findall(text))


def _meta(book_dir: Path):
    titulo, genero, familia, meta = book_dir.name, "", "", 0
    for rel in ("LEIA-ME.md", "02_ARQUITETURA/PLANO_DE_CAPITULOS.md"):
        t = _read(book_dir / rel)
        if not t:
            continue
        if titulo == book_dir.name:
            m = re.search(r"^#\s+(.+)$", t, re.MULTILINE)
            if m:
                titulo = m.group(1).strip()
        if not genero:
            m = re.search(r"[Gg][êe]nero:\s*`?([\w]+)`?", t)
            if m:
                genero = m.group(1).strip()
        if not familia:
            m = re.search(r"fam[íi]lia:\s*`?(\w+)`?", t)
            if m:
                familia = m.group(1).strip().lower()
        if not meta:
            m = re.search(r"[Mm]eta adotada:\s*\*{0,2}\s*([\d.\s]+)", t)
            if m:
                try:
                    meta = int(re.sub(r"\D", "", m.group(1)))
                except ValueError:
                    meta = 0
    return titulo, genero, familia, meta


def list_books(root: Path) -> list:
    base = Path(root) / "workspace" / "livros"
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        titulo, genero, familia, meta = _meta(d)
        caps = d / "04_CAPITULOS"
        chapters = written = 0
        if caps.is_dir():
            for p in sorted(caps.glob("cap_*.md")):
                chapters += 1
                written += _count_words(_read(p))
        pub = d / "08_PUBLICACAO"
        has_docx = bool(list(pub.glob("*.docx"))) if pub.is_dir() else False
        has_epub = bool(list(pub.glob("*.epub"))) if pub.is_dir() else False
        pct = round(100 * written / meta) if meta else 0
        out.append({
            "slug": d.name,
            "title": titulo,
            "genre": genero,
            "family": familia,
            "chapters_written": chapters,
            "written_words": written,
            "target_words": meta,
            "progress_pct": min(pct, 100),
            "has_docx": has_docx,
            "has_epub": has_epub,
        })
    out.sort(key=lambda b: b["title"].lower())
    return out


# ---- Detalhe e leitura (READ-ONLY, sandboxado) --------------------------

_DOCS = [
    ("biblia", "Bíblia", "01_FUNDACAO/BIBLIA.md"),
    ("outline", "Outline", "02_ARQUITETURA/OUTLINE_GERADO.md"),
    ("plano", "Plano de capítulos", "02_ARQUITETURA/PLANO_DE_CAPITULOS.md"),
    ("manuscrito", "Manuscrito", "08_PUBLICACAO/MANUSCRITO.md"),
    ("blurb", "Blurb", "08_PUBLICACAO/BLURB.md"),
    ("auditoria", "Auditoria", "07_REVISAO/AUDITORIA.md"),
    ("humanizacao", "Passe humanização", "07_REVISAO/PASSE_HUMANIZACAO.md"),
    ("redundancia", "Redundância semântica", "07_REVISAO/REDUNDANCIA_SEMANTICA.md"),
]

_MAX_READ_BYTES = 4 * 1024 * 1024   # 4 MB por arquivo lido


def _book_base(root: Path, slug: str) -> Path:
    return (Path(root) / "workspace" / "livros" / slug).resolve()


def _titulo_cap(texto: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", texto, re.MULTILINE)
    return m.group(1).strip() if m else fallback


_PLAN_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")


def _parse_plan(base: Path, written_map: dict) -> list:
    """Lê 02_ARQUITETURA/PLANO_DE_CAPITULOS.md e devolve TODOS os capítulos
    planejados: nº, título de trabalho e status (escrito/pendente). O status
    real vem de written_map (arquivos cap_*.md existentes) quando disponível,
    senão da coluna Status da tabela."""
    txt = _read(base / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md")
    plan = []
    for ln in txt.splitlines():
        m = _PLAN_ROW.match(ln)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        titulo_tab = m.group(5).strip()
        if titulo_tab in ("", "—", "-"):
            titulo_tab = ""
        status_tab = m.group(4).strip().lower()
        wrote = n in written_map
        plan.append({
            "n": n,
            "title": titulo_tab or (written_map.get(n, {}).get("title") or f"Capítulo {n}"),
            "status": "escrito" if (wrote or "escrito" in status_tab) else "pendente",
            "words": written_map.get(n, {}).get("words", 0),
        })
    return plan


def book_detail(root: Path, slug: str) -> dict | None:
    base = _book_base(root, slug)
    livros = (Path(root) / "workspace" / "livros").resolve()
    # sandbox: precisa estar dentro de workspace/livros e existir
    if livros not in base.parents or not base.is_dir():
        return None
    titulo, genero, familia, meta = _meta(base)
    caps = base / "04_CAPITULOS"
    chapters, written = [], 0
    written_map = {}
    if caps.is_dir():
        for p in sorted(caps.glob("cap_*.md")):
            txt = _read(p)
            w = _count_words(txt)
            written += w
            cap_titulo = _titulo_cap(txt, p.stem)
            chapters.append({
                "n": p.stem.replace("cap_", ""),
                "rel": f"04_CAPITULOS/{p.name}",
                "title": cap_titulo,
                "words": w,
            })
            try:
                written_map[int(p.stem.replace("cap_", ""))] = {"title": cap_titulo, "words": w}
            except ValueError:
                pass
    plan = _parse_plan(base, written_map)
    docs = []
    for key, label, rel in _DOCS:
        docs.append({"key": key, "label": label, "rel": rel,
                     "exists": (base / rel).exists()})
    pct = round(100 * written / meta) if meta else 0
    return {
        "slug": slug, "title": titulo, "genre": genero, "family": familia,
        "target_words": meta, "written_words": written,
        "progress_pct": min(pct, 100), "chapters": chapters,
        "plan": plan, "n_chapters": len(plan), "docs": docs,
    }


def read_book_file(root: Path, slug: str, rel: str) -> dict | None:
    """Lê UM arquivo de texto de dentro do livro. Sandboxado: só .md/.txt,
    só dentro de workspace/livros/<slug>, com teto de tamanho."""
    base = _book_base(root, slug)
    livros = (Path(root) / "workspace" / "livros").resolve()
    if livros not in base.parents:
        return None
    rel = (rel or "").replace("\\", "/").lstrip("/")
    target = (base / rel).resolve()
    # precisa estar DENTRO do diretório do livro (anti path-traversal)
    if base != target and base not in target.parents:
        return None
    if target.suffix.lower() not in (".md", ".txt"):
        return None
    if not target.is_file():
        return None
    try:
        if target.stat().st_size > _MAX_READ_BYTES:
            return {"rel": rel, "truncated": True,
                    "content": target.read_text(encoding="utf-8-sig", errors="replace")[:200000]}
        return {"rel": rel, "truncated": False,
                "content": target.read_text(encoding="utf-8-sig", errors="replace")}
    except Exception:
        return None
