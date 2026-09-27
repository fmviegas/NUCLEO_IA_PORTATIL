# NÚCLEO IA PORTÁTIL
## Memória Mestre do Projeto

> ⚠️ **DOCUMENTO HISTÓRICO, CONGELADO em 2026-09-13.** Cobre V0.1 até V0.9 FINAL.
> Para o estado atual do projeto (V0.9.20 em diante), leia primeiro
> `BIBLIA_NUCLEO_IA_PORTATIL.md` — ela é a fonte de verdade vigente e substitui
> as instruções de bootstrap das seções 0 e 32 deste arquivo. Este documento
> permanece como registro do histórico detalhado V0.1→V0.9.

**Última atualização:** 2026-09-13  
**Documento:** Memória técnica oficial / checkpoint de continuidade  
**Estado atual do desenvolvimento:** V0.9 FINAL consolidada (Escritor de Livros 360°)  
**Bases estáveis consolidadas:** V0.6 FINAL · V0.6.5 FINAL · V0.7 FINAL · V0.9 FINAL  
**Próximo passo:** (opcional) fatia 5 UI · modelo AVANÇADO no catálogo · teste multi-máquina

> Raiz do E: limpa (103→15 arquivos); instaladores/rollbacks/READMEs já usados
> movidos para `E:\NUCLEO_IA_PORTATIL\_historico\` (reversível). Na raiz ficam só:
> INICIAR, VERSION.json, este .md, lançadores (CRIAR_LIVRO/PLANO_LIVRO/OUTLINE/
> ESCREVER/HUMANIZAR/REVISAR/VALIDAR_MODELO/SIMULAR_SEM_NVIDIA/RESTAURAR_NVIDIA),
> VALIDAR_V0_9_FINAL e ROLLBACK_V0_9_FINAL.

> ⚠️ **Localização:** este `.md` mestre vive em `E:\NUCLEO_IA_PORTATIL\`. A pasta
> `D:\Codigos\NUCLEO IA` foi removida; `D:\Downloads\...md` é a cópia original
> (pré-sessão). Notas por versão em `E:\NUCLEO_IA_PORTATIL\docs\`.
>
> ⚠️ **Integridade (2026-09-13):** este arquivo já foi encontrado CORROMPIDO uma
> vez (sobrescrito com bytes de ZIP — provável cross-link durante a escrita dos
> ZIPs de ~9 GB na raiz do E:). O CÓDIGO estava íntegro (validador V0.7: 19/20
> SHA256 ok; só VERSION mudou por ser 0.9). Recomendado: `chkdsk E: /scan` e
> manter backup fora do E:. A memória persistente (Claude) e `E:\docs` são
> fontes redundantes.

---

# ★ ESTADO ATUAL CONSOLIDADO (2026-09-13) — SUPERSEDE menções antigas de "estado/próximo passo"

As seções históricas (a partir da nº 0) valem como registro; onde disserem
"estado = V0.6.5.1 / próximo = V0.6.5.2", vale este bloco.

## Bases estáveis (pontos de retorno)
1. **V0.6 FINAL** — Interface Local. 2. **V0.6.5 FINAL** — Análise Local Semântica.
3. **V0.7 FINAL** — Portabilidade Real. (validadores: `VALIDAR_V0_6_5_FINAL.bat`, `VALIDAR_V0_7_FINAL.bat`)

## Linha 0.6.5.x (→ V0.6.5 FINAL)
0.6.5.1 anti-truncamento · 0.6.5.2 leitura semântica de planilhas · 0.6.5.3 reaper
de llama-server órfão (anti-401) · 0.6.5.4 formulário multi-bloco. Validado com
`Calculo Precificação-V01.xlsx`.

## Linha 0.7 (→ V0.7 FINAL)
alpha1 `detect_safe`+`machine_id_v2`+perfil versionado · alpha2 fallback CPU sem
NVIDIA + simulação (`state\SIMULATE_NO_NVIDIA`) · alpha3 catálogo (`config/models_registry.json`+`app/catalog.py`)
· alpha4 calibração via catálogo + perfil schema v3 (`model_ids`) · alpha5 motor
resolve modelo por id · alpha6 `tools/validar_modelo.py` (§25). Consolidação:
manifest 20 arquivos SHA256, UI `V0.7`. **Abertos:** teste multi-máquina real;
modelo LEVE real. GGUF Qwen3 anunciam contexto 40960 (produção usa 4096).

## V0.9 — Escritor de Livros 360° (EM ANDAMENTO)
- **fatia 1 (alpha1):** `config/personas/` (ficcao_360/tecnico_360/humanizacao +
  exemplos/) e `app/book/` — `book_project.py` (scaffolder **00–08 universal** por
  gênero), `planner.py` (metas→capítulos×orçamento), `humanizar.py` (linter anti-IA:
  A1–A12 + 14 sinais). Lançadores CRIAR_LIVRO/PLANO_LIVRO/HUMANIZAR.bat. Livros em
  `workspace\livros\<slug>`.
- **fatia 2 (alpha2):** `app/book/outline.py` + `OUTLINE.bat` — outline via LLM
  (prompt compacto: bíblia + brief de gênero + humanização; persona completa não
  cabe em 4096). Subcomandos gerar/prompt/aplicar.
- **fatia 2.1 (alpha3):** teste real (4B) loopou → geração em **lotes** + títulos
  já usados + renumeração no cliente + `--modo quality` (8B) padrão.
- **fatia 2.2 (alpha4):** teste real (8B) melhorou muito, mas cada lote fechava um
  arco → **ritmo por ato** por lote ("não conclua antes do cap N"); parser remove
  prefixo "Capítulo N —"; warning maxsplit corrigido. **A instalar/testar no Avell.**
- **Princípio:** livro = pipeline capítulo a capítulo (4096 não segura o livro);
  coerência via resumo encadeado (`04_CAPITULOS/RESUMOS/`) + bíblia; humanização é
  ferramenta determinística. Fontes do autor: `I:\AI\MD\`.
- **fatia 3 (alpha5):** `app/book/escrever.py` + `ESCREVER.bat` — escrita
  capítulo a capítulo. Contexto enxuto (bíblia + ficha do cap + **resumo
  encadeado** dos anteriores + humanização); gera prosa **em cenas** (~900
  palavras/chamada, continuando do trecho anterior) até ~90% do orçamento;
  salva `04_CAPITULOS/cap_NN.md` + `RESUMOS/cap_NN.md`; atualiza o PLANO.
  Comandos: `capitulo`/`proximo`/`resumo`.
- **fatia 3.1 (alpha6):** teste real do cap_01 (8B) — prosa coerente mas com
  refrão repetido ~6x e contradições. Correção determinística: **corte de refrão**
  (frases ≥8 palavras repetidas >2x — 11 cortadas no cap_01 real) + **dedup de
  parágrafos** (Jaccard≥0.82) + tail 280→140 + prompt "avance/não repita".
  Contradições de continuidade NÃO são resolvidas por isto (dependem de modelo
  maior + revisão da fatia 4). **A instalar/testar.**
- **fatia 4 (alpha7):** `app/book/revisar.py` + `REVISAR.bat` — revisão/compilação
  determinística. `auditar` (nomes×bíblia → 🚨 nome do protagonista trocado;
  grafias divergentes; conflito dia/noite; tempos divergentes → `07_REVISAO/AUDITORIA.md`),
  `humanizar` (linter em todos os capítulos → `PASSE_HUMANIZACAO.md`), `compilar`
  (`08_PUBLICACAO/MANUSCRITO.md` + contagem), `tudo`. Validado no cap_01 real
  (pegou "Luís 28x vs bíblia Lucas" e dia/noite). **A instalar/testar.**
- **Próxima fatia:** 5 aba "Livros" na UI (opcional). Núcleo do Escritor 360°
  (fatias 1–4) completo: scaffolder → outline → escrita cap-a-cap → revisão/compilação.

## Fluxo de patch (cuidado conhecido)
Instalador copia o `E:\payload` INTEIRO sobre a raiz — ao editar código/UI,
atualizar TAMBÉM no `payload`. `.bat` que roda python com acentos: `chcp 65001` +
`PYTHONUTF8=1`.

---

## 0. INSTRUÇÃO PARA CONTINUIDADE EM NOVOS CHATS

Este documento é a **memória técnica oficial do projeto NÚCLEO IA PORTÁTIL**.

Ao iniciar uma nova conversa:

1. Leia este documento inteiro antes de propor alterações.
2. Respeite a última versão validada em campo.
3. Não regrida decisões técnicas já aprovadas sem motivo concreto.
4. Diferencie sempre:
   - ideia;
   - projeto;
   - build;
   - validação estática;
   - teste real em Windows;
   - versão estável.
5. Não altere modelos, engines, perfis, partições ou dados persistentes sem necessidade.
6. Preserve sempre rollback, compatibilidade e possibilidade de retorno à versão estável.
7. Não trate benchmark sintético como prova de estabilidade em chat real.
8. O princípio oficial de UX é **Minimalismo funcional**.
9. Serviços locais devem ficar restritos a `127.0.0.1`.
10. Não exponha cadeia de pensamento dos modelos.
11. Continue sempre a partir da seção **ESTADO ATUAL**.
12. Quando uma nova versão for validada em campo, atualize este documento.

---

# 1. VISÃO DO PROJETO

O **NÚCLEO IA PORTÁTIL** é uma plataforma de IA local e portátil cujo objetivo é viver em um dispositivo externo e se adaptar automaticamente ao hardware do computador hospedeiro.

A ideia central é:

- o dispositivo externo carrega modelos, runtimes, perfis, aplicação e dados;
- o computador hospedeiro fornece CPU, RAM e GPU;
- o NÚCLEO detecta o hardware;
- identifica a máquina;
- reaproveita um perfil já conhecido;
- ou calibra automaticamente uma máquina nova;
- escolhe a configuração adequada;
- inicia a IA local;
- disponibiliza uma interface gráfica leve;
- preserva sessões, perfis e histórico.

No futuro, o mesmo dispositivo poderá operar em dois modos:

### Modo Hospedeiro
Usa o Windows ou outro sistema já instalado no computador.

### Modo Autônomo
O próprio dispositivo inicializa um Linux leve e executa o NÚCLEO sem depender do sistema operacional do host.

---

# 2. PRINCÍPIOS OFICIAIS DO PROJETO

## 2.1 Portabilidade real

O projeto não deve depender de:

- letra fixa de unidade;
- instalação prévia de Python;
- instalação manual de bibliotecas;
- caminhos absolutos desnecessários;
- configuração manual por máquina, quando isso puder ser automatizado.

## 2.2 Minimalismo funcional

Princípio oficial introduzido na fase V0.6.

Objetivo:

> Maximizar recursos disponíveis para a IA e minimizar o custo da interface e da infraestrutura.

Diretrizes:

- HTML/CSS/JS puros;
- fontes do sistema;
- sem Electron;
- sem frameworks pesados se não houver benefício claro;
- sem animações decorativas desnecessárias;
- sem efeitos visuais custosos;
- painel técnico apenas sob demanda;
- polling moderado de RAM/VRAM;
- Python stdlib sempre que possível;
- dependências adicionais somente quando trouxerem valor real.

## 2.3 Segurança local

- Bind apenas em `127.0.0.1`.
- Não expor serviços para a LAN por padrão.
- Internet não é requisito para funcionamento normal.
- Arquivos anexados não devem executar macros, scripts ou código automaticamente.
- Reparos de engine devem ser locais, seletivos e reversíveis.
- Nunca formatar ou reparticionar o SSD principal sem planejamento explícito e backup.

## 2.4 Estabilidade acima de pico

Regra aprendida em campo:

> “Cabe na VRAM” não significa “roda bem na VRAM”.

O sistema deve priorizar configuração estável para chat real e não apenas melhor número de benchmark.

---

# 3. MÁQUINA DE REFERÊNCIA VALIDADA

Máquina principal usada nos testes de campo:

- **Sistema:** Windows 11 Pro build 26100
- **Notebook:** Avell High Performance 1513-5 BS
- **Placa-mãe:** GI5CN5E
- **CPU:** Intel Core i5-8300H @ 2.30 GHz
- **Núcleos físicos:** 4
- **Threads lógicas:** 8
- **RAM:** aproximadamente 16 GB
- **Arquitetura:** x64
- **Firmware:** UEFI
- **Secure Boot:** habilitado
- **GPU integrada:** Intel UHD 630
- **GPU dedicada:** NVIDIA GTX 1050
- **VRAM:** 4 GB
- **Driver NVIDIA:** 581.57

### Machine ID persistente

```text
b86b439ce669463f
```

Esse ID deve continuar sendo reconhecido sem recalibração sempre que possível.

---

# 4. DISPOSITIVO EXTERNO PRINCIPAL

SSD externo usado como base do NÚCLEO:

- unidade atual observada: `E:`
- sistema de arquivos: NTFS
- label histórico: `Backup_Projetos`
- bridge: Realtek RTL9210B-CG
- interface: USB
- mídia: SSD
- tabela: MBR
- capacidade aproximada: 489 GB
- não é disco de sistema
- não é disco de boot no estágio atual

### Benchmark de porta USB

Foi detectada diferença importante entre portas:

- porta ruim: aproximadamente 34 MB/s
- porta boa: aproximadamente 354 MB/s de escrita

Conclusão:

> O desempenho do armazenamento externo depende fortemente da porta USB usada.

---

# 5. RAIZ DEFINITIVA DO PROJETO

Raiz oficial atual:

```text
E:\NUCLEO_IA_PORTATIL
```

Não usar número de versão no nome da pasta principal.

Estrutura de referência:

```text
NUCLEO_IA_PORTATIL\
├── INICIAR_NUCLEO_IA.bat
├── VERSION.json
├── app\
│   ├── nucleo.py
│   ├── chat.py
│   ├── autotune.py
│   ├── benchmark.py
│   ├── hardware.py
│   ├── server.py
│   ├── engine_manager.py
│   ├── sessions.py
│   ├── calibration_manager.py
│   ├── maintenance_manager.py
│   ├── file_analysis.py          # V0.6.5+
│   ├── workspace.py              # V0.6.5+
│   └── manifests\
├── engine\
│   └── windows\
│       ├── cpu\
│       └── cuda\
├── models\
├── runtime\
│   └── python\
├── profiles\
│   └── machines\
├── sessions\
├── workspace\                    # V0.6.5+
│   └── sessions\
├── config\
├── state\
├── cache\
│   └── downloads\
├── logs\
├── tools\
├── docs\
└── backup\
```

---

# 6. RUNTIME PYTHON

Python portátil adotado na V0.5:

- **CPython 3.13.13 embeddable AMD64**

URL histórica:

```text
https://www.python.org/ftp/python/3.13.13/python-3.13.13-embed-amd64.zip
```

SHA256:

```text
8766a8775746235e23cf5aee5027ab1060bb981d93110577adcf3508aa0cbd55
```

Objetivo:

> O NÚCLEO deve funcionar sem exigir Python instalado no Windows hospedeiro.

---

# 7. LLAMA.CPP / ENGINE

Build adotada:

- llama.cpp Windows x64
- build: `b10516`
- CPU runtime
- CUDA 12.4 runtime

O projeto mantém engines separadas:

```text
engine\windows\cpu\
engine\windows\cuda\
```

## Regras

- CUDA é preferencial quando a máquina suporta.
- CPU fallback deve continuar sempre disponível.
- Reparos usam apenas ZIPs/cache locais quando possível.
- Reparos nunca devem tocar:
  - modelos;
  - perfis;
  - partições;
  - sessões do usuário.

## Recursos usados na V0.6 quando suportados

- `--api-key` efêmera
- `--parallel 1`
- `--no-webui`

Serviço local:

```text
127.0.0.1
```

---

# 8. MODELOS INSTALADOS

## 8.1 Qwen3-4B Q4_K_M

Uso atual:

- perfil RÁPIDO
- preferência AUTO na máquina Avell
- bom desempenho real

Características conhecidas:

- família: Qwen3
- parâmetros: ~4B
- quantização: Q4_K_M
- camadas: 36
- tamanho aproximado: 2,5 GB
- licença: Apache 2.0

SHA256:

```text
7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5
```

Desempenho observado no Avell:

- CUDA
- 8 threads
- 36 camadas GPU
- contexto 4096
- benchmark ~19,35 t/s
- chat real ~18,4–19,3 t/s

## 8.2 Qwen3-8B Q4_K_M

Uso atual:

- perfil QUALIDADE
- configuração estável com offload parcial

Características conhecidas:

- família: Qwen3
- parâmetros: ~8,2B
- quantização: Q4_K_M
- camadas: 36
- tamanho aproximado: 5,03 GB
- licença: Apache 2.0

SHA256:

```text
d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785
```

### Descoberta importante

Benchmark sintético com 27 camadas:

- ~8,99 t/s

Mas em chat real:

- VRAM ~3977/4096 MiB
- desempenho caiu para aproximadamente 3,9 t/s

Com 24 camadas:

- VRAM ~3563/4096 MiB
- headroom ~533 MiB
- geração ~8,2 t/s

Configuração estável oficial do 8B no Avell:

```text
backend = CUDA
threads = 6
gpu_layers = 24
context = 4096
```

### Regra

Headroom experimental mínimo adotado:

```text
~400 MiB de VRAM livre
```

---

# 9. MODOS ATUAIS

## RÁPIDO

```text
Modelo: Qwen3-4B Q4_K_M
Backend: CUDA
Threads: 8
GPU layers: 36
Contexto: 4096
Desempenho real: ~18,8–19,3 t/s
VRAM aproximada: ~2481 MiB
```

## QUALIDADE

```text
Modelo: Qwen3-8B Q4_K_M
Backend: CUDA
Threads: 6
GPU layers: 24
Contexto: 4096
Desempenho real: ~7,9–8,2 t/s
VRAM aproximada: ~3563 MiB
Headroom: ~533 MiB
```

## AUTO

No Avell:

```text
AUTO → RÁPIDO
```

Importante:

O nome “QUALIDADE” é uma classificação de perfil de uso, não uma afirmação absoluta de que o 8B sempre produz respostas melhores que o 4B.

Em testes anteriores, o 4B chegou a superar levemente o 8B em algumas avaliações qualitativas.

---

# 10. AUTOTUNE

O AutoTune evoluiu para distinguir:

```text
benchmark_peak
```

de:

```text
chat_stable
```

Essa distinção é obrigatória.

## Estratégia conhecida

- detectar CPU/RAM/GPU;
- medir backend;
- testar quantidade de camadas;
- observar VRAM;
- evitar saturação;
- recuar em passos;
- preferir configuração sustentável em chat real.

### Política atual

- contexto padrão: 4096
- VRAM headroom mínimo experimental: ~400 MiB
- layer backoff: 3 camadas
- máquina conhecida → usar perfil salvo
- máquina nova → calibrar e salvar perfil

---

# 11. HISTÓRICO DE VERSÕES

## V0.1 / V0.2.x

Primeiros detectores de hardware em Python.

Correções importantes:

- IDs de recursos do Windows;
- Secure Boot;
- armazenamento externo;
- identificação de disco;
- velocidade de USB;
- machine ID.

## V0.3 / V0.3.1

Primeira IA local real.

- llama.cpp CPU + CUDA
- Qwen3-4B
- testes reais de desempenho
- caminhos portáteis

## V0.3.2

Adicionou:

- menu;
- reutilização de máquina conhecida;
- caminhos relativos;
- supressão de thinking;
- distinção entre nome do produto e nome do modelo.

Supressão de reasoning:

- `--reasoning off`
- fallback via parâmetros de template quando necessário.

## V0.4 / V0.4.1 / V0.4.2

Adição do Qwen3-8B.

Grande aprendizado:

> Pico de benchmark ≠ estabilidade em chat.

Perfis FAST / QUALITY / AUTO consolidados.

## V0.5 — Autonomia e AutoTune Estável

Recursos:

- Python portátil;
- launcher único;
- banco por máquina;
- AutoTune;
- chat probe real;
- monitoramento de VRAM;
- fallback CUDA → CPU;
- máquina conhecida / nova máquina;
- benchmark peak vs chat stable.

Problema histórico:

Windows retornou erro 1392 em `llama-cli.exe`.

`chkdsk E: /scan` indicou disco saudável.

Foi criado reparo seletivo de CUDA que:

- preservou engine anterior;
- reextraiu ZIP local;
- validou hashes/versão;
- não tocou modelos/perfis/partições.

## Consolidação pós V0.5

Raiz oficial passou a ser:

```text
E:\NUCLEO_IA_PORTATIL
```

Sem número da versão no diretório principal.

## V0.6.0 Experimental — Interface Local

Arquitetura escolhida:

```text
Browser
  ↓
