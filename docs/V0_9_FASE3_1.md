# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 3.1 (alpha6)

## Anti-repetição na escrita (dedup de parágrafos + corte de refrão)

**Base:** V0.9.0-alpha5. **Escopo:** `app/book/escrever.py`, `VERSION.json`.

> Motivada por teste real (cap_01, 8B): prosa coerente, MAS refrão repetido ~6x
> ("O passado estava voltando… tudo conectado a ele") e um parágrafo quase
> duplicado. Passar o trecho anterior como "continue" amplificava o eco.

### Correções (determinísticas)
1. **Corte de refrão:** frases NARRATIVAS longas (≥8 palavras) repetidas além de
   2 vezes são removidas (preserva diálogo com "—"). No cap_01 real: 11 frases
   cortadas.
2. **Dedup de parágrafos:** parágrafos near-idênticos (Jaccard de tokens ≥ 0.82)
   são removidos, mantendo o primeiro.
3. **Prompt de cena mais forte:** "não repita frases/parágrafos; cada parágrafo
   traz info NOVA; a cena AVANÇA"; e o tail de continuidade caiu de 280→140
   palavras (menos material para ecoar).
O cabeçalho do `cap_NN.md` registra quantas repetições foram removidas.

### O que isto NÃO resolve (honesto)
Contradições de continuidade (datas divergentes, dia/noite trocados) são de
COERÊNCIA, não de repetição — dependem de modelo maior + passes de revisão
(fatia 4) e da bíblia/resumo. O dedup ataca só o eco mecânico.

### Validado (offline)
compile OK; testado no cap_01 real (11 frases-refrão cortadas; ~4,5% de redução;
fim do eco).

### Rollback
`ROLLBACK_V0_9_A6.bat` restaura `escrever.py` (alpha5) e VERSION.
