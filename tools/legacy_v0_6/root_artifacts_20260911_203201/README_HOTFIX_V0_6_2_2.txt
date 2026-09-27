NÚCLEO IA PORTÁTIL — HOTFIX V0.6.2.2
======================================

PROBLEMA
--------
A Calibração Gráfica podia parecer travada em 82% por vários minutos.

Diagnóstico:
- Qwen3 possui chat template;
- llama-cli pode entrar automaticamente em modo conversa;
- a sonda real fornecia um prompt, gerava a resposta e podia permanecer
  aguardando a próxima entrada;
- o AutoTune só avançava quando atingia o timeout de segurança;
- isso podia repetir o teste em várias quantidades de GPU layers e fazer
  a calibração durar muito mais que o necessário.

CORREÇÃO
--------
A sonda real agora:
- usa --single-turn quando o llama-cli oferece essa opção;
- fecha stdin com DEVNULL;
- continua com o timeout antigo apenas como proteção de segurança.

RESULTADO ESPERADO
------------------
Uma sonda que demorava até o timeout deve encerrar assim que os tokens
de teste forem gerados. O AutoTune também deve conseguir classificar
corretamente a configuração CUDA em vez de tratá-la como timeout.

COMO APLICAR
------------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     APLICAR_HOTFIX_V0_6_2_2.bat

3. Abra:
     INICIAR_NUCLEO_IA.bat

4. Execute:
     Detalhes > Recalibrar computador

Não apague o histórico, os modelos nem o benchmark base.

ROLLBACK
--------
ROLLBACK_HOTFIX_V0_6_2_2.bat
