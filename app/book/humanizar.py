#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — Escritor 360°: linter anti-IA (V0.9).

Ferramenta determinística que audita um .md (ou uma pasta de capítulos) e
reporta a DENSIDADE de "assinaturas de prosa-IA" — as A1–A12 do Módulo de
Humanização + os 14 sinais listados pelo autor. Não reescreve nada: mede e
aponta, para o passe de humanização (julgamento humano/LLM) agir.

Objetivo é REDUZIR densidade, não zerar — um tique isolado às vezes funciona.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---- Padrões (regex) das assinaturas -------------------------------------
PATTERNS = {
    "negar_e_reafirmar": (
        r"[Nn]ão (?:é|era|foi|são|eram) [^.!?\n]{1,80}[.!?]\s+(?:É|Era|Foi|São|Eram)\b"
        r"|não (?:é|são|era|foi) (?:apenas|só) [^;.\n]{1,80};\s*(?:é|são|era|foi)\b"
    ),
    "hedge_simile": r"\b(como se|uma espécie de|algo como|havia algo [a-zà-ÿ]+ (?:que|nele|nela))\b",
    "cascata_mente": r"\b[a-zà-ÿ]+mente,\s+[a-zà-ÿ]+mente\b",
    "frase_enchimento": (
        r"\b(é importante (?:destacar|ressaltar|notar|lembrar)|vale (?:destacar|ressaltar|lembrar|notar)"
        r"|no mundo atual|nos dias de hoje|em um cenário cada vez mais|cabe (?:destacar|ressaltar)"
        r"|é fundamental (?:destacar|entender|compreender))\b"
    ),
    "conclusao_previsivel": r"(?im)^\s*(em resumo|em suma|portanto|como vimos|dessa forma|sendo assim|em conclusão)\b[,: ]",
    "lexico_elevado": (
        r"\b(inabalável|cirúrgic[ao]|divisor de águas|matéria-prima|epicentro|verdadeiramente"
        r"|profundamente|sistema operacional da alma|reorganiza o possível|game[- ]?changer)\b"
    ),
    "abertura_ensaio": r"(?im)^\s*(e se eu (?:te|lhe) dissesse|imagine (?:uma|um|que)|você já (?:parou|se perguntou))\b",
    "exemplo_generico": r"\b(imagine uma empresa|suponha uma empresa|uma empresa que (?:deseja|quer|precisa)|considere um cenário)\b",
}

# Tricolon reflexo (três repetições da mesma partícula) — casado à parte
TRICOLON = [
    re.compile(r"(?i)\b(não [a-zà-ÿ]+,\s+){2}não \b"),
    re.compile(r"(?i)\b(sem [a-zà-ÿ]+,\s+){2}sem \b"),
    re.compile(r"(?i)\b(nem [a-zà-ÿ]+,\s+){2}nem \b"),
]

_COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}
_SENT_SPLIT = re.compile(r"[.!?…]+(?:\s+|$)")
_WORD = re.compile(r"\b[\wÀ-ÿ][\wÀ-ÿ'-]*\b", re.UNICODE)


def _words(text: str) -> int:
    return len(_WORD.findall(text))


def _sentences(text: str):
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def _list_lines(text: str) -> int:
    return sum(1 for ln in text.splitlines()
               if re.match(r"\s*([-*+]|\d+[.)])\s+", ln))


