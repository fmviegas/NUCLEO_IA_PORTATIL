# NÚCLEO IA PORTÁTIL — V0.7 Fase 3, fatia 2 (alpha4)

## Calibração dirigida pelo Catálogo (perfil schema v3)

**Base:** V0.7.0-alpha3. **Escopo:** `app/autotune.py`, `app/catalog.py`,
`config/models_registry.json`, `VERSION.json`. Sem dependências novas. Aditivo.

> Alpha. Base de retorno: V0.6.5 FINAL. Só afeta uma **nova calibração**;
> perfis existentes continuam válidos e o motor não muda de comportamento.

---

### O que muda

1. **`autotune.py` passa a calibrar a partir do catálogo**, não mais dos
   `4b/8b` fixos:
   - carrega o registry + calcula `caps` do hardware real;
   - para cada modelo `present && validated && viável`, calibra o papel dele
     (`fast`/`quality`) usando o benchmark correspondente (`bench_key`);
   - **numa máquina onde o QUALIDADE (8B) não cabe, ele é PULADO** (log
     explícito) em vez de falhar — o ganho concreto de portabilidade.
2. **`config/models_registry.json`** ganha `bench_key` (`4b`/`8b`) ligando cada
   modelo ao pipeline de benchmark atual.
3. **Perfil schema v3:** `profile_schema_version: 3`, `catalog_version`, e
   `model_ids` (mapa papel→id, ex.: `{"fast":"qwen3-4b-q4km","quality":"qwen3-8b-q4km"}`);
   cada modo também grava `model_id`.

### Comportamento no Avell (sem regressão)

Ambos os modelos são viáveis → calibra `fast`(4B) e `quality`(8B), exatamente
como antes. A única diferença observável é o perfil mais rico (schema v3 +
`model_ids`).

### Validação feita (fora do Windows real)

- `py_compile` OK (`autotune.py`, `catalog.py`); registry com `bench_key` válido.
- Lógica de seleção testada:
  - Avell (cuda,4GB,16GB) → {fast:4B, quality:8B};
  - CPU-only 8GB → {fast:4B} (QUALIDADE **pulado**);
  - CPU-only 32GB → {fast:4B, quality:8B}.

### Como fechar o teste em campo

No NÚCLEO: **Detalhes → Recalibrar computador** (uma vez). Depois, conferir o
perfil salvo em `profiles/machines/<machine_id>.json`:
- `profile_schema_version` = 3;
- `catalog_version` presente;
- `model_ids` = `{"fast":"qwen3-4b-q4km","quality":"qwen3-8b-q4km"}`;
- comportamento AUTO/RÁPIDO/QUALIDADE inalterado.

### Limitações conhecidas (próximas fatias)

- O **benchmark** (`benchmark.py`) ainda roda `4b` e `8b` sempre; o "pular
  QUALIDADE" acontece na CALIBRAÇÃO, não no benchmark. Gating do benchmark por
  viabilidade é uma fatia futura (evita benchmarkar 8B em máquina fraca).
- O **motor/AUTO ainda não usa `model_ids`** para trocar de modelo por hardware
  (próxima fatia: wire no `engine_manager`). Esta fatia só registra.

### Rollback

`ROLLBACK_V0_7_A4.bat` restaura `autotune.py`, `catalog.py`,
`models_registry.json` e `VERSION.json` (raiz e payload) → volta ao alpha3.
