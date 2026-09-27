#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: revisão e compilação (V0.9 fatia 4).

Ferramentas DETERMINÍSTICAS (sem LLM) para o Estágio de Revisão:
  auditar   — consistência: nomes próprios × bíblia, grafias divergentes do
              mesmo nome, expressões de tempo e conflito dia/noite por capítulo.
  humanizar — roda o linter anti-IA em todos os capítulos e consolida o relatório.
  compilar  — monta 08_PUBLICACAO/MANUSCRITO.md (capa + capítulos) + contagem.
  tudo      — roda os três e grava os relatórios em 07_REVISAO.

Uso:
  python app/book/revisar.py auditar  --dir workspace/livros/<slug>
  python app/book/revisar.py humanizar --dir workspace/livros/<slug>
  python app/book/revisar.py compilar --dir workspace/livros/<slug>
  python app/book/revisar.py tudo     --dir workspace/livros/<slug>
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

APP_BOOK = Path(__file__).resolve().parent
APP_DIR = APP_BOOK.parent
sys.path.insert(0, str(APP_BOOK))
sys.path.insert(0, str(APP_DIR))

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

# stopwords/inícios de frase que NÃO são nomes próprios (Title Case por posição)
_STOP = {
    "A", "O", "As", "Os", "E", "Ele", "Ela", "Eles", "Elas", "Eu", "Você", "Nós",
    "Mas", "Porque", "Quando", "Se", "Não", "Sim", "Um", "Uma", "Uns", "Umas",
    "De", "Do", "Da", "Dos", "Das", "Em", "No", "Na", "Nos", "Nas", "Por", "Para",
    "Com", "Sem", "Como", "Que", "Ao", "Aos", "À", "Às", "Depois", "Antes", "Então",
    "Ainda", "Já", "Só", "Talvez", "Havia", "Era", "Foi", "Tinha", "Seu", "Sua",
    "Isso", "Aquilo", "Este", "Esse", "Aquele", "Esta", "Essa", "Aquela", "Tudo",
    "Nada", "Algo", "Alguém", "Ninguém", "Cada", "Todo", "Toda", "Todos", "Todas",
    "Capítulo", "Parte", "Seção", "Vamos", "Ele", "Numa", "Num", "Dela", "Dele",
}
_NAME_TOKEN = r"[A-ZÀ-Ý][a-zà-ÿ]{2,}"
_NAME_RUN = re.compile(rf"\b{_NAME_TOKEN}(?:\s+(?:d[aeo]s?\s+)?{_NAME_TOKEN}){{0,3}}\b")
_WORD = re.compile(r"\b[\wÀ-ÿ][\wÀ-ÿ'-]*\b", re.UNICODE)

DIA = re.compile(r"(?i)\b(manhã|amanhecer|meio-dia|sol a pino|luz do sol|de dia|madrugada clara)\b")
NOITE = re.compile(r"(?i)\b(noite|anoitecer|escureceu|lua|estrelas|breu|meia-noite)\b")
TEMPO_SPAN = re.compile(r"(?i)\bhá\s+(\w+)\s+(anos?|meses|mês|dias?|semanas?|décadas?)\b")


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _chapter_files(book_dir: Path):
    d = book_dir / "04_CAPITULOS"
    return sorted(d.glob("cap_*.md")) if d.exists() else []


def _strip_meta(text: str) -> str:
    # remove título markdown e comentário HTML de rascunho
    text = re.sub(r"(?m)^#.*$", "", text, count=1)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text.strip()


def _name_candidates(text: str) -> Counter:
    c = Counter()
    for m in _NAME_RUN.finditer(text):
        run = m.group(0).strip()
        toks = run.split()
        # descarta se o único token é stopword de início de frase
        core = [t for t in toks if t not in _STOP]
        if not core:
            continue
        c[run] += 1
    return c


