# NÚCLEO IA PORTÁTIL — V0.7 Fase 3, fatia 1 (alpha3)

## Catálogo de Modelos — registry + leitura (sem tocar no motor)

**Base:** V0.7.0-alpha2. **Escopo:** novos `config/models_registry.json` e
`app/catalog.py`; `VERSION.json`. Sem dependências novas. **Aditivo** — não
altera calibração nem o motor; nenhum modelo é baixado.

> Alpha de desenvolvimento. Base de retorno: V0.6.5 FINAL.

---

### O que entra

1. **`config/models_registry.json`** — catálogo dos 2 Qwen3 atuais, com
   metadados: `id`, `file`, `sha256`, `license`, `chat_template`, `tier`,
   `roles`, `requirements` (min_ram_gb / min_vram_gb_cuda / cpu_only_ok),
   `status` (só `validated` é oferecido), `llama_cpp_min_build`.

2. **`app/catalog.py`** (somente leitura):
   - `load_registry()` — lê o JSON ou **sintetiza** um padrão se ausente;
     marca `present` conferindo o arquivo em `models/`.
   - `caps_from_hardware(hw, cuda_available)` — extrai `{cuda_available, vram_gb,
     ram_gb, cores}` de um `HardwareInfo`.
   - `viable_models(caps)` — modelos presentes+validados que rodam (cuda OU cpu).
   - `select_roles(caps)` — mapa papel→modelo: `fast` (menor viável fast/light),
     `quality` (maior viável quality; senão cai para o fast, com
     `quality_is_fallback=True`).
   - `get_model(id)`.

### Tiers

Metadados: `LEVE (1.5–3B) · RAPIDO (4B) · QUALIDADE (8B) · AVANCADO (12–14B) ·
PESADO (20B+)`. O tier **LEVE existe no schema** mas só será oferecido quando um
modelo pequeno for realmente validado (§25) — não fabricamos LEVE a partir do 4B.

### Comportamento inalterado

Esta fatia **não** muda o motor nem a calibração. O `catalog.py` é uma camada de
consulta, pronta para as próximas fatias (wire no `autotune` e no AUTO).

### Validação feita (fora do Windows real)

- `py_compile` OK; JSON válido (2 modelos).
- Seleção testada e correta:
  - Avell (cuda, 4GB, 16GB) → fast=4B, quality=8B (sem fallback);
  - CPU-only 8GB → fast=4B, quality=4B (fallback);
  - CPU-only 32GB → fast=4B, quality=8B;
  - CPU-only 4GB → nenhum viável;
  - GPU 2GB, 16GB → ambos via CPU.
- Fallback sintetizado funciona quando o JSON está ausente.

### Diagnóstico rápido (opcional)

```
runtime\python\python.exe app\catalog.py
```
imprime o catálogo, os `caps` do hardware atual e o `select_roles`.

### Rollback

`ROLLBACK_V0_7_A3.bat` restaura `VERSION.json` e **remove** `app/catalog.py` e
`config/models_registry.json` (raiz e payload). Volta ao alpha2.
