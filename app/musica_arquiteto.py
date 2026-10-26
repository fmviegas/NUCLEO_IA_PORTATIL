#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
musica_arquiteto.py — "Arquiteto Sônico" do menu Música: o modelo local do chat
transforma um TEMA (em português) na ficha que o ACE-Step entende (descrição,
roteiro, BPM, tom, compasso, duração), para uma música ou um álbum inteiro.

O texto completo do Arquiteto (config/musica/referencias, do usuário, fora do
git) tem ~11 mil tokens e não cabe no contexto de 4096 dos modos do chat: aqui
vai uma versão própria e curta, só com as regras que valem para o ACE-Step.

A saída do modelo é JSON preso a um schema (llama-server: response_format), e
tudo é conferido/ajustado depois (normalizar_ficha) antes de virar faixa.

Álbum = 2 etapas: plano (identidade, som do álbum e uma linha por faixa) e,
depois, a ficha de cada faixa. O álbum é gravado em config/musica/albuns/
depois de cada etapa, então uma parada no meio não perde o que já foi escrito.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import musica as M

AVULSAS_ID = "arquiteto-avulsas"
AVULSAS_TITULO = "Músicas do Arquiteto"
FONTE = "Arquiteto Sônico (NÚCLEO)"

# descrição ≤ ~200 tokens (4,2 a 4,5 caracteres por token medidos no OUTREMER)
LIMITE_CARACTERES = 820
LIMITE_SOM_ALBUM = 220
FAIXAS_MIN, FAIXAS_MAX = 2, 12
LETRAS = {"instrumental": "instrumental (no vocals)",
          "pt": "sung, lyrics in Brazilian Portuguese",
          "en": "sung, lyrics in English",
          "misto": "you decide per track (instrumental or sung in Brazilian Portuguese)"}

TONS = [n + s for n in ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
        for s in (" minor", " major")]
COMPASSOS = ["2", "3", "4", "6"]

# JSON preso a schema: sem DRY (a estrutura do JSON e o refrão repetem de propósito)
AMOSTRAGEM = {"temperature": 0.8, "top_p": 0.95, "top_k": 50, "min_p": 0.05,
              "repeat_penalty": 1.05, "repeat_last_n": 128, "dry_multiplier": 0.0}

REGRAS = """You are ARQUITETO SONICO, a music producer and prompt engineer. You write generation sheets for ACE-Step 1.5, a local text-to-music model that only knows what the sheet says. Complexity serves emotion; every song needs a purpose and one memorable element.

Every field whose name starts with "english_" MUST be written in English, even when the theme is in Portuguese. "titulo_pt" and "conceito_pt" are in Brazilian Portuguese. "lyrics" lines are in the requested lyrics language.

"english_caption": ONE flowing paragraph, 500 to {lim} characters:
- order: genre and subgenre -> groove and rhythmic feel -> main instruments and their role -> harmony and atmosphere -> vocals (type, gender, delivery) or "No vocals." -> production character.
- it describes the WHOLE song; what happens in each part goes in "sections".
- never write BPM, key, time signature or duration in it (they have their own fields).
- there is NO negative prompt: write what you want ("tight, controlled low end"), never "avoid" or "without". Only allowed negative: "No vocals."
- no artist or band names. Instruments must make sense for the theme and its place and time.

"sections": 5 to 9 parts in playing order. "name" like Intro, Verse 1, Pre-Chorus, Chorus, Verse 2, Bridge, Breakdown, Guitar Solo, Instrumental, Interlude, Outro. "english_description": short, what happens musically (instruments, dynamics, vocal type); use "long" or "brief" to weight a part; the last part describes the ending explicitly (e.g. slow fade on a ringing chord).
{letra}

Fields: "bpm" 40-220 fitting the genre; "key" like "E minor" (a mode such as Phrygian or Dorian goes in the caption, key gets the base); "meter" one of "2","3","4","6" (2/4, 3/4, 4/4, 6/8; for an odd meter pick the nearest and describe the feel in a section); "duration_s" 60 to 360.
"conceito_pt": 2-3 sentences explaining the musical idea.

EXAMPLE of the format (another theme; never copy its words):
{exemplo}
Answer ONLY with the JSON object."""

