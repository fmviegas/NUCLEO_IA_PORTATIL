NÚCLEO IA PORTÁTIL — V0.7 FASE 1 (alpha1)
Robustez de detecção + perfil versionado
=========================================

ALPHA de desenvolvimento. Base de retorno: V0.6.5 FINAL.

O QUE MUDA (aditivo, retrocompatível)
-------------------------------------
- machine_id() (v1) INALTERADO -> Avell não recalibra.
- machine_fingerprint(): sinais normalizados (diagnóstico + base do v2).
- machine_id_v2(): id estável a ruído (RAM/VRAM arredondadas), guardado ao
  lado do v1 (migração futura, sem quebrar perfis).
- detection_confidence(): high/medium/low.
- detect_safe()/_minimal_hardware(): detecção que nunca derruba o app (CPU-only
  se tudo falhar). engine_manager passa a usar detect_safe().
- Perfil grava profile_schema_version=2 + machine_id_v2 + fingerprint +
  detection_confidence (calibração CLI e gráfica).

ARQUIVOS ALTERADOS
------------------
- app/hardware.py, app/autotune.py, app/engine_manager.py, VERSION.json (0.7.0-alpha1)

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A1.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_A1.bat
4. Reabra INICIAR_NUCLEO_IA.bat -> o Avell NÃO deve recalibrar.

OBS: após instalar, VALIDAR_V0_6_5_FINAL.bat acusará diferença nos 3 arquivos
(esperado — você saiu da baseline 0.6.5 para a linha 0.7).

ROLLBACK
--------
ROLLBACK_V0_7_A1.bat volta para V0.6.5 FINAL (restaura os 3 arquivos +
VERSION.json na raiz E no payload, evitando reaplicação acidental).

VALIDADO (fora do Windows real)
-------------------------------
- py_compile OK; testes de lógica TODOS OK (v1 inalterado por diff; v2 estável;
  confiança high/low; detect_safe não lança; fingerprint arredonda).
- Import conjunto engine_manager+hardware OK.
