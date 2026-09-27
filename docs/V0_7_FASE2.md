# NÚCLEO IA PORTÁTIL — V0.7 Fase 2 (alpha2)

## Fallback CPU sem NVIDIA + modo de simulação

**Base:** V0.7.0-alpha1 (Fase 1). **Escopo:** `app/engine_manager.py`,
`VERSION.json`. Sem novas dependências. Aditivo.

> Alpha de desenvolvimento. Base de retorno: V0.6.5 FINAL.

---

### O que muda

1. **Não tenta CUDA quando não há NVIDIA.** Antes, o `start()` tentava o
   backend do perfil (cuda) e só então caía para CPU. Agora, se não houver GPU
   NVIDIA detectada (ou a simulação estiver ativa), o NÚCLEO inicia **direto em
   CPU** — essencial para portabilidade (perfil calibrado em máquina CUDA
   rodando numa máquina CPU-only). O caminho CPU usa `fallback_cpu_threads` e
   `n-gpu-layers 0` (já suportado pelo `_build_command`).

2. **Modo de simulação "sem NVIDIA".** Para testar o fallback no próprio Avell
   (que tem GPU), sem precisar de uma segunda máquina. Ativação (relida a cada
   início do motor — toggle a quente):
   - variável de ambiente `NUCLEO_SIMULATE_NO_NVIDIA=1`; **ou**
   - arquivo vazio `state\SIMULATE_NO_NVIDIA` (crie para simular; apague para
     restaurar). Os .bat `SIMULAR_SEM_NVIDIA` / `RESTAURAR_NVIDIA` fazem isso.

3. **Transparência no snapshot.** Novos campos: `backend_reason`
   ("conforme perfil" / "sem GPU NVIDIA detectada" / "simulação sem NVIDIA" /
   "CPU forçado (manutenção)"), `cuda_available`, `simulate_no_nvidia`.

### Como testar no Avell (com GPU)

1. Instale o alpha2.
2. Ligue a simulação: rode `SIMULAR_SEM_NVIDIA.bat` (cria o flag).
3. Abra o NÚCLEO (ou, se já aberto, troque de modo / reinicie o motor pela
   Manutenção). O motor deve subir em **CPU**, com `backend_reason` =
   "simulação sem NVIDIA". Espere geração mais lenta (8B em CPU é pesado; o
   4B/RÁPIDO é mais viável).
4. Desligue a simulação: `RESTAURAR_NVIDIA.bat` e reinicie o motor → volta a
   CUDA.

> Observação: a simulação afeta apenas a ESCOLHA de backend. O fallback real em
> uma máquina sem NVIDIA usará o mesmo caminho de código.

### Limitações (próximas fatias da Fase 2)

- Ainda **não** há "níveis de hardware" (LEVE/intermediário/forte) escolhendo
  modelo/contexto conforme a máquina. Rodar o 8B em CPU fraca será lento; a
  seleção automática de modelo por hardware entra na próxima fatia + Catálogo
  de Modelos (Fase 3).
- Sem catálogo, o CPU-only usa o mesmo modelo do perfil (só muda o backend).

### Validação feita (fora do Windows real)

- `py_compile` OK.
- Testes de lógica: `_cuda_available` respeita nvidia real; simulação por env e
  por arquivo liga/desliga corretamente; sem flag volta a CUDA. **TODOS OK.**

### Pendente (teste real)

- No Avell: simular sem NVIDIA → motor sobe em CPU (RÁPIDO) e responde;
  restaurar → volta a CUDA.

### Rollback

`ROLLBACK_V0_7_A2.bat` restaura `engine_manager.py` e `VERSION.json` (raiz e
payload) para o estado anterior (V0.7.0-alpha1).
