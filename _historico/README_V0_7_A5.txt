NÚCLEO IA PORTÁTIL — V0.7 FASE 3 fatia 3 (alpha5)
Motor resolve o modelo por id (catálogo em runtime)
===================================================

ALPHA. Base de retorno: V0.6.5 FINAL. Retrocompatível com perfis v2.

O QUE MUDA
----------
- engine_manager._resolve_model_path(): resolve o arquivo do modelo pelo
  model_id (catálogo); se faltar id/registro/arquivo, cai para o campo legado
  'model' (perfis v2). Fecha o ciclo catálogo->calibração->motor.
- snapshot e public_modes expõem o model_id ativo.
- import do catalog é opcional (try/except).

ARQUIVOS ALTERADOS
------------------
- app/engine_manager.py, VERSION.json (0.7.0-alpha5)

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A5.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_A5.bat
4. Reabra e alterne RÁPIDO/QUALIDADE; Detalhes mostra o model_id ativo.

NO AVELL: sem regressão (resolve para os mesmos Qwen3-4B/8B).

ROLLBACK
--------
ROLLBACK_V0_7_A5.bat volta ao alpha4 (restaura raiz e payload).

VALIDADO (fora do Windows real)
-------------------------------
- compile OK; _resolve_model_path por id / legado / id-invalido->legado: OK.
