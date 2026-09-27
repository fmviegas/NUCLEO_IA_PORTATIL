# NÚCLEO IA PORTÁTIL — V0.9 FINAL

## Estado
Consolida o **Escritor de Livros 360°** sobre a V0.7 FINAL. Base estável de
retorno (junto com V0.6 FINAL, V0.6.5 FINAL e V0.7 FINAL). Sem novas dependências.

## Consolida (alphas 1–7)
- **a1** scaffolder da estrutura **00–08** por gênero + planner + linter anti-IA.
- **a2/a3/a4** outline via LLM: prompt compacto → lotes anti-loop → ritmo por ato.
- **a5/a6** escrita capítulo a capítulo (resumo encadeado) + anti-repetição (dedup + corte de refrão).
- **a7** revisão: auditoria de consistência (nomes×bíblia, dia/noite), passe de
  humanização consolidado, e compilação do manuscrito.

## Ferramentas (lançadores na raiz)
`CRIAR_LIVRO` · `PLANO_LIVRO` · `OUTLINE` · `ESCREVER` · `HUMANIZAR` · `REVISAR`.
Livros em `workspace\livros\<slug>\` com a estrutura 00–08. Personas em
`config\personas\`. Módulos em `app\book\`.

## Fluxo
```
CRIAR_LIVRO → (preencher 01_FUNDACAO/BIBLIA.md e 00_GOVERNANCA)
OUTLINE gerar/aplicar → ESCREVER proximo (cap a cap) → REVISAR tudo → 08_PUBLICACAO/MANUSCRITO.md
```

## Integridade
`app/manifests/manifest_v0_9_final.json` (29 arquivos SHA256). Rode
`VALIDAR_V0_9_FINAL.bat` a qualquer momento.

## Itens em aberto (não bloqueiam)
- fatia 5: aba "Livros" na UI (hoje o fluxo é por .bat/CLI).
- modelo AVANÇADO no catálogo (12–14B+) para prosa longa de melhor qualidade;
  4B/8B geram rascunho — a coerência vem do resumo encadeado + bíblia + auditoria.
- teste multi-máquina real (portabilidade V0.7).

## STATUS
**ESTÁVEL / BASE DE RETORNO.**
