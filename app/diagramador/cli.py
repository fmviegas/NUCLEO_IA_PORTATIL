"""Interface de linha de comando do diagramador."""
import os
import argparse
from .config import GENEROS, FORMATOS, PASTA_PADRAO, EXTS_DOC, resolver_corpo
from .leitura import carregar, carregar_multiplos
from .exportar_docx import diagramar_docx
from .exportar_epub import exportar_epub

def listar_generos():
    print("\n╔══ GÊNEROS E FONTES RECOMENDADAS " + "═" * 34)
    for chave, g in GENEROS.items():
        corpo = resolver_corpo(g)
        print(f"║\n║ ▸ {chave.upper():<12} {g.nome}")
        print(f"║   {g.descricao}")
        print(f"║   Fonte principal : {g.fonte_corpo}  ({g.tam_corpo} pt, "
              f"entrelinha efetiva {corpo.entrelinha})")
        print(f"║   Corpo efetivo   : recuo {corpo.recuo} cm; antes/depois {corpo.antes}/{corpo.depois} pt")
        print(f"║   Alternativas    : {', '.join(g.fontes_alternativas)}")
        print(f"║   💡 {g.dicas}")
    print("╚" + "═" * 66)
    print("\nFormatos de miolo disponíveis:")
    for chave, f in FORMATOS.items():
        print(f"  --formato {chave:<6} → {f.nome}")


_EXTS_CAP = EXTS_DOC


def _pasta_tem_capitulos(pasta: str) -> bool:
    """True se a pasta contém ao menos um .md/.txt/.docx utilizável."""
    return any(
        f.lower().endswith(_EXTS_CAP) and not f.startswith(("~$", "."))
        for f in os.listdir(pasta))


def menu_interativo(args):
    """Menu simples quando o script é chamado sem argumentos: pergunta o
    arquivo e o gênero (e se quer EPUB / autor)."""
    print("\n" + "═" * 60)
    print("  DIAGRAMADOR — modo interativo")
    print("  (deixe em branco para aceitar o valor entre [colchetes])")
    print("═" * 60)

    # 1) Arquivo -----------------------------------------------------------
    while True:
        caminho = input(f"\n📄 Arquivo/pasta dos capítulos [{PASTA_PADRAO}]: ").strip()
        caminho = caminho.strip('"').strip("'").strip()   # tira aspas de drag-and-drop
        if not caminho:
            caminho = PASTA_PADRAO                          # Enter → pasta padrão

        if not os.path.exists(caminho):
            if caminho == PASTA_PADRAO:
                # cria a pasta padrão e orienta o usuário (ainda não há o que fazer)
                os.makedirs(caminho, exist_ok=True)
                print(f"   📁 Criei a pasta '{caminho}/' em {os.getcwd()}.")
                print(f"      Coloque seus capítulos (.md) nela e rode novamente.")
                return None
            print(f"   ✗ Não encontrei: {caminho}")
            continue

        # existe: se for pasta, precisa ter capítulos dentro
        if os.path.isdir(caminho) and not _pasta_tem_capitulos(caminho):
            print(f"   ⚠ A pasta '{caminho}' não tem arquivos .md/.txt/.docx.")
            if caminho == PASTA_PADRAO:
                print("      Coloque seus capítulos nela e rode novamente.")
                return None
            continue
        break

    # 2) Gênero ------------------------------------------------------------
    chaves = list(GENEROS.keys())
    print("\n📚 Gênero:")
    for idx, ch in enumerate(chaves, 1):
        print(f"   {idx:>2}. {GENEROS[ch].nome}")
    while True:
        escolha = input(f"\nEscolha (1-{len(chaves)}) ou o nome [1]: ").strip() or "1"
        if escolha.isdigit() and 1 <= int(escolha) <= len(chaves):
            genero = chaves[int(escolha) - 1]
            break
        if escolha in GENEROS:
            genero = escolha
            break
        print("   ✗ Opção inválida.")

    # 3) Autor (opcional) --------------------------------------------------
    autor = input("\n✍️  Autor (Enter para pular): ").strip()

    # 4) EPUB? -------------------------------------------------------------
    epub = input("\n📖 Gerar EPUB também? (s/N): ").strip().lower().startswith("s")

    args.entrada = [caminho]
    args.genero = genero
    if autor:
        args.autor = autor
    args.epub = args.epub or epub
    print()
    return args


