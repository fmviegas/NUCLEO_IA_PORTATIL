NÚCLEO IA PORTÁTIL — PATCH V0.6.5.2
Leitura Semântica de Planilhas
========================================

O QUE MUDA
----------
Planilhas do tipo FORMULÁRIO/CALCULADORA (seções, pares rótulo->valor,
subtotais) passam a ser entendidas semanticamente, e não mais como uma
tabela genérica.

Antes:  coluna_3 / 12000 / 5 / 6 / 0.7 / "valores faltantes"
Agora:  SEÇÃO 1 — SUAS METAS E CARGA HORÁRIA
        - Quanto quer ganhar por mês?: R$ 12.000,00 [B2]
        - Dias por semana: 5 [B3]
        - Percentual faturável: 70% [B5]

Planilhas tabulares normais continuam funcionando como antes.

ARQUIVOS ALTERADOS
------------------
- app/file_analysis.py   (classificador + extrator de formulário + formatos)
- app/workspace.py       (prompt: NÚCLEO calcula sim; só não recalcula Excel)
- VERSION.json           (0.6.5.1 -> 0.6.5.2)

Sem novas dependências (apenas stdlib: zipfile + xml.etree).

INSTALAÇÃO
----------
1. Copie a pasta deste patch para dentro de E:\NUCLEO_IA_PORTATIL
   (de modo que INSTALAR_V0_6_5_2.bat e a pasta payload\ fiquem na raiz
    do projeto, ao lado de app\, runtime\, VERSION.json).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_6_5_2.bat
4. Reabra INICIAR_NUCLEO_IA.bat
5. Anexe a planilha Calculo Precificação-V01.xlsx e peça:
   "Faça uma análise desta planilha."

O instalador cria backup técnico automático em:
   backup\pre_v0_6_5_2_files_<data_hora>\

ROLLBACK
--------
Execute ROLLBACK_V0_6_5_2.bat para voltar ao estado anterior a V0.6.5.2.
A base V0.6 FINAL CONSOLIDADA permanece intacta como ponto de retorno.

VALIDAÇÃO JÁ FEITA (fora do Windows real)
-----------------------------------------
- py_compile OK no Python portátil 3.13.13 do projeto.
- Teste funcional com XLSX-calculadora sintético: todos os 10 critérios
  de sucesso da seção 30 da memória passaram.
- Teste de regressão: planilha tabular continua classificada como tabela.

PENDENTE (só você pode fazer)
-----------------------------
- Teste REAL em Windows com a planilha original de precificação.
  Enquanto isso não ocorrer, a V0.6.5.2 NÃO é "final consolidada".
