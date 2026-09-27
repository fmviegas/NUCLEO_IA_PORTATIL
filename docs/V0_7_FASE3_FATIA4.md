# NÚCLEO IA PORTÁTIL — V0.7 Fase 3, fatia 4 (alpha6)

## `validar_modelo.py` — portão de validação de modelo (§25)

**Base:** V0.7.0-alpha5. **Escopo:** novo `tools/validar_modelo.py`,
`VERSION.json`. Só stdlib. **Aditivo** (arquivo novo; não altera o motor).

> Alpha. Base de retorno: V0.6.5 FINAL.

---

### Objetivo

Validar um `.gguf` **antes** de adicioná-lo ao catálogo, cumprindo a §25 do
projeto, **sem executar o modelo** — apenas lendo bytes/cabeçalho.

### Verificações

- existência e tamanho;
- magic + versão GGUF;
- metadados lidos do próprio GGUF (sem carregar pesos): `general.architecture`,
  `<arch>.context_length`, `tokenizer.chat_template`, `general.size_label`;
- arquitetura em lista conhecida (aviso se desconhecida);
- SHA256 (compara com o esperado, informado por `--sha256` ou vindo do registry
  via `--id`);
- nota informativa de compat com llama.cpp `b10516` (não executa — pede
  confirmação real antes de marcar `validated`).

Ao final, imprime uma **sugestão de entrada de registry** (com sha256, contexto
e tier estimado) para o usuário revisar (`roles`, `license`, `requirements`) e
só então marcar `status: validated`.

### Uso

```
runtime\python\python.exe tools\validar_modelo.py <arquivo.gguf> [--sha256 HEX] [--json]
runtime\python\python.exe tools\validar_modelo.py --id <model_id>
```

Código de saída 0 se não houver FALHA; 1 caso contrário.

### Validação feita (fora do Windows real, com os modelos reais)

- 4B: GGUF v3, arch `qwen3`, context_length **40960**, chat template presente,
  SHA256 confere com o registry (`7485fe6f…`).
- 8B (via `--id`): arch `qwen3`, SHA256 confere (`d98cdcbd…`).
- SHA256 errado → FALHA; arquivo não-GGUF → FALHA.

(Bônus: confirmou os dois SHA256 documentados no registry/memória.)

### Observação

Descobrimos que os GGUF Qwen3 anunciam `context_length = 40960`. O NÚCLEO usa
4096 em produção por estabilidade/VRAM; contextos maiores ficam para máquinas
mais fortes (V0.7 portabilidade) — relevante inclusive para o futuro
"Escritor de Livros 360°".

### Rollback

`ROLLBACK_V0_7_A6.bat` restaura `VERSION.json` e **remove**
`tools/validar_modelo.py` (raiz e payload) → volta ao alpha5.