Python backend local
  ↓
llama-server
  ↓
modelo
```

Características:

- HTML/CSS/JS puros;
- backend stdlib;
- loopback only;
- streaming;
- modo AUTO/RÁPIDO/QUALIDADE;
- terminal virou infraestrutura/fallback.

Teste de campo:

> Funcionou sem problemas.

## V0.6.1 — Sessões e Histórico Local

Implementado:

- sessões JSON;
- escrita atômica;
- IDs de 16 caracteres;
- máximo de 500 mensagens;
- título pela primeira pergunta;
- estrutura por ano/mês;
- restauração da última conversa;
- exclusão;
- sessões vazias ocultas.

Teste real:

> “histórico salvo”

Validada.

## V0.6.2 — Calibração Gráfica

Adicionou:

- calibração pela interface;
- progresso;
- cancelamento;
- erros amigáveis;
- recalibração manual.

### Problema 1 — CP1252

A saída redirecionada do Python no Windows usava CP1252 e quebrou com o caractere grego Δ.

Erro:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\u0394'
```

Correções:

- evitar Unicode desnecessário em caminhos de console;
- `PYTHONIOENCODING=utf-8`
- `PYTHONUTF8=1`

### Problema 2 — calibração travando em 82%

Qwen3/llama-cli podia permanecer em modo conversa após uma resposta.

