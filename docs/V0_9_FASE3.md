# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 3 (alpha5)

## Escrita CAPÍTULO A CAPÍTULO (resumo encadeado)

**Base:** V0.9.0-alpha4. **Escopo:** novo `app/book/escrever.py` + `ESCREVER.bat`.
É o coração do pipeline: transforma outline+bíblia em prosa, um capítulo por vez.

### Como funciona
Para o capítulo N:
- monta contexto ENXUTO (cabível em 4096): bíblia aparada + ficha do capítulo
  (título do PLANO + sinopse do OUTLINE_GERADO + posição/ato) + **RESUMO
  ENCADEADO** dos capítulos anteriores (04_CAPITULOS/RESUMOS) + regras curtas de
  humanização;
- gera a prosa EM CENAS: várias chamadas de ~900 palavras, cada uma continuando
  do último trecho (passa as ~280 últimas palavras), até ~90% do orçamento,
  conduzindo ao FECHO na última cena;
- salva `04_CAPITULOS/cap_NN.md` (marcado como rascunho);
- gera `04_CAPITULOS/RESUMOS/cap_NN.md` (5–8 linhas) — a memória do próximo;
- atualiza status/palavras no `PLANO_DE_CAPITULOS.md`.

### Comandos
```
ESCREVER.bat capitulo --dir workspace\livros\<slug> --n 1 [--modo quality] [--partes 4]
ESCREVER.bat proximo  --dir workspace\livros\<slug>          (primeiro pendente)
ESCREVER.bat resumo   --dir workspace\livros\<slug> --n 1     (regera o resumo)
```

### Validado (offline)
- compile OK; ficha (título+sinopse+orçamento+ato), resumo encadeado (lê cap
  anterior), atualização de status no plano e "primeiro pendente" testados.
- A geração reusa `_run_engine` (mesmo contrato do stream_chat, já validado).

### Honestidade
- Prosa é RASCUNHO (4B/8B). Depois de escrever, rode `HUMANIZAR.bat` no capítulo
  e faça o line/copy edit. A fatia 4 integra os passes de revisão + compilação.
- Cada cena ≤ ~900 palavras (limite de 4096); um capítulo de 3.000 são ~3–4 cenas.
  Pode variar; ajuste `--partes`.
- Continuidade vem do resumo encadeado + bíblia — não do modelo sozinho.

### Rollback
`ROLLBACK_V0_9_A5.bat` remove `escrever.py` e `ESCREVER.bat` e restaura VERSION.
Não toca em workspace/livros.
