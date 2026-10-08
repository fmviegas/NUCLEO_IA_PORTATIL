# 📖 BÍBLIA DO NÚCLEO IA PORTÁTIL

**Documento mestre de continuidade — estado atual e como retomar.**
Última atualização: **2026-09-22**. Autor do projeto: **Fabricio Viegas**.

> Este arquivo é a fonte de verdade para retomar o projeto em qualquer chat/sessão
> nova sem perder contexto. Organizado por TEMA (não por cronologia). O histórico
> detalhado e antigo (até 13/09, V0.9 FINAL) está em
> `NUCLEO_IA_PORTATIL_MEMORIA_PROJETO.md` e nas notas por versão em `docs/`.

---

## 1. O QUE É

**NÚCLEO IA PORTÁTIL** — plataforma de IA **local, portátil e offline** para Windows,
que roda modelos GGUF via **llama.cpp**, com interface web (servida em **127.0.0.1**).
Vive em `E:\NUCLEO_IA_PORTATIL` (cópia de trabalho/dev) e é feito para **caber num
SSD/pendrive e rodar em qualquer Windows** (com driver NVIDIA para GPU; sem NVIDIA,
cai para CPU).

**Princípios (inegociáveis):**
- **Minimalismo funcional:** backend em Python stdlib (sem frameworks, sem banco de
  dados); UI em HTML/CSS/JS puro (sem build no runtime).
- **Offline-first:** nada sai do computador; sem chamadas de nuvem.
- **Estabilidade > pico:** validação de campo real; disciplina staging→validar→consolidar
  com rollback.
- **Honestidade sobre limitações.**

**Estilo do usuário (Fernando):** PT-BR; gosta de honestidade técnica, de validar de
verdade, e de manter a raiz limpa. Aprecia que cada mudança seja testada antes de dar
por concluída.

---

## 2. MÁQUINA DE REFERÊNCIA (a Avell do dev)

- CPU **Intel i5-8300H** (4 físicos / 8 threads, 2.30 GHz)
- **15,88 GB RAM** · GPU **NVIDIA GTX 1050 4 GB** (+ Intel UHD 630)
- **machine_id: `b86b439ce669463f`** (fingerprint da máquina; o perfil é keyed por isso)
- Referências de velocidade: fast(4B) ~18,7 t/s · quality(8B) ~8,3 t/s · advanced(30B) ~5,1 t/s · code(7B) ~6,1 t/s

**Teto de hardware:** ~30B-A3B (IQ3). Modelos generalistas maiores **não rodam** aqui
(a aba Diagnóstico classifica folga/limite/não-roda).

**⚠️ SSD externo E: tem glitches de escrita intermitentes** (já causou: python-docx
corrompido `WinError 1392`, pasta `cuda_corrompido`, arquivos sumindo, arquivo de
memória sobrescrito com bytes de ZIP). Se um arquivo em `runtime/python/Lib/site-packages`
ou similar ficar ilegível → `chkdsk E: /f` + reinstalar/recopiar. Manter backup fora do E:.

---

## 3. ARQUITETURA (pastas e arquivos-chave)

