"""Modelo de conteúdo independente dos formatos de entrada e saída."""
from dataclasses import dataclass, field

@dataclass
class Bloco:
    """Um bloco de conteúdo: parágrafo, título, código, citação..."""
    tipo: str          # 'h1'|'h2'|'h3'|'p'|'code'|'quote'|'list'|'hr'|'image'|'table'
    texto: str
    itens: list = field(default_factory=list)   # listas: itens; tabelas: linhas (lista de listas)
    ordenada: bool = False   # para listas numeradas (<ol>)
    extra: str = ""          # imagem: texto alternativo (alt)
    base_dir: str = ""       # origem deste bloco, inclusive listas e tabelas


@dataclass
class Livro:
    titulo: str = "Sem título"
    subtitulo: str = ""
    autor: str = "Autor desconhecido"
    ano: str = ""
    blocos: list = field(default_factory=list)
    base_dir: str = ""       # pasta do arquivo-fonte (para resolver imagens)
    # ---- Pré-textuais (detectados pelo nome do arquivo na pasta) --------
    capa: str = ""                                   # caminho da imagem de capa
    homenagens: list = field(default_factory=list)   # blocos da dedicatória/homenagens
    homenagens_titulo: str = ""                      # título opcional dessa página
    prefacio: list = field(default_factory=list)     # blocos do prefácio
    prefacio_titulo: str = "Prefácio"                # título da página de prefácio

