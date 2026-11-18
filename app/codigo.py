#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codigo.py — Menu CÓDIGO: tarefas de programação com o modelo local do modo
CODIGO (Python avançado — local e web — e T-SQL / SQL Server).

Cada tarefa = instruções curtas (o modelo local tem contexto pequeno) com o
processo, o formato de saída e os erros a evitar. Texto PRÓPRIO do NÚCLEO:
os skills de terceiros em skills/ serviram só de inspiração e não são
distribuídos (ficam fora do git e da cópia portátil).

Regra de honestidade para todas as tarefas: o app NÃO executa código. O
modelo nunca diz que rodou/testou nada; entrega o comando exato para rodar.

Cada stack tem GATILHOS (palavras do pedido/código) para a tela sugerir a stack
sozinha — sugerir_stack(). Ideia aproveitada do catalog.json de skills/fontes;
a lista é própria e evita palavras genéricas ("erro", "dados", "modelo").
"""
from __future__ import annotations

import re
import unicodedata

# Amostragem p/ código: temperatura baixa e SEM a penalidade de repetição do
# chat (1.15 + DRY), que pune o que código repete de propósito (indentação,
# nomes, padrões). Um leve repeat_penalty segura loop em modelo pequeno.
AMOSTRAGEM_CODIGO = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "min_p": 0.05,
    "repeat_penalty": 1.05,
    "repeat_last_n": 128,
    "dry_multiplier": 0.0,
}

# Sobra mínima de contexto p/ valer a pena gerar: abaixo disso o motor só consegue
# escrever um toco e o modelo pequeno se perde (recomeça a resposta do início).
MIN_SAIDA_TOKENS = 600


def tokens_estimados(system: str, msgs: list) -> int:
    """Estimativa p/ a GUARDA de contexto do código: ~3,5 caracteres por token.
    Código tende a ~3,5-4 chars/token (menos tokens que PT-BR), então 3,5 é menos
    pessimista que os ~3,2 do motor — o guard deixa de disparar cedo demais, sem liberar
    pedidos que de fato não cabem. Sem tokenizer."""
    chars = len(system or "") + sum(len(str(m.get("content") or "")) for m in msgs)
    return max(1, int(chars / 3.5)) + (len(msgs) + 1) * 8


def folga_contexto(system: str, msgs: list, context_size: int) -> int:
    """Tokens que sobram p/ a resposta (pode ser negativo). 320 = margem de segurança do motor."""
    return int(context_size) - tokens_estimados(system, msgs) - 320

STACKS = {
    "python": {
        "label": "Python — sistema local (CLI, automação, desktop, serviços)",
        "regras": [
            "Python 3.11+ with type hints, dataclasses or Pydantic where they help, pathlib for paths, logging (not print) for diagnostics.",
            "Prefer the standard library; add a third-party dependency only when it clearly pays off, and list it in requirements.txt with a pinned minimum version.",
            "Structure: small functions with one job, a main() guarded by if __name__ == '__main__', argparse (or Typer if already used) for CLIs.",
            "Catch specific exceptions; never use bare except or silently swallow errors. Close resources with context managers. Let errors surface with context instead of hiding them.",
            "Correctness of 'empty': distinguish `is None` from truthiness — 0, 0.0, '' and [] are valid values, so test `if x is None` (not `if not x`) whenever the zero/empty case is meaningful, and never compare with `== None`.",
            "Classic traps: never use a mutable default argument (use None and create the list/dict inside); never compare floats with == (math.isclose) and keep money in decimal.Decimal or integer cents; int() truncates, round() rounds; sorted() returns a new list while list.sort() returns None; itertools.groupby only groups consecutive items, so sort by the same key first; test membership in a set, not a list, inside loops.",
            "Files: open text inside `with` and always pass encoding='utf-8' (Windows defaults to cp1252); read CSV with the csv module, never split(','); parse dates with datetime instead of keeping strings — Brazilian dd/mm/yyyy always with an explicit format ('%d/%m/%Y', or pd.to_datetime(..., format='%d/%m/%Y')), never letting the parser guess day vs month; write important output atomically (temp file in the same folder, then os.replace); json.dump(..., ensure_ascii=False).",
            "Idiomatic Python: prefer comprehensions and generator expressions over manual accumulation loops; iterate with enumerate/zip and use dict.get(key, default)/setdefault; reach for the standard library (collections, itertools, pathlib, datetime) before writing it by hand.",
            "Desktop UI: Tkinter (standard library) unless the user names PySide6/PyQt.",
            "Data work: use pandas/numpy for tabular data — vectorize, avoid Python row loops; inspect first (df.head/info/describe, check NA and dtypes) before transforming; read/write CSV/Excel with explicit encoding and dtypes.",
            "Talking to the web: requests with a timeout and r.raise_for_status(); parse static HTML with BeautifulSoup and reach for Selenium only on JS-rendered pages; set a real User-Agent, respect robots.txt and rate limits, and read tokens/secrets from environment variables.",
            "80/20 pragmatism: prefer the few tools that cover most cases; every script runs as-is (no '...'), shows the exact command to run it, and is idempotent — dry-run first for anything destructive.",
            "Windows is the user's OS: give commands for PowerShell (python -m venv .venv; .venv\\Scripts\\Activate.ps1; pip install -r requirements.txt).",
        ],
        "gatilhos": {
            "fortes": ["python", "pathlib", "argparse", "tkinter", "pyinstaller", "venv", "pyside6", "pyqt"],
            "fracos": ["script", "automacao", "automatizar", "def", "import", "pip", "requirements", "planilha",
                       "excel", "csv", "pasta", "cli", "selenium", "beautifulsoup", "requests", "scraping",
                       "pytest", "openpyxl", "pandas", "dataframe", "numpy"],
        },
    },
    "pyweb": {
        "label": "Python — web (FastAPI, Flask ou Django)",
        "regras": [
            "Default to FastAPI + Pydantic v2 + Uvicorn unless the user names Flask or Django; then follow that framework's current idioms.",
            "Database access with SQLAlchemy 2.0 style (select(), Session) or the framework ORM; always parameterized queries, never string-built SQL.",
            "Validate input at the boundary (Pydantic models / forms); keep business logic in plain functions or services, not in route handlers.",
            "Correct HTTP semantics: GET safe, POST create/action, PUT replace, PATCH partial, DELETE remove; 201 on create, 204 on empty success, 400/401/403/404/409/422 used precisely; one consistent error shape (RFC 9457 problem+json when there is no existing convention).",
            "Authentication is not authorization: check that the caller may access THIS resource. Secrets come from environment variables (.env + .env.example), never hard-coded.",
            "List endpoints need pagination (limit/offset or cursor) from the start.",
            "Give the run command (uvicorn app.main:app --reload) and the URL of the auto docs when using FastAPI.",
        ],
        "gatilhos": {
            "fortes": ["fastapi", "flask", "django", "uvicorn", "pydantic", "endpoint", "api rest", "rest api", "jinja"],
            "fracos": ["api", "rota", "http", "jwt", "login", "autenticacao", "middleware", "cors", "webhook",
                       "site", "backend"],
        },
    },
    "tsql": {
        "label": "T-SQL — SQL Server (procedures, consultas, índices)",
        "regras": [
            "Confirm the engine first: this stack targets SQL Server; if the user's code, error or connection string shows another engine (PostgreSQL, MySQL, SQLite, Oracle), say so in one line and use that engine's dialect instead of forcing T-SQL.",
            "Target Microsoft SQL Server (T-SQL). Schema-qualify every object (dbo.Table). No SELECT * in production code.",
            "Procedures: SET NOCOUNT ON; SET XACT_ABORT ON; BEGIN TRY / BEGIN TRAN ... COMMIT / END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK; THROW; END CATCH.",
            "Use CREATE OR ALTER and idempotent scripts (IF NOT EXISTS / IF OBJECT_ID(...) IS NULL) so they can be re-run safely.",
            "Validate parameters first (NULL, <= 0, invalid combinations such as same source and target). Exact syntax: THROW 50001, N'mensagem clara', 1;  (three arguments separated by commas; the statement before THROW must end with ;).",
            "No check-then-act races: put the condition inside the UPDATE (WHERE Id = @Id AND Saldo >= @Valor) and test @@ROWCOUNT; every UPDATE/DELETE that must hit a row is followed by IF @@ROWCOUNT = 0 THROW.",
            "Dates: DATETIME2 with SYSDATETIME() (or SYSUTCDATETIME()), not GETDATE(). Script files go in a sql/ folder named after the object (sql/dbo.NomeDoObjeto.sql).",
            "Never build SQL by concatenating user input; for dynamic SQL use sp_executesql with parameters and QUOTENAME for identifiers.",
            "NULL and order: test with IS NULL / IS NOT NULL (never = NULL); `col <> 'x'` silently drops NULL rows, so add OR col IS NULL when they count; TOP always comes with ORDER BY; parenthesize mixed AND/OR.",
            "Check the grain before aggregating: a join that multiplies rows inflates SUM — aggregate before joining or fix the join, never hide duplicates with DISTINCT; in a LEFT JOIN count COUNT(child.col), not COUNT(*); a WHERE filter on the right-hand table turns the LEFT JOIN into an INNER one — put it in ON.",
            "Write SARGable predicates (no functions on indexed columns in WHERE/JOIN); suggest supporting indexes with key columns + INCLUDE and explain why — every index slows writes, so it is a conscious trade; when a scan happens despite an index, compare estimated vs actual rows (stale statistics) before adding another.",
            "Right types: DATETIME2, DECIMAL(p,s) for money, NVARCHAR for user text, explicit lengths. Prefer set-based logic over cursors/WHILE loops.",
            "Do not recommend NOLOCK as a performance fix; mention isolation trade-offs instead. Be careful with MERGE (prefer separate UPDATE/INSERT unless MERGE is clearly right).",
            "Performance is measured, not guessed: read the execution plan to find the real bottleneck before changing anything; show the verification query and its expected output.",
            "SELECT/JOIN/aggregation, CTEs and window functions are the daily core — reach for a window function or CTE instead of a correlated subquery, self-join or cursor when it fits. A window function cannot go in WHERE: compute it in a CTE and filter outside; running totals spell the frame (ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) because the default RANGE frame sums ties together; a recursive CTE needs a termination condition.",
            "DDL: name every constraint (PK_, FK_, UQ_, CK_, DF_); adding a NOT NULL column to a populated table needs a DEFAULT; plan ALTER/REBUILD on large tables for low-traffic windows; a plain view organizes a query but does not make it faster.",
            "Destructive commands (UPDATE/DELETE/DROP/TRUNCATE) run inside an explicit transaction as a safety net, after a SELECT that previews the affected rows, then check @@ROWCOUNT before COMMIT; never leave a transaction open (every script ends in COMMIT or ROLLBACK); TRUNCATE is not DELETE (resets IDENTITY, fires no triggers); back up before structural changes — and a backup only counts after a tested restore.",
        ],
        "gatilhos": {
            "fortes": ["t-sql", "tsql", "sql server", "procedure", "ssms", "mssql", "plano de execucao",
                       "create table", "alter table", "sp_executesql"],
            "fracos": ["sql", "select", "join", "where", "indice", "consulta", "query", "tabela", "banco de dados",
                       "view", "cte", "window function", "deadlock", "transacao", "rollback", "backup", "restore",
                       "trigger"],
        },
    },
    "pysql": {
        "label": "Python + SQL Server — integração (pyodbc/SQLAlchemy, ETL, CRUD)",
        "regras": [
            "Connect with pyodbc and 'ODBC Driver 18 for SQL Server' (Encrypt=yes; TrustServerCertificate=yes only on a local dev server), or SQLAlchemy 2.0 with mssql+pyodbc when an ORM or pandas is involved. Server, database and credentials come from environment variables; use Trusted_Connection=yes when the user uses Windows authentication.",
            "Every value goes as a parameter: cursor.execute('... WHERE Id = ?', (id_,)) or SQLAlchemy text() with :name binds — never f-strings, % or concatenation. Table and column names cannot be parameters: check them against an explicit whitelist.",
            "Explicit unit of work: autocommit off, conn.commit() once at the end, conn.rollback() on any exception, then close. pyodbc's `with conn:` commits or rolls back but does NOT close the connection — close it (contextlib.closing or finally).",
            "Bulk loads: cursor.fast_executemany = True with executemany in batches (1,000-10,000 rows); with pandas, create_engine(..., fast_executemany=True) and df.to_sql(..., chunksize=...); read with pd.read_sql(sql, conn, params=...).",
            "Map types on purpose: decimal.Decimal for DECIMAL/money, datetime for DATETIME2, None for NULL, str for NVARCHAR — never float for money.",
            "Errors: catch pyodbc.Error (pyodbc.IntegrityError for duplicate keys/constraints), log the SQLSTATE and the operation, and re-raise with context; retry only transient errors (deadlock 1205, timeout) with a small limit and backoff.",
            "ETL is idempotent: validate the file first (encoding, delimiter, header, types), load into a staging table, then upsert into the target inside one transaction; report rows read, inserted, updated and rejected.",
            "SQL side keeps T-SQL discipline: schema-qualified names (dbo.Table), no SELECT *, SET NOCOUNT ON in procedures called from Python, and the least-privileged login (never sa).",
            "Windows is the user's OS: show the PowerShell check for the installed driver (Get-OdbcDriver), pip install pyodbc, and the exact run command.",
        ],
        "gatilhos": {
            "fortes": ["pyodbc", "pymssql", "sqlalchemy", "read_sql", "to_sql", "fast_executemany", "odbc", "etl",
                       "string de conexao", "connection string"],
            "fracos": ["carga", "importar", "exportar", "crud", "persistencia", "integracao"],
        },
    },
    "dados": {
        "label": "Dados — análise e estatística honesta (pandas + estatística aplicada)",
        "regras": [
            "Look at the data before modelling it: df.head/info/describe, plot the distribution, count groups and NAs — descriptive statistics before any inference.",
            "Read data explicitly: encoding='utf-8', explicit dtypes, Brazilian dates with format='%d/%m/%Y' (never let the parser guess day vs month), and when the user has several files read them all (pathlib glob + pd.concat) instead of a single hard-coded name.",
            "Draws and categories (lottery, dice, survey answers): stack all draw columns into one before counting (melt or ravel), include values that never appeared (count 0), compare with the uniform expectation using a chi-square goodness-of-fit test (scipy.stats.chisquare), and state plainly that past frequencies do not predict the next draw — independent draws have no memory (gambler's fallacy).",
            "Never present a bare estimate. Every number ships with its magnitude (the effect size, not just 'significant') and its uncertainty (a confidence interval). A number alone is a suspect number.",
            "Keep sample and population apart: you compute on the sample but conclude about the population; never treat the sample as if it were the whole population, and ask how the sample was selected — non-random selection can manufacture correlations.",
            "Decide first: predict or explain? Prediction is judged out of sample, with predictors available at the moment of use; explanation needs a causal story (a DAG): control for confounders, never for colliders — 'control for everything' can create bias.",
            "Correlation is not causation, and a correlation can even flip sign under a confounder (Simpson's paradox). Check subgroups and state the assumptions behind any causal claim.",
            "Read the p-value correctly: it is P(data this extreme | H0 true), NOT the probability that H0 is true; 'not significant' is not 'no effect'. Report effect size + confidence interval, not just p.",
            "Test defaults that avoid classic errors: Welch's t-test (equal_var=False); two-sided unless the direction was fixed before seeing the data; correct for multiple comparisons (Holm or FDR); chi-square only with expected counts >= 5 (otherwise Fisher's exact test); a confidence interval uses the standard error s/sqrt(n), not s.",
            "Regression: inspect the residuals and never trust R2 alone — a high R2 can mislead, and coefficients shift with confounders and collinearity (check VIF; above 5 is an alarm); compare adjusted R2, validate out of sample and never extrapolate beyond the range of the data.",
            "Describe honestly: codes that look numeric (CEP, IDs) are labels, not numbers; with skewed data report the median beside the mean; never report a correlation r without its scatter plot; check normality (histogram, Q-Q plot) instead of assuming it.",
            "Reproducibility: every number, table and figure comes from runnable Python (pandas/numpy, scipy/statsmodels); set a random seed; nothing computed by hand.",
            "Say honestly what the data does and does NOT allow concluding; prefer a few tools used correctly (mean/SD, confidence interval, one hypothesis test, correlation, regression) over exotic methods.",
        ],
        "gatilhos": {
            "fortes": ["estatistica", "p-valor", "p valor", "intervalo de confianca", "teste de hipotese", "hipotese",
                       "regressao", "correlacao", "desvio padrao", "significancia", "significativo", "significativa",
                       "statsmodels", "scipy", "anova", "teste t", "qui-quadrado", "probabilidade", "aleatorio",
                       "aleatoriamente", "sorteio", "loteria"],
            "fracos": ["media", "mediana", "amostra", "distribuicao", "outlier", "grafico", "matplotlib", "seaborn",
                       "analise", "analisar", "tendencia", "variancia", "frequencia", "sorteados", "dezena"],
        },
    },
    "ia": {
        "label": "IA — sistemas de IA, agentes e contexto (do modelo à produção)",
        "regras": [
            "Using a model is not building a system: production needs context, data, evaluation, integration, security, observability and failure handling — not just a good prompt.",
            "Smallest sufficient architecture: pick the least complex design that meets the requirement; add RAG, tools or agents only when a concrete need justifies it.",
            "Define verifiable success criteria and evaluate on task-like conditions BEFORE shipping; never generalise capability from one impressive demo — build an eval set with metrics.",
            "Eval hygiene: keep few-shot examples, training data and the eval set separate, and never generate the eval with the same model; an LLM judge comes from another model family, scores both orderings and is calibrated against humans; in RAG grade faithfulness to the retrieved context, not only correctness.",
            "Diagnose the right layer (model / application / data / integration): if the app retrieved the wrong document, swapping the model will not fix it.",
            "RAG discipline: control which documents and versions, enforce the caller's permissions, cite the sources, and when information is missing return 'insufficient' instead of inventing; evaluate retrieval, not only generation — a reranker cannot recover a passage that never reached the candidates, so measure recall first; vector similarity is not equivalence (negations look alike).",
            "Structured output is a contract: define it with Pydantic or JSON Schema, validate it, retry a bounded number of times, then abstain instead of guessing. Agent loops have a step limit and a verifiable stop criterion; a task is done only when the state holds the evidence — the model saying 'done' is not proof.",
            "Side effects need idempotency: a timeout does not undo a write, so send an idempotency key or query the previous attempt before retrying; retry in ONE layer only (disable SDK/library retries or yours) and honour 429 Retry-After with backoff and a cap.",
            "Prompt injection is stopped by software, not by a sentence in the prompt: tool outputs, retrieved documents and MCP prompts are untrusted data; give each tool a least-privilege credential scoped to it — never the application's master key — and require confirmation for irreversible actions.",
            "Pin exact model identifiers (never a 'latest' alias), log the model id the API returns in every trace and treat a model change as a release; traces that capture prompt content are masked, access-controlled and expire. Fast-moving frameworks (LangGraph, DSPy, MCP SDKs, LangChain): state the version you assume and tell the user to check it against the current docs.",
            "Treat the system as probabilistic: repeatability is not correctness; pin model, parameters, prompt and data versions in a reproducible config, set temperature/seed where possible, and log inputs and outputs.",
            "Secrets and data boundaries: keys from environment, never in code; least privilege; never send restricted data to an external model without authorization.",
            "Always ask: what problem, what evidence it works, what are its limits, what data and permissions it uses, what happens when a dependency fails, and who is responsible.",
        ],
        "gatilhos": {
            "fortes": ["llm", "rag", "embedding", "langchain", "llamaindex", "llama.cpp", "gguf", "openai", "ollama",
                       "prompt", "agente", "chatbot", "fine-tuning", "fine tuning", "vetorial", "inteligencia artificial",
                       "modelo de linguagem", "transformers", "mcp", "graphrag", "busca semantica", "langgraph",
                       "dspy", "deepeval", "reranker", "llm-as-judge", "prompt injection"],
            "fracos": ["tokens", "contexto", "eval", "alucinacao", "chunk", "chunking", "retrieval", "ia"],
        },
    },
}

BASE = """You are the CODE assistant of NÚCLEO IA PORTÁTIL, a senior software engineer.
Explanations in Brazilian Portuguese; code identifiers in English; code comments in Portuguese, only where they explain WHY.
You CANNOT run code, tests or commands. Never claim you ran, tested or verified anything — instead give the exact command the user should run.
Never invent APIs, library functions or table/column names that the user did not give; when something is unknown, state the assumption in one line.
Before writing commands that depend on the database engine, version, driver or framework, identify them from the request, code or error; if they are not given, state in one line which one you assume.
When you adapt or extend the user's code, say briefly what was kept, what is new and what is an assumption; mark assumptions in code comments with (confirmar).
Never repeat secrets or personal data found in the input (passwords, tokens, API keys, connection strings with credentials, CPF, e-mails, phone numbers): replace them with placeholders such as <SENHA> or <CPF>, in the answer and in examples.
Put every file in its own fenced block, preceded by a line with the file path in bold, like **app/main.py**.