```
E:\NUCLEO_IA_PORTATIL\
├─ app\                  # backend Python (stdlib)
│  ├─ server.py          # servidor HTTP + rotas /api/* + SSE
│  ├─ engine_manager.py  # sobe/gerencia o llama-server; modos; amostragem anti-loop+DRY
│  ├─ hardware.py        # detecção CPU/RAM/GPU (PowerShell, SEM psutil); machine_id
│  ├─ catalog.py         # lê models_registry; viabilidade/roles por hardware
│  ├─ autotune.py        # calibração base (fast+quality) — precisa app/manifests/manifest_v0_5.json
│  ├─ benchmark.py       # benchmark 4B vs 8B (CPU threads + CUDA ngl)
│  ├─ calibration_manager.py  # roda autotune como subprocesso; progresso (classify_line + creep)
│  ├─ gguf_advisor.py    # consultor GGUF (folga/limite/nao_roda) da aba Diagnóstico
│  ├─ file_analysis.py   # análise de xlsx/csv/txt/md/json/pdf(nativo)/docx
│  ├─ workspace.py       # contexto de arquivos anexados
│  ├─ book\              # PIPELINE do Escritor de Livros 360°
│  │  ├─ book_project.py  # scaffolder 00-08 + BIBLIA por meta (intake do "Novo livro")
│  │  ├─ planner.py       # 18 gêneros, GENRE_TARGETS (metas de tamanho)
│  │  ├─ outline.py       # gera o outline via IA (batched)
│  │  ├─ escrever.py      # escreve capítulo a capítulo (cenas), dedup, EXPANSÃO, ::PROG::
│  │  ├─ revisar.py       # auditoria + humanização + redundância + compila manuscrito
│  │  ├─ publicar.py      # PUBLICAR: .docx/.epub via diagramador; pré-textuais
│  │  ├─ similaridade.py, humanizar.py, livros_index.py
│  ├─ diagramador\       # vendorado: exporta docx/epub (rosto/créditos/dedicatória/prefácio/sumário)
│  └─ manifests\         # manifest_v0_5.json (autotune!) + manifest_v0_9_*_final.json (SHA256)
├─ ui\                   # index.html, app.js, app.css + forja\ (React vendorado) + vendor\
├─ config\               # models_registry.json (catálogo) + personas\ (ficcao/tecnico/humanizacao)
├─ engine\windows\{cpu,cuda}\  # llama-server/cli/bench.exe + DLLs (ggml, cuda, VC++ runtime)
├─ models\               # os GGUF (ver seção 4)
├─ runtime\python\       # Python 3.13 embarcado (traz vcruntime140.dll próprio)
├─ tools\                # validar_v0_9_*.py, calibrar_advanced.py, montar_portatil.py, etc.
├─ profiles\machines\<machine_id>.json   # PERFIL calibrado por máquina
├─ state\, sessions\, logs\, cache\, workspace\livros\   # runtime/estado
├─ backup\               # pre_v0_9_*_final_* (pontos de rollback) — só VERSION.json + ui/index.html
├─ VERSION.json          # versão/features/stage
├─ INICIAR_NUCLEO_IA.bat + lançadores de operação + VALIDAR/ROLLBACK_V0_9_XX
├─ MONTAR_PORTATIL.bat   # monta a cópia portátil num destino
├─ BIBLIA_NUCLEO_IA_PORTATIL.md (este) + NUCLEO_IA_PORTATIL_MEMORIA_PROJETO.md (histórico)
```

**payload/ foi APOSENTADA (V0.9.14):** não existe mais fluxo de instalador; edita-se
direto na raiz, sem sincronizar payload.

---

## 4. MODELOS & MODOS

Catálogo em `config/models_registry.json`. Cada modelo tem id/file/roles/requirements/sha256.
Os **modos** (fast/quality/advanced/code) vêm dos `roles` e são gravados no PERFIL da máquina
pela calibração.

| Modo | Botão | Modelo (GGUF) | Tam | Calibração | Nesta Avell |
|---|---|---|---|---|---|
| **fast** | RÁPIDO | Qwen3-4B-Q4_K_M | 2,4 GB | autotune base | ~18,7 t/s (ngl36) |
| **quality** | QUALIDADE | Qwen3-8B-Q4_K_M | 4,7 GB | autotune base | ~8,3 t/s (ngl27) |
| **advanced** | (só no painel de livros) | Qwen3-30B-A3B-Instruct-2507-IQ3_XXS (MoE 30B/3B) | 12 GB | `calibrar_advanced.py` (à parte) | ~5,1 t/s (ngl12) |
| **code** | CÓDIGO | Qwen2.5-Coder-7B-Instruct-Q4_K_M | 4,4 GB | `calibrar_advanced --mode code` | ~6,1 t/s (ngl12) |
| **(code_hd)** | — (catalogado, inativo) | Qwen2.5-Coder-14B-Instruct-Q5_K_M | 7,5 GB | não calibrado (p/ "super máquina") | roda folga porém lento ~3-4 t/s |

**Detalhes de fiação de um modo:** `_select_key` do engine é GENÉRICO (aceita qualquer
modo do perfil). Para um modo aparecer no chat: (1) registrar no models_registry com um
role; (2) `server.py /api/mode` precisa liberar a chave (whitelist: auto/fast/quality/code);
(3) `engine.public_modes` expõe (fast/quality/code); (4) botão em `index.html`
(`data-mode="X"`); (5) `gateModeButtons()` em app.js esconde o botão se `/api/modes` não
tiver o modo (p/ máquina sem essa calibração). O `advanced` NÃO é botão de chat — é usado
só no painel de livros (dropdown de modo).

**`calibrar_advanced.py` é GENÉRICO** (2026-09-21): `--id <model_id> --mode <chave>
--mode-name <ROTULO> --model-key <label> --ngl-inicial N`. Sonda o modelo por llama-cli,
escolhe o melhor ngl com margem de VRAM, grava o modo no perfil **preservando os outros**
(faz backup automático). Ex.: code foi calibrado com `--id qwen25-coder-7b-q4km --mode code
--mode-name CODIGO --model-key coder-7b --ngl-inicial 24` → ngl=12, 6,1 t/s.

---

## 5. FUNCIONALIDADES (o que o app faz)

