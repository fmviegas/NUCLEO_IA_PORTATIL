# NÚCLEO IA PORTÁTIL — V0.6.5.3

## Hotfix: Reaper de engines órfãs (anti-401)

**Base:** V0.6.5.2 (instale a V0.6.5.2 antes).
**Escopo:** `app/engine_manager.py`, `VERSION.json`.
**Sem novas dependências.**

---

### Problema observado em campo

Mensagem no chat:

```
llama-server HTTP 401: {"error":{"message":"Invalid API Key",...}}
```

**Causa raiz:** quando o backend Python encerra de forma suja (fechar janela,
crash, troca de sessão), o `llama-server` continua rodando como processo
**órfão**, segurando a porta 18081 e esperando a **chave efêmera antiga**
(`--api-key`, V0.6.4). A sessão seguinte gera uma chave nova; a requisição
colide com o servidor velho e recebe **401**.

Diagnóstico real capturado:

```
PID 2764  llama-server 8B  porta 18081  (órfão da sessão anterior)
PID 11096 llama-server 4B                (sessão atual)
```

### Correção

Novo método `EngineManager._reap_orphan_servers()`:

- **Windows apenas** (no-op fora dele e em qualquer falha — best-effort).
- Lista processos `llama-server.exe` (via PowerShell `Get-CimInstance`).
- Encerra (`taskkill /PID <pid> /F /T`) apenas os cujo executável está sob a
  pasta `engine\` **deste projeto** — nunca toca em um `llama-server` de outro
  caminho.
- Preserva o processo atual (`self.process.pid`).
- Registra o que encerrou em `logs\v0_6\orphan_reap.log`.

Chamado em dois pontos:

1. **Na inicialização** (`__init__`) — limpa restos de um crash anterior.
2. **No `start()`**, após parar a engine própria e antes de reservar a porta —
   garante porta/chave consistentes a cada (re)início.

### Segurança

- Escopo restrito ao `engine\` do próprio projeto (comparação de caminho).
- Não altera modelos, perfis, sessões ou partições.
- Falha silenciosa: se a varredura não funcionar, o início segue normal.

### Validação feita (fora do Windows real)

- `py_compile` OK no Python portátil 3.13.13.
- Teste unitário da lógica (subprocess mockado): encerra apenas 2764 e 11096
  (engines do projeto), ignora `C:\Outro\llama-server.exe` e entrada sem
  caminho. **RESULTADO: OK.**

Pendente: teste real em Windows (abrir NÚCLEO, trocar de perfil, fechar sujo,
reabrir → não deve mais dar 401).

### Rollback

`ROLLBACK_V0_6_5_3.bat` restaura `engine_manager.py` e `VERSION.json` do backup
técnico. A base V0.6 FINAL CONSOLIDADA permanece intacta.