LETRA_CANTADA = """"lyrics" of each part: Intro, Instrumental, Solo, Interlude and Outro get []; every Verse, Pre-Chorus, Chorus and Bridge gets 2 to 6 short singable lines with natural prosody and strong images. The chorus is memorable and every Chorus repeats the same lines."""
LETRA_INSTRUMENTAL = """Instrumental piece: no lyrics at all; the caption ends with "No vocals."."""

EXEMPLO_CANTADA = """{{"titulo_pt": "Cidade de Vidro", "conceito_pt": "Uma balada sobre uma cidade que guarda as vozes de quem partiu. Começa contida e se abre num refrão largo.", "english_caption": "Melancholic alternative rock ballad with a slow, swaying groove. Clean arpeggiated electric guitars and warm fretless bass carry a bittersweet minor harmony, while brushed drums and a distant string pad open into a wide, hopeful chorus. Intimate female vocals, breathy in the verses and soaring in the chorus. Warm analog production with spacious reverb and gentle tape saturation.", "sections": [{{"name": "Intro", "english_description": "lone clean guitar arpeggio over distant rain", "lyrics": []}}, {{"name": "Verse 1", "english_description": "breathy female vocals over bass and brushed drums", "lyrics": ["A cidade acorda em vidro", "Cada janela guarda um nome", "Eu caminho entre reflexos", "De quem já não volta mais"]}}, {{"name": "Chorus", "english_description": "full band, soaring vocals", "lyrics": ["Se a luz atravessar", "O que restou de nós", "Eu ainda vou te ouvir", "Na cidade de vidro"]}}, {{"name": "Guitar Solo", "english_description": "brief, melodic and restrained", "lyrics": []}}, {{"name": "Outro", "english_description": "the opening arpeggio alone, slow fade on a ringing chord", "lyrics": []}}], "bpm": 72, "key": "A minor", "meter": "4", "duration_s": 210}}"""

EXEMPLO_INSTRUMENTAL = """{{"titulo_pt": "Maré de Cobre", "conceito_pt": "Uma peça instrumental sobre a maré subindo num porto abandonado, do silêncio ao clímax e de volta.", "english_caption": "Instrumental cinematic post-rock with a patient, rolling groove. Tremolo-picked electric guitars, deep sustained bass and tom-heavy drums build layer by layer over a warm minor harmony, with a glockenspiel melody floating above. Vast, contemplative and finally triumphant. Wide, airy production with long reverb tails and a powerful, dynamic climax. No vocals.", "sections": [{{"name": "Intro", "english_description": "glockenspiel melody and soft guitar swells"}}, {{"name": "Build", "english_description": "long, tom-heavy drums and bass enter, guitars layer up"}}, {{"name": "Climax", "english_description": "full band, tremolo guitars carry the melody at full power"}}, {{"name": "Outro", "english_description": "everything falls away to the glockenspiel alone, fading out"}}], "bpm": 90, "key": "D minor", "meter": "4", "duration_s": 240}}"""


def regras(lim: int, cantada: bool) -> str:
    return REGRAS.format(lim=lim, letra=LETRA_CANTADA if cantada else LETRA_INSTRUMENTAL,
                         exemplo=(EXEMPLO_CANTADA if cantada else EXEMPLO_INSTRUMENTAL).format())


PLANO = """You are ARQUITETO SONICO, a producer and concept album architect. Plan a concept album of {n} tracks: a work with beginning, development and conclusion, not a playlist.
- "titulo": album title. "resumo": 2-3 sentences in Brazilian Portuguese with the concept and the emotional journey.
- "english_album_sound": in ENGLISH, 1-2 short sentences, at most {lim_som} characters, starting with "Album sound:" - the shared production signature (guitar/drum/ambience character, space) that every track keeps.
- "motivo": in Brazilian Portuguese, one recurring melodic or rhythmic motif and how it evolves.
- "faixas": exactly {n} tracks. Each one has a distinct narrative role and identity: vary tempo, key, meter, density and intensity, plan an energy curve (no permanent maximum), and make the last track answer the first.
  per track: "titulo"; "papel" (Brazilian Portuguese, one sentence: narrative function, emotion, energy 1-10); "identidade" (Brazilian Portuguese, one short sentence: focus of genre and the signature moment); "cantada" (true/false); "bpm" 40-220; "tom" like "E minor"; "compasso" one of "2","3","4","6"; "duracao" seconds 120-360.
Answer ONLY with the JSON object."""


