#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: escrita CAPÍTULO A CAPÍTULO (V0.9 fatia 3).

Para um capítulo N, monta contexto ENXUTO (cabível em 4096):
  bíblia aparada + ficha do capítulo (do OUTLINE_GERADO) + RESUMO ENCADEADO do
  capítulo anterior + regras curtas de humanização, e gera a prosa EM CENAS
  (várias chamadas de ~900 palavras, cada uma continuando de onde parou), até
  ~90% do orçamento — conduzindo ao fecho. Se ao esgotar `partes` o capítulo
  ainda ficou curto, um PASSO DE EXPANSÃO concede passes extras pedindo material
  NOVO (nova beat/cena na ficção; outro exemplo/caso/armadilha no técnico), com
  trava que para quando o modelo "seca" para não empurrar refrão. Salva
  04_CAPITULOS/cap_NN.md e gera RESUMOS/cap_NN.md (memória). Atualiza o PLANO.

Uso:
  python app/book/escrever.py capitulo --dir <livro> --n 1 [--modo quality] [--partes 4]
  python app/book/escrever.py proximo  --dir <livro>            (primeiro pendente)
  python app/book/escrever.py resumo   --dir <livro> --n 1      (regera o resumo)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_BOOK = Path(__file__).resolve().parent
APP_DIR = APP_BOOK.parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_BOOK))
sys.path.insert(0, str(APP_DIR))
import planner          # noqa: E402
import outline as O     # reusa _read, _detect_genre, briefs, _run_engine  # noqa: E402

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

MAX_BIBLE = 2800        # bíblia traz voz/banidos/estrutura + campos detalhados — cabe em 4096
ALVO_CENA = 900          # palavras-alvo por cena/chamada

# Passo de EXPANSÃO (capítulos curtos): concede passes EXTRA além de `partes`
# até chegar perto do orçamento, sem inflar com repetição.
EXPAND_ALVO = 0.90       # expande enquanto abaixo de 90% do orçamento
EXPAND_MAX = 3           # no máximo N passes extras por capítulo
EXPAND_MIN_GANHO = 120   # se um passe rende < isto (palavras novas), o modelo
                         # secou → para (empurrar mais só geraria refrão)