**Menu lateral (5 views):**
- **Chat** — streaming; modos AUTO/RÁPIDO/QUALIDADE/CÓDIGO; anexar arquivos; **auto-continuar**
  (emenda ao bater no limite, até 5×, com Parar e checkbox); **exportar** conversa/última
  resposta em .md/.txt e tabela→.csv; histórico local persistente.
- **Escrever Livros** — pipeline completo NO PAINEL: criar (form de fundação → BIBLIA),
  gerar Outline, **escrever capítulo** (escolher específico ou próximo pendente; streaming SSE;
  **barra de progresso por cena**; passo de EXPANSÃO p/ capítulos curtos), Revisar, Publicar
  (.docx/.epub com pré-textuais), Ler. Motor ÚNICO com handoff (pausa o chat, subprocesso
  assume, religa). 18 gêneros com metas de tamanho.
- **Análise de Arquivos** — anexa (xlsx/csv/txt/md/json/pdf-nativo/docx) e pergunta no chat;
  leitura semântica de planilhas, fórmulas auditadas.
- **Forja de Prompts** — gerador de prompts (React vendorado, 100% local, sem nuvem); tema
  âmbar próprio; baixar prompt .md/.txt. **Engenharia reversa de imagem** (2026-09-27):
  `askClaude` manda a imagem (data-URL) de verdade pro `/api/forja`; o servidor troca o
  motor pro modo `vision` (Gemma 3 4B + `--mmproj`), gera com a imagem anexada, e restaura
  o modo anterior do chat no `finally` — mesmo handoff do pipeline de livros. Antes disso
  `askClaude` ignorava a imagem e o modelo (texto puro) inventava uma análise sem relação
  com a foto real. Modelo baixado (`gemma-3-4b-it-Q4_K_M.gguf` 2,49 GB + `mmproj-model-f16.gguf`
  0,85 GB, sha256 no registry, status `validated`) e modo `vision` CALIBRADO na máquina
  b86b439c (CUDA, ngl 18, 12,4 tok/s, ~1,25 GB de folga de VRAM). Falta só: validar em campo
  com foto real na Forja.
- **Diagnóstico** — detecta CPU/RAM/GPU e classifica GGUF em **✅ folga / ⚠️ limite / ⛔ não roda**
  (`gguf_advisor.py`, heurística mmap-aware); relatório .txt baixável. Tabela curada inclui
  modelos de código (tamanhos verificados na API do Hugging Face).

**Tema:** NOTURNO fixo (desde V0.9.15; `:root` escuro + `color-scheme:dark`; claro só via
`data-theme="light"`, sem UI que ative).

**Segurança:** só 127.0.0.1; CSP com `script-src 'self'` e `style-src 'self' 'unsafe-inline'`
(o unsafe-inline é necessário p/ a Forja e estilos dinâmicos da UI — app local, single-user).

---

## 6. VERSIONAMENTO / DISCIPLINA DE CONSOLIDAÇÃO

Cada versão FINAL tem: `VERSION.json` (version/release/features/stage) + manifest SHA256
(`app/manifests/manifest_v0_9_XX_final.json`, ~49-50 arquivos) + validador
(`tools/validar_v0_9_XX_final.py`) + marcador (`state/v0_9_XX_final_install.json`) + backup
(`backup/pre_v0_9_XX_final_*` com VERSION.json + ui/index.html) + lançadores VALIDAR/ROLLBACK.

**Ritual de consolidação:** bump dos rótulos da UI (2 lugares no index.html: `sideFoot` e
`span.version`), VERSION.json (version + consolidated_from + features + stage), escrever o
validador (existência + py_compile + agulhas de código + import de deps + integridade SHA256
do manifest), rodar o backup+manifest+state via script, criar os lançadores, **rodar o
validador (exit 0)**, remover os lançadores da versão anterior (raiz limpa), atualizar a memória.

**Se adicionar ARQUIVO NOVO:** incluir no file-set do manifest E nas listas required/compile
do validador (aconteceu com `gguf_advisor.py` na V0.9.19).

**Armadilhas do fluxo:**
- Hook do PowerShell bloqueia comandos com "Remove-Item"+"/file" (falso positivo) → usar
  python/bash nesses casos.
- NUNCA editar arquivos UTF-8 com PowerShell Get/Set-Content (corrompe UTF-8-sem-BOM) →
  usar Write/Edit ou python/cp. Bumps de rótulo via Edit/python.
- Ao encerrar/reiniciar, avisar o usuário para fechar e reabrir o NÚCLEO (instância em
  memória fica com código velho). Verificar/limpar llama-server **órfãos** (seguram VRAM/log).

