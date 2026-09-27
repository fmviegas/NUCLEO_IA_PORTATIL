NÚCLEO IA PORTÁTIL — V0.6.3
================================

FOCO
----
Manutenção e Recuperação pela Interface.

Princípio mantido:
  MINIMALISMO FUNCIONAL

NOVO NA INTERFACE
-----------------
Botão "Manutenção" com diagnóstico de:

- motor CUDA;
- motor CPU;
- modelos locais;
- cache usado para reparo;
- backend atualmente em uso.

AÇÕES
-----
Reiniciar motor
  Reinicia o llama-server com o modo atual.

Usar CPU agora
  Força CPU apenas durante a execução atual do NÚCLEO.
  O perfil salvo não é alterado.

Usar backend do perfil
  Remove o fallback manual e volta ao comportamento normal
  AUTO / RÁPIDO / QUALIDADE.

Reparar CUDA
  Usa exclusivamente:
    cache\downloads\llama-b10516-bin-win-cuda-12.4-x64.zip
    cache\downloads\cudart-llama-bin-win-cuda-12.4-x64.zip

Reparar CPU
  Usa exclusivamente:
    cache\downloads\llama-b10516-bin-win-cpu-x64.zip

POLÍTICA DE REPARO
------------------
- nenhuma conexão com a internet;
- nenhum modelo é modificado;
- nenhum perfil é apagado;
- nenhuma partição é alterada;
- a pasta antiga do motor é preservada como backup;
- o novo motor é validado antes de ser ativado;
- llama-cli --version é executado após o reparo no Windows.

LOGS
----
O painel pode mostrar os trechos recentes de:
- llama-server.log
- calibration.log
- maintenance.log

COMO INSTALAR
-------------
1. Extraia este ZIP em:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     INSTALAR_V0_6_3.bat

3. Abra:
     INICIAR_NUCLEO_IA.bat

4. Clique:
     Manutenção

TESTE SEGURO SUGERIDO
---------------------
Não é necessário corromper nenhum arquivo para testar a V0.6.3.

1. Abra Manutenção e confirme:
     CUDA       OK
     CPU        OK
     Modelos    OK

2. Clique "Usar CPU agora".
   O chat deve voltar usando CPU.

3. Envie uma mensagem curta.

4. Clique "Usar backend do perfil".
   No Avell calibrado, o NÚCLEO deve voltar a CUDA.

5. Teste "Reiniciar motor".

6. Abra "Ver logs recentes".

Os botões Reparar CUDA/CPU devem ser usados principalmente quando o
diagnóstico indicar problema. Não recomendamos provocar corrupção
artificial em um SSD com dados importantes.

BASE
----
Esta versão pressupõe a V0.6.2.2 já validada.
Ela NÃO sobrescreve:
- app\autotune.py (hotfix single-turn permanece);
- app\benchmark.py (hotfix UTF-8 permanece);
- app\calibration_manager.py (hotfix UTF-8 permanece);
- sessions\;
- profiles\.

ROLLBACK
--------
ROLLBACK_V0_6_3.bat