def schema_ficha(com_album: bool, cantada: bool) -> dict:
    parte = {"name": {"type": "string"}, "english_description": {"type": "string"}}
    if cantada:
        parte["lyrics"] = {"type": "array", "items": {"type": "string"}}
    props = {
        "titulo_pt": {"type": "string"},
        "conceito_pt": {"type": "string"},
        "english_caption": {"type": "string"},
        "sections": {"type": "array", "minItems": 3, "items": {
            "type": "object", "properties": parte, "required": list(parte), "additionalProperties": False}},
        "bpm": {"type": "integer"},
        "key": {"type": "string", "enum": TONS},
        "meter": {"type": "string", "enum": COMPASSOS},
        "duration_s": {"type": "integer"},
    }
    ordem = list(props)
    if com_album:   # título, BPM, tom etc. já vieram do plano do álbum
        ordem = ["conceito_pt", "english_caption", "sections"]
    return {"type": "object", "properties": {k: props[k] for k in ordem}, "required": ordem,
            "additionalProperties": False}


def ficha_do_modelo(d: dict) -> dict:
    """Campos em inglês do schema → campos da tela (descrição, roteiro com [tags] e letra)."""
    blocos = []
    for s in d.get("sections") or []:
        if not isinstance(s, dict):
            continue
        nome = re.sub(r"[\[\]]", "", str(s.get("name") or "").strip()) or "Section"
        desc = re.sub(r"[\[\]]", "", str(s.get("english_description") or "").strip())
        linhas = [re.sub(r"\s+", " ", str(x)).strip() for x in (s.get("lyrics") or [])]
        blocos.append("\n".join([f"[{nome} - {desc}]" if desc else f"[{nome}]"] + [x for x in linhas if x]))
    return {"titulo": d.get("titulo_pt"), "conceito": d.get("conceito_pt"), "descricao": d.get("english_caption"),
            "roteiro": "\n\n".join(blocos), "bpm": d.get("bpm"), "tom": d.get("key"),
            "compasso": d.get("meter"), "duracao": d.get("duration_s")}


SCHEMA_PLANO = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"}, "resumo": {"type": "string"},
        "english_album_sound": {"type": "string"}, "motivo": {"type": "string"},
        "faixas": {"type": "array", "items": {
            "type": "object",
            "properties": {"titulo": {"type": "string"}, "papel": {"type": "string"},
                           "identidade": {"type": "string"}, "cantada": {"type": "boolean"},
                           "bpm": {"type": "integer"}, "tom": {"type": "string", "enum": TONS},
                           "compasso": {"type": "string", "enum": COMPASSOS}, "duracao": {"type": "integer"}},
            "required": ["titulo", "papel", "identidade", "cantada", "bpm", "tom", "compasso", "duracao"],
            "additionalProperties": False}},
    },
    "required": ["titulo", "resumo", "english_album_sound", "motivo", "faixas"],
    "additionalProperties": False,
}

SCHEMA_ENCURTAR = {"type": "object", "properties": {"english_caption": {"type": "string"}},
                   "required": ["english_caption"], "additionalProperties": False}


def amostragem(schema: dict) -> dict:
    return dict(AMOSTRAGEM, response_format={"type": "json_schema",
                                             "json_schema": {"name": "ficha", "schema": schema}})


