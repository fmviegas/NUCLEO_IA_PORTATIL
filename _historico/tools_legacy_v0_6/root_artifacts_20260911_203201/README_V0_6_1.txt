NÚCLEO IA PORTÁTIL — V0.6.1
================================

FOCO
----
Sessões e Histórico Local, mantendo o princípio de Minimalismo funcional.

NOVO
----
- histórico persistente em JSON;
- botão ☰ abre o histórico somente sob demanda;
- até 20 conversas recentes carregadas inicialmente;
- recuperação automática da última conversa não vazia;
- título automático simples pela primeira mensagem do usuário;
- nenhuma chamada extra ao modelo para criar título;
- exclusão individual de conversas;
- Nova conversa;
- prompt do usuário é salvo antes da geração;
- resposta é salva quando a geração termina;
- histórico permanece inteiramente no SSD.

ARMAZENAMENTO
-------------
sessions\
  YYYY\
    MM\
      <session_id>.json

Não há SQLite, banco externo, nuvem ou serviço de terceiros.

COMO INSTALAR
-------------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     INSTALAR_V0_6_1.bat

3. Depois:
     INICIAR_NUCLEO_IA.bat

TESTE SUGERIDO
--------------
1. Abra uma conversa e faça duas perguntas.
2. Clique em ☰ e confirme que a conversa aparece no histórico.
3. Feche o NÚCLEO.
4. Abra novamente.
5. A última conversa deve ser restaurada automaticamente.
6. Crie uma Nova conversa.
7. Volte à conversa anterior pelo histórico.
8. Exclua uma conversa de teste.

ROLLBACK
--------
ROLLBACK_V0_6_1.bat

O rollback restaura a interface V0.6.0 e PRESERVA a pasta sessions\.
