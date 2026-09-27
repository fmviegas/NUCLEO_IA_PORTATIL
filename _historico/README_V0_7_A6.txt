NÚCLEO IA PORTÁTIL — V0.7 FASE 3 fatia 4 (alpha6)
validar_modelo.py — portão de validação de modelo (§25)
=======================================================

ALPHA. Arquivo novo; não altera o motor. Base de retorno: V0.6.5 FINAL.

O QUE É
-------
tools/validar_modelo.py valida um .gguf ANTES de adicioná-lo ao catálogo,
SEM executar o modelo: existência/tamanho, magic+versão GGUF, metadados
(arquitetura, context_length, chat template) lidos do cabeçalho, arquitetura
conhecida, e SHA256 (compara com --sha256 ou com o do registry via --id).
Imprime uma sugestão de entrada de registry para revisão.

USO
---
runtime\python\python.exe tools\validar_modelo.py <arquivo.gguf> [--sha256 HEX] [--json]
runtime\python\python.exe tools\validar_modelo.py --id <model_id>

ARQUIVOS
--------
- tools/validar_modelo.py (novo), VERSION.json (0.7.0-alpha6)

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_A6.bat + payload\).
2. Feche o NÚCLEO (não obrigatório; é um utilitário).
3. Execute INSTALAR_V0_7_A6.bat (roda autoteste com o 4B presente).

ROLLBACK
--------
ROLLBACK_V0_7_A6.bat remove o tool e restaura VERSION.json (volta ao alpha5).

VALIDADO (fora do Windows real, com modelos reais)
--------------------------------------------------
- 4B: GGUF v3, qwen3, context 40960, chat template presente, SHA256 confere.
- 8B (--id): SHA256 confere. SHA errado -> FALHA; não-GGUF -> FALHA.
