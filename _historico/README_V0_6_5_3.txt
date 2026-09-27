NÚCLEO IA PORTÁTIL — HOTFIX V0.6.5.3
Reaper de engines órfãs (corrige HTTP 401 Invalid API Key)
========================================

PROBLEMA CORRIGIDO
------------------
Mensagem no chat:
  llama-server HTTP 401: {"error":{"message":"Invalid API Key",...}}

CAUSA
-----
Ao encerrar o NÚCLEO de forma suja (fechar janela/crash/troca de sessão), o
llama-server ficava rodando como processo ÓRFÃO, segurando a porta 18081 com
a chave efêmera ANTIGA. A sessão seguinte gerava chave nova -> 401.

CORREÇÃO
--------
Novo _reap_orphan_servers() no engine_manager.py:
- encerra apenas llama-server cujo executável está sob a pasta engine\ DESTE
  projeto (nunca toca em llama-server de outro caminho);
- preserva o processo atual;
- roda na inicialização e a cada start();
- registra em logs\v0_6\orphan_reap.log.

Windows apenas; falha silenciosa (best-effort).

ARQUIVOS ALTERADOS
------------------
- app/engine_manager.py
- VERSION.json  (0.6.5.2 -> 0.6.5.3)

PRÉ-REQUISITO
-------------
Instale a V0.6.5.2 ANTES (o VERSION.json deste hotfix já inclui as flags da
0.6.5.2). Se ainda não instalou, rode INSTALAR_V0_6_5_2.bat primeiro.

INSTALAÇÃO
----------
1. Copie a pasta deste patch para dentro de E:\NUCLEO_IA_PORTATIL
   (INSTALAR_V0_6_5_3.bat e payload\ na raiz do projeto).
2. Feche o NÚCLEO e encerre qualquer llama-server ainda ativo
   (o instalador NÃO mata processos; a limpeza automática passa a valer
    a partir do próximo INICIAR).
3. Execute INSTALAR_V0_6_5_3.bat
4. Reabra INICIAR_NUCLEO_IA.bat

COMO TESTAR
-----------
- Abra o NÚCLEO, troque de perfil (RÁPIDO <-> QUALIDADE), feche a janela sem
  encerrar limpo, reabra. NÃO deve mais aparecer 401.
- Confira logs\v0_6\orphan_reap.log para ver o que foi encerrado.

ROLLBACK
--------
ROLLBACK_V0_6_5_3.bat restaura o estado anterior. A base V0.6 FINAL
CONSOLIDADA permanece intacta.

VALIDAÇÃO JÁ FEITA (fora do Windows real)
-----------------------------------------
- py_compile OK no Python portátil 3.13.13.
- Teste unitário da lógica do reaper (subprocess mockado): encerra só as
  engines do projeto, ignora as de fora. RESULTADO: OK.
