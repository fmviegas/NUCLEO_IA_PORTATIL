# NÚCLEO IA PORTÁTIL — Versão LINUX no SSD externo (passo a passo)

> Documento de MONTAGEM. Nada aqui inicia/roda o NÚCLEO — é o blueprint para criar a
> variante Linux sobre um SSD externo bootável. Gerado a partir da V0.9.20 FINAL (Windows).
> Fonte de verdade do projeto: `BIBLIA_NUCLEO_IA_PORTATIL.md`.

---

## 0. Visão geral e decisão de arquitetura

O NÚCLEO tem **duas camadas**:

| Camada | Portável entre SO? | Observação |
|---|---|---|
| Backend Python (`app/`, `app/book/`, `app/diagramador/`) | ✅ sim | stdlib + `python-docx/ebooklib/lxml/pypdf/openpyxl` |
| UI (`ui/`), `config/`, **modelos GGUF** (`models/`) | ✅ sim | bytes idênticos nos dois SO |
| `app/hardware.py` | ✅ já tem ramo Linux | `/proc/cpuinfo`, `detect_storage_linux()` |
| **Motor** llama.cpp (`engine/windows/*.exe`) | ❌ não | precisa build **Linux** |
| **Runtime** (`runtime/python/python.exe`) | ❌ não | precisa Python **Linux** |
| VC++ DLLs (`vcruntime140.dll`…) | ❌ não | no Linux o par é glibc/libstdc++ |
| Lançadores `.bat` | ❌ não | trocar por `.sh` |

Ou seja: **~85% do projeto é reaproveitado sem tocar**. A porta Linux se resume a
(a) binários Linux do motor, (b) um Python Linux, (c) uma pequena camada que resolve
o caminho do motor/runtime por SO, e (d) lançadores `.sh`.

### Duas formas de "Linux portátil no SSD"

- **A) Instalação Linux COMPLETA no SSD externo (RECOMENDADO).**
  O SSD vira um disco bootável próprio (partição EFI + raiz ext4). Dá driver NVIDIA
  proprietário + CUDA de verdade → os tiers de GPU (fast/quality/advanced/code) rodam
  com performance real. Boota em qualquer PC pelo menu de boot (F12/F9/ESC).
- **B) Live USB persistente (Ventoy/Rufus).** Mais simples de gravar, porém driver
  NVIDIA/CUDA fica frágil e a performance de GPU cai. **Não recomendado** para GGUF pesado.

Este guia segue a **Opção A**.

---

## 1. Preparar o SSD externo com Linux (feito por VOCÊ, fora do NÚCLEO)

1. Baixe uma ISO LTS: **Ubuntu 24.04 LTS** (ou 22.04) — melhor suporte a NVIDIA.
2. Grave a ISO num pendrive de instalação (Rufus/Ventoy no Windows, ou `dd` no Linux).
3. Boote pelo pendrive, escolha **"Instalar Ubuntu"** e, no particionamento,
   selecione o **SSD externo** como destino (cuidado para NÃO escolher o disco interno).
   - Partições no SSD: `EFI` (~512 MB, FAT32) + `/` raiz **ext4** (o resto).
   - `ext4` **não tem** o limite de 4 GB/arquivo do FAT32 → os GGUF de 12 GB cabem numa boa.
4. Conclua a instalação, boote no Linux do SSD, e faça o `apt update && apt upgrade`.
5. **GPU NVIDIA** (para os tiers de GPU):
   - `ubuntu-drivers devices` → instale o driver recomendado (`sudo ubuntu-drivers autoinstall`).
   - Reinicie e confirme com `nvidia-smi` (tem que listar a GPU).
   - CUDA: o driver já traz o runtime CUDA que o llama.cpp CUDA precisa; não é obrigatório
     instalar o CUDA Toolkit completo para só **rodar** binários prontos.

> Sem NVIDIA reconhecida, o NÚCLEO cai no modo **CPU** automaticamente (igual ao Windows).

---

## 2. Obter os binários Linux do motor (llama.cpp)

Coloque-os em `linux/engine/cuda/` e `linux/engine/cpu/` (ver `LEIA-ME.txt` de cada pasta).

Duas vias:

- **Prontos (mais rápido):** baixe o release Linux do llama.cpp
  (GitHub `ggml-org/llama.cpp` → *Releases* → asset `…-ubuntu-x64` e o `…-cuda` correspondente).
  Extraia e copie `llama-server`, `llama-cli`, `llama-bench` (sem extensão) para as pastas.
- **Compilar (controle total):**
  ```
  sudo apt install -y build-essential cmake libcurl4-openssl-dev
  git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
  # CPU:
  cmake -B build-cpu -DGGML_NATIVE=ON && cmake --build build-cpu -j --config Release
  # CUDA (com driver instalado):
  cmake -B build-cuda -DGGML_CUDA=ON && cmake --build build-cuda -j --config Release
  ```
  Os binários saem em `build-*/bin/`. Copie os três para `linux/engine/{cpu,cuda}/`
  e dê permissão de execução: `chmod +x linux/engine/*/llama-*`.

> **Compatibilidade de versão:** use uma versão do llama.cpp que aceite os mesmos GGUF já
> validados (arquitetura `qwen3` e `qwen3moe` para o 30B-A3B). Uma release recente cobre isso.

---

## 3. Python no Linux

