# NÚCLEO IA PORTÁTIL — V0.7 Fase 3, fatia 3 (alpha5)

## Motor resolve o modelo por id (catálogo em runtime)

**Base:** V0.7.0-alpha4. **Escopo:** `app/engine_manager.py`, `VERSION.json`.
Sem dependências novas. Aditivo e retrocompatível.

> Alpha. Base de retorno: V0.6.5 FINAL.

---

### O que muda

1. **`_resolve_model_path(mode)`** — o motor passa a resolver o arquivo do
   modelo pelo `model_id` (via `catalog.get_model`), procurando em `models/`.
   Se o `model_id` faltar, o registro não existir, ou o arquivo não estiver
   presente, **cai para o campo legado `model`** — 100% compatível com perfis
   v2 (sem `model_id`).
2. **`_build_command`** usa `_resolve_model_path` em vez de `self.root /
   profile["model"]`.
3. **Snapshot e `public_modes`** expõem o `model_id` ativo (transparência p/ UI).
4. Import do `catalog` é **opcional** (`try/except`): se ausente, o motor segue
   pelo caminho legado.

Isto **fecha o ciclo** catálogo → calibração (`model_ids`) → motor.

### Comportamento no Avell (sem regressão)

O perfil recalibrado (schema v3) tem `model_id` por modo; a resolução por id
aponta para os mesmos `Qwen3-4B/8B` de sempre. Nenhuma mudança observável além
do `model_id` aparecer no snapshot.

### Validação feita (fora do Windows real)

- `py_compile` OK.
- `_resolve_model_path` testado:
  - por `model_id` → arquivo do catálogo (mesmo com `model` legado quebrado);
  - sem `model_id` → caminho legado;
  - `model_id` inexistente → fallback para o legado.

### Pendente (teste real)

- Reabrir o NÚCLEO, alternar RÁPIDO/QUALIDADE; conferir no snapshot/Detalhes o
  `model_id` ativo e que a geração funciona normalmente (sem regressão).

### Próximas fatias da Fase 3/4

- `tools/validar_modelo.py` (portão de validação — §25);
- (decisão à parte) adicionar um modelo LEVE real e habilitar o tier;
- opcional: gating do `benchmark.py` por viabilidade (não benchmarkar modelo
  inviável em máquina fraca).

### Rollback

`ROLLBACK_V0_7_A5.bat` restaura `engine_manager.py` e `VERSION.json`
(raiz e payload) → volta ao alpha4.
