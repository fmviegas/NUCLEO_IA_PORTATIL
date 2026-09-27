NÚCLEO IA PORTÁTIL — V0.6.2
================================

FOCO
----
Calibração Gráfica mantendo o princípio de Minimalismo funcional.

O QUE MUDA
----------
- Detalhes > Recalibrar computador;
- progresso da calibração na própria interface;
- máquina sem perfil abre automaticamente a tela "Novo computador detectado";
- CPU/GPU ficam livres para o AutoTune durante o processo;
- ao concluir, o perfil é recarregado e o modo AUTO inicia sozinho;
- cancelar é permitido;
- erro mostra mensagem amigável e detalhes técnicos sob demanda;
- perfil anterior é preservado se uma recalibração falhar;
- nenhuma dependência nova.

IMPORTANTE
----------
A V0.6.2 NÃO cria um segundo algoritmo de calibração.

Ela usa:
  app\autotune.py
  app\benchmark.py

ou seja, o AutoTune chat-stable validado na V0.5 continua sendo a referência.

FLUXO DE MÁQUINA NOVA
---------------------
SSD conectado
  -> NÚCLEO detecta Machine ID
  -> nenhum perfil encontrado
  -> navegador abre
  -> "Novo computador detectado"
  -> Iniciar calibração
  -> CPU / CUDA / RAM / VRAM / chat-stable
  -> profiles\machines\<machine_id>.json
  -> AUTO inicia o perfil recomendado

COMO INSTALAR
-------------
1. Extraia este ZIP dentro de:
     E:\NUCLEO_IA_PORTATIL

2. Execute:
     INSTALAR_V0_6_2.bat

3. Abra:
     INICIAR_NUCLEO_IA.bat

TESTE NA MÁQUINA ATUAL
----------------------
Como o Avell já possui perfil:

1. Abra Detalhes.
2. Clique "Recalibrar computador".
3. Confirme que aparecem CPU, RAM, GPU e Machine ID.
4. Inicie a calibração.
5. Acompanhe a barra de progresso.
6. Ao final, confirme RÁPIDO / QUALIDADE / AUTO.
7. Envie uma mensagem no chat para verificar que o motor voltou.

A V0.5 reutiliza o benchmark base quando ele já pertence à mesma máquina.
Por isso a recalibração do Avell pode ser mais curta do que a primeira
calibração em um computador novo.

ROLLBACK
--------
ROLLBACK_V0_6_2.bat

O rollback restaura a V0.6.1 e preserva:
- sessions\
- profiles\machines\
- state\
- logs\