Correções:

- `--single-turn` / `-st`
- `stdin=subprocess.DEVNULL`
- timeout mantido apenas como proteção.

Resultado de calibração após correções:

```text
RÁPIDO: ~19,3 t/s
QUALIDADE: ~7,9 t/s
AUTO: RÁPIDO
```

Validada.

## V0.6.3 — Manutenção e Recuperação

Adicionou painel para:

- diagnóstico CUDA;
- diagnóstico CPU;
- modelos;
- backend atual;
- cache;
- reiniciar engine;
- forçar CPU;
- retornar ao perfil;
- reparar CUDA;
- reparar CPU;
- ver logs.

Teste real:

```text
Fallback manual para CPU solicitado.
Motor reiniciado em CPU.
Reinício do motor solicitado pela interface.
Motor reiniciado: backend=cuda mode=auto
```

Validada.

## V0.6.4 — Polimento e Estabilidade

Recursos:

- heartbeat de calibração;
- cache de `--help`;
- API key efêmera;
- `--parallel 1`;
- `--no-webui`;
- detecção de segunda instância;
- reapertura da UI existente;
- botões de reparo apenas quando necessários;
- status CPU forçado;
- limpeza de temporários;
- limpeza de sessões vazias antigas;
- headers de segurança;
- launcher mais limpo.

