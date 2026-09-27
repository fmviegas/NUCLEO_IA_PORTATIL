# NÚCLEO IA PORTÁTIL — V0.7 FINAL

## Estado

A V0.7 consolida a **Portabilidade Real** sobre a V0.6.5 FINAL. Continua
Windows-hospedeiro (boot autônomo é V0.8). Sem dependências novas.

Princípio oficial: **Minimalismo funcional**.

## Consolida (alphas 1–6)

- **alpha1** — detecção defensiva (`detect_safe`) + identidade estável
  (`machine_id_v2`, `machine_fingerprint`, `detection_confidence`) + perfil
  versionado;
- **alpha2** — fallback CPU quando não há NVIDIA (real ou simulado) + modo de
  simulação (`SIMULATE_NO_NVIDIA`);
- **alpha3** — Catálogo de Modelos (`config/models_registry.json` + `catalog.py`,
  leitura);
- **alpha4** — calibração dirigida pelo catálogo + perfil **schema v3**
  (`model_ids`); QUALIDADE é pulado quando não cabe;
- **alpha5** — motor resolve o modelo por `model_id` (fallback ao campo legado);
- **alpha6** — `validar_modelo.py` (portão de validação §25, sem executar o
  modelo) + saída UTF-8.

## Entregas (além da V0.6.5 FINAL)

- `machine_id` v1 preservado (Avell `b86b439ce669463f`) — sem recalibração forçada.
- Início à prova de crash: nunca fica sem `HardwareInfo` (cai para CPU-only).
- Fallback CPU automático sem NVIDIA; simulável no Avell.
- Catálogo de modelos com metadados (sha256, licença, tier, roles, requirements).
- Seleção papel→modelo por hardware; perfil grava `model_ids`.
- Portão de validação de GGUF (magic, metadados, SHA256) antes de adicionar modelo.

## Validação em campo (Avell — `b86b439ce669463f`)

- RÁPIDO — Qwen3-4B-Q4_K_M — ~18.7 t/s
- QUALIDADE — Qwen3-8B-Q4_K_M — ~6.1 t/s
- AUTO — RÁPIDO
- Perfil schema v3 gravado; fallback CPU confirmado por simulação
  (llama-server.log: cuda→cpu com o flag ativo).

## Integridade

`app/manifests/manifest_v0_7_final.json` guarda SHA256 + tamanho de 20 arquivos
de código/UI. Rode `VALIDAR_V0_7_FINAL.bat` a qualquer momento.

## Itens em aberto (não bloqueiam a release)

- **Teste multi-máquina real** (2ª/3ª máquina) — objetivo final da portabilidade;
  até lá, a simulação cobre o caminho CPU.
- **Modelo LEVE real** — baixar + validar (§25) um modelo pequeno para habilitar
  o tier LEVE em máquinas fracas.
- Opcional: gating do `benchmark.py` por viabilidade.

## Dados preservados

Modelos, perfis, sessões, workspace, logs e calibração permanecem locais e não
são tocados por instalação/rollback.

## STATUS

**ESTÁVEL / BASE DE RETORNO** (junto com V0.6 FINAL e V0.6.5 FINAL).
