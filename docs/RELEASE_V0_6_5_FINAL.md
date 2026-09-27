# NÚCLEO IA PORTÁTIL — V0.6.5 FINAL

## Estado

A V0.6.5 consolida a **Análise Local com leitura semântica de planilhas** em
uma única base estável, sobre a V0.6 FINAL.

Princípio oficial: **Minimalismo funcional**. Sem novas dependências — apenas
stdlib (`zipfile` + `xml.etree`) para XLSX.

## Consolida

- 0.6.5 — anexos e análise determinística de arquivos (XLSX/CSV/TXT/MD/JSON);
- 0.6.5.1 — orçamento de conclusão + detecção de `finish_reason` (anti-truncamento);
- 0.6.5.2 — leitura semântica: tabela × formulário, seções, pares rótulo→valor,
  formato numérico, fórmula associada ao rótulo; correção do prompt de cálculo;
- 0.6.5.3 — reaper de engines órfãs (corrige `401 Invalid API Key`);
- 0.6.5.4 — formulário multi-bloco + classificador por adjacência rótulo→valor.

## Entregas consolidadas (além da V0.6 FINAL)

- Anexos locais por sessão (`workspace/sessions/<id>/uploads`).
- Extração determinística: linhas, colunas, soma, média, mín, máx, frequência.
- XLSX lido como ZIP/XML (sem macros, sem recálculo do motor do Excel).
- Classificação automática **tabela × formulário/calculadora**.
- Formulários **multi-bloco** (colunas lado a lado) extraídos por bloco.
- Seções + pares rótulo→valor com coordenada preservada (`C15`).
- Formato numérico interpretado (moeda / percentual / inteiro / decimal / data / hora).
- Fórmulas lidas e associadas ao rótulo mais próximo (nunca recalculadas).
- Vazio estrutural diferenciado de dado ausente.
- Reaper automático de `llama-server` órfão (chave efêmera / porta).

## Validação em campo (Avell — machine ID `b86b439ce669463f`)

- RÁPIDO — Qwen3-4B-Q4_K_M — ~19.3 t/s
- QUALIDADE — Qwen3-8B-Q4_K_M — ~7.9 t/s
- AUTO — RÁPIDO
- `Calculo Precificação-V01.xlsx` (2 formulários lado a lado):
  4 seções, 22 campos rótulo→valor, moeda/horas/% corretos, fórmulas associadas.

## Integridade

`app/manifests/manifest_v0_6_5_final.json` guarda SHA256 + tamanho dos arquivos
de código/UI. Rode `VALIDAR_V0_6_5_FINAL.bat` a qualquer momento para conferir.

## Dados preservados por atualização

Modelos, perfis, sessões, workspace, logs e estado de calibração permanecem
locais e não são tocados por instalação/rollback.

## Pendências conhecidas (não bloqueiam a release)

- Teste de estresse do reaper (fechar sujo → reabrir sem 401).
- Ordem das seções agrupada por bloco (1,3,2,4), não numérica.
- `_effective_kind` (moeda×unidade) é heurístico por palavra-chave PT-BR.

## STATUS

**ESTÁVEL / BASE DE RETORNO** (junto com a V0.6 FINAL).
