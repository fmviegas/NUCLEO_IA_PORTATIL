# NÚCLEO IA PORTÁTIL — V0.7 Fase 1 (alpha1)

## Robustez de detecção e perfil versionado

**Base:** V0.6.5 FINAL. **Escopo:** `app/hardware.py`, `app/autotune.py`,
`app/engine_manager.py`, `VERSION.json`. Sem novas dependências. Aditivo e
retrocompatível — perfis antigos continuam válidos.

> Alpha de desenvolvimento (não é release estável). A base de retorno continua
> sendo V0.6.5 FINAL.

---

### Objetivo da Fase 1

Preparar o terreno para a portabilidade multi-máquina (V0.7) endurecendo a
detecção de hardware e versionando o perfil — **sem** alterar a identidade da
máquina já validada (Avell `b86b439ce669463f`).

### O que muda

1. **`machine_id()` (v1) INALTERADO.** Confirmado por diff — o hash do Avell é
   preservado; nenhuma recalibração é forçada.
2. **`machine_fingerprint(hw)`** — sinais normalizados (fabricante, modelo, CPU,
   RAM inteira, arquitetura, GPUs com VRAM inteira). Diagnóstico + base do v2.
3. **`machine_id_v2(hw)`** — id **estável a ruído** de detecção (RAM/VRAM
   arredondadas, strings normalizadas). Prefixo `v2_`. É **armazenado ao lado**
   do v1 no perfil; ainda **não** substitui o nome do arquivo de perfil. É a
   base para uma migração futura sem invalidar perfis existentes.
4. **`detection_confidence(hw)`** — `high | medium | low` conforme os campos-
   chave detectados. Confiança baixa sinaliza risco de o id divergir do id
   "cheio" da mesma máquina (ex.: PowerShell/WMI indisponível). Exposto no
   snapshot; registrado em `last_error` (não bloqueia).
5. **`detect_safe()` + `_minimal_hardware()`** — detecção que **nunca lança**:
   se o detector da plataforma falhar, cai para um `HardwareInfo` mínimo
   (CPU-only, só stdlib). O `engine_manager` passa a usar `detect_safe()`.
6. **Perfil versionado** — `autotune.py` grava `profile_schema_version: 2`,
   `machine_id_v2`, `machine_fingerprint` e `detection_confidence` no perfil.
   Cobre tanto a calibração por linha de comando quanto a **gráfica** (que
   executa `autotune.py`).

### Segurança / compatibilidade

- Nada removido; só campos e funções novas. Perfis antigos (sem
  `profile_schema_version`) continuam carregando normalmente.
- `machine_id` v1 idêntico → sem recalibração indevida no Avell.
- `detect_safe` é usado só para não derrubar o app; a detecção normal continua
  sendo a primária.

### Validação feita (fora do Windows real)

- `py_compile` OK nos 3 módulos.
- Testes de lógica: v1 inalterado (diff vazio); v2 estável a ruído RAM/VRAM;
  v2 distingue máquinas; confiança high/low; `detect_safe` não lança mesmo com
  o detector falhando; fingerprint arredonda. **TODOS OK.**
- Import conjunto `engine_manager`+`hardware` OK.

### Pendente (teste real em Windows)

- Reabrir o NÚCLEO e confirmar que o Avell **não** recalibra (id v1 estável).
- Conferir no snapshot/menu os campos `machine_id_v2` e `detection_confidence`.
- (Fase 2) fallback direto para CPU quando não houver NVIDIA/CUDA.

### Observação sobre o VALIDAR_V0_6_5_FINAL

Este alpha altera 3 arquivos que faziam parte do manifesto da V0.6.5 FINAL.
Portanto, após instalar o 0.7-alpha1, `VALIDAR_V0_6_5_FINAL.bat` vai acusar
diferença nesses 3 arquivos — **é esperado** (você saiu da baseline 0.6.5 para
a linha 0.7). Para voltar à baseline, use `ROLLBACK_V0_7_A1.bat`.

### Rollback

`ROLLBACK_V0_7_A1.bat` restaura `hardware.py`, `autotune.py`,
`engine_manager.py` e `VERSION.json` do backup técnico. V0.6.5 FINAL volta a
ser o estado corrente.
