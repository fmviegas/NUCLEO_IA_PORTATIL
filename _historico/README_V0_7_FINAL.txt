NÚCLEO IA PORTÁTIL — V0.7 FINAL (CONSOLIDAÇÃO)
==============================================
Portabilidade Real. Base estável de retorno (junto com V0.6 e V0.6.5 FINAL).

Consolida alphas 1–6: detecção defensiva + perfil versionado; fallback CPU sem
NVIDIA + simulação; catálogo de modelos; calibração via catálogo (schema v3);
motor resolve modelo por id; validar_modelo.py (§25).

A consolidação grava VERSION 0.7/final/stable, manifesto SHA256 (20 arquivos),
validador e release doc; NÃO altera o código do app (já em alpha6).

INSTALAÇÃO
1. Copie para E:\NUCLEO_IA_PORTATIL (INSTALAR_V0_7_FINAL.bat + payload\).
2. Feche o NÚCLEO.
3. Execute INSTALAR_V0_7_FINAL.bat  (valida ao final).
4. Reconferir quando quiser: VALIDAR_V0_7_FINAL.bat

ROLLBACK: ROLLBACK_V0_7_FINAL.bat (volta VERSION; código fica na base alpha6).

ITENS EM ABERTO (não bloqueiam): teste multi-máquina real; modelo LEVE real.
