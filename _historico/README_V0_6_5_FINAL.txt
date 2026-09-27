NÚCLEO IA PORTÁTIL — V0.6.5 FINAL (CONSOLIDAÇÃO)
================================================

O QUE É
-------
Marca a linha 0.6.5.x como base ESTÁVEL de retorno (junto com a V0.6 FINAL):
- 0.6.5   anexos + análise determinística
- 0.6.5.1 anti-truncamento (finish_reason)
- 0.6.5.2 leitura semântica de planilhas
- 0.6.5.3 reaper de engines órfãs (anti-401)
- 0.6.5.4 formulário multi-bloco + classificador por adjacência

O QUE A CONSOLIDAÇÃO FAZ
------------------------
- grava VERSION.json = 0.6.5 / release=final / channel=stable;
- adiciona app/manifests/manifest_v0_6_5_final.json (SHA256 do código/UI);
- adiciona tools/validar_v0_6_5_final.py e docs/RELEASE_V0_6_5_FINAL.md;
- grava state/v0_6_5_final_install.json (marcador de retorno);
- valida tudo com o validador (arquivos, compilação, funções, SHA256).

NÃO altera o código do app (já está em 0.6.5.4), nem modelos/perfis/sessões.

PRÉ-REQUISITO
-------------
A linha 0.6.5.x já instalada (state\v0_6_5_2/3/4_install.json presentes).

INSTALAÇÃO
----------
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_6_5_FINAL.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_6_5_FINAL.bat
4. (Opcional) rode VALIDAR_V0_6_5_FINAL.bat quando quiser reconferir.

ROLLBACK
--------
ROLLBACK_V0_6_5_FINAL.bat volta o VERSION.json ao estado anterior
(o código permanece na base 0.6.5.4). A V0.6 FINAL nunca é tocada.
