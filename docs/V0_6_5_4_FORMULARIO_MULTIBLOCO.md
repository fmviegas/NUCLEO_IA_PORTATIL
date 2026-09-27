# NÚCLEO IA PORTÁTIL — V0.6.5.4

## Hotfix: Formulário multi-bloco + classificador por adjacência

**Base:** V0.6.5.2 / V0.6.5.3.
**Escopo:** `app/file_analysis.py`, `VERSION.json`. Sem novas dependências.

---

### Problema observado em campo

A `Calculo Precificação-V01.xlsx` real continuava saindo como `coluna_3` /
`coluna_6` / "faltantes", mesmo com a V0.6.5.2 instalada.

**Causa (confirmada inspecionando o arquivo real):** a planilha tem **dois
formulários lado a lado**:

```
Bloco esquerdo (B/C)          Bloco direito (E/F)
SEÇÃO 1: METAS/CARGA          SEÇÃO 2: CUSTOS
SEÇÃO 3: VALOR DA HORA        SEÇÃO 4: CALCULADORA
rótulo em B, valor em C       rótulo em E, valor em F
```

- O classificador antigo usava **largura de linha**: com B,C,E,F preenchidos,
  cada linha parecia "larga" → classificado como TABELA.
- Mesmo forçado a formulário, o extrator antigo (row-major) juntava os rótulos
  dos dois blocos e embaralhava as seções.

### Correção

1. **Classificador por adjacência rótulo→valor** (`_classify_structure`):
   conta a fração de valores que têm um texto imediatamente à esquerda.
   - Formulário (inclusive multi-bloco): fração alta → `form`.
   - Tabela de dados: valores em grade → fração baixa → `table`.
   - Salvaguarda: cabeçalho textual largo (≥3 col) + ≥3 linhas de dados → `table`.
2. **Extração por blocos de colunas** (`_column_blocks` + `_extract_form_block`):
   separa blocos contíguos (quebrados por coluna vazia) e extrai cada um de
   cima para baixo, preservando as seções. Ordem: esquerda → direita.
3. **Kind efetivo por rótulo** (`_effective_kind`): quando o estilo do Excel
   marca a coluna inteira como moeda, rótulos de unidade não-monetária
   (horas, dias, %, margem) deixam de exibir `R$`; rótulos monetários
   (valor, custo, preço, salário, orçamento…) mantêm `R$`.

### Resultado com o arquivo REAL (validado)

```
Seções: 4 | campos rótulo→valor: 22
SEÇÃO 1: SUAS METAS E CARGA HORÁRIA
- Quanto quer ganhar por mês de "salário"?: R$ 12.000,00 [C3]
- Quantas horas por dia quer trabalhar?: 6 [C5]
SEÇÃO 3: CÁLCULO DO VALOR DA HORA
- Total de Horas FATURÁVEIS no Mês: 90,93 [C11] (fórmula =C10*C6)
- CUSTO MÍNIMO DA HORA (ponto de equilíbrio): R$ 151,66 [C12] (fórmula =C9/C11)
- VALOR FINAL PARA CALCULO DA HORA: R$ 13.880,93 [C15] (fórmula =C11*(1+C12))
SEÇÃO 2: CUSTOS OPERACIONAIS MENSAIS
- Energia / Aluguel (parte): R$ 1.500,00 [F7]
- TOTAL DE CUSTOS FIXOS: R$ 1.790,00 [F11] (fórmula =SUM(F3:F9))
SEÇÃO 4: CALCULADORA DE PROJETO
- VALOR FINAL DO ORÇAMENTO: R$ 151,66 [F18] (fórmula =F16+F17)
```

Regressão: tabela CSV normal continua classificada como `table`.

### Limitações conhecidas (honestas)

- Ordem das seções é por bloco (esquerda inteira, depois direita): 1, 3, 2, 4.
  É logicamente agrupada, não em ordem numérica dos títulos.
- `_effective_kind` é heurístico por palavra-chave em PT-BR; rótulos muito
  atípicos podem escapar. É conservador (só afeta exibição de `R$`).

### Rollback

`ROLLBACK_V0_6_5_4.bat` restaura `file_analysis.py` e `VERSION.json`.
V0.6 FINAL permanece intacta.
