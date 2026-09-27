# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 2 (alpha2)

## Geração de OUTLINE via LLM

**Base:** V0.9.0-alpha1. **Escopo:** novo `app/book/outline.py`, launcher
`OUTLINE.bat`, `VERSION.json`. **Aditivo.** É a primeira fatia que usa o motor
dentro do pipeline.

> Alpha. Base de retorno: V0.7 FINAL. Requer a fatia 1 instalada (planner/personas).

---

### O que faz

`outline.py` monta um prompt **compacto e cabível em 4096** a partir de:
- `01_FUNDACAO/BIBLIA.md` (aparada em ~2.600 chars);
- gênero + plano (`02_ARQUITETURA/PLANO_DE_CAPITULOS.md`);
- um **brief destilado** do gênero (ficção/técnico) — a persona completa NÃO
  entra no prompt (não cabe em 4096; ela orienta autor/revisão);
- **regras curtas de humanização** (o que evitar).

E pede ao motor um outline estruturado:
- **Ficção:** premissa · estrutura (começo/virada/clímax) · arco · capítulos (1 linha cada).
- **Técnico:** objetivo · pré-requisitos · sumário (com tipo Diátaxis) · mapa de dependências.

Grava em `02_ARQUITETURA/OUTLINE_GERADO.md` (marcado como rascunho; avisa se
truncou por contexto).

### Comandos

```
OUTLINE.bat gerar   --dir workspace\livros\<slug> [--modo auto|fast|quality]
OUTLINE.bat prompt  --dir workspace\livros\<slug>     (só escreve o prompt p/ uso manual)
OUTLINE.bat aplicar --dir workspace\livros\<slug>     (leva os títulos ao PLANO)
```

- `gerar` usa o motor do NÚCLEO (carrega o modelo, gera, encerra). Se o motor
  não estiver disponível/calibrado, cai para `prompt` (escreve `OUTLINE_PROMPT.md`
  para você colar no chat do NÚCLEO).
- `aplicar` extrai `N. título — …` do outline e preenche os títulos de trabalho
  no `PLANO_DE_CAPITULOS.md`.

### Validação feita (fora do Windows real)

- `py_compile` OK.
- Prompt montado para romance_padrão: **~497 tokens** de entrada (folga grande
  em 4096) → sobra bastante para a saída.
- `aplicar` reconheceu capítulos e preencheu os títulos no plano.
- O `gerar` segue o contrato do `stream_chat` (deltas + `done.truncated`,
  `stop()` no `finally`), com fallback para prompt-only.

### Pendente (teste real no Avell)

- Rodar `OUTLINE.bat gerar --dir workspace\livros\<slug>` e conferir o
  `OUTLINE_GERADO.md`. Em livro longo, o outline pode truncar — nesse caso,
  gerar em partes (fatia futura fará isso automaticamente).

### Rollback

`ROLLBACK_V0_9_A2.bat` remove `app/book/outline.py` e `OUTLINE.bat`, e restaura
`VERSION.json`. Não toca em `workspace/livros`.
