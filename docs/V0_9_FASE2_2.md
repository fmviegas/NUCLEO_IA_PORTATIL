# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 2.2 (alpha4)

## Outline com ritmo por ato + limpeza de formato

**Base:** V0.9.0-alpha3. **Escopo:** `app/book/outline.py`, `VERSION.json`.

> Motivada por teste real (alpha3, --modo quality): qualidade deu grande salto
> (28 caps coerentes), mas cada LOTE de 8 "fechava" um arco (cap 8 e cap 16
> soavam finais), houve repetição temática nos lotes finais e o formato degradou
> ("Capítulo N —", gerando numeração dupla).

### Correções
1. **Ritmo por ato:** cada lote recebe sua POSIÇÃO no livro (ATO 1 montagem /
   ATO 2 desenvolvimento / pré-clímax / ATO 3 clímax-resolução) e a ordem
   explícita "NÃO conclua a história antes do capítulo N". Impede o lote 1 de
   resolver a trama.
2. **Limpeza de formato:** o parser remove o prefixo redundante "Capítulo N —"
   (fim da numeração dupla tipo "9. Capítulo 9 —").
3. **Warning eliminado:** `re.split(..., maxsplit=1)` (era DeprecationWarning
   inofensivo — NÃO era erro).

### Uso (inalterado)
```
OUTLINE.bat gerar --dir workspace\livros\<slug> --modo quality [--lote 8]
```
Dica: para máximo controle de repetição, use `--lote 6`.

### Validado (offline)
- compile sem DeprecationWarning; parse remove "Capítulo N —"; ritmo por ato
  mapeia 1-8=ATO1 … 25-28=ATO3 corretamente.

### Ainda assim
Modelo pequeno: mesmo com ato-pacing, revise o outline. A repetição temática
(não literal) pode persistir; a marcação de repetição pega títulos iguais, não
sinônimos. Ganho maior com modelo AVANÇADO (Catálogo) — futuro.

### Rollback
`ROLLBACK_V0_9_A4.bat` restaura `outline.py` (alpha3) e `VERSION.json`.
