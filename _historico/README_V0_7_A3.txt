NÚCLEO IA PORTÁTIL — V0.7 FASE 3 fatia 1 (alpha3)
Catálogo de Modelos (registry + catalog.py, só leitura)
=======================================================

ALPHA. NÃO altera o motor nem a calibração. Base de retorno: V0.6.5 FINAL.

NOVOS ARQUIVOS
--------------
- config/models_registry.json  (catálogo dos 2 Qwen3, com metadados)
- app/catalog.py               (load_registry / viable_models / select_roles)
VERSION.json -> 0.7.0-alpha3

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A3.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_A3.bat  (valida compile + JSON + seleção).
4. Diagnóstico opcional: runtime\python\python.exe app\catalog.py

ROLLBACK
--------
ROLLBACK_V0_7_A3.bat restaura VERSION.json e remove os arquivos novos
(raiz e payload). Volta ao alpha2.

VALIDADO (fora do Windows real)
-------------------------------
- compile OK; JSON válido; seleção correta em 5 cenários (Avell, CPU 8/32GB,
  4GB, GPU 2GB); fallback sintetizado quando o JSON está ausente.