# ---------------------------------------------------------------- pedidos ao modelo
def conferir_pedido(body: dict) -> dict:
    tipo = str(body.get("tipo") or "musica")
    if tipo not in ("musica", "album", "faixa"):
        raise ValueError("Tipo inválido.")
    tema = str(body.get("tema") or "").strip()
    if tipo != "faixa" and not tema:
        raise ValueError("Escreva o tema da música ou do álbum.")
    if len(tema) > 3000 or len(str(body.get("estilo") or "")) > 400:
        raise ValueError("Tema longo demais (até 3.000 caracteres).")
    letra = str(body.get("letra") or "instrumental")
    if letra not in LETRAS or (tipo == "musica" and letra == "misto"):
        raise ValueError("Escolha se a música é instrumental ou cantada.")
    try:
        n = int(body.get("faixas") or 6)
        dur = int(body.get("duracao") or 0)
    except (TypeError, ValueError):
        raise ValueError("Número de faixas e duração precisam ser números.")
    if tipo == "album" and not FAIXAS_MIN <= n <= FAIXAS_MAX:
        raise ValueError(f"O álbum pode ter de {FAIXAS_MIN} a {FAIXAS_MAX} faixas.")
    if tipo == "faixa":
        a = carregar_album(str(body.get("album") or ""))
        if not a or a.get("fonte") != FONTE:
            raise ValueError("Esse álbum não foi criado pelo Arquiteto.")
        if not any(f.get("n") == body.get("faixa") for f in a["faixas"]):
            raise ValueError("Faixa não encontrada no álbum.")
    return {"tipo": tipo, "tema": tema, "estilo": str(body.get("estilo") or "").strip(), "letra": letra,
            "faixas": n, "duracao": max(0, min(dur, M.DURACAO_MAX)),
            "album": str(body.get("album") or ""), "faixa": body.get("faixa")}


def mensagens_musica(p: dict) -> tuple[str, str]:
    system = regras(LIMITE_CARACTERES, p["letra"] != "instrumental")
    partes = [f"THEME (in Portuguese): {p['tema']}", f"VOCALS: {LETRAS[p['letra']]}"]
    if p["estilo"]:
        partes.append(f"STYLE requested by the user: {p['estilo']}")
    else:
        partes.append("STYLE: choose the genre that best serves the theme.")
    if p["duracao"]:
        partes.append(f"DURATION: about {p['duracao']} seconds.")
    partes.append("titulo_pt: a strong song title. Remember: english_caption and english_description in English.")
    return system, "\n".join(partes)


def mensagens_plano(p: dict) -> tuple[str, str]:
    system = PLANO.format(n=p["faixas"], lim_som=LIMITE_SOM_ALBUM)
    partes = [f"THEME (in Portuguese): {p['tema']}", f"VOCALS: {LETRAS[p['letra']]}"]
    partes.append(f"STYLE requested by the user: {p['estilo']}" if p["estilo"]
                  else "STYLE: choose the musical identity that best serves the theme.")
    return system, "\n".join(partes)


def mensagens_faixa(album: dict, f: dict) -> tuple[str, str]:
    som = album.get("som_do_album") or ""
    lim = max(450, LIMITE_CARACTERES - len(som) - 1)
    system = regras(lim, bool(f.get("cantada")))
    vizinhas = [x for x in album["faixas"] if abs(int(x["n"]) - int(f["n"])) == 1]
    partes = [
        f"ALBUM: {album.get('titulo')} - {album.get('resumo')}",
        f"ALBUM THEME (in Portuguese): {album.get('tema') or ''}",
        f"RECURRING MOTIF: {album.get('motivo') or ''}",
        f"ALBUM SOUND (it will be appended after your descricao, do NOT repeat it): {som}",
        f"THIS TRACK: {f['n']} of {len(album['faixas'])}, \"{f['titulo']}\" - role: {f.get('papel', '')} - identity: {f.get('identidade', '')}",
        f"FIXED FIELDS: {f.get('bpm')} BPM, {f.get('tom')}, meter {M.COMPASSOS.get(str(f.get('compasso')), '4/4')}, {f.get('duracao')} s.",
        "VOCALS: " + (("sung, lyrics in " + ("English" if album.get("letra") == "en" else "Brazilian Portuguese"))
                      if f.get("cantada") else "instrumental (no vocals)"),
    ]
    if vizinhas:
        partes.append("NEIGHBOUR TRACKS: " + "; ".join(f"{x['n']}. {x['titulo']} ({x.get('papel', '')})" for x in vizinhas))
    partes.append("Write only conceito_pt, english_caption and sections (the other fields are already set). "
                  "Remember: english_caption and english_description in English.")
    return system, "\n".join(partes)