**Estado das versões:** V0.6 → V0.9.19 são bases de retorno. Bump de rótulo é só cosmético;
o código é o mesmo dentro da mesma versão.

---

## 7. ESTADO ATUAL (2026-09-30)

> LOCALIZAÇÃO: SSD externo em case USB → a LETRA VARIA (já foi E:, agora **F:**; usuário vai
> fixar em F:). Sempre localizar o projeto por Test-Path em C/D/E/F/G. Backup da Bíblia em
> `D:\Codigos\BIBLIA_NUCLEO_IA_PORTATIL_2026-09-22.md` (disco interno, sempre acessível).

**Consolidado: V0.9.24 FINAL (íntegra; reconsolidada em 2026-10-08).** Bases de retorno
V0.6→V0.9.24. Manifesto = **71 arquivos** (mesma lista da V0.9.23). Rótulo na UI e VERSION.json
= **V0.9.24**. Rollback: `ROLLBACK_V0_9_24.bat` (só rótulo/VERSION). Backup em `backup/pre_v0_9_24_final_*`.

**O QUE ENTROU NA V0.9.24 — FIX DO EXPORTADOR .xlsx (gerador de planilhas REMOVIDO):**
1. **Fix do EXPORTADOR xlsx** (`app/exporters.py`): `_strip_md()` tira `**bold**`/`*it*`/
   `` `code` `` das células e do cabeçalho; `_num()` entende moeda ("R$ 5.000,00"→5000.0) e
   devolve texto limpo quando não é número.
2. **Gerador de planilhas por template — testado e RETIRADO** (2026-10-08, a pedido do usuário:
   "não ficou como pensei"). Saíram `app/planilhas.py`, as rotas `/api/planilhas` e
   `/api/planilhas/gerar`, a aba 📊 Planilhas, o JS (`loadPlanilhas/gerarPlanilha`) e o CSS
   `.plan*`. Código guardado em `_historico/planilhas_v0_9_24_removido.py` (template
   `controle_financeiro_pf` com Lançamentos/Resumo SUMIFS/Categorias/Orçamento) caso a ideia volte
   em outro formato. Motivação original: o modelo recusava criar arquivos ou devolvia tabela com
   placeholders ao pedir planilha no chat.
3. Nota: em 30/09 o rollback da V0.9.24 foi rodado por engano; a reconsolidação acima corrige.

**O QUE ENTROU NA V0.9.23 — EXPORTAR .docx / .xlsx (+ Linux validado):**
1. **Exportação no Chat e na Análise** (a Análise É o próprio chat — o botão só troca p/ a view
   chat e abre o anexo) para **.docx** e **.xlsx**, gerados no SERVIDOR. Novo **`app/exporters.py`**:
   `md_to_docx(md)` via **python-docx** (títulos `#`, listas, negrito/itálico/código inline, e
   TABELAS markdown → tabela do Word); `md_to_xlsx(md)` via **openpyxl** (cada tabela markdown
   vira uma ABA; números pt-BR "1.240,50" → 1240.5; cabeçalho em negrito, freeze_panes; sem tabela
   → despeja o texto). Helper `parse_md_tables`.
2. **Rota `POST /api/export`** (`server.py` → `_export_file`): recebe `{formato,content,titulo}`,
   devolve o BINÁRIO com `Content-Type` correto + `Content-Disposition: attachment`. Formato
   inválido → 400; conteúdo vazio → 400.
3. **UI** (`ui/index.html` menu `#baixarMenu` + `ui/app.js`): novos itens **Conversa (.docx)**,
   **Última resposta (.docx)** e **Tabela → .xlsx** (gateado por `_hasTable`, como o CSV). Helper
   `_exportServer(formato,content,base,titulo)` faz POST + baixa o blob (detecta erro por
   Content-Type JSON). CSP inalterada (geração no servidor).
4. **openpyxl 3.1.5** adicionado: runtime Windows (`runtime/python`, viaja no `montar_portatil`)
   e venv Linux (`linux/setup/03_python.sh`, `PORTATIL_LINUX.md`, `montar_linux.py`, diagnóstico).
   VERSION.json `runtime_deps` += openpyxl. RECOMPILAR não é preciso (só Python).
   TESTADO (Windows): `/api/export` 200 (docx 36 KB, xlsx 5 KB, CT certo, inválido→400); arquivos
   abrem válidos (docx com tabela; xlsx com número); menu no DOM; console limpo.
5. **Linux validado em campo** (2026-09-27) — feature-flag `linux_field_validated` (ver nota abaixo).
6. **Selados refinamentos do usuário** em `app/server.py` (+2 KB) e `ui/forja/forja.js` (+764 B),
   feitos ~27/09 em outra sessão (rodou calibração no mesmo dia). Verificado: SEM rotas novas no
   server; `forja.nucleo.tsx` (fonte) consistente com o build. NÃO catalogados em detalhe — se
   precisar, perguntar ao usuário o que mudou.