def _bible_names(book_dir: Path) -> set:
    b = _read(book_dir / "01_FUNDACAO" / "BIBLIA.md")
    names = set()
    # captura "Protagonista: X", "Personagem: X", e nomes Title Case do texto
    # Só nomes DECLARADOS explicitamente (evita pegar rótulos de campo como
    # "Premissa", "Conflito", que são Title Case por início de linha).
    for m in re.finditer(r"(?im)^(?:protagonista|personagem|antagonista|nome[^:]*|elenco)\s*:\s*(.+)$", b):
        for run in _NAME_RUN.findall(m.group(1)):
            names.add(run.strip())
    # inclui nomes das fichas em 03_CONHECIMENTO/PERSONAGENS
    pdir = book_dir / "03_CONHECIMENTO" / "PERSONAGENS"
    if pdir.exists():
        for f in pdir.glob("*.md"):
            for m in re.finditer(r"(?im)^#\s*PERSONAGEM\s*[—-]\s*(.+)$", _read(f)):
                for run in _NAME_RUN.findall(m.group(1)):
                    names.add(run.strip())
    return {n for n in names if n and n not in _STOP}


def _first_token(name: str) -> str:
    return name.split()[0].lower()


def auditar(book_dir: Path) -> str:
    book_dir = Path(book_dir)
    files = _chapter_files(book_dir)
    bible_names = _bible_names(book_dir)
    bible_first = {_first_token(n) for n in bible_names}

    all_names = Counter()
    per_chapter_time = {}
    daynight = {}
    for f in files:
        txt = _strip_meta(_read(f))
        all_names.update(_name_candidates(txt))
        spans = [f"há {a} {b}" for (a, b) in TEMPO_SPAN.findall(txt)]
        if spans:
            per_chapter_time[f.name] = spans
        dia, noite = bool(DIA.search(txt)), bool(NOITE.search(txt))
        if dia and noite:
            daynight[f.name] = True

    # nomes frequentes (>=3) que parecem personagens
    freq = {n: c for n, c in all_names.items() if c >= 3}

    criticos, tensoes, lacunas = [], [], []

    # 1) grafias divergentes do mesmo nome (mesmo primeiro token, formas diferentes)
    by_first = defaultdict(set)
    for n in freq:
        by_first[_first_token(n)].add(n)
    for ft, formas in by_first.items():
        if len(formas) > 1:
            tensoes.append(f"Grafias divergentes do mesmo nome: {sorted(formas)} "
                           f"(padronize contra a bíblia/GLOSSARIO).")

    # 2) nome de personagem que diverge do protagonista da bíblia
    if bible_first:
        for n, c in sorted(freq.items(), key=lambda x: -x[1])[:8]:
            if _first_token(n) not in bible_first:
                # é um nome recorrente que não bate com nenhum nome da bíblia
                criticos.append(f"'{n}' aparece {c}x nos capítulos, mas não consta na "
                                f"bíblia (nomes da bíblia: {sorted(bible_names)[:6]}). "
                                f"Personagem novo não registrado OU nome do protagonista trocado?")
                break
    else:
        lacunas.append("A bíblia não fixa nomes de personagens — impossível auditar "
                       "consistência de nome. Preencha 'Protagonista: <nome>' em 01_FUNDACAO/BIBLIA.md.")

    # 3) conflito dia/noite no mesmo capítulo
    for fn in daynight:
        tensoes.append(f"{fn}: marcadores de DIA e NOITE no mesmo capítulo — confira a linha do tempo.")

    # 4) expressões de tempo divergentes (mesmo capítulo com spans diferentes)
    for fn, spans in per_chapter_time.items():
        u = sorted(set(s.lower() for s in spans))
        if len(u) > 1:
            tensoes.append(f"{fn}: expressões de tempo divergentes {u} — verifique se se referem ao mesmo fato.")

    linhas = ["# RELATÓRIO DE AUDITORIA DE CONSISTÊNCIA", "",
              f"Capítulos analisados: {len(files)} | nomes recorrentes: {len(freq)}", ""]
    linhas.append("## 🚨 CRÍTICO")
    linhas += [f"- {x}" for x in criticos] or ["- (nenhum)"]
    linhas.append("")
    linhas.append("## 🟡 TENSÃO (verificar)")
    linhas += [f"- {x}" for x in tensoes] or ["- (nenhum)"]
    linhas.append("")
    linhas.append("## 🟢 LACUNA")
    linhas += [f"- {x}" for x in lacunas] or ["- (nenhum)"]
    linhas.append("")
    linhas.append("## Nomes recorrentes detectados (freq.)")
    for n, c in sorted(freq.items(), key=lambda x: -x[1])[:20]:
        marca = "✓ na bíblia" if _first_token(n) in bible_first else "⚠ fora da bíblia"
        linhas.append(f"- {n}: {c}  [{marca}]")
    return "\n".join(linhas) + "\n"