O backend é stdlib puro, mas a publicação de livros precisa de 4 libs. No Linux use um **venv**:

```
sudo apt install -y python3 python3-venv python3-pip
cd /caminho/do/NUCLEO_IA_PORTATIL
python3 -m venv .venv
. .venv/bin/activate
pip install "python-docx>=1.2.0" "ebooklib>=0.20" lxml "pypdf>=6.18" "openpyxl>=3.1"
```

O lançador `.sh` (passo 5) ativa esse `.venv` sozinho.

---

## 4. Camada que resolve o motor por SO — ✅ JÁ APLICADA

Criado `app/plat.py` como **fonte única** do layout do motor:

```python
IS_WINDOWS = (os.name == "nt")
EXE_SUFFIX = ".exe" if IS_WINDOWS else ""
def engine_root(root):   # Windows: <root>/engine/windows   ·   Linux: <root>/linux/engine
    return (root/"engine"/"windows") if IS_WINDOWS else (root/"linux"/"engine")
def engine_dir(root, backend):  return engine_root(root) / backend
def engine_exe(root, backend, nome):  return engine_dir(root, backend) / (nome + EXE_SUFFIX)
```

Os 6 pontos que tinham `.exe` fixo agora passam por `plat`:

- `app/engine_manager.py` `_server_exe` → `plat.engine_exe(...)`
- `app/autotune.py` (sonda CUDA, perfil CPU) → `plat.engine_exe/…_rel`; bloqueio
  `os.name != "nt"` removido e `detect_windows()` → `detect_safe()`
- `app/benchmark.py` (perfil, `required`, bench CPU/CUDA) → `plat.engine_exe`; mesmo
  desbloqueio de SO e `detect_safe()`
- `app/chat.py` `build_cmd` → `plat.engine_exe(...)`
- `app/maintenance_manager.py` (`engine_root`, listas de binários) → `plat.*`
- `app/hardware.py` `detect_engine` → `plat.engine_dir(...)` (Linux passa a olhar `linux/engine`)

**No Windows o resultado é idêntico** ao de antes (`engine/windows/…​.exe`, `os.name=="nt"`),
então a versão Windows não muda de comportamento.

> ⚠️ Como isso **edita** arquivos que estão no manifesto V0.9.20 FINAL (muda hashes), é
> **drift de versão nova**: a consolidar como **V0.9.21-linux** (manifesto/validador/rollback
> próprios). Não é patch silencioso na V0.9.20 — o rótulo só muda na consolidação.
> **Não testado em Linux real ainda** (você ainda vai instalar o Linux); no Windows segue igual.

---

## 5. Lançadores `.sh` (em `linux/`)

- `linux/nucleo.sh` — inicia o backend (ativa `.venv` se existir; serve em 127.0.0.1).
- `linux/calibrar.sh` — calibração avançada (`--mode advanced|code`) na máquina Linux atual.

Dê permissão uma vez: `chmod +x linux/*.sh`.

---

## 6. Montar a árvore Linux do projeto no SSD

Rode **no Linux** (ou numa área exFAT de staging), a partir de uma cópia dos fontes:

```
python3 linux/montar_linux.py --dest /media/voce/SSD/NUCLEO_IA_PORTATIL --modelos all
```

O `montar_linux.py` copia só o multiplataforma (`app`, `ui`, `config`, `tools`, `models`)
mais a pasta `linux/` inteira (motor Linux + `.sh` + guia) e **exclui** o que é Windows
(`engine/windows`, `runtime/python`, `*.bat`, `*.dll`, `*.exe`, `*.ps1`, validadores de
versão, `__pycache__`). Cria as pastas de trabalho vazias e um `PORTATIL_LINUX.txt` no destino.

> Do **Windows não dá** para escrever direto na partição `ext4` do SSD. Faça a montagem
> **rodando no Linux do próprio SSD** (ou copie via uma partição exFAT intermediária).

---

## 7. Calibrar na máquina Linux (passo separado — NÃO agora)

Na 1ª execução numa máquina nova o `machine_id` não casa e o NÚCLEO calibra sozinho os
tiers base (fast+quality, ~10 min). Os tiers **advanced** e **code** calibram à parte com
`calibrar_advanced` (agora `--mode`), igual no Windows. O botão CÓDIGO fica gateado até calibrar.

---

## Ordem de execução resumida

1. Instalar Ubuntu LTS no SSD externo (+ driver NVIDIA).                 ← você
2. Baixar/compilar `llama-server/cli/bench` Linux → `linux/engine/`.     ← você
3. Criar `.venv` + `pip install` das 5 libs.                            ← você
4. Camada `app/plat.py` (resolve motor por SO).                         ← ✅ FEITO
5. `python3 linux/montar_linux.py --dest <SSD> --modelos all`.          ← no Linux
6. `chmod +x linux/*.sh` e calibrar (passo à parte).                    ← você, ao rodar

**Estado agora:** a camada `plat.py` (passo 4) está **aplicada** (drift p/ V0.9.21-linux, a
consolidar); os passos 2/3/5 são seus, no Linux. Nada foi iniciado. Os arquivos-base
(este guia, `linux/engine/`, `linux/*.sh`, `linux/montar_linux.py`, `app/plat.py`) já
existem no repositório mestre. Falta só você instalar o Linux e trazer os binários.