**O QUE ENTROU NA V0.9.22 — FORJA NOVA + SETUP LINUX:**
1. **Forja de Prompts redesenhada** (a partir da `forja-de-prompts-NOVO.tsx` do usuário — um
   redesign CLARO). Gerada `forja-de-prompts/forja.nucleo.tsx` com as 4 adaptações do NÚCLEO:
   (a) `import React` → `const {…} = React` (UMD global); (b) `askClaude()` do conector
   `window.claude` → `POST /api/forja` (não-streaming); (c) sem `@import` do Google Fonts
   (fontes do sistema); (d) `export default App` → `function App` + `window.__mountForja`.
   Mais: **conversão de paleta CLARA→ESCURA** (mapa determinístico ~17 tokens; PRESERVA de
   propósito o preview de HQ: papel branco/calhas pretas `#111`/`#333`/`#d9d3c6`/`bg-white`).
   Compilado: **esbuild** → `ui/forja/forja.js`, **tailwindcss@3** (config `tailwind.config.js`
   aponta p/ `forja.nucleo.tsx`, preflight off) → `ui/forja/forja.css`. Node v25 + npx.
   TESTADO no navegador (Windows): tema escuro coerente, console limpo (sem CSP), `POST
   /api/forja 200`, geração real de prompt OK. Reverse/visão mantém paridade (texto via
   /api/forja; sem multimodal local). Backup pré-troca: `backup/pre_forja_novo_*`.
2. **`linux/setup/`** selado (era drift da V0.9.21): 5 scripts numerados 00–04 + LEIA-ME
   (ver bloco de setup na seção 8-LINUX/abaixo).

Para RECOMPILAR a Forja no futuro (a partir de `forja-de-prompts/forja.nucleo.tsx`):
`cd forja-de-prompts && npx esbuild forja.nucleo.tsx --jsx=transform --jsx-factory=React.createElement --jsx-fragment=React.Fragment --format=esm --target=es2020 --outfile=../ui/forja/forja.js`
e `npx tailwindcss@3.4.17 -c tailwind.config.js -i tw-input.css -o ../ui/forja/forja.css`.

**O QUE ENTROU NA V0.9.21 — PORTA LINUX (camada plat.py):**
1. **`app/plat.py`** — fonte ÚNICA do layout do motor por SO. Windows resolve
   `engine/windows/<backend>/llama-*.exe` (IDÊNTICO à V0.9.20); Linux resolve
   `linux/engine/<backend>/llama-*` (sem sufixo). Funções: `engine_root/engine_dir/engine_exe/engine_exe_rel/engine_bin_names`, `IS_WINDOWS`, `EXE_SUFFIX`.
2. **6 pontos com `.exe` fixo agora passam por `plat`**: `engine_manager._server_exe`,
   `autotune` (sonda CUDA + perfil CPU), `benchmark` (perfil/required/bench), `chat.build_cmd`,
   `maintenance_manager` (engine_root + listas de binários), `hardware.detect_engine`.
3. **Calibração destravada p/ Linux**: removidos os `if os.name != "nt": return` de
   `autotune.main` e `benchmark.main`; `detect_windows()` → `detect_safe()` (despacha por SO).
4. **Nova pasta raiz `linux/`** (tudo do Linux num lugar): `engine/{cpu,cuda}/LEIA-ME.txt`
   (binários a colocar), `nucleo.sh`, `calibrar.sh`, `montar_linux.py`, `PORTATIL_LINUX.md`,
   `LEIA-ME.txt`. Ver seção 8-LINUX.
5. **Windows inalterado** (verificado: identidade de caminhos via plat + compile + import dos
   7 módulos). **Linux VALIDADO EM CAMPO (2026-09-27)** — ver nota abaixo. Passo a passo
   completo em `linux/PORTATIL_LINUX.md`; configuração via `linux/setup/` (V0.9.22).

**TESTE EM CAMPO — Windows (2026-09-22): ✅ APROVADO.** Fechado e reaberto o NÚCLEO na
máquina de referência (i5-8300H/GTX1050-4GB). Resultados: servidor no ar em
`http://127.0.0.1:18080` (porta 18080), `GET /` HTTP 200 exibindo **V0.9.21**; `/api/status`
= `ready`, perfil disponível, `machine_id b86b439ce669463f`, confiança alta; `POST /api/mode
{"mode":"fast"}` → HTTP 200, backend **cuda**, modelo Qwen3-4B. **Prova da camada `plat.py`
em runtime:** o `engine.start` subiu `llama-server.exe` a partir de
`engine\windows\cuda\llama-server.exe` (resolvido por `plat.engine_exe`, ngl 36). **Geração
confirmada:** chat "olá, teste rápido" → resposta coerente em **2,6 s / 23 deltas** (SSE OK).
Servidor encerrado de forma limpa (processos python+llama-server = 0, porta 18080 liberada).
Conclusão: no Windows o comportamento é idêntico ao da V0.9.20, agora sob o rótulo V0.9.21.