def humanizar_tudo(book_dir: Path) -> str:
    book_dir = Path(book_dir)
    import humanizar as H
    files = _chapter_files(book_dir)
    linhas = ["# PASSE DE HUMANIZAÇÃO (consolidado)", "",
              f"Capítulos: {len(files)}", ""]
    total_flags = 0
    for f in files:
        a = H.analyze_text(_strip_meta(_read(f)))
        flags = a.get("flags") or []
        total_flags += len(flags)
        linhas.append(f"## {f.name} ({a['words']} palavras, ritmo desvio {a['ritmo_stdev']})")
        if flags:
            linhas += [f"- ⚠ {x}" for x in flags]
        else:
            linhas.append("- ✔ sem alertas de densidade")
    if len(files) > 1:
        red = H.cross_redundancy(files)
        linhas += ["", "## Redundância entre capítulos (trechos de 8 palavras)"]
        linhas += ([f"- [{r['entre']}] \"{r['trecho']}\"" for r in red[:12]]
                   or ["- ✔ nenhum trecho longo repetido entre capítulos"])
    linhas += ["", f"TOTAL de alertas: {total_flags}", "",
               "Rode o CHECKLIST DE JULGAMENTO do humanizar.py e ajuste à mão o que fizer sentido."]
    return "\n".join(linhas) + "\n"


def redundancia_semantica(book_dir: Path, limiar: float = 0.5) -> str:
    """Relatório NÃO-destrutivo de redundância semântica (TF-IDF por frase):
    pega a circularidade conceitual (mesma tese reescrita) que o dedup léxico
    não vê. Não apaga nada — cortar é decisão do autor."""
    book_dir = Path(book_dir)
    import similaridade as S
    files = _chapter_files(book_dir)
    res = S.analisar_livro(files, limiar=limiar)

    linhas = ["# REDUNDÂNCIA SEMÂNTICA (TF-IDF por frase)", "",
              f"Capítulos: {len(files)} | limiar de cosseno: {limiar}",
              "",
              "> Cada par abaixo são duas frases que dizem quase a mesma coisa com",
              "> palavras diferentes. NÃO foram apagadas: variações numéricas e",
              "> paralelismos legítimos dão cosseno alto também. Reescreva/una à mão",
              "> as que forem repetição de tese de fato.", ""]

    total = 0
    linhas.append("## Dentro de cada capítulo (circularidade)")
    for f in files:
        info = res["intra"].get(f.name, {"pares": [], "frases": 0})
        pares = info["pares"]
        total += len(pares)
        linhas.append(f"\n### {f.name} — {info['frases']} frases, {len(pares)} par(es) suspeito(s)")
        if not pares:
            linhas.append("- ✔ sem redundância semântica acima do limiar")
            continue
        for p in pares[:15]:
            linhas.append(f"- cos {p['score']}:")
            linhas.append(f"    - “{p['a'][:130]}”")
            linhas.append(f"    - “{p['b'][:130]}”")

    linhas.append("")
    linhas.append("## Entre capítulos (mesma ideia recontada em outro capítulo)")
    if res["cross"]:
        for p in res["cross"][:12]:
            linhas.append(f"- cos {p['score']} [{p['entre']}]:")
            linhas.append(f"    - “{p['a'][:130]}”")
            linhas.append(f"    - “{p['b'][:130]}”")
    else:
        linhas.append("- ✔ nada acima do limiar entre capítulos")

    linhas += ["", f"TOTAL de pares intra-capítulo: {total}", "",
               "Dica: no modo advanced (30B) a circularidade some mais reescrevendo a "
               "tese UMA vez e deixando os exemplos carregarem o resto."]
    return "\n".join(linhas) + "\n"