STACK: {stack_label}
{stack_regras}
"""

TAREFAS = {
    "gerar": {
        "label": "✍️ Gerar código",
        "dica": "Descreva o que o código deve fazer (entradas, saídas, regras). Cole código existente se for para encaixar nele.",
        "max_tokens": 3500,
        "instrucoes": """TASK: write production-quality code for the request.
1. Start with "## Entendimento": 2-4 bullets with what will be built and any assumption you had to make. If the request is truly ambiguous in a way that changes the design, ask up to 3 short questions instead of writing code.
2. "## Código": complete, runnable files (no "..." or "rest of the code here"). Handle the error and edge cases that really happen (empty input, missing file, invalid value, duplicated key, network/DB failure).
3. "## Como rodar": exact commands.
4. "## Testes sugeridos": 3-6 behaviour cases worth testing (pytest for Python; a test script with expected results for T-SQL).
If existing code was given, follow its style, names and structure instead of inventing a new one — but fix its errors (never carry a bug over into your files) and still apply every STACK rule.""",
    },
    "revisar": {
        "label": "🔍 Revisar código",
        "dica": "Cole o código (ou anexe arquivos). Diga o que ele deveria fazer, se não for óbvio.",
        "max_tokens": 2500,
        "instrucoes": """TASK: review the code for real defects, behaviour first, style last.
