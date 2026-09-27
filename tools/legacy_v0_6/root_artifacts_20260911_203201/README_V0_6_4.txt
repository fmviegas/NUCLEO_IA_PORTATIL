NÚCLEO IA PORTÁTIL — V0.6.4
================================

FOCO
----
Polimento e Estabilidade.

Esta versão não tenta acrescentar um novo grande recurso.
Ela consolida e endurece o que já foi validado em campo.

PRINCÍPIO
---------
Minimalismo funcional.

MELHORIAS
---------
1. Hotfixes consolidados
   - UTF-8/CP1252 da V0.6.2.1 incorporado ao código normal.
   - sonda real single-turn da V0.6.2.2 incorporada ao AutoTune.

2. Calibração com heartbeat
   A tela agora mostra tempo total e tempo da etapa.
   Se uma sonda demorar, aparece explicitamente "Teste em andamento".

3. Menor consumo do llama-server
   Quando suportado pela versão instalada:
   - --parallel 1
   - --no-webui
   O NÚCLEO é mono-usuário; não precisamos manter slots extras.

4. Proteção do llama-server
   Quando --api-key é suportado, uma chave efêmera é criada a cada
   execução. A chave nunca é mostrada ao navegador; fica apenas entre
   backend Python e llama-server.

5. Inicialização duplicada
   Se o NÚCLEO já estiver rodando em 127.0.0.1:18080, um segundo
   INICIAR_NUCLEO_IA.bat apenas reabre o navegador. Não carrega outro modelo.

6. Interface
   - botão Reparar só fica habilitado quando o componente realmente
     apresenta problema;
   - estado "CPU forçada" aparece no rodapé;
   - polling de calibração é encerrado ao finalizar/cancelar/errar.

7. Sessões
   - arquivos temporários abandonados são limpos;
   - conversas vazias com mais de 24 horas são removidas;
   - conversas reais nunca são apagadas por essa limpeza.

8. Servidor web local
   Cabeçalhos de segurança adicionados:
   - Content-Security-Policy
   - X-Frame-Options
   - X-Content-Type-Options
   - Referrer-Policy

INSTALAÇÃO
----------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     INSTALAR_V0_6_4.bat

3. Abra:
     INICIAR_NUCLEO_IA.bat

TESTE CURTO RECOMENDADO
-----------------------
Não é necessário executar outra calibração completa.

1. Chat
   Envie uma mensagem curta em AUTO.

2. Histórico
   Confirme que a conversa continua sendo salva.

3. Inicialização duplicada
   Com o NÚCLEO aberto, execute INICIAR_NUCLEO_IA.bat novamente.
   Deve apenas reabrir a interface, sem carregar outro modelo.

4. Manutenção
   Abra Manutenção.
   Em uma máquina saudável, Reparar CUDA/CPU deve permanecer desabilitado.

5. CPU
   Use "Usar CPU agora", envie uma mensagem curta e depois
   "Usar backend do perfil".

6. Heartbeat da calibração
   Opcional: abra Recalibrar, inicie e observe o contador de tempo.
   Pode cancelar o teste; não é necessário completar outra calibração.

ROLLBACK
--------
ROLLBACK_V0_6_4.bat

O rollback restaura os arquivos exatamente como estavam antes da instalação.
Perfis, sessões, modelos e logs não são apagados.