def _words(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÿ][\wÀ-ÿ'-]*\b", text, flags=re.UNICODE))


def _emit_prog(**kw):
    """Marcador de progresso para o painel (o servidor repassa via SSE; a UI
    intercepta linhas '::PROG:: {json}' para mover a barra por cena)."""
    try:
        print("::PROG:: " + json.dumps(kw, ensure_ascii=False), flush=True)
    except Exception:
        pass


def _last_words(text: str, k: int = 280) -> str:
    ws = text.split()
    return " ".join(ws[-k:]) if len(ws) > k else text


def _bible_essentials(book_dir: Path) -> str:
    b = O._read(book_dir / "01_FUNDACAO" / "BIBLIA.md").strip()
    return (b[:MAX_BIBLE] + " [...]") if len(b) > MAX_BIBLE else b


def _outline_line(book_dir: Path, n: int) -> str:
    txt = O._read(book_dir / "02_ARQUITETURA" / "OUTLINE_GERADO.md")
    m = re.search(rf"(?m)^\s*{n}\.\s+(.+?)\s*$", txt)
    return m.group(1).strip() if m else ""


def _plano_title_budget(book_dir: Path, n: int):
    plano = O._read(book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md")
    title, budget = "", 3000
    for ln in plano.splitlines():
        m = re.match(r"^\|\s*0*%d\s*\|\s*([\d.]+)\s*\|.*\|\s*(.*?)\s*\|$" % n, ln)
        if m:
            try:
                budget = int(m.group(1).replace(".", ""))
            except ValueError:
                pass
            t = m.group(2).strip()
            if t and t != "—":
                title = t
            break
    return title, budget


def _chapter_ficha(book_dir: Path, n: int) -> dict:
    genre = O._detect_genre(book_dir)
    ps = O._plan_summary(book_dir, genre)
    ntot = int(ps["n_chapters"])
    title, budget = _plano_title_budget(book_dir, n)
    line = _outline_line(book_dir, n)
    # separa título — sinopse do outline
    sin = ""
    parts = re.split(r"\s+[—-]\s+", line, maxsplit=1)
    if not title and parts:
        title = parts[0].strip()
    if len(parts) > 1:
        sin = parts[1].strip()
    elif line:
        sin = line
    return {"n": n, "ntot": ntot, "title": title or f"Capítulo {n}",
            "synopsis": sin, "budget": budget,
            "fase": O._ritmo_por_ato(n, n, ntot, planner.is_fiction(genre)),
            "fiction": planner.is_fiction(genre)}


def _prev_resumo(book_dir: Path, n: int) -> str:
    parts = []
    for k in (n - 2, n - 1):
        if k >= 1:
            r = O._read(book_dir / "04_CAPITULOS" / "RESUMOS" / f"cap_{k:02d}.md").strip()
            if r:
                parts.append(f"[Resumo do cap. {k}]\n{r}")
    return "\n\n".join(parts)


def _ja_coberto(book_dir: Path, n: int) -> str:
    """V0.9.2: lista compacta dos TÍTULOS já cobertos (caps 1..n-1) — sinal
    anti-redundância: o capítulo atual não deve reexplicar esses tópicos."""
    itens = []
    for k in range(1, n):
        t, _ = _plano_title_budget(book_dir, k)
        if t:
            itens.append(f"cap {k}: {t}")
    return "; ".join(itens)


def _scene_message(ficha: dict, bible: str, prev: str, tail: str, instr: str,
                   ja: str = "") -> str:
    brief = O.BRIEF_FICCAO if ficha["fiction"] else O.BRIEF_TECNICO
    blocos = [
        brief, O.HUMANIZ_BRIEF,
        "BÍBLIA (voz/fatos — não contradiga):", bible or "[vazia]",
    ]
    if ja:
        blocos += [
            "JÁ COBERTO em capítulos anteriores (NÃO reexplique estes tópicos; "
            "no máximo cite em 1 linha e AVANCE para o conteúdo NOVO deste capítulo):",
            ja,
        ]
    if prev:
        blocos += ["MEMÓRIA (resumo do que veio antes — para continuidade, NÃO reescrever):", prev]
    blocos += [
        f"CAPÍTULO {ficha['n']} de {ficha['ntot']} — \"{ficha['title']}\". "
        f"Posição: {ficha['fase']}",
        f"O QUE ESTE CAPÍTULO PRECISA FAZER: {ficha['synopsis'] or '[defina pela bíblia/outline]'}",
    ]
    if tail:
        blocos += ["ÚLTIMO TRECHO JÁ ESCRITO (continue a partir daqui, sem repetir):", tail]
    if ficha["fiction"]:
        tarefa = ("TAREFA: escreva PROSA em português do Brasil, cena viva (mostre, não "
                  "resuma), diálogo quando servir. " + instr +
                  " Não use títulos/cabeçalhos nem comentários — só a narrativa.")
    else:
        tarefa = ("TAREFA: escreva o TEXTO DIDÁTICO deste capítulo em português do Brasil. "
                  "É um livro TÉCNICO — NÃO invente história, personagens, cenário ou diálogo. "
                  "Explique com intuição ANTES da fórmula; dê um exemplo concreto e, quando "
                  "útil, um trecho de código Python comentado; antecipe o equívoco comum; "
                  "conclua com uma regra prática. Escreva em parágrafos e listas curtas quando "
                  "fizer sentido. " + instr + " Não repita o que já foi dito.")
    blocos += [tarefa]
    return "\n\n".join(blocos)


def _resumo_message(ficha: dict, texto: str) -> str:
    corpo = texto[:3200]
    return ("Resuma o capítulo abaixo em 5 a 8 linhas objetivas (fatos que "
            "aconteceram, mudanças de estado, o que ficou pendente) para servir "
            "de MEMÓRIA ao próximo capítulo. Seco, sem floreio, sem repetir a "
            "prosa.\n\n[Capítulo " + str(ficha['n']) + " — " + ficha['title'] + "]\n" + corpo)


def _tok(s: str) -> set:
    return set(re.findall(r"[\wà-ÿ]+", s.lower()))


def _dedup_paragrafos(text: str, thresh: float = 0.82) -> tuple[str, int]:
    """Remove parágrafos near-idênticos (Jaccard de tokens >= thresh),
    mantendo o primeiro. Preserva a ordem. Não mexe em diálogo curto."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    kept, kept_tok, removed = [], [], 0
    for p in paras:
        tp = _tok(p)
        dup = False
        if len(tp) >= 12:  # só compara parágrafos com corpo (evita cortar diálogo curto)
            for kt in kept_tok:
                if not kt:
                    continue
                inter = len(tp & kt)
                uni = len(tp | kt) or 1
                if inter / uni >= thresh:
                    dup = True
                    break
        if dup:
            removed += 1
            continue
        kept.append(p)
        kept_tok.append(tp)
    return "\n\n".join(kept), removed


def _corta_refrao(text: str, min_palavras: int = 8, max_ocorr: int = 2) -> tuple[str, int]:
    """Corta frases NARRATIVAS longas repetidas além de max_ocorr vezes
    (o 'refrão' típico do modelo pequeno). Preserva linhas de diálogo (—)."""
    contagem = {}
    cortadas = 0
    saida_paras = []
    for para in re.split(r"(\n\s*\n)", text):  # mantém separadores
        if para.strip().startswith("—") or para.strip().startswith("-") or para == "" or para.isspace() or "\n\n" in para:
            saida_paras.append(para)
            continue
        # divide em frases preservando o delimitador
        pedacos = re.split(r"(?<=[.!?…])\s+", para)
        novas = []
        for s in pedacos:
            chave = re.sub(r"[^\wà-ÿ ]", "", s.lower()).strip()
            np = len(chave.split())
            if np >= min_palavras:
                contagem[chave] = contagem.get(chave, 0) + 1
                if contagem[chave] > max_ocorr:
                    cortadas += 1
                    continue
            novas.append(s)
        saida_paras.append(" ".join(x for x in novas if x).strip())
    return "".join(saida_paras), cortadas


def escrever_capitulo(book_dir: Path, n: int, modo: str = "advanced",
                      partes: int = 4, max_tokens: int = 1536,
                      expandir: bool = True, max_expand: int = EXPAND_MAX) -> Path:
    book_dir = Path(book_dir)
    ficha = _chapter_ficha(book_dir, n)
    bible = _bible_essentials(book_dir)
    prev = _prev_resumo(book_dir, n)
    ja = _ja_coberto(book_dir, n)

    sys.path.insert(0, str(APP_DIR))
    import engine_manager  # noqa: E402
    eng = engine_manager.EngineManager()
    if not eng.has_profile():
        raise RuntimeError("Máquina sem perfil calibrado. Calibre o NÚCLEO antes de escrever.")

    anti = ("REGRA DURA: NÃO repita frases nem parágrafos já escritos; NÃO "
            "use refrões ou frases-eco. Cada parágrafo traz informação NOVA.")
    draft = ""
    resumo = ""
    expansoes = 0
    try:
        eng.start(modo)
        p = 0
        alvo = int(ficha["budget"])
        _emit_prog(phase="inicio", n=n, partes=partes, words=0, target=alvo)
        while p < partes and _words(draft) < alvo * 0.9:
            p += 1
            _emit_prog(phase="cena", scene=p, partes=partes, words=_words(draft), target=alvo)
            restante = alvo - _words(draft)
            fic = ficha["fiction"]
            if p == 1:
                if fic:
                    instr = (f"Escreva a ABERTURA do capítulo (entre tarde, perto do conflito); "
                             f"cerca de {ALVO_CENA} palavras. {anti} A cena AVANÇA.")
                else:
                    instr = (f"Abra o capítulo apresentando o problema/conceito com a INTUIÇÃO "
                             f"primeiro; cerca de {ALVO_CENA} palavras. {anti}")
            else:
                fechar = restante <= alvo * 0.4
                if fic:
                    instr = (f"CONTINUE a partir do último trecho, AVANÇANDO a história; "
                             f"cerca de {ALVO_CENA} palavras. {anti}"
                             + (" Conduza a cena ao FECHO do capítulo neste trecho." if fechar else ""))
                else:
                    instr = (f"CONTINUE o desenvolvimento do conceito (exemplo/código/erro comum); "
                             f"cerca de {ALVO_CENA} palavras. {anti}"
                             + (" Feche com uma regra prática e o que vem no próximo capítulo." if fechar else ""))
            msg = _scene_message(ficha, bible, prev, _last_words(draft, 140), instr, ja)
            txt, _ = O._run_engine(eng, msg, max_tokens=max_tokens)
            if not txt.strip():
                break
            draft += ("\n\n" if draft else "") + txt.strip()

        # Passo de EXPANSÃO: se o capítulo ficou curto (o laço acima esgotou
        # `partes` sem chegar perto do orçamento), concede passes EXTRA pedindo
        # material NOVO. Para assim que o modelo "seca" (ganho ínfimo) para não
        # empurrar refrão/enchimento.
        while (expandir and draft and expansoes < max_expand
               and _words(draft) < alvo * EXPAND_ALVO):
            _emit_prog(phase="expansao", scene=expansoes + 1, max_expand=max_expand,
                       words=_words(draft), target=alvo)
            restante = alvo - _words(draft)
            fechar = restante <= alvo * 0.4
            fic = ficha["fiction"]
            if fic:
                instr = ("EXPANDA este capítulo com material NOVO e concreto (uma nova "
                         "beat/cena, aprofundar sensações e subtexto, mostrar a "
                         "consequência de algo já ocorrido); "
                         f"cerca de {ALVO_CENA} palavras. {anti} NÃO recapitule o que já "
                         "foi narrado."
                         + (" Conduza a cena ao FECHO do capítulo." if fechar else ""))
            else:
                instr = ("APROFUNDE este capítulo com conteúdo NOVO (outro exemplo ou "
                         "caso, um contraexemplo, um detalhe de implementação, uma "
                         "armadilha adicional, um mini-exercício); "
                         f"cerca de {ALVO_CENA} palavras. {anti} NÃO repita explicações "
                         "já dadas."
                         + (" Feche com uma regra prática e a ponte para o próximo capítulo." if fechar else ""))
            msg = _scene_message(ficha, bible, prev, _last_words(draft, 140), instr, ja)
            txt, _ = O._run_engine(eng, msg, max_tokens=max_tokens)
            add = txt.strip()
            if not add:
                break
            expansoes += 1
            ganho = _words(add)
            draft += "\n\n" + add
            if ganho < EXPAND_MIN_GANHO:
                break  # modelo secou: incorpora o pouco que veio e encerra

        # resumo encadeado (mesma sessão)
        if draft:
            _emit_prog(phase="resumo", words=_words(draft), target=alvo)
            resumo, _ = O._run_engine(eng, _resumo_message(ficha, draft), max_tokens=400)
    finally:
        try:
            eng.stop()
        except Exception:
            pass

    if not draft:
        raise RuntimeError("O motor não retornou prosa.")

    # Limpeza determinística anti-repetição (fatia 3.1)
    draft, _rp = _dedup_paragrafos(draft)
    draft, _rf = _corta_refrao(draft)
    limpeza = f"{_rp} parágrafo(s) duplicado(s) e {_rf} frase(s)-refrão removidos" \
        if (_rp or _rf) else "sem repetições detectadas"

    caps = book_dir / "04_CAPITULOS"
    (caps / "RESUMOS").mkdir(parents=True, exist_ok=True)
    cap_path = caps / f"cap_{n:02d}.md"
    cap_path.write_text(
        f"# Capítulo {n} — {ficha['title']}\n\n"
        f"<!-- rascunho gerado; revise (line edit + humanização + cópia). "
        f"~{_words(draft)} palavras / alvo {ficha['budget']} | "
        f"expansao: {expansoes} passe(s) | limpeza: {limpeza} -->\n\n" + draft + "\n",
        encoding="utf-8")
    if resumo.strip():
        (caps / "RESUMOS" / f"cap_{n:02d}.md").write_text(resumo.strip() + "\n", encoding="utf-8")

    _atualizar_plano(book_dir, n, _words(draft))
    _emit_prog(phase="fim", scene=n, words=_words(draft), target=int(ficha["budget"]), expansoes=expansoes)
    return cap_path


def _atualizar_plano(book_dir: Path, n: int, escritas: int):
    path = book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md"
    plano = O._read(path)
    if not plano:
        return
    out = []
    for ln in plano.splitlines():
        m = re.match(r"^\|\s*0*%d\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|$" % n, ln)
        if m:
            b = f"{escritas:,}".replace(",", ".")
            out.append(f"| {n:02d} | {m.group(1)} | {b} | ✅ escrito | {m.group(4)} |")
        else:
            out.append(ln)
    path.write_text("\n".join(out) + ("\n" if not "\n".join(out).endswith("\n") else ""), encoding="utf-8")


def _primeiro_pendente(book_dir: Path) -> int:
    plano = O._read(book_dir / "02_ARQUITETURA" / "PLANO_DE_CAPITULOS.md")
    for ln in plano.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|.*\|\s*(⬜|✅)?\s*(pendente|escrito)?\s*\|", ln)
        if m and (m.group(3) == "pendente" or (m.group(2) == "⬜")):
            return int(m.group(1))
    # fallback: primeiro cap_NN.md ausente
    genre = O._detect_genre(book_dir)
    ntot = int(O._plan_summary(book_dir, genre)["n_chapters"])
    for i in range(1, ntot + 1):
        if not (book_dir / "04_CAPITULOS" / f"cap_{i:02d}.md").exists():
            return i
    return 1


def regenerar_resumo(book_dir: Path, n: int, modo: str = "fast") -> Path:
    book_dir = Path(book_dir)
    cap = O._read(book_dir / "04_CAPITULOS" / f"cap_{n:02d}.md")
    if not cap.strip():
        raise RuntimeError(f"cap_{n:02d}.md não encontrado/está vazio.")
    ficha = _chapter_ficha(book_dir, n)
    sys.path.insert(0, str(APP_DIR))
    import engine_manager  # noqa: E402
    eng = engine_manager.EngineManager()
    try:
        eng.start(modo)
        resumo, _ = O._run_engine(eng, _resumo_message(ficha, cap), max_tokens=400)
    finally:
        try:
            eng.stop()
        except Exception:
            pass
    out = book_dir / "04_CAPITULOS" / "RESUMOS" / f"cap_{n:02d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text((resumo.strip() or "[resumo vazio]") + "\n", encoding="utf-8")
    return out


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Escrita capítulo a capítulo — Escritor 360°.")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("capitulo"); c.add_argument("--dir", required=True); c.add_argument("--n", type=int, required=True)
    c.add_argument("--modo", default="advanced", choices=["auto", "fast", "quality", "advanced"]); c.add_argument("--partes", type=int, default=4)
    c.add_argument("--sem-expansao", dest="sem_expansao", action="store_true"); c.add_argument("--max-expansao", type=int, default=EXPAND_MAX)
    pr = sub.add_parser("proximo"); pr.add_argument("--dir", required=True); pr.add_argument("--modo", default="advanced", choices=["auto", "fast", "quality", "advanced"]); pr.add_argument("--partes", type=int, default=4)
    pr.add_argument("--sem-expansao", dest="sem_expansao", action="store_true"); pr.add_argument("--max-expansao", type=int, default=EXPAND_MAX)
    rs = sub.add_parser("resumo"); rs.add_argument("--dir", required=True); rs.add_argument("--n", type=int, required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    if not d.exists():
        print(f"Livro não encontrado: {d}"); return 2
    try:
        if args.cmd == "capitulo":
            out = escrever_capitulo(d, args.n, args.modo, args.partes,
                                    expandir=not args.sem_expansao, max_expand=args.max_expansao)
            print(f"Capítulo escrito: {out}")
        elif args.cmd == "proximo":
            n = _primeiro_pendente(d)
            print(f"Escrevendo o primeiro pendente: capítulo {n}")
            out = escrever_capitulo(d, n, args.modo, args.partes,
                                    expandir=not args.sem_expansao, max_expand=args.max_expansao)
            print(f"Capítulo escrito: {out}")
        elif args.cmd == "resumo":
            out = regenerar_resumo(d, args.n)
            print(f"Resumo gerado: {out}")
        else:
            ap.print_help()
        return 0
    except Exception as exc:
        print(f"Falha: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
