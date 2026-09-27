NÚCLEO IA PORTÁTIL — HOTFIX V0.6.2.1
======================================

PROBLEMA
--------
Durante a Calibração Gráfica, benchmark.py podia falhar no Windows com:

  UnicodeEncodeError: 'charmap' codec can't encode character '\u0394'

Causa:
- a calibração executa Python com stdout redirecionado;
- nesse cenário o Windows pode selecionar CP1252;
- o benchmark imprimia o símbolo grego Delta (Δ), que não existe em CP1252.

CORREÇÃO
--------
1. benchmark.py deixa de depender do símbolo Δ e usa texto ASCII.
2. calibration_manager.py força:
     PYTHONIOENCODING=utf-8
     PYTHONUTF8=1
   para AutoTune, benchmark e demais processos Python filhos.
3. O log da calibração passa a preservar corretamente caracteres UTF-8.

COMO APLICAR
------------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     APLICAR_HOTFIX_V0_6_2_1.bat

3. Abra:
     INICIAR_NUCLEO_IA.bat

4. Vá a:
     Detalhes > Recalibrar computador

Não é necessário apagar perfil, histórico, modelos ou benchmark anterior.

ROLLBACK
--------
ROLLBACK_HOTFIX_V0_6_2_1.bat