Look for: wrong logic, unhandled edge cases, broken contracts, data loss, security problems (injection, secrets in code, missing authorization, unsafe file paths, unsafe deserialization), resource leaks, concurrency/transaction problems, performance traps (N+1 queries, non-SARGable SQL, loading everything in memory).
Do NOT report formatting or import order. Do NOT pad with generic advice. Only review what was given; if a verdict depends on code you cannot see, say so.
Severity follows the consequence: anything that fails when the code runs (SyntaxError, a misspelled name that raises NameError/AttributeError, a wrong column or key, a library call with invalid arguments) is Bloqueante with high impact — never "impacto baixo".
Before the verdict, trace the main path in your head: for each function, what does it return for a small sample input (does it process every row or only the first)? Check each library call's arguments against how the library really works (e.g. a resample rule must be a frequency such as 'MS'; several DataFrame columns are selected with a list, df[['a', 'b']]).
Output exactly:
## Pontos fortes
- (brief; skip if none)
## Bloqueante
- [file:line or function] — problem — impact — smallest concrete fix
## Deveria corrigir
- [location] — problem — fix
## Considerar
- [location] — optional improvement
## Veredito
Pronto | Pronto com as correções acima | Não está pronto — motivo
Say "Pronto com as correções acima" only if, after your fixes, the traced main path would run with no Bloqueante left; otherwise "Não está pronto" and what is still missing.
Skip empty sections. After the verdict, show corrected code ONLY for the Bloqueante items: just the changed function or excerpt (with a few lines of context), each one applying the fix you proposed.
NEVER reprint the whole file or unchanged parts. If there is no Bloqueante item, stop right after the verdict.""",
    },
    "depurar": {
        "label": "🐞 Depurar erro",
        "dica": "Cole o erro/stack trace, o código envolvido e como reproduzir (o que você fez, o que esperava, o que aconteceu).",
        "max_tokens": 2500,
        "instrucoes": """TASK: find the ROOT CAUSE of the bug. You cannot run anything, so reason from the evidence.
