"""Configuração editorial compartilhada, sem dependências externas."""
from dataclasses import dataclass

@dataclass
class PresetGenero:
    nome: str
    descricao: str
    fonte_corpo: str
    fontes_alternativas: list
    fonte_titulos: str
    fonte_codigo: str
    tam_corpo: float        # pt
    tam_capitulo: float     # pt
    tam_secao: float        # pt
    entrelinha: float       # múltiplo (1.0 = simples)
    recuo_primeira_linha: float  # cm
    espaco_entre_paragrafos: float  # pt
    justificado: bool
    cor_titulos: str        # hex sem '#'
    capitulo_caixa_alta: bool
    dicas: str
    espacamento_titulo: float = 0   # tracking em pt (títulos de capítulo)


GENEROS = {
    "romance": PresetGenero(
        nome="Romance / Ficção literária",
        descricao="Leitura imersiva e longa; serifas clássicas e elegantes.",
        fonte_corpo="Garamond",
        fontes_alternativas=["EB Garamond", "Palatino Linotype", "Minion Pro", "Sabon"],
        fonte_titulos="Garamond",
        fonte_codigo="Consolas",
        tam_corpo=12, tam_capitulo=22, tam_secao=14,
        entrelinha=1.25, recuo_primeira_linha=0.75,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="1F1F1F", capitulo_caixa_alta=False,
        dicas="Sem espaço entre parágrafos; recuo na 1ª linha (exceto no "
              "1º parágrafo do capítulo). Garamond é o padrão-ouro de romances."),
    "tecnico": PresetGenero(
        nome="Técnico / Programação",
        descricao="Clareza e escaneabilidade; sans-serif + monoespaçada para código.",
        fonte_corpo="Calibri",
        fontes_alternativas=["Source Sans Pro", "Open Sans", "Segoe UI"],
        fonte_titulos="Cambria",
        fonte_codigo="Consolas",
        tam_corpo=11, tam_capitulo=20, tam_secao=14,
        entrelinha=1.3, recuo_primeira_linha=0,
        espaco_entre_paragrafos=8, justificado=False,
        cor_titulos="1F3864", capitulo_caixa_alta=False,
        dicas="Sem recuo; espaço entre parágrafos. Blocos de código em "
              "Consolas com fundo cinza. Alinhado à esquerda facilita leitura técnica."),
    "academico": PresetGenero(
        nome="Acadêmico / Científico",
        descricao="Formalidade e tradição; padrões ABNT-friendly.",
        fonte_corpo="Times New Roman",
        fontes_alternativas=["Cambria", "Book Antiqua", "STIX Two Text"],
        fonte_titulos="Times New Roman",
        fonte_codigo="Courier New",
        tam_corpo=12, tam_capitulo=16, tam_secao=14,
        entrelinha=1.5, recuo_primeira_linha=1.25,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="000000", capitulo_caixa_alta=True,
        dicas="Entrelinha 1,5 e recuo de 1,25 cm seguem a ABNT NBR 14724."),
    "infantil": PresetGenero(
        nome="Infantil",
        descricao="Letras grandes, amigáveis e de alta legibilidade.",
        fonte_corpo="Century Gothic",
        fontes_alternativas=["Comic Neue", "Andika", "Sassoon Primary", "OpenDyslexic"],
        fonte_titulos="Century Gothic",
        fonte_codigo="Consolas",
        tam_corpo=14, tam_capitulo=24, tam_secao=18,
        entrelinha=1.5, recuo_primeira_linha=0,
        espaco_entre_paragrafos=10, justificado=False,
        cor_titulos="C05621", capitulo_caixa_alta=False,
        dicas="Fontes com 'a' e 'g' de um andar (como Century Gothic e Andika) "
              "ajudam leitores em alfabetização."),
    "poesia": PresetGenero(
        nome="Poesia",
        descricao="Respiro visual; serifas refinadas, versos sem justificação.",
        fonte_corpo="Palatino Linotype",
        fontes_alternativas=["Baskerville", "Cormorant Garamond", "Adobe Caslon"],
        fonte_titulos="Palatino Linotype",
        fonte_codigo="Consolas",
        tam_corpo=12, tam_capitulo=18, tam_secao=14,
        entrelinha=1.4, recuo_primeira_linha=0,
        espaco_entre_paragrafos=12, justificado=False,
        cor_titulos="1F1F1F", capitulo_caixa_alta=False,
        dicas="Nunca justifique poesia — os versos devem terminar onde o poeta quis."), 
    "terror": PresetGenero(
        nome="Terror / Horror / Gótico",
        descricao="Atmosfera fria e densa; serifas de alto contraste, títulos dramáticos.",
        fonte_corpo="Baskerville Old Face",
        fontes_alternativas=["Libre Baskerville", "Adobe Caslon", "Janson Text", "Book Antiqua"],
        fonte_titulos="Baskerville Old Face",
        fonte_codigo="Consolas",
        tam_corpo=11.5, tam_capitulo=24, tam_secao=14,
        entrelinha=1.2, recuo_primeira_linha=0.75,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="2B0A0A", capitulo_caixa_alta=True,
        dicas="Corpo legível como no romance, mas com serifa fria (Baskerville) e "
              "entrelinha fechada para uma mancha densa. Títulos em CAIXA-ALTA "
              "espaçada e vinho quase-preto criam a atmosfera — nunca use fonte "
              "'assustadora' no corpo do texto.",
        espacamento_titulo=2),
    "suspense": PresetGenero(
        nome="Suspense / Thriller / Fantasia",
        descricao="Ritmo de leitura ágil; serifas com boa mancha de página.",
        fonte_corpo="Palatino Linotype",
        fontes_alternativas=["Georgia", "Charter", "Bookerly"],
        fonte_titulos="Palatino Linotype",
        fonte_codigo="Consolas",
        tam_corpo=11.5, tam_capitulo=22, tam_secao=14,
        entrelinha=1.25, recuo_primeira_linha=0.75,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="1F1F1F", capitulo_caixa_alta=True,
        dicas="Capítulos curtos em caixa-alta reforçam o ritmo do gênero."),
    "distopia": PresetGenero(
        nome="Pós-apocalíptico / Distopia",
        descricao="Mancha densa e árida; corpo sóbrio e legível, títulos com cara "
                  "utilitária/industrial.",
        fonte_corpo="Vollkorn",
        fontes_alternativas=["Bitter", "Alegreya", "Spectral", "Georgia"],
        fonte_titulos="Bahnschrift",
        fonte_codigo="Courier New",
        tam_corpo=11.5, tam_capitulo=22, tam_secao=14,
        entrelinha=1.2, recuo_primeira_linha=0.75,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="26292E", capitulo_caixa_alta=True,
        dicas="O clima do gênero mora nos TÍTULOS e nos 'documentos encontrados', "
              "nunca no corpo — a fonte corrida deve ser uma serifa robusta e "
              "legível (Vollkorn/Bitter são livres; instale antes de usar, senão o "
              "Word substitui). Títulos em caixa-alta espaçada com uma condensada "
              "industrial (Bahnschrift já vem no Windows; Oswald e Saira Stencil "
              "são livres). Truque: blocos de código (```) viram logs/telas de "
              "terminal/memorandos em monoespaçada — troque Courier New por Special "
              "Elite (livre) para o efeito 'máquina de escrever degradada'. No EPUB "
              "o embedding é instável: não deixe nenhuma informação depender da "
              "fonte de título.",
        espacamento_titulo=3),
    "autoajuda": PresetGenero(
        nome="Autoajuda / Negócios",
        descricao="Acessível e moderno; híbrido entre livro e material de consulta.",
        fonte_corpo="Georgia",
        fontes_alternativas=["Merriweather", "PT Serif", "Charter"],
        fonte_titulos="Segoe UI",
        fonte_codigo="Consolas",
        tam_corpo=11.5, tam_capitulo=20, tam_secao=14,
        entrelinha=1.35, recuo_primeira_linha=0,
        espaco_entre_paragrafos=8, justificado=False,
        cor_titulos="1F3864", capitulo_caixa_alta=False,
        dicas="Combinação serifada (corpo) + sans-serif (títulos) cria contraste moderno."),
    "biografia": PresetGenero(
        nome="Biografia / História",
        descricao="Tom clássico e sóbrio; serifas tradicionais.",
        fonte_corpo="Book Antiqua",
        fontes_alternativas=["Bembo", "Caslon", "Janson Text"],
        fonte_titulos="Book Antiqua",
        fonte_codigo="Consolas",
        tam_corpo=12, tam_capitulo=20, tam_secao=14,
        entrelinha=1.3, recuo_primeira_linha=0.75,
        espaco_entre_paragrafos=0, justificado=True,
        cor_titulos="3B3B3B", capitulo_caixa_alta=False,
        dicas="Book Antiqua (Palatino) é sóbria e atemporal — perfeita para não-ficção narrativa."),
}