def compilar(book_dir: Path) -> Path:
    book_dir = Path(book_dir)
    files = _chapter_files(book_dir)
    biblia = _read(book_dir / "01_FUNDACAO" / "BIBLIA.md")
    titulo = ""
    m = re.search(r"(?im)^t[íi]tulo[^:]*:\s*(.+)$", biblia)
    if m:
        titulo = m.group(1).strip()
    autor = ""
    m = re.search(r"(?im)^autor\s*:\s*(.+)$", biblia)
    if m:
        autor = m.group(1).strip()
    total = 0
    partes = [f"# {titulo or book_dir.name}", ""]
    if autor:
        partes.append(f"por {autor}\n")
    partes.append("\n---\n")
    for f in files:
        corpo = _strip_meta(_read(f))
        # recupera o título do capítulo (primeira linha # do arquivo original)
        head = ""
        m = re.match(r"^#\s*(.+)$", _read(f).lstrip())
        if m:
            head = m.group(1).strip()
        total += len(_WORD.findall(corpo))
        partes.append(f"\n## {head or f.stem}\n\n{corpo}\n")
    out = book_dir / "08_PUBLICACAO" / "MANUSCRITO.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    partes.append(f"\n---\n\n<!-- Total: {total} palavras em {len(files)} capítulo(s). -->\n")
    out.write_text("\n".join(partes), encoding="utf-8")
    return out


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Revisão e compilação — Escritor 360°.")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("auditar", "humanizar", "redundancia", "compilar", "tudo"):
        sp = sub.add_parser(name)
        sp.add_argument("--dir", required=True)
        if name in ("redundancia", "tudo"):
            sp.add_argument("--limiar", type=float, default=0.5,
                            help="limiar de cosseno da redundância semântica (0-1)")
    args = ap.parse_args()
    d = Path(args.dir)
    if not d.exists():
        print(f"Livro não encontrado: {d}")
        return 2
    rev = d / "07_REVISAO"
    rev.mkdir(parents=True, exist_ok=True)
    if args.cmd in ("auditar", "tudo"):
        rep = auditar(d)
        (rev / "AUDITORIA.md").write_text(rep, encoding="utf-8")
        print(rep)
        print(f"[gravado em 07_REVISAO/AUDITORIA.md]")
    if args.cmd in ("humanizar", "tudo"):
        rep = humanizar_tudo(d)
        (rev / "PASSE_HUMANIZACAO.md").write_text(rep, encoding="utf-8")
        print(f"[PASSE_HUMANIZACAO.md gravado — {len(_chapter_files(d))} capítulo(s)]")
    if args.cmd in ("redundancia", "tudo"):
        rep = redundancia_semantica(d, limiar=getattr(args, "limiar", 0.5))
        (rev / "REDUNDANCIA_SEMANTICA.md").write_text(rep, encoding="utf-8")
        print(f"[REDUNDANCIA_SEMANTICA.md gravado — limiar {getattr(args, 'limiar', 0.5)}]")
    if args.cmd in ("compilar", "tudo"):
        out = compilar(d)
        print(f"[manuscrito compilado: {out}]")
    if args.cmd not in ("auditar", "humanizar", "redundancia", "compilar", "tudo"):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
