NÚCLEO IA PORTÁTIL — V0.9 ESCRITOR DE LIVROS 360° (alpha1)
Scaffolder + Planejador + Linter anti-IA
=========================================================

ALPHA. Offline; não altera o motor. Base de retorno: V0.7 FINAL.

O QUE ENTRA
- config/personas/ : ficcao_360.md, tecnico_360.md, humanizacao.md (+ exemplos/)
- app/book/        : book_project.py (scaffolder 00–08), planner.py, humanizar.py
- Lançadores UTF-8 : CRIAR_LIVRO.bat, PLANO_LIVRO.bat, HUMANIZAR.bat

INSTALAÇÃO
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_9_A1.bat + payload\).
2. Execute INSTALAR_V0_9_A1.bat

USO
  CRIAR_LIVRO.bat --slug meu-livro --genero romance_padrao --titulo "T" --autor "A"
  PLANO_LIVRO.bat generos
  HUMANIZAR.bat   workspace\livros\meu-livro\04_CAPITULOS
Gêneros: novela, romance_curto, romance_padrao, romance_longo, fantasia,
ficcao_historica, contos, tecnico_guia, tecnico_curto, tecnico_padrao,
tecnico_aprofundado, tecnico_referencia.

Os livros ficam em workspace\livros\<slug>\ com a estrutura 00–08.

ROLLBACK
ROLLBACK_V0_9_A1.bat remove app/book, config/personas e os lançadores, e
restaura VERSION.json. NÃO toca em workspace\livros (seus livros ficam).

VALIDADO (fora do Windows real)
- compile OK; criou livro ficção (romance_padrao→85k/28 caps) e técnico;
  linter detectou os tiques de IA num texto de teste.
