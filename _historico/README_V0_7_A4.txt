NÚCLEO IA PORTÁTIL — V0.7 FASE 3 fatia 2 (alpha4)
Calibração dirigida pelo Catálogo (perfil schema v3)
====================================================

ALPHA. Só afeta uma NOVA calibração; motor e perfis atuais não mudam.
Base de retorno: V0.6.5 FINAL.

O QUE MUDA
----------
- autotune.py calibra a partir do catálogo (não mais 4b/8b fixos):
  calibra só modelos present+validated+viáveis; QUALIDADE (8B) é PULADO
  quando não cabe no hardware (em vez de falhar).
- config/models_registry.json ganha bench_key (4b/8b).
- Perfil schema v3: profile_schema_version=3, catalog_version, model_ids
  (mapa papel->id) e model_id por modo.

ARQUIVOS ALTERADOS
------------------
- app/autotune.py, app/catalog.py, config/models_registry.json,
  VERSION.json (0.7.0-alpha4)

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A4.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_A4.bat
4. (para ver o efeito) Reabra e faça: Detalhes -> Recalibrar computador.
   Depois confira profiles\machines\<machine_id>.json:
     profile_schema_version=3, catalog_version, model_ids.

NO AVELL: sem regressão (ambos viáveis -> fast:4B, quality:8B).

ROLLBACK
--------
ROLLBACK_V0_7_A4.bat volta ao alpha3 (restaura raiz e payload).

VALIDADO (fora do Windows real)
-------------------------------
- compile OK; seleção testada: Avell {fast,quality}; CPU-only 8GB {fast}
  (QUALIDADE pulado); CPU-only 32GB {fast,quality}.
