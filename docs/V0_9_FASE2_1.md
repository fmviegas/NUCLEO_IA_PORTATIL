# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 2.1 (alpha3)

## Outline em LOTES (correção do loop do modelo pequeno)

**Base:** V0.9.0-alpha2. **Escopo:** `app/book/outline.py`, `VERSION.json`.

> Motivada por teste real no Avell: com 28 capítulos pedidos de uma vez, o 4B
> entrou em loop (títulos repetidos: "A Conflita/Decisão/Luta"...) e perdeu a
> contagem (22 → 29 → 32). Correção abaixo.

---

### O que muda

1. **Geração em duas etapas + lotes:**
   - 1ª chamada: só o **cabeçalho** (premissa/estrutura/arco na ficção;
     objetivo/pré-requisitos no técnico) — sem capítulos.
   - depois: capítulos em **lotes de `--lote` (padrão 8)**; cada lote recebe os
     **títulos já usados** com instrução explícita de **não repetir e avançar a
     trama**. Isso quebra o loop do modelo pequeno.
2. **Renumeração no cliente:** os números do modelo são ignorados; o outline sai
   sempre **1..N contíguo** (fim do "22 → 29 → 32").
3. **Marcação de repetição:** títulos duplicados são sinalizados
   `⚠(possível repetição — revise)` e contados no aviso do topo.
4. **`--modo quality` por padrão** (8B): melhor coerência que o 4B para outline.
5. Avisos no topo do arquivo: quantos capítulos saíram de N, repetições, truncamento.

### Comandos (inalterados; novos flags)

```
OUTLINE.bat gerar --dir workspace\livros\<slug> [--modo quality|fast|auto] [--lote 8]
OUTLINE.bat aplicar --dir workspace\livros\<slug>
```

### Validação feita (fora do Windows real)

- `py_compile` OK.
- Parse + renumeração + dedup testados no output ruim real: renumerou 1..N e
  marcou as 2 repetições corretamente.
- A geração em lotes reusa o mesmo `stream_chat` já validado.

### Ainda assim (honestidade)

O 4B/8B são pequenos; mesmo com lotes, um outline de 100k palavras pode sair
raso ou com alguma repetição — daí a marcação. Ganhos maiores virão com um
**modelo maior** (tier AVANÇADO do Catálogo, quando adicionado) e/ou refino
manual. A fatia 3 (escrita capítulo a capítulo) usa o mesmo princípio: pequenos
blocos, contexto enxuto, estado encadeado.

### Rollback

`ROLLBACK_V0_9_A3.bat` restaura `outline.py` (do alpha2) e `VERSION.json`.