Teste real:

> “tudo certo”

Validada.

## V0.6 FINAL CONSOLIDADA

Release estável oficial.

Consolida:

- 0.6.0
- 0.6.1
- 0.6.2
- 0.6.2.1
- 0.6.2.2
- 0.6.3
- 0.6.4

Estado:

```text
version = 0.6
release = final
channel = stable
codename = Interface Local
```

Teste final do usuário:

> “tudo certo”

### STATUS

**ESTÁVEL / BASE DE RETORNO**

---

# 12. V0.6.5 — ARQUIVOS E ANÁLISE LOCAL

Objetivo:

Transformar o NÚCLEO de chat local em ferramenta de trabalho com arquivos.

Princípio:

```text
LLM interpreta.
Ferramentas determinísticas calculam.
```

## Formatos iniciais

- XLSX
- CSV
- TXT
- MD
- JSON

## Workspace

Arquivos por conversa:

```text
workspace\
└── sessions\
    └── <session_id>\
        └── uploads\
```

## Limites iniciais

```text
25 MB por arquivo
5 arquivos por conversa
50 MB por conversa
```

## Segurança

- macros não executadas;
- scripts não executados;
- internet desnecessária;
- XLSX tratado como ZIP/XML;
- proteção contra expansão excessiva de ZIP;
- arquivos locais apenas.

