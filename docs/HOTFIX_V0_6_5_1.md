# V0.6.5.1 — correção de conclusão de análises

O teste de campo mostrou uma resposta XLSX cortada no meio de uma palavra.

A causa estava no limite histórico de 1024 tokens de saída em
`EngineManager.stream_chat()`. A V0.6.5 acrescentou contexto de arquivos,
fazendo uma resposta detalhada atingir esse teto com mais facilidade.

A V0.6.5.1 mantém o contexto 4096 da máquina, aumenta o teto máximo de saída,
faz orçamento aproximado de contexto e detecta `finish_reason`.

Também reduz ruído de planilhas tipo formulário ao omitir colunas totalmente
vazias do resumo determinístico.

Validação de runtime real continua dependendo do teste no Windows/llama-server.