@dataclass
class Formato:
    nome: str
    largura_cm: float
    altura_cm: float
    margem_sup: float
    margem_inf: float
    margem_int: float   # margem interna (lado da lombada)
    margem_ext: float   # margem externa
    medianiz: float     # gutter extra para encadernação


FORMATOS = {
    "14x21":  Formato("14×21 cm (padrão nacional)", 14, 21, 2.0, 2.2, 2.0, 1.6, 0.5),
    "16x23":  Formato("16×23 cm (não-ficção)",      16, 23, 2.2, 2.4, 2.2, 1.8, 0.5),
    "a5":     Formato("A5 · 14,8×21 cm",            14.8, 21, 2.0, 2.2, 2.0, 1.6, 0.5),
    "6x9":    Formato('6×9" · 15,2×22,9 cm (KDP)',  15.24, 22.86, 2.0, 2.2, 2.0, 1.6, 0.5),
    "a4":     Formato("A4 · 21×29,7 cm (apostilas)", 21, 29.7, 2.5, 2.5, 3.0, 2.0, 0.0),
}


RECUO_PRIMEIRA_LINHA_CM = 0.63   # recuo da 1ª linha do parágrafo


ESPACO_ANTES_PT = 4              # espaçamento "Antes" do parágrafo


ESPACO_DEPOIS_PT = 4             # espaçamento "Depois" do parágrafo


ENTRELINHA = 1.16               # entrelinha (múltiplos)


PASTA_PADRAO = "caps"

EXTS_DOC = (".md", ".txt", ".docx")


@dataclass(frozen=True)
class CorpoTexto:
    recuo: float
    antes: float
    depois: float
    entrelinha: float


def resolver_corpo(preset):
    """Ajustes globais vencem o preset; None delega o valor ao gênero.

    Fonte, tamanho e justificação continuam sempre definidos pelo preset.
    Antes não tem equivalente no preset e usa zero quando o global é None.
    Zero é um ajuste explícito válido, não um pedido de fallback.
    """
    return CorpoTexto(
        preset.recuo_primeira_linha if RECUO_PRIMEIRA_LINHA_CM is None else RECUO_PRIMEIRA_LINHA_CM,
        0 if ESPACO_ANTES_PT is None else ESPACO_ANTES_PT,
        preset.espaco_entre_paragrafos if ESPACO_DEPOIS_PT is None else ESPACO_DEPOIS_PT,
        preset.entrelinha if ENTRELINHA is None else ENTRELINHA,
    )