## Estratégia XLSX inicial

Foi decidido evitar dependências pesadas.

Não foram adicionados:

- pandas;
- numpy;
- LibreOffice;
- openpyxl.

O XLSX inicial é lido diretamente com:

- `zipfile`
- XML da stdlib
- parsing próprio

## Capacidades determinísticas iniciais

Para tabelas:

- linhas;
- colunas;
- faltantes;
- soma;
- média;
- mínimo;
- máximo;
- frequência de valores;
- amostras.

Para XLSX:

- abas;
- fórmulas;
- valor salvo das células;
- padrões de fórmulas;
- possíveis diferenças em relação ao padrão dominante.

### Limitação importante

O NÚCLEO não possui motor Excel/LibreOffice.

Ele:

- lê fórmulas;
- lê valores armazenados;
- compara padrões;

mas:

> NÃO recalcula a pasta de trabalho como o Excel faria.

---

# 13. V0.6.5.1 — HOTFIX DE CONCLUSÃO DE RESPOSTAS

O primeiro teste XLSX real mostrou uma resposta interrompida no meio da palavra:

```text
A coluna numérica (col
```

## Causa

O `engine_manager.py` ainda herdava:

```text
max_tokens = 1024
```

A interface também não tratava corretamente:

```text
finish_reason
```

Portanto, uma resposta cortada por limite parecia ter finalizado normalmente.

## Correções

- teto aumentado para até ~1536 tokens;
- orçamento aproximado considerando contexto 4096;
- detecção de `finish_reason`;
- aviso quando resposta é truncada;
- contexto de arquivos mais compacto;
- omissão de colunas 100% vazias;
- instrução para priorizar conclusões;
- redução de repetições.

## Teste de campo após hotfix

Usuário repetiu a análise.

Resultado:

> respostas melhoraram bastante.

A resposta passou a:

- finalizar;
- apresentar principais achados;
- apresentar inconsistências;
- apresentar conclusão.

### STATUS

**V0.6.5.1 validada parcialmente em campo.**

Validado:

- arquivo `.MD` → OK;
- XLSX → resposta completa após hotfix;
- contexto de arquivo → funcional;
- continuidade da conversa sobre o arquivo → funcional.

Ainda não considerado “final consolidado”.

---

# 14. PROBLEMA ATUAL IDENTIFICADO EM XLSX

O extrator atual funciona bem para planilhas tradicionais em formato tabular:

```text
cabeçalho
linha
linha
linha
```

Mas a planilha real de teste é uma calculadora estruturada em seções:

- metas;
- carga horária;
- custos;
- fórmulas;
- subtotais;
- resultados.

O parser atual interpreta esse layout como uma tabela genérica.

Consequências observadas:

- nomes como `coluna_3`;
- células estruturais vazias tratadas como dados faltantes;
- baixa compreensão da relação entre rótulo e valor;
- análise excessivamente genérica;
- sugestões pouco específicas;
- dificuldade em entender que um número pertence a um item específico.

Exemplo:

Em vez de entender:

```text
Quanto quer ganhar por mês? → R$ 12.000
Dias por semana → 5
Horas por dia → 6
Percentual faturável → 70%
```

o extrator pode entregar algo próximo de:

```text
coluna_3:
12000
5
6
0.7
```

Isso reduz muito a qualidade semântica.