Output:
## O que o erro diz
(read the traceback/message literally: where it fails and what value/type was wrong)
## Hipóteses (da mais provável à menos)
1. cause — why it fits the evidence — how to confirm it in 1 step (a print/log, a query, a REPL command)
(2 to 4 hypotheses; rank by likelihood and how cheap it is to check)
## Correção
Fix the root cause, not the symptom. Never "fix" by wrapping in a broad try/except or by ignoring the error. Show the corrected code.
## Teste que prova
A pytest test (or a T-SQL check script) that FAILS before the fix and PASSES after — and the command to run it.
## Outros lugares com o mesmo problema
(other call sites that may share the cause, if visible)
If the evidence is not enough to decide, say exactly which information is missing (full traceback, input value, versions) instead of guessing.""",
    },
    "testes": {
        "label": "🧪 Gerar testes",
        "dica": "Cole o código a testar. Diga se já existe algum padrão de testes no projeto.",
        "max_tokens": 3000,
        "instrucoes": """TASK: write tests that catch real breakage.
Python: pytest; test through the public interface; parametrize similar cases; use tmp_path for files and monkeypatch/fixtures for time, randomness, network and environment; mock only slow/external boundaries, never the logic under test; assert on outputs and side effects, not on "was called".
T-SQL: a test script that sets up data in a transaction, runs the object, checks results with IF ... THROW, and ROLLBACKs at the end (or tSQLt if the user uses it).
Cover in this order: main behaviour, realistic edge/failure cases (empty, boundary values, invalid input, duplicates, None/NULL), then regressions mentioned by the user. Name each test as a behaviour sentence. No trivial tests to pad coverage.
Output: the test file(s), then "## Cobertura" (what is covered, what is not and why), then "## Como rodar" with the exact command. Remember: you did not run them.""",
    },
    "refatorar": {
        "label": "♻️ Refatorar",
        "dica": "Cole o código e diga o que incomoda (difícil de ler, repetido, lento, difícil de testar…).",
        "max_tokens": 3500,
        "instrucoes": """TASK: refactor WITHOUT changing behaviour.
