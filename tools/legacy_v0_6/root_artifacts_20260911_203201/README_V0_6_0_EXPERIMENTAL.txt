NÚCLEO IA PORTÁTIL — V0.6.0 EXPERIMENTAL
==========================================

OBJETIVO
--------
Primeiro protótipo funcional da Interface Local.

Princípio:
  MINIMALISMO FUNCIONAL

Stack:
  - Python padrão/stdlib
  - llama-server existente
  - HTML puro
  - CSS puro
  - JavaScript puro
  - nenhuma dependência web externa
  - nenhuma instalação Node/Electron/React

ESCOPO DESTA EXPERIMENTAL
-------------------------
Incluído:
  - navegador como interface principal
  - inicialização automática do llama-server
  - AUTO / RÁPIDO / QUALIDADE
  - streaming de resposta
  - botão Parar
  - Nova conversa
  - detalhes técnicos sob demanda
  - loopback somente em 127.0.0.1
  - fallback CUDA -> CPU
  - tratamento amigável de erros do motor

Ainda NÃO incluído:
  - histórico persistente
  - calibração gráfica
  - anexos/RAG
  - voz
  - internet
  - plugins
  - interface escondendo totalmente a janela de console

COMO INSTALAR
-------------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     INSTALAR_V0_6_0_EXPERIMENTAL.bat

3. Depois execute normalmente:
     INICIAR_NUCLEO_IA.bat

O navegador padrão deve abrir sozinho.

TESTE SUGERIDO
--------------
1. Confirme que aparece IA PRONTA.
2. AUTO deve selecionar RÁPIDO no Avell já calibrado.
3. Envie:
     Responda apenas: interface local funcionando.
4. Troque para QUALIDADE.
5. Envie:
     Responda apenas: modo qualidade na interface funcionando.
6. Teste Shift+Enter para múltiplas linhas.
7. Teste o botão Parar em uma resposta longa.

ROLLBACK
--------
Se a experimental não funcionar:
  ROLLBACK_V0_6_0_EXPERIMENTAL.bat

O instalador faz backup somente dos pequenos arquivos substituídos.
Modelos e perfis V0.5 não são alterados.
