# NÚCLEO IA PORTÁTIL — V0.6.5.2

## Leitura Semântica de Planilhas

**Base:** V0.6.5.1 (Arquivos e Análise Local)
**Escopo:** `app/file_analysis.py`, `app/workspace.py`, `VERSION.json`
**Sem novas dependências.** Continua usando apenas `zipfile` + `xml.etree` da stdlib.

---

### Problema resolvido

O extrator da V0.6.5.x tratava **toda** aba de XLSX como tabela
(`cabeçalho + linhas`). Em planilhas do tipo **formulário/calculadora**
(seções, pares rótulo→valor, subtotais) isso gerava:

- nomes genéricos como `coluna_3`;
- células estruturais vazias tratadas como "dados faltantes";
- perda da relação rótulo→valor;
- análise genérica e pouco útil.

### O que a V0.6.5.2 faz

1. **Classifica a estrutura de cada aba** (`_classify_structure`)
   - `TABELA` — largura útil ≥ 3 e maioria das linhas "largas" (comportamento antigo, preservado).
   - `FORMULÁRIO/CALCULADORA` — predominância de linhas estreitas (rótulo→valor / seções).
2. **Extrai seções** (`_extract_form`) — linhas só-texto que titulam blocos (ex.: `SEÇÃO 1 — ...`, texto em CAIXA ALTA).
3. **Associa rótulo → valor por adjacência**, preservando a coordenada (`B2`, `C15`).
4. **Diferencia vazio estrutural de dado ausente** — espaçadores não viram "faltante".
5. **Interpreta formatação numérica** via `xl/styles.xml` (`_xlsx_number_formats`):
   moeda (`R$ 12.000,00`), percentual (`70%`), inteiro, decimal, data, hora.
6. **Associa fórmulas ao rótulo mais próximo** — `Custo Total Mensal [B13] (fórmula =B8+B9+B10+B2)`.
7. **Corrige a contradição de prompt** (memória, seção 15): o intro de contexto
   agora afirma que o NÚCLEO **realiza** cálculos determinísticos e apenas
   **não recalcula** o motor de fórmulas do Excel.

### Fluxo

```
XLSX
 ↓ _xlsx_grid (grade esparsa rica: valor, fórmula, estilo/coordenada)
 ↓ _classify_structure
 ├── TABELA     → _grid_to_rows → _analyze_rows (V0.6.5.1)
 └── FORMULÁRIO → _extract_form  → seções + pares rótulo→valor
 ↓ context_for_analysis
 ↓ contexto compacto e semântico
 Qwen3 interpreta
```

### Segurança (inalterada)

- Nenhuma macro/código é executado.
- XLSX tratado como ZIP/XML com limites de expansão (`_safe_xlsx_zip`).
- Fórmulas são **lidas e comparadas**, nunca recalculadas.
- Somente arquivos locais; sem rede.

### Critérios de sucesso (memória, seção 30)

Validados com XLSX-calculadora sintético (seções + moeda + percentual + fórmula):

| Critério | Estado |
|---|---|
| Reconhecer finalidade/estrutura | ✅ classifica como formulário |
| Identificar seções | ✅ 3 seções |
| Associar rótulo↔valor | ✅ 8 campos |
| Explicar cálculos identificáveis | ✅ fórmula + valor salvo |
| Diferenciar vazio estrutural | ✅ espaçadores omitidos |
| Evitar `coluna_3` | ✅ ausente do contexto |
| Interpretar moeda/percentual | ✅ `R$ 12.000,00`, `70%` |
| Preservar coordenadas | ✅ `[B2]`, `[B13]` |
| Não dizer "não pode calcular" | ✅ intro corrigido |
| Deixar claro que não recalcula Excel | ✅ observação final |

### Rollback

`ROLLBACK_V0_6_5_2.bat` restaura `VERSION.json`, `app/workspace.py` e
`app/file_analysis.py` do backup técnico criado na instalação. A base
**V0.6 FINAL CONSOLIDADA** permanece intacta como ponto de retorno.