1. "## Diagnóstico": the 2-5 concrete problems (duplication, long function, hidden dependencies, mixed responsibilities, bad names, slow query) — each with where it is.
2. "## Plano": small safe steps, in order; each step keeps the code working.
3. "## Código refatorado": complete files. Same public interface (function names, parameters, return values, SQL object names and result columns) unless the user allowed changes — if a change is unavoidable, list it under "Quebra de compatibilidade".
4. "## Como conferir": the tests or comparison queries that prove the behaviour did not change.
Do not add features, do not change formatting for its own sake, do not introduce new dependencies.""",
    },
    "documentar": {
        "label": "📄 Documentar",
        "dica": "Cole o código ou descreva o projeto. Diga para quem é a documentação (você mesmo, equipe, usuário final).",
        "max_tokens": 3000,
        "instrucoes": """TASK: write documentation that helps the reader DO something.
Default deliverable: a README.md with — what it is (1-2 sentences), requirements, installation, configuration (environment variables with an example), how to run, examples of use, project structure (short tree), common problems. For T-SQL: purpose of each object, parameters, result sets, permissions needed, deploy order.
If the user asked for docstrings, add Google-style docstrings to the given code (Args/Returns/Raises) and return the full code.
Only document what exists in the given code — do not invent commands, options or endpoints. Mark anything you had to assume with (confirmar).""",
    },
    "commit": {
        "label": "📝 Mensagem de commit / PR",
        "dica": "Cole o diff (git diff) ou descreva as mudanças.",
        "max_tokens": 1200,
        "instrucoes": """TASK: write the commit message and a pull-request description from the diff.