**TESTE EM CAMPO — LINUX no SSD externo (2026-09-27): ✅ APROVADO (relato do usuário).** A
porta Linux foi validada numa instalação Linux real no SSD externo: configuração feita com os
scripts `linux/setup/`, motor `llama.cpp` em `linux/engine/`, e o NÚCLEO rodou de fato. Marco
que derruba a antiga ressalva "Linux não testado em máquina real". DETALHE A CONFIRMAR com o
usuário: backend usado (CPU vs CUDA/GPU) e se a calibração automática da 1ª vez rodou limpa —
registrar aqui quando ele informar. Camada `plat.py` (resolução de motor por SO) e os scripts
de setup comprovados na prática.

**O QUE ENTROU NA V0.9.20 (histórico, consolidado):**
1. **Barra de progresso da calibração** — `calibration_manager.py`: `_creep_from_config_line`
   (barra anda +1% a cada config medida) + reconhece o probe do 30B.
2. **`tools/montar_portatil.py` + `MONTAR_PORTATIL.bat`** — monta cópia portátil (ver seção 8).
3. **Perfis pré-semeados** no montar_portatil (copia `profiles/machines/*.json`).
4. **VC++ runtime empacotado** em `engine/windows/{cpu,cuda}` (ver seção 8).
5. **Modo CÓDIGO** (Qwen2.5-Coder-7B) — registrado, calibrado, testado, com botão gateado.
6. **14B-Coder catalogado** (role code_hd, inativo).
7. Config: `models_registry.json`, `server.py` (whitelist code), `engine_manager.py`
   (public_modes code), `app.js`/`index.html` (botão + gate), `calibrar_advanced.py` (generalizado).

