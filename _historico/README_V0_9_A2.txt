NÚCLEO IA PORTÁTIL — V0.9 ESCRITOR 360 (alpha2) — Outline via LLM
================================================================
ALPHA. Requer a fatia 1. Base de retorno: V0.7 FINAL.

O QUE ENTRA: app/book/outline.py + OUTLINE.bat + VERSION.
USO:
  OUTLINE.bat gerar   --dir workspace\livros\<slug> [--modo auto|fast|quality]
  OUTLINE.bat prompt  --dir workspace\livros\<slug>
  OUTLINE.bat aplicar --dir workspace\livros\<slug>
Monta prompt compacto (bíblia + brief de gênero + humanização) e pede o outline
ao motor; grava 02_ARQUITETURA/OUTLINE_GERADO.md. 'aplicar' leva os títulos ao
PLANO_DE_CAPITULOS. Se o motor não estiver pronto, cai para OUTLINE_PROMPT.md.

INSTALAR: INSTALAR_V0_9_A2.bat   ·   ROLLBACK: ROLLBACK_V0_9_A2.bat
VALIDADO (offline): prompt ~497 tokens (cabe em 4096); aplicar OK. 'gerar' via
motor: testar no Avell.