def mensagens_encurtar(descricao: str, limite: int) -> tuple[str, str]:
    system = ("You shorten music captions for ACE-Step. Keep genre, groove, instruments, atmosphere, vocals "
              "and production, in one English paragraph, no BPM/key/meter. Answer ONLY with the JSON object.")
    return system, f"Rewrite this caption in at most {limite} characters:\n{descricao}"


# ---------------------------------------------------------------- conferência
_TAG_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")


def ler_json(texto: str) -> dict:
    t = (texto or "").strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("O modelo não devolveu a ficha (resposta vazia ou cortada).")
    try:
        return json.loads(t[i:j + 1])
    except ValueError:
        raise ValueError("A resposta do modelo veio cortada. Tente de novo (ou um modelo mais rápido).")


def _frases(texto: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", texto) if s.strip()]


_NOVOC_RE = re.compile(r"\bno vocals\b", re.I)
# frases que o ACE-Step não deve ler na descrição: proibições (não há negative prompt)
# e andamento/compasso/tom, que já vão nos campos próprios
_FORA_RE = re.compile(r"\b(avoid|avoiding|without|bpm|time signature|meter)\b|\b\d+\s*/\s*\d+\b", re.I)


def limpar_descricao(desc: str, instrumental: bool = False) -> str:
    """Um parágrafo, sem frases proibidas; "No vocals." sempre no fim (se instrumental)."""
    desc = re.sub(r"\s+", " ", str(desc or "")).strip()
    instrumental = instrumental or bool(_NOVOC_RE.search(desc))
    fica = [s for s in _frases(desc) if not _FORA_RE.search(s) and not _NOVOC_RE.search(s)]
    return " ".join(fica + (["No vocals."] if instrumental else []))


def cortar_frases(desc: str, limite: int) -> str:
    fim = " No vocals." if desc.endswith("No vocals.") else ""
    if fim:
        desc, limite = desc[:-len(fim)].rstrip(), limite - len(fim)
    out = ""
    for s in _frases(desc):
        if len(out) + len(s) + 1 > limite:
            break
        out = (out + " " + s).strip()
    return (out or desc[:limite].rsplit(" ", 1)[0]) + fim


def limpar_roteiro(rot: str, instrumental: bool) -> str:
    linhas = [l.rstrip() for l in str(rot or "").replace("\r", "").split("\n")]
    blocos, atual = [], []
    for l in linhas:
        if _TAG_RE.match(l):
            if atual:
                blocos.append(atual)
            atual = [l.strip()]
        elif l.strip() and atual and not instrumental:
            atual.append(l.strip())
    if atual:
        blocos.append(atual)
    if not blocos:
        return "[Instrumental]" if instrumental else str(rot or "").strip()
    return "\n\n".join("\n".join(b) for b in blocos)


def normalizar_ficha(d: dict, base: dict | None = None) -> dict:
    """Ficha do modelo → faixa no formato dos álbuns (o mesmo do OUTREMER)."""
    base = dict(base or {})
    d = ficha_do_modelo(d) if "english_caption" in d else d
    f = dict(base)
    for k in ("titulo", "bpm", "tom", "compasso", "duracao"):
        if k not in base and k in d:
            f[k] = d[k]
    f["titulo"] = str(f.get("titulo") or "Sem título").strip()[:120]
    try:
        f["bpm"] = max(40, min(int(f.get("bpm") or 100), 220))
    except (TypeError, ValueError):
        f["bpm"] = 100
    f["tom"] = f.get("tom") if f.get("tom") in TONS else ""
    f["compasso"] = str(f.get("compasso")) if str(f.get("compasso")) in COMPASSOS else "4"
    try:
        f["duracao"] = max(30, min(int(f.get("duracao") or 180), M.DURACAO_MAX))
    except (TypeError, ValueError):
        f["duracao"] = 180
    desc = limpar_descricao(d.get("descricao"), base.get("cantada") is False)
    instrumental = desc.endswith("No vocals.")
    f["descricao"] = desc
    f["roteiro"] = limpar_roteiro(d.get("roteiro"), instrumental)
    f["conceito"] = str(d.get("conceito") or "").strip()
    f["gerado_em"] = time.strftime("%Y-%m-%d %H:%M")
    return f


def juntar_som(desc: str, som: str) -> str:
    som = (som or "").strip()
    if not som:
        return cortar_frases(desc, LIMITE_CARACTERES) if len(desc) > LIMITE_CARACTERES else desc
    if not som.lower().startswith("album sound"):
        som = "Album sound: " + som
    if len(som) > LIMITE_SOM_ALBUM:
        som = cortar_frases(som, LIMITE_SOM_ALBUM)
    if som[-1] not in ".!?":
        som += "."
    resto = LIMITE_CARACTERES - len(som) - 1
    if len(desc) > resto:
        desc = cortar_frases(desc, resto)
    # "No vocals." fica por último, depois do som do álbum (como no OUTREMER)
    novoc = re.search(r"\s*No vocals\.?\s*$", desc, re.I)
    if novoc:
        return (desc[:novoc.start()].rstrip() + " " + som + " No vocals.").strip()
    return (desc + " " + som).strip()


# ---------------------------------------------------------------- álbuns em disco
def _arquivo(album_id: str) -> Path:
    return M.ALBUNS / (M.slug(album_id) + ".json")


def carregar_album(album_id: str) -> dict | None:
    p = _arquivo(album_id)
    if not album_id or not p.is_file():
        return None
    try:
        a = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return a if isinstance(a, dict) and isinstance(a.get("faixas"), list) else None


def salvar_album(a: dict) -> None:
    M.ALBUNS.mkdir(parents=True, exist_ok=True)
    tmp = _arquivo(a["id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_arquivo(a["id"]))


def id_livre(titulo: str) -> str:
    base = M.slug(titulo) or "album"
    cand, i = base, 2
    while _arquivo(cand).exists():
        cand, i = f"{base}-{i}", i + 1
    return cand


def novo_album(plano: dict, p: dict) -> dict:
    faixas = []
    for i, x in enumerate(plano.get("faixas") or [], 1):
        cantada = bool(x.get("cantada"))
        if p["letra"] == "instrumental":
            cantada = False
        elif p["letra"] in ("pt", "en"):
            cantada = True
        f = normalizar_ficha({}, {"n": i, "titulo": x.get("titulo"), "bpm": x.get("bpm"), "tom": x.get("tom"),
                                  "compasso": x.get("compasso"), "duracao": x.get("duracao")})
        f.update(papel=str(x.get("papel") or "").strip(), identidade=str(x.get("identidade") or "").strip(),
                 cantada=cantada, descricao="", roteiro="")
        faixas.append(f)
    titulo = str(plano.get("titulo") or "Álbum").strip()[:120]
    som = str(plano.get("english_album_sound") or "").strip()
    return {"id": id_livre(titulo), "titulo": titulo, "resumo": str(plano.get("resumo") or "").strip(),
            "fonte": FONTE, "tema": p["tema"], "estilo": p["estilo"], "letra": p["letra"],
            "som_do_album": cortar_frases(som, LIMITE_SOM_ALBUM) if len(som) > LIMITE_SOM_ALBUM else som,
            "motivo": str(plano.get("motivo") or "").strip(), "criado_em": time.strftime("%Y-%m-%d %H:%M"),
            "faixas": faixas}


def guardar_avulsa(f: dict, p: dict) -> dict:
    a = carregar_album(AVULSAS_ID) or {
        "id": AVULSAS_ID, "titulo": AVULSAS_TITULO, "fonte": FONTE, "faixas": [],
        "resumo": "Músicas avulsas escritas pelo Arquiteto a partir de um tema. A mais nova fica no fim."}
    f = dict(f, n=max([int(x.get("n") or 0) for x in a["faixas"]] + [0]) + 1, tema=p["tema"],
             identidade=p["estilo"] or "", cantada=p["letra"] != "instrumental")
    a["faixas"].append(f)
    salvar_album(a)
    return a
