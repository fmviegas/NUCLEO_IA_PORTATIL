# NÚCLEO IA PORTÁTIL — V0.9 Escritor 360°, fatia 4 (alpha7)

## Revisão (auditoria + humanização) e compilação

**Base:** V0.9.0-alpha6. **Escopo:** novo `app/book/revisar.py` + `REVISAR.bat`.
Ferramentas determinísticas (sem LLM) para o Estágio de Revisão.

### Comandos
```
REVISAR.bat auditar   --dir workspace\livros\<slug>
REVISAR.bat humanizar --dir workspace\livros\<slug>
REVISAR.bat compilar  --dir workspace\livros\<slug>
REVISAR.bat tudo      --dir workspace\livros\<slug>
```

### O que faz
- **auditar** → `07_REVISAO/AUDITORIA.md`: nomes próprios recorrentes × bíblia
  (🚨 nome do protagonista trocado/não declarado), grafias divergentes do mesmo
  nome, conflito DIA/NOITE no mesmo capítulo (🟡), expressões de tempo divergentes.
- **humanizar** → `07_REVISAO/PASSE_HUMANIZACAO.md`: roda o linter anti-IA em
  todos os capítulos + redundância entre capítulos, consolidado.
- **compilar** → `08_PUBLICACAO/MANUSCRITO.md`: capa (título/autor da bíblia) +
  capítulos em ordem + contagem total de palavras.
- **tudo** → os três.

### Validado (fora do Windows real, no cap_01 gerado)
- auditar pegou: 🚨 "Luís aparece 28x; bíblia diz Lucas" e 🟡 dia/noite no mesmo
  capítulo — exatamente as inconsistências reais.
- compilar montou o MANUSCRITO.md com contagem; humanizar consolidou os alertas.

### Como usar no fluxo
Depois de escrever capítulos: `REVISAR.bat tudo` → leia AUDITORIA.md (corrija
nomes/tempo), aja sobre PASSE_HUMANIZACAO.md (reduza tiques à mão), e gere o
MANUSCRITO.md. A auditoria é o antídoto para a deriva de nome/coerência que o
modelo pequeno produz.

### Rollback
`ROLLBACK_V0_9_A7.bat` remove `revisar.py` e `REVISAR.bat` e restaura VERSION.
