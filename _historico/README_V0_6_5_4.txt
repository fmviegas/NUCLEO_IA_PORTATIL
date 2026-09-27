NÚCLEO IA PORTÁTIL — HOTFIX V0.6.5.4
Formulário multi-bloco + classificador por adjacência
========================================

PROBLEMA
--------
A planilha real de precificação ainda saía como coluna_3/coluna_6/"faltantes"
mesmo com a V0.6.5.2, porque ela tem DOIS formulários lado a lado (B/C e E/F).
O classificador via "linhas largas" e chamava de tabela.

CORREÇÃO
--------
- classificador por adjacência rótulo->valor (não por largura);
- extração por BLOCOS de colunas (separa B/C de E/F pela coluna vazia);
- kind por rótulo: horas/dias/% não exibem R$; valor/custo/preço mantêm R$.

ARQUIVOS ALTERADOS
------------------
- app/file_analysis.py
- VERSION.json  (-> 0.6.5.4)

PRÉ-REQUISITO: V0.6.5.2 e V0.6.5.3 já instaladas.

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_6_5_4.bat + payload\ na raiz).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_6_5_4.bat
4. Reabra INICIAR_NUCLEO_IA.bat e reanalise a planilha.

ROLLBACK: ROLLBACK_V0_6_5_4.bat.

VALIDADO (fora do Windows real) contra o arquivo REAL:
4 seções, 22 campos rótulo->valor, moeda/horas/% corretos, fórmulas
associadas. Regressão de tabela CSV: continua tabela.
