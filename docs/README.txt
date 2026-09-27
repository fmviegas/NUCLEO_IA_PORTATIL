NÚCLEO IA PORTÁTIL — V0.5 CONSOLIDADA
========================================

Status: V0.5 aprovada em teste real.

Entrada única:
  INICIAR_NUCLEO_IA.bat

Perfis já validados no Avell 1513-5 BS:
  RÁPIDO     Qwen3-4B / CUDA / 8 threads / 36 GPU layers / ~18.8 t/s
  QUALIDADE  Qwen3-8B / CUDA / 6 threads / 24 GPU layers / ~8.2 t/s
  AUTO       RÁPIDO

A pasta raiz definitiva é:
  \NUCLEO_IA_PORTATIL

A partir desta consolidação, números de versão não devem mais fazer parte
do nome da pasta principal. Versão e layout ficam registrados em VERSION.json.

Segurança:
- não formata o SSD;
- não altera partições;
- não altera Secure Boot;
- não instala Python no Windows;
- não apaga automaticamente a pasta antiga.

Após a migração, teste os modos RÁPIDO e QUALIDADE antes de remover o legado.