def main():
    ap = argparse.ArgumentParser(
        description="Diagramador de livros e e-books (MD/TXT/DOCX → DOCX/EPUB)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemplos:\n"
               "  python diagramador.py            (interativo: pergunta arquivo e gênero)\n"
               "  python diagramador.py livro.md -o livro.docx --genero romance\n"
               "  python diagramador.py livro.txt -o livro.docx --genero suspense --formato 6x9 --epub\n"
               "  python diagramador.py velho.docx -o novo.docx --genero tecnico\n"
               "  python diagramador.py --listar-generos")
    ap.add_argument("entrada", nargs="*",
                    help="Arquivo(s) .md/.txt/.docx ou uma pasta com os capítulos")
    ap.add_argument("-o", "--saida", help="Arquivo .docx de saída")
    ap.add_argument("--genero", default="romance", choices=GENEROS.keys())
    ap.add_argument("--formato", default="16x23", choices=FORMATOS.keys())
    ap.add_argument("--titulo", help="Título do livro (sobrepõe o detectado)")
    ap.add_argument("--subtitulo", default="")
    ap.add_argument("--autor", help="Nome do autor")
    ap.add_argument("--ano", default="")
    ap.add_argument("--sem-sumario", action="store_true")
    ap.add_argument("--sem-capa-no-miolo", action="store_true",
                    help="não põe a imagem de capa como 1ª página do DOCX; use para "
                         "gerar o miolo pronto para o KDP print (a capa vai separada)")
    ap.add_argument("--epub", action="store_true", help="Gera também um .epub")
    ap.add_argument("--listar-generos", action="store_true",
                    help="Mostra gêneros, fontes e formatos disponíveis")
    args = ap.parse_args()

    if args.listar_generos:
        listar_generos()
        return
    if not args.entrada:
        try:
            args = menu_interativo(args)
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            return
        if args is None:          # menu criou a pasta / não havia o que processar
            return

    try:
        if len(args.entrada) > 1 or os.path.isdir(args.entrada[0]):
            print(f"🔗 Unindo {len(args.entrada)} entrada(s):")
            livro = carregar_multiplos(args.entrada)
        else:
            livro = carregar(args.entrada[0])
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    if args.titulo:
        livro.titulo = args.titulo
    if args.subtitulo:
        livro.subtitulo = args.subtitulo
    if args.autor:
        livro.autor = args.autor
    if args.ano:
        livro.ano = args.ano

    preset = GENEROS[args.genero]
    fmt = FORMATOS[args.formato]
    base = args.entrada[0].rstrip("/\\")
    saida = args.saida or os.path.splitext(base)[0] + "_diagramado.docx"

    n_caps = sum(1 for b in livro.blocos if b.tipo == "h1")
    print(f"📖 {livro.titulo} — {livro.autor}")
    print(f"   Gênero: {preset.nome} · Fonte: {preset.fonte_corpo} {preset.tam_corpo}pt")
    print(f"   Formato: {fmt.nome} · Capítulos detectados: {n_caps}")

    diagramar_docx(livro, preset, fmt, saida,
                   incluir_sumario=not args.sem_sumario,
                   capa_no_miolo=not args.sem_capa_no_miolo)
    print(f"✅ DOCX gerado: {saida}")

    if args.epub:
        saida_epub = os.path.splitext(saida)[0] + ".epub"
        exportar_epub(livro, preset, saida_epub)
        print(f"✅ EPUB gerado: {saida_epub}")

