# NÚCLEO IA PORTÁTIL — V0.6 FINAL

## Estado

A V0.6 consolida a Interface Local em uma única base estável.

Princípio oficial: **Minimalismo funcional** — máximo de recursos para a IA,
mínimo para a interface.

## Entregas consolidadas

- Interface local em HTML/CSS/JavaScript puro.
- Backend Python portátil, sem frameworks web externos.
- `llama-server` controlado pelo NÚCLEO.
- Modos AUTO, RÁPIDO e QUALIDADE.
- Streaming de respostas e interrupção de geração.
- Histórico local em JSON e recuperação da última sessão.
- Calibração gráfica de computadores conhecidos e novos.
- Heartbeat/tempo de calibração.
- AutoTune com sonda real `single-turn`.
- Cadeia UTF-8 corrigida no Windows.
- Diagnóstico e manutenção pela interface.
- Fallback manual/automático para CPU.
- Reparo de motores CPU/CUDA usando apenas o cache local.
- Visualização de logs recentes.
- Prevenção de segunda instância carregando outro modelo.
- Segurança local reforçada e acesso restrito a `127.0.0.1`.

## Validação no Avell

Machine ID: `b86b439ce669463f`

Resultado recente da calibração:

- RÁPIDO — Qwen3-4B-Q4_K_M — ~19.3 t/s
- QUALIDADE — Qwen3-8B-Q4_K_M — ~7.9 t/s
- AUTO — RÁPIDO

## Dados preservados por atualização

A atualização não apaga:

- `models\`
- `engine\`
- `profiles\`
- `sessions\`
- `cache\`
- `logs\`
- `state\`

## Próxima fronteira

A V0.6 encerra a fase de Interface Local. A próxima grande etapa pode ser
tratada separadamente, sem alterar esta base consolidada.