def _stdev(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def analyze_text(text: str) -> dict:
    words = _words(text) or 1
    counts = {}
    hits = {}
    for name, rx in _COMPILED.items():
        found = rx.findall(text)
        counts[name] = len(found)
    tri = sum(len(rx.findall(text)) for rx in TRICOLON)
    counts["tricolon"] = tri
    counts["travessao"] = text.count("—")

    sents = _sentences(text)
    slens = [len(_WORD.findall(s)) for s in sents] or [0]
    ritmo_std = round(_stdev(slens), 2)
    mean_len = round(sum(slens) / len(slens), 1) if slens else 0
    lists = _list_lines(text)

    per_1k = {k: round(v * 1000 / words, 2) for k, v in counts.items()}
    flags = []
    # Heurísticas de alerta (ajustáveis)
    if per_1k["negar_e_reafirmar"] > 0.33:   # ~1 a cada 3.000 palavras é o teto
        flags.append("negar-e-reafirmar acima do teto (1/3000)")
    if per_1k["hedge_simile"] > 1.0:
        flags.append("excesso de hedges de símile ('como se'...)")
    if counts["tricolon"] > 0:
        flags.append("tricolon reflexo presente")
    if per_1k["frase_enchimento"] > 0.5:
        flags.append("frases de enchimento")
    if per_1k["conclusao_previsivel"] > 0.4:
        flags.append("conclusões previsíveis ('em resumo/portanto')")
    if per_1k["lexico_elevado"] > 0.6:
        flags.append("léxico elevado-neutro")
    if lists * 1000 / words > 8:
        flags.append("excesso de listas")
    if ritmo_std < 4 and len(slens) >= 8:
        flags.append(f"ritmo uniforme (desvio de frase {ritmo_std}; varie mais)")
    return {
        "words": words, "sentences": len(sents),
        "mean_sentence_len": mean_len, "ritmo_stdev": ritmo_std,
        "list_lines": lists,
        "counts": counts, "per_1000w": per_1k, "flags": flags,
    }


def _shingles(text: str, k: int = 8):
    ws = [w.lower() for w in _WORD.findall(text)]
    return {" ".join(ws[i:i + k]) for i in range(len(ws) - k + 1)}


def cross_redundancy(files: list[Path], k: int = 8) -> list:
    """Detecta trechos de k-palavras repetidos entre capítulos (redundância)."""
    seen = {}
    dup = Counter()
    examples = {}
    for p in files:
        try:
            sh = _shingles(p.read_text(encoding="utf-8", errors="replace"), k)
        except Exception:
            continue
        for s in sh:
            if s in seen and seen[s] != p.name:
                dup[s] += 1
                examples.setdefault(s, (seen[s], p.name))
            else:
                seen.setdefault(s, p.name)
    out = []
    for s, c in dup.most_common(15):
        a, b = examples[s]
        out.append({"trecho": s, "entre": f"{a} ↔ {b}"})
    return out


CHECKLIST = """
✅ CHECKLIST DE JULGAMENTO (depois da caça — reduzir densidade, não zerar)
[ ] Reduzi o negar-e-reafirmar ao teto? Cada sobrevivente se justifica?
[ ] Cortei frases que explicavam o subtexto (nomear a emoção após o gesto)?
[ ] Quebrei tricolons que eram só simetria?
[ ] O ritmo tem picos e vales, ou está uniforme? (ler em voz alta / TTS)
[ ] Troquei número/frase-enfeite por detalhe concreto?
[ ] Cada capítulo tem UMA metáfora central, não uma pilha?
[ ] O narrador/autor toma posição, ou está "neutro e de bom gosto"?
[ ] Exemplos são concretos (nomes, números, decisões) e não genéricos?
[ ] Cavei fundo em algo, ou só passei horizontal por muitos temas?
[ ] Nenhum conceito/parágrafo reaparece como novo entre capítulos?
""".strip()


def _report(path: Path, a: dict) -> str:
    lines = [f"### {path.name}  ({a['words']} palavras, {a['sentences']} frases)"]
    lines.append(f"- ritmo: comprimento médio {a['mean_sentence_len']} | desvio {a['ritmo_stdev']}")
    lines.append(f"- listas: {a['list_lines']} linhas | travessões: {a['counts']['travessao']}")
    dens = a["per_1000w"]
    interessantes = ["negar_e_reafirmar", "hedge_simile", "tricolon", "frase_enchimento",
                     "conclusao_previsivel", "lexico_elevado", "cascata_mente",
                     "abertura_ensaio", "exemplo_generico"]
    lines.append("- densidade (por 1.000 palavras):")
    for k in interessantes:
        lines.append(f"    {k:22} {a['counts'][k]:>3}  ({dens.get(k,0)}/1k)")
    if a["flags"]:
        lines.append("- ⚠ ALERTAS: " + "; ".join(a["flags"]))
    else:
        lines.append("- ✔ sem alertas de densidade (revise o checklist mesmo assim)")
    return "\n".join(lines)


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Linter anti-IA do Escritor 360°.")
    ap.add_argument("alvo", help="arquivo .md ou pasta (varre cap_*.md e *.md)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    target = Path(args.alvo)
    files = []
    if target.is_dir():
        files = sorted(target.glob("cap_*.md")) or sorted(target.glob("*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"Alvo não encontrado: {target}")
        return 2

    results = {}
    for p in files:
        results[p.name] = analyze_text(p.read_text(encoding="utf-8", errors="replace"))

    if args.json:
        import json
        red = cross_redundancy(files) if len(files) > 1 else []
        print(json.dumps({"files": results, "cross_redundancy": red},
                         ensure_ascii=False, indent=2))
        return 0

    print("=" * 72)
    print("        NÚCLEO IA PORTÁTIL — LINTER ANTI-IA (Escritor 360°)")
    print("=" * 72)
    for p in files:
        print()
        print(_report(p, results[p.name]))
    if len(files) > 1:
        red = cross_redundancy(files)
        print()
        print("### Redundância entre capítulos (trechos de 8 palavras repetidos)")
        if red:
            for r in red[:10]:
                print(f"  - [{r['entre']}] \"{r['trecho']}\"")
        else:
            print("  ✔ nenhum trecho longo repetido entre capítulos")
    print()
    print(CHECKLIST)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
