# V0.6.5 — Arquivos e Análise Local

## Objetivo

Adicionar anexos locais sem transformar o NÚCLEO em uma suíte pesada.

## Formatos iniciais

- XLSX
- CSV
- TXT
- MD
- JSON

Tudo é processado localmente. Não há upload para nuvem.

## Planilhas

O NÚCLEO calcula de forma determinística:

- quantidade de linhas/colunas;
- faltantes;
- soma, média, mínimo e máximo em colunas numéricas;
- valores categóricos frequentes;
- abas e fórmulas em XLSX;
- possíveis diferenças de padrão de fórmulas.

### Limitação importante

A V0.6.5 **não possui motor do Excel**.

Ela lê fórmulas e valores armazenados no XLSX, mas não recalcula a pasta de
trabalho. Uma inconsistência de fórmula é um indício para revisão, não a prova
de que o cálculo está errado.

## Segurança

- macros não são executadas;
- scripts anexados não são executados;
- apenas extensões permitidas são aceitas;
- 25 MB por arquivo;
- 5 arquivos e 50 MB por conversa;
- XLSX possui limites de expansão para reduzir risco de ZIP bomb;
- arquivos ficam em `workspace/sessions/<session_id>/`.

## Arquitetura

Usuário pergunta -> ferramenta extrai/calcula -> contexto compacto ->
Qwen interpreta.

A conversa salva o texto normal. O contexto técnico dos arquivos é injetado
somente no momento da geração e não polui o histórico.