Commit: Conventional Commits subject (feat|fix|refactor|docs|test|chore|perf: ...) in Portuguese, max 72 chars, imperative; blank line; body with WHY and the main changes as short bullets.
PR: "## O que muda", "## Por quê", "## Como testar" (exact steps/commands), "## Riscos" (only real ones: migrations, breaking changes, config needed).
Describe only what is in the diff; do not claim tests passed.""",
    },
}


def listar() -> dict:
    """Tarefas e stacks para a interface."""
    return {
        "tarefas": [{"id": k, "label": v["label"], "dica": v["dica"]} for k, v in TAREFAS.items()],
        "stacks": [{"id": k, "label": v["label"]} for k, v in STACKS.items()],
    }


def _sem_acento(texto: str) -> str:
    t = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Gatilho = palavra inteira (aceita plural com "s"), sem acento e sem maiúsculas.
_GATILHOS = {
    sid: [(g, re.compile(r"(?<![a-z0-9_])" + re.escape(_sem_acento(g)) + r"s?(?![a-z0-9_])"), peso)
          for chave, peso in (("fortes", 3), ("fracos", 1))
          for g in s.get("gatilhos", {}).get(chave, [])]
    for sid, s in STACKS.items()
}
# Empate de pontos: a stack mais específica vence (web cobre o banco; Python+SQL antes de só T-SQL).
PRIORIDADE_STACK = ("pyweb", "pysql", "ia", "dados", "tsql", "python")
MIN_PONTOS_SUGESTAO = 2


def sugerir_stack(pedido: str = "", codigo: str = "", erro: str = "") -> dict:
    """Sugere a stack pelo texto do pedido (e começo do código/erro).
    Devolve {"stack": id ou None, "pontos": n, "por": [gatilhos achados]}. Só sugere: quem decide é a tela."""
    texto = _sem_acento(" ".join([pedido or "", erro or "", (codigo or "")[:3000]]))
    pontos, achados = {}, {}
    for sid, lista in _GATILHOS.items():
        hits = [(g, peso) for g, rx, peso in lista if rx.search(texto)]
        pontos[sid] = sum(p for _, p in hits)
        achados[sid] = [g for g, _ in sorted(hits, key=lambda h: -h[1])]
    # Python explícito + SQL Server explícito (e não é web) = integração Python + SQL.
    if pontos["python"] >= 3 and pontos["tsql"] >= 3 and pontos["pyweb"] == 0:
        pontos["pysql"] += pontos["python"] + pontos["tsql"]
        achados["pysql"] = achados["pysql"] + achados["python"][:1] + achados["tsql"][:1]
    ordem = sorted(STACKS, key=lambda s: (-pontos[s], PRIORIDADE_STACK.index(s) if s in PRIORIDADE_STACK else 99))
    melhor = ordem[0]
    if pontos[melhor] < MIN_PONTOS_SUGESTAO:
        return {"stack": None, "pontos": 0, "por": []}
    return {"stack": melhor, "pontos": pontos[melhor], "por": achados[melhor][:3]}


# Verificação estática (app/verificador.py): fatos certos sobre o código Python colado, sem
# executá-lo. Vão no FIM do pedido — o modelo pequeno respeita mais o que vem por último.
PY_STACKS = ("python", "pyweb", "pysql", "dados", "ia")
TAREFAS_COM_VERIFICACAO = ("gerar", "revisar", "depurar", "refatorar", "testes")
# Tarefas cuja resposta traz arquivos completos (a conferência da resposta vê tudo); nas outras
# a resposta traz trechos, e só erro certo (sintaxe, coluna, tupla, resample) é conferido.
SAIDA_COMPLETA = ("gerar", "refatorar", "testes")
# Lembrete da stack no FIM do pedido (o modelo pequeno respeita mais o que vem por último):
# as 2-4 regras que mais falharam nos testes reais. As regras completas seguem no system.
LEMBRETE_STACK = {
    "python": "LEMBRETE PYTHON: encoding='utf-8' em todo open/read_csv; nada de argumento default mutável; "
              "data dd/mm/aaaa com formato explícito ('%d/%m/%Y'); o arquivo roda sozinho (main) e você mostra o comando.",
    "pyweb": "LEMBRETE WEB: validação na borda (Pydantic); consulta sempre parametrizada; código HTTP certo "
             "(201, 204, 404, 422); segredos do ambiente; listas com paginação.",
    "tsql": "LEMBRETE T-SQL: IS NULL, nunca = NULL; confira a granularidade antes de SUM/COUNT (COUNT(coluna) "
            "no LEFT JOIN); comando destrutivo dentro de transação, com @@ROWCOUNT antes do COMMIT; "
            "SET NOCOUNT ON e SET XACT_ABORT ON nas procedures.",
    "pysql": "LEMBRETE PYTHON + SQL: valores sempre como parâmetro (?); transação explícita com commit/rollback "
             "e a conexão fechada no fim; credenciais do ambiente; fast_executemany em carga.",
    "dados": "LEMBRETE DADOS: conte também as categorias com zero (reindex com fill_value=0); em sorteio ou "
             "categorias, faça o teste de uniformidade (scipy.stats.chisquare) e diga que o passado não prevê "
             "o próximo sorteio; todo número com sua incerteza; diga o que os dados NÃO permitem concluir.",
    "ia": "LEMBRETE IA: identificador fixo do modelo; saída estruturada validada, com abstenção; retry numa "
          "camada só, com idempotência; agente com limite de passos; injeção barrada no software, não no prompt.",
}
LEMBRETE_REVISAR = (
    "ANTES DE RESPONDER: (1) o que faz o código falhar ao rodar é Bloqueante, nunca \"impacto baixo\"; "
    "(2) rode de cabeça o caminho principal: o que cada função devolve? usa todas as linhas ou só a primeira? "
    "os argumentos de cada chamada de biblioteca estão certos?; (3) \"Pronto com as correções acima\" só se não "
    "sobrar Bloqueante; mostre só os trechos alterados, nunca o arquivo inteiro.")


def fatos_estaticos(tarefa: str, stack: str, codigo: str) -> list:
    """Fatos do verificador para tarefas que recebem código Python; [] quando não se aplica."""
    if tarefa not in TAREFAS_COM_VERIFICACAO or stack not in PY_STACKS or not (codigo or "").strip():
        return []
    import verificador
    return verificador.verificar_python(codigo)


def fatos_da_resposta(tarefa: str, stack: str, texto: str) -> list:
    """Confere o código que o MODELO gerou (rede de segurança: o 7B já trouxe de volta um
    resample('Data') que a revisão tinha corrigido). [] quando não se aplica."""
    if stack not in PY_STACKS or tarefa in ("commit", "documentar") or not (texto or "").strip():
        return []
    import verificador
    return verificador.verificar_python(texto, resposta=True, completo=tarefa in SAIDA_COMPLETA)


def montar(tarefa: str, stack: str, pedido: str, codigo: str = "", erro: str = "") -> tuple[str, str, int]:
    """Devolve (system, primeira_mensagem_do_usuario, max_tokens)."""
    t = TAREFAS.get(tarefa)
    s = STACKS.get(stack)
    if not t:
        raise ValueError(f"Tarefa desconhecida: {tarefa}")
    if not s:
        raise ValueError(f"Stack desconhecida: {stack}")
    if not (pedido.strip() or codigo.strip() or erro.strip()):
        raise ValueError("Descreva o pedido ou cole o código.")
    system = BASE.format(stack_label=s["label"], stack_regras="\n".join("- " + r for r in s["regras"]))
    system += "\n" + t["instrucoes"]
    partes = []
    if pedido.strip():
        partes.append("PEDIDO:\n" + pedido.strip())
    if erro.strip():
        partes.append("ERRO / COMPORTAMENTO OBSERVADO:\n" + erro.strip())
    if codigo.strip():
        partes.append("CÓDIGO:\n" + codigo.strip())
    if tarefa in TAREFAS_COM_VERIFICACAO and stack in PY_STACKS and codigo.strip():
        import verificador
        fatos = fatos_estaticos(tarefa, stack, codigo)
        if fatos:
            n_bloq = sum(1 for f in fatos if f.get("gravidade") != "conferir")
            n_conf = len(fatos) - n_bloq
            # a contagem explícita: o modelo pequeno larga a lista no meio (teste real: parou no 9º de 12)
            if tarefa == "revisar":
                instrucao = (f"\nTotal: {n_bloq} item(ns) [Bloqueante] e {n_conf} [Conferir]. "
                             f"A seção Bloqueante precisa ter os {n_bloq}, na mesma ordem — confira a contagem antes "
                             "do veredito. Itens [Bloqueante] fazem o código falhar ao rodar: impacto alto, um por "
                             "um, com a correção certa — nenhum vai para Deveria corrigir. Itens [Conferir] são "
                             "suspeitas de lógica: verifique cada um e, se confirmar, corrija.")
            else:
                instrucao = (f"\nTotal: {n_bloq} item(ns) [Bloqueante] e {n_conf} [Conferir]. Os [Bloqueante] são "
                             f"erros reais do código fornecido: o código que você entregar NÃO pode repetir nenhum "
                             f"dos {n_bloq} — corrija todos. Itens [Conferir] são suspeitas de lógica: verifique e, "
                             "se confirmar, corrija.")
            partes.append("VERIFICAÇÃO ESTÁTICA DO NÚCLEO (fatos certos, achados lendo o código sem executá-lo):\n"
                          + verificador.formatar(fatos) + instrucao)
        else:
            partes.append("VERIFICAÇÃO ESTÁTICA DO NÚCLEO: nenhum erro de escrita encontrado "
                          "(sintaxe, nomes, colunas). Procure erros de lógica.")
    if tarefa == "revisar":
        partes.append(LEMBRETE_REVISAR)
    if tarefa not in ("commit", "documentar") and stack in LEMBRETE_STACK:
        partes.append(LEMBRETE_STACK[stack])
    return system, "\n\n".join(partes), int(t["max_tokens"])
