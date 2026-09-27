# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 1 (alpha1)

## Scaffolder + Planejador + Linter anti-IA

**Base:** V0.7 FINAL. **Escopo:** novos `app/book/` e `config/personas/`,
`VERSION.json`. Só stdlib. **Aditivo, offline, não toca no motor.**

> Alpha de desenvolvimento. Base de retorno: V0.7 FINAL.

---

### O que entra

**`config/personas/`** (fonte da verdade das personas 360°):
- `ficcao_360.md` — Criador de eBooks 360° (ficção).
- `tecnico_360.md` — Criador de Livros Técnicos 360° (genérico, domínio-agnóstico).
- `humanizacao.md` — Módulo de Humanização da Prosa (transversal).
- `exemplos/tecnico_estatistica_360.md` — exemplo de persona técnica especializada.

**`app/book/`** (ferramentas determinísticas, sem IA):
- `book_project.py` — **scaffolder**: cria a estrutura **00–08 universal**
  adaptada por gênero, pré-preenche templates (com as regras de humanização
  embutidas em `ESTILO_E_VOZ.md` e `STYLE_SHEET_ANTITIQUE.md`) e copia a persona
  do gênero + `humanizacao.md` para `00_GOVERNANCA/` (livro autocontido).
- `planner.py` — **planejador**: gênero → nº de capítulos × orçamento de
  palavras (metas por gênero) e medição de progresso.
- `humanizar.py` — **linter anti-IA**: mede a densidade das assinaturas A1–A12
  + os 14 sinais do autor (negar-e-reafirmar, frases de enchimento, conclusões
  previsíveis, léxico elevado, excesso de listas, ritmo uniforme, exemplos
  genéricos, redundância entre capítulos…). Não reescreve; aponta.

### Estrutura 00–08 (universal, adaptada por gênero)

```
00_GOVERNANCA  persona + ESTILO_E_VOZ (humanização) + STYLE_SHEET + decisões
01_FUNDACAO    bíblia (premissa/tipo, público, promessa, meta)
02_ARQUITETURA ESTRUTURA + PLANO_DE_CAPITULOS (capítulos × orçamento)
03_CONHECIMENTO ficção: PERSONAGENS/AMBIENTACAO/CRONOLOGIA · técnico: FONTES/NOTACAO/DATASETS
04_CAPITULOS   manuscrito (cap_NN.md) + RESUMOS/ (resumo encadeado)
05_PROJETO_PRATICO técnico: CODIGO/ · ficção: dossiê (opcional)
06_EXERCICIOS  técnico: exercícios · ficção: extras (opcional)
07_REVISAO     REVISAO + PASSE_HUMANIZACAO (saída do linter)
08_PUBLICACAO  METADADOS + BLURB
```

### Uso (lançadores com UTF-8)

```
CRIAR_LIVRO.bat  --slug meu-livro --genero romance_padrao --titulo "T" --autor "A"
PLANO_LIVRO.bat  generos
HUMANIZAR.bat    workspace\livros\meu-livro\04_CAPITULOS
```
Gêneros: novela, romance_curto, romance_padrao, romance_longo, fantasia,
ficcao_historica, contos, tecnico_guia, tecnico_curto, tecnico_padrao,
tecnico_aprofundado, tecnico_referencia.

### Validação feita (fora do Windows real)

- `py_compile` OK nos 3 módulos.
- Criou livro de ficção (romance_padrao → 85k / 28 caps) e técnico (estrutura
  FONTES/NOTACAO/DATASETS/CODIGO/EXERCICIOS) corretos.
- Linter detectou, num texto de teste, negar-e-reafirmar, frase de enchimento,
  conclusão previsível, léxico elevado, abertura-ensaio, exemplo genérico,
  excesso de listas e ritmo uniforme.

### Próximas fatias

- fatia 2: geração de **outline** (Estágio 1) via LLM + persona.
- fatia 3: geração **capítulo a capítulo** com resumo encadeado + bíblia.
- fatia 4: passes de revisão/humanização integrados + compilação (08).
- fatia 5: aba "Livros" na UI (opcional; começa por CLI).

### Rollback

`ROLLBACK_V0_9_A1.bat` remove `app/book/`, `config/personas/` e os lançadores,
e restaura `VERSION.json` (raiz e payload) → volta à V0.7 FINAL.
