# Relatório de testes — Controle Financeiro

Gerado em 2026-10-08 13:57 por `tools/testar_financeiro.py`, no **Microsoft Excel** (COM), com dados fictícios numa cópia de teste.
Modelo: `config/templates/financeiro/ControleFinanceiro.xlsx`.

## ControleFinanceiro_Recriado.xlsx — 13/13 aprovados

| Item | Teste | Resultado | Detalhe |
|---|---|---|---|
| 1 — Existência, ordem e nomes das 16 abas | 16 abas na ordem | ✅ aprovado | Início, Contas e Cadastro, Evolução, C.Crédito, Jan, Fev, Mar, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez |
| 8 — Proteção das abas mantida | protecao mantida nas 16 abas | ✅ aprovado | desprotegidas:  |
| 2 — Totais e porcentagens do mês (dados fictícios) | Jan totais (U5=6000, U6=1500, U7=4500) | ✅ aprovado | U5=6000 U6=1500 U7=4500 |
| 2 — Totais e porcentagens do mês (dados fictícios) | Jan percentuais (I6=83,33%, Q6=80%) | ✅ aprovado | I6=0,833333333333333 Q6=0,8 |
| 2 — Totais e porcentagens do mês (dados fictícios) | linha vazia sem erro (I8 e Q8 = 0%) | ✅ aprovado | I8='0' Q8='0' |
| 3 — Passagem de saldo Jan → Fev → … → Dez | Jan U10 = (U7+U9)-U8 = 5000 | ✅ aprovado | U10=5000 |
| 3 — Passagem de saldo Jan → Fev → … → Dez | Fev U9 = Jan U10 e U10 = 4500 | ✅ aprovado | U9=5000 U10=4500 |
| 3 — Passagem de saldo Jan → Fev → … → Dez | saldo chega a Dez (U9=U10=4500) | ✅ aprovado | Dez U9=4500 U10=4500 |
| 4 — Evolução mensal, total anual e investido acumulado | Evolucao entradas/saidas/liquido e totais | ✅ aprovado | E39=6000 S39=10000 S40=6000 F41=-500 S41=4000 |
| 4 — Evolução mensal, total anual e investido acumulado | Evolucao investido acumulado (E42=F42=P42=500) e saldo (E43=5000, F43=4500) | ✅ aprovado | E42=500 F42=500 P42=500 E43=5000 F43=4500 |
| 5 — Soma mensal do cartão na coluna U | cartao U17=1200, U18=600, U117=1800 | ✅ aprovado | U17=1200 U18=600 U117=1800 |
| 6 — Cálculo e transporte de saldo das contas | contas H4=1300, I4=1300, L4=1350, AZ4=1350 | ✅ aprovado | H4=1300 I4=1300 L4=1350 AZ4=1350 |
| 7 — Sem #DIV/0!, #REF!, #VALUE!, #NAME? (vazio e com dados) | nenhum erro (#DIV/0!, #REF!...) vazio e com dados | ✅ aprovado | vazio:  | dados:  |

Gráficos (inclui treemaps): **38** · formas/botões: **110** · abas: 16

## ControleFinanceiro_Aprimorado.xlsx — 17/17 aprovados

| Item | Teste | Resultado | Detalhe |
|---|---|---|---|
| 1 — Existência, ordem e nomes das 16 abas | 16 abas na ordem | ✅ aprovado | Início, Contas e Cadastro, Evolução, C.Crédito, Jan, Fev, Mar, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez, Notas |
| 8 — Proteção das abas mantida | protecao mantida nas 16 abas | ✅ aprovado | desprotegidas:  |
| 2 — Totais e porcentagens do mês (dados fictícios) | Jan totais (U5=6000, U6=1500, U7=4500) | ✅ aprovado | U5=6000 U6=1500 U7=4500 |
| 2 — Totais e porcentagens do mês (dados fictícios) | Jan percentuais (I6=83,33%, Q6=80%) | ✅ aprovado | I6=0,833333333333333 Q6=0,8 |
| 2 — Totais e porcentagens do mês (dados fictícios) | linha vazia sem erro (I8 e Q8 = 0%) | ✅ aprovado | I8='0' Q8='0' |
| 3 — Passagem de saldo Jan → Fev → … → Dez | Jan U10 = (U7+U9)-U8 = 5000 | ✅ aprovado | U10=5000 |
| 3 — Passagem de saldo Jan → Fev → … → Dez | Fev U9 = Jan U10 e U10 = 4500 | ✅ aprovado | U9=5000 U10=4500 |
| 3 — Passagem de saldo Jan → Fev → … → Dez | saldo chega a Dez (U9=U10=4500) | ✅ aprovado | Dez U9=4500 U10=4500 |
| 4 — Evolução mensal, total anual e investido acumulado | Evolucao entradas/saidas/liquido e totais | ✅ aprovado | E39=6000 S39=10000 S40=6000 F41=-500 S41=4000 |
| 4 — Evolução mensal, total anual e investido acumulado | Evolucao investido acumulado (E42=F42=P42=500) e saldo (E43=5000, F43=4500) | ✅ aprovado | E42=500 F42=500 P42=500 E43=5000 F43=4500 |
| 5 — Soma mensal do cartão na coluna U | cartao U17=1200, U18=600, U117=1800 | ✅ aprovado | U17=1200 U18=600 U117=1800 |
| 6 — Cálculo e transporte de saldo das contas | contas H4=1300, I4=1300, L4=1350, AZ4=1350 | ✅ aprovado | H4=1300 I4=1300 L4=1350 AZ4=1350 |
| 7 — Sem #DIV/0!, #REF!, #VALUE!, #NAME? (vazio e com dados) | nenhum erro (#DIV/0!, #REF!...) vazio e com dados | ✅ aprovado | vazio:  | dados:  |
| A — Melhorias da versão aprimorada | titulos D2 por mes | ✅ aprovado | JANEIRO,FEVEREIRO,MARÇO,ABRIL,MAIO,JUNHO,JULHO,AGOSTO,SETEMBRO,OUTUBRO,NOVEMBRO,DEZEMBRO |
| A — Melhorias da versão aprimorada | listas suspensas (Validation.Type=3) | ✅ aprovado | F6=3 N55=3 J6=3 R30=3 |
| A — Melhorias da versão aprimorada | conferencia cartao V17=OK, V18=Difere, V117='1 difere(m)' | ✅ aprovado | V17=OK | V18=Difere R$ 300,00 | V117=1 difere(m) |
| A — Melhorias da versão aprimorada | destaques condicionais presentes | ✅ aprovado | Jan!U10=1 Jan!O6=1 Evolução!F41=1 Contas e Cadastro!H4=1 C.Crédito!V18=1 |

Gráficos (inclui treemaps): **38** · formas/botões: **110** · abas: 17

## Diferenças entre as versões

- Gráficos idênticos nas duas: sim (38 × 38).
- Formas/botões idênticos: sim (110 × 110).
- Fiel: cópia byte a byte do original (inclusive o título JANEIRO nas abas Fev–Dez).
- Aprimorada: títulos corrigidos, listas suspensas, destaques, conferência do cartão (coluna V), aba Notas, recálculo ao abrir. Proteção original intacta.

## Limitações declaradas

- O teste visual (cores, mesclagens, larguras, gráficos) foi feito comparando PDFs exportados pelo Excel das duas versões; não há comparação pixel a pixel automática.
- As listas suspensas usam OFFSET para crescer com o cadastro; exigem Excel 2010+.
