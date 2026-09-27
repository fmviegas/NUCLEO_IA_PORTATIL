NÚCLEO IA PORTÁTIL — V0.7 FASE 2 (alpha2)
Fallback CPU sem NVIDIA + modo de simulação
===========================================

ALPHA de desenvolvimento. Base de retorno: V0.6.5 FINAL.

O QUE MUDA
----------
- Sem GPU NVIDIA (real OU simulado) => o motor inicia DIRETO em CPU
  (essencial para rodar em máquina sem NVIDIA). Usa fallback_cpu_threads e
  n-gpu-layers 0.
- Modo de simulação para testar no Avell (que tem GPU):
    * variável NUCLEO_SIMULATE_NO_NVIDIA=1, OU
    * arquivo state\SIMULATE_NO_NVIDIA (use os .bat abaixo).
- Snapshot ganha backend_reason, cuda_available, simulate_no_nvidia.

ARQUIVOS ALTERADOS
------------------
- app/engine_manager.py, VERSION.json (0.7.0-alpha2)

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A2.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_A2.bat
4. Reabra INICIAR_NUCLEO_IA.bat

COMO TESTAR O FALLBACK (no Avell)
---------------------------------
1. SIMULAR_SEM_NVIDIA.bat        (cria o flag)
2. No NÚCLEO: Manutenção -> Reiniciar motor (ou reabra). Deve subir em CPU;
   backend_reason = "simulação sem NVIDIA". Prefira o modo RÁPIDO (4B) — o 8B
   em CPU é lento.
3. RESTAURAR_NVIDIA.bat          (remove o flag) e reinicie o motor -> CUDA.

ROLLBACK
--------
ROLLBACK_V0_7_A2.bat volta para o alpha1 (restaura raiz e payload).

VALIDADO (fora do Windows real)
-------------------------------
- py_compile OK; testes de lógica TODOS OK (env, arquivo-flag e nvidia real).