---

# 15. CONTRADIÇÃO DE PROMPT IDENTIFICADA

Na resposta da V0.6.5.1 o modelo afirmou:

> “O NÚCLEO IA PORTÁTIL ... não pode realizar cálculos”

Isso está incorreto.

O NÚCLEO já realizou:

- soma;
- média;
- mínimo;
- máximo.

A formulação correta deve ser:

> O NÚCLEO pode realizar cálculos determinísticos sobre dados extraídos, mas não recalcula nativamente o motor de fórmulas do Excel.

Essa correção deve entrar na próxima atualização.

---

# 16. PRÓXIMA VERSÃO PLANEJADA

## V0.6.5.2 — Leitura Semântica de Planilhas

Objetivo:

Distinguir diferentes tipos de planilha e extrair significado estrutural antes de enviar contexto ao modelo.

Fluxo planejado:

```text
XLSX
 ↓
detecção de estrutura
 ↓
┌──────────────────────────────┐
│ TABELA                       │
│ linhas / colunas             │
├──────────────────────────────┤
│ FORMULÁRIO / CALCULADORA     │
│ seções / rótulos / valores   │
└──────────────────────────────┘
 ↓
extração apropriada
 ↓
cálculos determinísticos
 ↓
contexto semântico
 ↓
Qwen interpreta
```

## Melhorias desejadas

### 1. Reconhecimento de seções

Exemplo:

```text
SEÇÃO 1 — SUAS METAS E CARGA HORÁRIA
SEÇÃO 2 — CUSTOS OPERACIONAIS MENSAIS
SEÇÃO 3 — CÁLCULO DO VALOR DA HORA
```

### 2. Reconhecimento de pares rótulo → valor

Exemplo:

```text
B3 → "Quanto quer ganhar por mês?"
C3 → 12000
```

deve virar:

```text
Quanto quer ganhar por mês: R$ 12.000
```

### 3. Diferenciar vazio estrutural de dado realmente ausente

Nem toda célula vazia representa erro ou dado faltante.

### 4. Preservar coordenadas

Exemplo:

```text
C15
fórmula = ...
valor salvo = 13.880,93
rótulo associado = Custo Total Mensal
```

### 5. Interpretar formatação numérica

Distinguir quando possível:

- moeda;
- percentual;
- inteiro;
- decimal;
- horas;
- datas.

### 6. Fórmulas associadas ao significado

Em vez de apenas:

```text
8 fórmulas
```

entregar:

```text
Custo Total Mensal:
fórmula = ...
valor salvo = ...
```

### 7. Melhor prompt de interpretação

Evitar respostas genéricas como:

- “preencher valores faltantes”;
- “organizar melhor a planilha”;

quando o próprio layout já é intencional.

---

# 17. UI DE ARQUIVOS

Interface atual inclui:

```text
[ 📎 Anexar ]
```

Suporta:

```text
XLSX
CSV
TXT
MD
JSON
```

Exibe metadados básicos do arquivo.

O arquivo fica vinculado à sessão.

Arquitetura:

```text
arquivo
 ↓
workspace local
 ↓
extrator determinístico
 ↓
contexto compacto
 ↓
Qwen3
 ↓
resposta no chat
```

---

# 18. REGRAS PARA ANÁLISE DE ARQUIVOS

## Regra principal

> Se uma ferramenta pode calcular com precisão, o LLM não deve fazer a conta “de cabeça”.

Exemplo:

```text
Usuário:
"Qual é a média da coluna faturamento?"

Ferramenta:
calcula média

Qwen:
explica o resultado
```

## Segurança

- `.xlsm` futuramente poderá ser lido, mas macros nunca devem executar automaticamente.
- código anexado pode ser analisado, mas não executado por padrão.
- executáveis não devem ser executados.
- links externos não devem ser abertos automaticamente.
- ferramentas devem ter limites de memória/tempo quando necessário.

---

# 19. CONTEXTO ATUAL DO MODELO

Configuração de produção atual:

```text
context_size = 4096
```

Isso significa que arquivos grandes não podem ser despejados integralmente no prompt.

Estratégia:

```text
arquivo grande
 ↓
extrair estrutura
 ↓
calcular
 ↓
filtrar
 ↓
resumir
 ↓
entregar apenas dados relevantes ao modelo
```

Essa estratégia é deliberada.

---

# 20. LIÇÕES TÉCNICAS IMPORTANTES

## 20.1 VRAM

> Cabe na VRAM ≠ configuração saudável.

## 20.2 Benchmark

> Benchmark sintético ≠ chat real.

## 20.3 Windows stdout

Processos Python redirecionados podem cair em CP1252.

Usar:

```text
PYTHONIOENCODING=utf-8
PYTHONUTF8=1
```

quando apropriado.

## 20.4 llama-cli / Qwen3

Probes precisam ser realmente single-turn:

```text
--single-turn
```

ou:

```text
-st
```

e:

```text
stdin = DEVNULL
```

## 20.5 Segunda instância

Abrir o launcher novamente não deve carregar um segundo modelo.

Deve:

- detectar instância ativa;
- reabrir UI existente.

## 20.6 Reparo

Não provocar falha artificial em engine saudável só para testar.

## 20.7 Tokens/s

Na UI, t/s pode ser calculado por:

```text
completion_tokens / wall_time
```

quando uso de streaming estiver disponível.

Não fingir precisão superior à realmente medida.

## 20.8 Contexto

Ainda não existe medição exata do uso do tokenizer na UI.

Não inventar porcentagem exata de contexto.

---

# 21. HISTÓRICO E SESSÕES

Sessões locais:

- JSON;
- atomic write;
- limite de 500 mensagens;
- ID 16 caracteres;
- título pela primeira mensagem;
- restauração automática;
- histórico lateral;
- exclusão.

A conversa deve permanecer local.

---

# 22. MANUTENÇÃO

Painel atual pode:

- diagnosticar engine;
- reiniciar engine;
- forçar CPU;
- voltar ao backend do perfil;
- reparar CPU;
- reparar CUDA;
- mostrar logs.

Regra:

> Reparos devem preservar dados e serem reversíveis.

---

# 23. UX

Interface atual deve continuar leve.

Elementos desejados:

```text
NÚCLEO IA PORTÁTIL
LOCAL
IA PRONTA

AUTO
RÁPIDO
QUALIDADE

chat

[ 📎 Anexar ]
```

Linha inferior:

- modelo;
- backend;
- tokens/s.

Detalhes técnicos:

- somente sob demanda.

Atalhos:

- Enter envia;
- Shift+Enter cria nova linha.

---

# 24. ROADMAP

## V0.6

Interface local e autonomia.

**Status:** FINAL / ESTÁVEL.

## V0.6.5.x

Arquivos e análise local.

**Status atual:** em evolução.

Subetapas:

- V0.6.5 — anexos e análise determinística;
- V0.6.5.1 — correção de truncamento;
- V0.6.5.2 — leitura semântica de planilhas.

## V0.7 — Portabilidade Real / Multi-Máquina

Objetivo:

Provar que o NÚCLEO funciona em máquinas diferentes.

Testes planejados:

### Máquina mais fraca

Objetivo:

- fallback;
- modelo leve;
- CPU-only;
- baixo recurso;
- ausência de NVIDIA.

### Máquina intermediária

Objetivo:

- consistência;
- perfil independente;
- reconhecimento de hardware.

### Máquina forte

Objetivo:

- escalabilidade;
- mais VRAM;
- mais RAM;
- modelos maiores;
- AutoTune subindo de nível.

Fluxo ideal:

```text
SSD no Avell
 ↓
perfil conhecido
 ↓
sem recalibração

SSD em outra máquina
 ↓
Machine ID novo
 ↓
calibração
 ↓
novo perfil salvo

SSD volta ao Avell
 ↓
perfil antigo reaproveitado
```

## V0.7 — Catálogo de Modelos

Direção planejada:

Desacoplar código central de apenas 4B/8B.

Registry futuro pode conter:

- id;
- arquivo;
- família;
- parâmetros;
- quantização;
- tamanho;
- contexto;
- licença;
- SHA256;
- função;
- requisitos;
- template;
- compatibilidade.

Possíveis faixas:

```text
LEVE        1.5B–3B
RÁPIDO      4B
QUALIDADE   8B
AVANÇADO    12B–14B
PESADO      20B+
```

Não assumir esses tamanhos como definitivos.

AUTO futuro poderá escolher modelo por hardware.

## V0.8 — NÚCLEO Bootável

Usuário possui um pendrive de 32 GB reservado para laboratório.

Estratégia:

### Primeiro usar pendrive separado

Nunca começar reparticionando o SSD principal.

Fluxo:

```text
PC desligado
 ↓
pendrive + SSD conectados
 ↓
boot UEFI pelo pendrive
 ↓
Linux leve
 ↓
detecta hardware
 ↓
monta SSD
 ↓
encontra modelos/perfis
 ↓
inicia NÚCLEO
```

### Possível divisão futura

Pendrive:

- Linux;
- boot;
- drivers;
- runtime.

SSD:

- modelos;
- perfis;
- sessões;
- workspace;
- cache;
- dados.

### Questões críticas

- UEFI;
- Secure Boot;
- NVIDIA;
- AMD;
- Intel;
- rede;
- persistência;
- drivers;
- boot confiável.

Avell tem Secure Boot habilitado.

Não recomendar desativação permanente sem necessidade.

## V0.9 — Recursos Avançados

Possíveis recursos:

- RAG;
- documentos;
- múltiplos arquivos;
- comparação;
- gráficos;
- geração de planilhas;
- exportação de resultados;
- ferramentas;
- voz;
- eventualmente multimodal.

## V1.0

Objetivo:

Plataforma consolidada, portátil e autônoma.

---

# 25. MODELOS FUTUROS

A família atual Qwen3 é adequada como cérebro/orquestrador para:

- resumo;
- interpretação;
- planejamento;
- análise semântica;
- tool calling;
- explicação dos resultados.

Não usar o LLM isoladamente para:

- milhares de somas;
- estatística exata;
- recálculo de planilha;
- operações determinísticas disponíveis em ferramenta.

Possível terceira opção futura:

> modelo pequeno para máquinas fracas.

Adicionar modelos somente após validar:

- licença;
- SHA256;
- GGUF;
- arquitetura;
- chat template;
- compatibilidade com llama.cpp b10516;
- RAM;
- VRAM;
- contexto;
- estabilidade.

Multimodal não é “só mais um GGUF”.

Imagem/áudio exigirão alterações de engine e UI.

---

# 26. ARTEFATOS HISTÓRICOS IMPORTANTES

Arquivos gerados durante o desenvolvimento:

```text
Nucleo_IA_Portatil_PATCH_v0_5.zip
Nucleo_IA_Portatil_REPARO_CUDA_V0_5.zip
Nucleo_IA_Portatil_CONSOLIDACAO_POS_V0_5.zip

Nucleo_IA_Portatil_PATCH_v0_6_0_EXPERIMENTAL.zip
Nucleo_IA_Portatil_PATCH_v0_6_1.zip
Nucleo_IA_Portatil_PATCH_v0_6_2.zip
Nucleo_IA_Portatil_HOTFIX_v0_6_2_1.zip
Nucleo_IA_Portatil_HOTFIX_v0_6_2_2.zip
Nucleo_IA_Portatil_PATCH_v0_6_3.zip
Nucleo_IA_Portatil_PATCH_v0_6_4.zip

Nucleo_IA_Portatil_V0_6_FINAL_CONSOLIDADA.zip

Nucleo_IA_Portatil_PATCH_v0_6_5_DIRETO.zip
Nucleo_IA_Portatil_HOTFIX_v0_6_5_1.zip
```