**Próximo:** porta Linux CONCLUÍDA e validada em campo (2026-09-27). Itens abertos para escolher
(seção 10): Forja visão local (multimodal Qwen2-VL/MiniCPM-V + `--mmproj`); refinos do escritor
(epígrafe dedicada, truncamento por prioridade, bug do fence ``` ); portátil bootável mínimo.
Housekeeping: confirmar backend do teste Linux (CPU/GPU) e, se quiser, criar um validador
Linux-específico (checa `linux/engine/<backend>/llama-*` + `plat`, sem exigir `.exe`/DLLs).

**PORTA LINUX — resumo de execução (ver `linux/PORTATIL_LINUX.md` para detalhe):**
- Opção recomendada: instalação Linux COMPLETA no SSD externo (partição EFI + raiz **ext4** —
  ext4 não tem o limite de 4 GB/arquivo do FAT32, os GGUF de 12 GB cabem). Boota em qualquer PC.
- Motor Linux: `engine/linux` NÃO é usado; o motor Linux fica em **`linux/engine/{cpu,cuda}/`**
  (o `plat.py` resolve lá). Binários: release Linux do llama.cpp OU compilar (`-DGGML_CUDA=ON`).
- Python: backend é stdlib; publicar precisa de `.venv` com docx/ebooklib/lxml/pypdf.
- Montagem: `linux/montar_linux.py` copia app/ui/config/tools/models + a pasta `linux/` inteira;
  EXCLUI engine/windows, runtime/python, *.bat/*.dll/*.exe/*.ps1. Rode NO LINUX (destino ext4).

**SCRIPTS DE SETUP LINUX (2026-09-24) — `linux/setup/` (drift pós-V0.9.21, ainda NÃO no manifesto):**
Criados para configurar a aplicação no Linux passo a passo (o usuário montou o Linux no SSD e
travou em erros de permissão/link). São 5 scripts numerados + LEIA-ME, todos em **LF, sintaxe
`bash -n` OK**; o `montar_linux.py` já os leva (copia `linux/` inteira, não exclui `.sh`):
- `00_diagnostico.sh` — read-only; checa SO, **filesystem do projeto** (alerta se exFAT/NTFS/vfat/
  fuseblk → não guardam +x nem symlink = CAUSA #1 dos erros), presença de app/server.py + linux/
  nucleo.sh, python3/venv/unzip, GPU (nvidia-smi/nvcc), **CRLF nos .sh** (CAUSA #2), binários do
  motor, .venv + libs, pastas de trabalho. Rodar PRIMEIRO e colar a saída se pedir ajuda.
- `01_preparar.sh` — `sed -i 's/\r$//'` nos .sh (mata CRLF), cria pastas de trabalho, `chmod +x`
  scripts+binários, `chown` p/ usuário se estiver como root, avisa se FS não mantém +x.
- `02_binarios.sh` — coloca llama.cpp em `linux/engine/{cpu,cuda}/`. Padrão: BAIXA CPU do release
  oficial (acha asset ubuntu-x64 via API GitHub + python3, copia .so junto). `--build` compila do
  fonte (cmake, `-DGGML_NATIVE=ON`); `--build --cuda` compila CUDA (precisa driver + nvcc). CUDA
  pronto p/ Linux quase nunca existe em release → GPU = compilar.
- `03_python.sh` — cria `.venv` e instala python-docx/ebooklib/lxml/pypdf (só p/ PUBLICAR).
- `04_iniciar.sh` — preflight (plat resolve motor; binário executa via `LD_LIBRARY_PATH=engine dir`
  p/ achar .so; libs) e então `exec linux/nucleo.sh`. `--check` só verifica.
- As DUAS CAUSAS recorrentes (documentadas em `linux/setup/LEIA-ME.txt` e `linux/LEIA-ME.txt`):
  **#1 projeto em exFAT/NTFS** (mover p/ ext4: `cp -a . ~/NUCLEO`); **#2 CRLF do Windows** nos .sh.
Backup de origem: `D:\Codigos\NUCLEO_LINUX_SETUP\` (staging enquanto o E: esteve offline; fonte de
verdade agora é `linux/setup/`). A SELAR quando validado no Linux real → **consolidar V0.9.22**.

---

## 8. PORTÁTIL (montar_portatil) — como e armadilhas

**`MONTAR_PORTATIL.bat`** (interativo: pede letra + tier, faz dry-run, confirma) ou
`python tools/montar_portatil.py --dest F:\NUCLEO_IA_PORTATIL --modelos all [--dry-run]`.

**Copia SÓ o essencial** (INCLUDE: app, ui, config, runtime, engine, tools + lançadores de
operação + VERSION.json + modelos do tier). **EXCLUI:** backup, _historico, docs,
forja-de-prompts (fonte), __pycache__, validadores de versão, e QUALQUER caminho com
"corrompido"/"_bak"/".bak". **Cria pastas de trabalho vazias** e **pré-semeia os perfis**
(profiles/machines/*.json). Grava `PORTATIL.txt`.

**Tiers:** `min`(só 4B ~4,6GB) · `fast`(4B+8B ~9GB) · `code`(4B+8B+coder ~14GB) ·
`all`(4B+8B+30B+coder ~24GB) · `none`.

**⚠️ ARMADILHAS CRÍTICAS (todas já resolvidas, mas ficar atento):**
1. **FAT32 não serve** — o GGUF de 30B (12GB) e o de 8B (4,7GB) estouram o limite de 4GB/arquivo.
   Formatar o destino em **exFAT** (recomendado) ou NTFS. O script recusa FAT32 com arquivo >4GB.
2. **VC++ Redistributable** — os binários do motor (llama-*.exe) são MSVC e precisam de
   `VCRUNTIME140.dll` + `MSVCP140.dll` (& cia). Máquina limpa não tem → erro "não pode
   continuar". **JÁ EMPACOTADO** dentro de `engine/windows/{cpu,cuda}` (copiado do System32:
   vcruntime140[_1].dll, msvcp140[_1,_2,_atomic_wait,_codecvt_ids].dll, concrt140.dll,
   vcomp140.dll). O montar_portatil os inclui (estão em engine/). (O Python embarcado já traz
   o próprio vcruntime140.)
3. **manifest_v0_5.json** — o `autotune.py` importa `app/manifests/manifest_v0_5.json` no topo;
   sem ele a máquina nova NÃO calibra. montar_portatil **inclui** app/manifests (não excluir!).
4. **USB 2.0 vs 3.0 / pendrive vs SSD** — o llama.cpp lê o GGUF via mmap; em pendrive lento o
   30B trava. **Preferir SSD** (o dev migrou p/ SSD em F:; cópia de ~19,6GB levou ~14min).

**Cópia atual no SSD (F:):** feita com --modelos all + sincronizada depois com o **modo CÓDIGO**
(coder GGUF SHA256 conferido íntegro + arquivos do modo + perfil com 4 modos). Na Avell sobe
na hora (perfil pré-semeado); em máquina nova calibra (ver seção 9).

---

## 9. CALIBRAÇÃO (como funciona e tempos)

- **base (fast+quality):** `autotune.py` roda `benchmark.py` (4B/8B em CPU t=4/6/8 + CUDA vários
  ngl) + sondas reais. **Numa máquina nova = ~10 min** (medido). Reusa cache
  `state/calibration/comparison_v0_4.json` SE for da mesma máquina (então na mesma máquina são só
  ~51s de re-sonda). Escreve `profiles/machines/<machine_id>.json`.
- **advanced (30B) e code (7B):** calibrados À PARTE por `calibrar_advanced.py` (sonda dirigida,
  sem o benchmark completo). Adicionam o modo ao perfil preservando os outros.
- **⚠️ Rodar autotune SOBRESCREVE o perfil e remove advanced/code** (ele só refaz fast+quality).
  Se precisar recalibrar a base, **fazer backup do perfil** e re-adicionar advanced/code depois.
- **"Novo computador detectado"** numa cópia portátil é ESPERADO/correto (machine_id novo →
  profiles/ não casa → calibra na 1ª vez). O botão CÓDIGO fica **gateado** (some) até calibrar
  `code` naquela máquina.
- A **barra de progresso** agora anda continuamente (creep por config) e mostra etapa/tempo —
  resolve a percepção de "travado" que fez o usuário cancelar antes.

---

## 10. ITENS ABERTOS / ROADMAP

- **[EM CAMPO] Teste do portátil em máquina nova** — validar que, com as VC++ DLLs, a
  calibração passa da sonda e conclui. (Antes falhava por DLL faltando.)
- **[A FAZER] Consolidar V0.9.20** (ver seção 7).
- Escrever no painel: escolher regenerar cena específica; barra de progresso intra-cena
  (streaming token-a-token — hoje é por cena).
- **[EM CAMPO] Forja: visão local (modo `vision`, Gemma 3 4B + mmproj) baixada, validada e
  calibrada — falta só o teste com foto real na Forja; ver seção 5.**
  Vendorar fontes DM Mono/Archivo Black (offline).
- Publish: campo de EPÍGRAFE dedicado (hoje usar a dedicatória).
- Análise: OCR p/ PDF escaneado (adiado — pesa na portabilidade).
- Escrever: truncamento da bíblia é corte seco em MAX_BIBLE(2800) → futuro truncamento por
  prioridade de campo. Fence ``` sem fechar em alguns caps (artefato do modelo). Testar Q3_K_M.
- Ativar **CÓDIGO HD** (14B) numa máquina melhor: `calibrar_advanced --id qwen25-coder-14b-q5km
  --mode code_hd --mode-name "CODIGO HD"` + liberar code_hd no whitelist/public_modes/botão.
- **Calibração "lite"** opcional (pular 30B / menos configs) p/ encurtar em máquina nova (com a
  barra andando, ficou opcional).

---

## 11. LIÇÕES & ARMADILHAS RECORRENTES

- **SSD externo E: instável** (glitches de escrita). chkdsk + recopiar quando um arquivo ficar
  ilegível. Backup fora do E:.
- **llama-server órfão** segura VRAM/log e causa ConnectionReset em testes → matar antes
  (`taskkill //IM llama-server.exe //F`) e checar `netstat` nas portas 1808x.
- **GTX 1050 4 GB** é o gargalo: duas instâncias disputando travam. Antes de subir instância de
  teste, checar se a do usuário está de pé.
- **Console cp1252**: prints com emoji/acentos podem dar UnicodeEncodeError no meu terminal —
  é só o print, o arquivo/UTF-8 está certo. Usar `sed 's/[^[:print:]]//g'` para ler logs.
- **Caminho F: em Python (Windows)**: `Path('/f/...')` vira `\f\...` (errado). Usar `F:/...`.
- Botões da UI têm `title=` → o find do navegador acha pelo title, não só pelo texto.

---

## 12. COMO RETOMAR NUM NOVO CHAT

1. Ler esta Bíblia inteira (é a fonte de verdade atual).
2. Conferir o estado real: `VERSION.json` (versão consolidada) e `git`? não há git — usar os
   marcadores `state/` e `backup/`.
3. Confirmar a máquina: `python app/hardware.py`? ou subir o NÚCLEO e ver o Diagnóstico.
4. Antes de mexer, **fechar instâncias abertas** e checar órfãos (netstat/tasklist).
5. Seguir a **disciplina de consolidação** (seção 6) para qualquer mudança.
6. Próximo passo provável: **validar o portátil na outra máquina** e **consolidar a V0.9.20**.

> Memória persistente do Claude (auto-memory) e este arquivo são fontes redundantes.
> Em caso de divergência, **este arquivo + VERSION.json + o código valem** (a auto-memory
> reflete o que era verdade quando foi escrita).
