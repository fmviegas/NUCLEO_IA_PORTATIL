#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
musica.py — menu Música: álbuns prontos (config/musica/albuns/*.json), pedido
de geração e as músicas já geradas (workspace/musica/<album>/).

A geração em si roda em tools/musica_gerar.py com o Python do ACE-Step
(engine/acestep/python_embeded); aqui só se monta e confere o pedido.

Os álbuns são do usuário (textos dele, ex.: OUTREMER) e ficam fora do git,
como a planilha do Financeiro. Sem álbum na pasta, o menu ainda gera a partir
do prompt colado à mão.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
ACE = ROOT / "engine" / "acestep"
ACE_PY = ACE / "python_embeded" / "python.exe"
ALBUNS = ROOT / "config" / "musica" / "albuns"
SAIDA = ROOT / "workspace" / "musica"
GERADOR = ROOT / "tools" / "musica_gerar.py"

COMPASSOS = {"": "automático", "2": "2/4", "3": "3/4", "4": "4/4", "6": "6/8"}
DURACAO_MAX = 360          # GTX 1050 4 GB sem o LM de 5 Hz (gpu_config tier1)
CARACTERES_POR_TOKEN = 4.2  # estimativa da tela (OUTREMER mediu 4,2 a 4,5); a contagem exata é feita pelo gerador
LIMITE_DESCRICAO = 202      # 256 - ~54 tokens fixos (instrução + metadados)
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode().lower()
    return _SLUG_RE.sub("-", t).strip("-")[:60] or "musica"


def instalado() -> dict:
    """O ACE-Step está na pasta e com os modelos baixados?"""
    faltando = [str(p.relative_to(ROOT)) for p in (
        ACE_PY, ACE / "acestep", ACE / "checkpoints" / "acestep-v15-turbo",
        ACE / "checkpoints" / "Qwen3-Embedding-0.6B", ACE / "checkpoints" / "vae") if not p.exists()]
    return {"ok": not faltando, "faltando": faltando, "pasta": "engine/acestep"}


def albuns() -> list:
    out = []
    if not ALBUNS.is_dir():
        return out
    for f in sorted(ALBUNS.glob("*.json")):
        try:
            a = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(a, dict) and isinstance(a.get("faixas"), list):
            a["id"] = slug(a.get("id") or f.stem)
            out.append(a)
    return out


def geradas() -> list:
    """Músicas já geradas, da mais nova para a mais antiga."""
    out = []
    if not SAIDA.is_dir():
        return out
    for mp3 in SAIDA.rglob("*.mp3"):
        if "_ace" in mp3.parts:
            continue
        ficha = {}
        js = mp3.with_suffix(".json")
        if js.is_file():
            try:
                ficha = json.loads(js.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                ficha = {}
        out.append({
            "rel": mp3.relative_to(SAIDA).as_posix(),
            "titulo": ficha.get("titulo") or mp3.stem,
            "album": ficha.get("album") or (mp3.parent.name if mp3.parent != SAIDA else ""),
            "duracao": ficha.get("duracao"), "seed": ficha.get("seed"),
            "gerado_em": ficha.get("gerado_em") or time.strftime("%Y-%m-%d %H:%M", time.localtime(mp3.stat().st_mtime)),
            "tempo_geracao_s": ficha.get("tempo_geracao_s"),
            "mtime": mp3.stat().st_mtime,
        })
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out


def listar() -> dict:
    return {"instalado": instalado(), "albuns": albuns(), "geradas": geradas(),
            "compassos": COMPASSOS, "duracao_max": DURACAO_MAX,
            "caracteres_por_token": CARACTERES_POR_TOKEN, "limite_descricao": LIMITE_DESCRICAO}


def arquivo_gerado(rel: str) -> Path | None:
    """Caminho seguro de um .mp3 em workspace/musica (nada fora dela)."""
    try:
        p = (SAIDA / str(rel)).resolve()
        p.relative_to(SAIDA.resolve())
    except (ValueError, OSError):
        return None
    return p if p.is_file() and p.suffix.lower() == ".mp3" else None


def montar_pedido(body: dict) -> dict:
    """Confere o pedido da tela e devolve o job do gerador (ValueError se inválido)."""
    caption = str(body.get("caption") or "").strip()
    if not caption:
        raise ValueError("Escreva a descrição da música.")
    if len(caption) > 4000 or len(str(body.get("roteiro") or "")) > 12000:
        raise ValueError("Texto longo demais.")
    compasso = str(body.get("compasso") or "")
    if compasso not in COMPASSOS:
        raise ValueError("Compasso inválido: o ACE-Step aceita 2/4, 3/4, 4/4 e 6/8.")
    try:
        bpm = int(body.get("bpm") or 0) or None
        dur = int(body.get("duracao") or 120)
    except (TypeError, ValueError):
        raise ValueError("BPM e duração precisam ser números.")
    if bpm is not None and not 30 <= bpm <= 300:
        raise ValueError("BPM entre 30 e 300.")
    dur = max(10, min(dur, DURACAO_MAX))
    tom = str(body.get("tom") or "").strip()
    if tom and not re.fullmatch(r"[A-G][#b]? (major|minor)", tom):
        raise ValueError('Tom no formato do ACE-Step, ex.: "E minor", "F# minor", "Bb major".')
    titulo = str(body.get("titulo") or "").strip()[:120] or "Música"
    album = slug(body.get("album") or "avulsas")
    faixa = body.get("faixa")
    base = (f"{int(faixa):02d}_" if str(faixa or "").isdigit() else "") + slug(titulo)
    return {
        "caption": caption, "roteiro": str(body.get("roteiro") or "").strip(), "bpm": bpm, "tom": tom,
        "compasso": compasso, "duracao": dur, "seed": str(body.get("seed") or "").strip(),
        "titulo": titulo, "album": album, "faixa": faixa,
        "saida": str(SAIDA / album), "nome": base + time.strftime("_%Y%m%d_%H%M%S"),
    }