A V0.6 FINAL CONSOLIDADA deve permanecer como checkpoint estável de retorno.

---

# 27. BACKUP

Antes da V0.6.5, o usuário informou que realizou backup manual do estado atual.

Regra permanente:

> Antes de alterações estruturais importantes, garantir backup fora do fluxo de atualização.

Para pequenas hotfixes, pode haver apenas backup técnico dos arquivos substituídos para rollback, desde que o backup completo já exista.

---

# 28. ESTADO ATUAL

## Base estável

```text
V0.6 FINAL CONSOLIDADA
```

Status:

**VALIDADA EM CAMPO / ESTÁVEL**

## Desenvolvimento atual

```text
V0.6.5.1
Arquivos e Análise Local
```

Status observado:

```text
MD                         ✅ OK
XLSX                       ✅ abre e analisa
resposta truncada          ✅ corrigida
continuidade da conversa   ✅ funcional
cálculos básicos           ✅ funcional
leitura de fórmulas        ✅ funcional
recalcular Excel           ❌ não implementado
interpretação semântica    ⚠ limitada
```

## Próximo passo imediato

```text
V0.6.5.2 — Leitura Semântica de Planilhas
```

Objetivo imediato:

> Fazer o NÚCLEO entender planilhas de formulário/calculadora como estrutura semântica, e não apenas como tabela genérica.

---

# 29. TESTE REAL QUE MOTIVOU A V0.6.5.2

Arquivo testado:

```text
Calculo Precificação-V01.xlsx
```

Características percebidas:

- aproximadamente 17 linhas;
- seções de metas;
- carga horária;
- custos operacionais;
- cálculo de valor/hora;
- fórmulas.

Após V0.6.5.1, a resposta passou a finalizar corretamente, mas ainda gerou expressões como:

```text
coluna_3
valores faltantes
SEÇÃO 1
SEÇÃO 2
```

sem reconstruir plenamente as relações semânticas.

A próxima implementação deve tentar produzir contexto próximo de:

```text
SEÇÃO 1 — METAS E CARGA HORÁRIA

Quanto quer ganhar por mês:
R$ 12.000,00

Dias por semana:
5

Horas por dia:
6

Percentual faturável:
70%
```

e não:

```text
coluna_3:
12000
5
6
0.7
```

---

# 30. CRITÉRIO DE SUCESSO DA V0.6.5.2

Ao perguntar:

```text
Faça uma análise desta planilha.
```

o NÚCLEO deverá:

1. reconhecer a finalidade provável da planilha;
2. identificar seções;
3. associar rótulos e valores;
4. explicar os cálculos identificáveis;
5. apontar fórmulas relevantes;
6. diferenciar vazio estrutural de dado ausente;
7. evitar nomes genéricos como `coluna_3` quando houver contexto suficiente;
8. produzir conclusão específica;
9. não afirmar que “não pode realizar cálculos”;
10. deixar claro que não recalcula o motor nativo do Excel.

---

# 31. REGRAS DE DESENVOLVIMENTO A PARTIR DE AGORA

1. Não reabrir a V0.6 FINAL para adicionar features.
2. Evoluções atuais entram na linha V0.6.5.x.
3. Cada hotfix deve ter rollback.
4. Cada nova versão deve ser validada:
   - sintaticamente;
   - funcionalmente;
   - em Windows real.
5. Não afirmar “validado” apenas porque compilou.
6. Teste real do usuário é a referência final.
7. Não adicionar dependência pesada sem benefício mensurável.
8. Não baixar novamente modelos já existentes.
9. Não alterar engines saudáveis sem necessidade.
10. Não tocar em partições durante a fase Windows.
11. Future bootable work deve usar primeiro o pendrive de 32 GB.
12. O SSD principal deve ser preservado até o boot experimental estar maduro.

---

# 32. CHECKPOINT PARA O PRÓXIMO CHAT

Ao abrir novo chat, usar algo como:

> Leia integralmente o arquivo `NUCLEO_IA_PORTATIL_MEMORIA_PROJETO.md`.  
> Ele é a memória técnica oficial do projeto.  
> Continue exatamente do estado atual.  
> O próximo desenvolvimento é a V0.6.5.2 — Leitura Semântica de Planilhas.  
> Não altere a V0.6 FINAL consolidada.

---

# 33. RESUMO EXECUTIVO

O projeto já possui:

- IA local funcional;
- dois modelos Qwen3;
- CPU/CUDA;
- AutoTune;
- perfis por máquina;
- histórico;
- interface web local;
- calibração;
- manutenção;
- recuperação;
- anexos;
- análise determinística básica de arquivos.

A base estável é:

```text
V0.6 FINAL
```

A linha atual de desenvolvimento é:

```text
V0.6.5.1
```

O maior problema atual não é estabilidade da IA, mas:

> interpretação estrutural de planilhas não tabulares.

Próximo passo:

```text
V0.6.5.2
Leitura Semântica de Planilhas
```

Depois disso, o roadmap segue para:

```text
V0.7  Portabilidade real / multi-máquina
V0.8  Bootável
V0.9  Ferramentas avançadas
V1.0  Plataforma consolidada
```

---

**FIM DO CHECKPOINT — 2026-09-12**
