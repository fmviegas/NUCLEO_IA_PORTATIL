#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, importlib, json, py_compile, sys
from pathlib import Path
for _s in ("stdout", "stderr"):
    try:
        getattr(sys, _s).reconfigure(encoding="utf-8")
    except Exception:
        pass
ROOT = Path(__file__).resolve().parents[1]
checks = []
def check(n, ok, d=""):
    checks.append((n, bool(ok), d))

try:
    v = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8-sig"))
    check("VERSION.json version=0.9.17", v.get("version") == "0.9.17", str(v.get("version")))
    check("VERSION.json release=final", v.get("release") == "final", str(v.get("release")))
    check("VERSION.json modo advanced", "advanced" in (v.get("features", {}).get("modes") or []),
          ",".join(v.get("features", {}).get("modes") or []))
except Exception as e:
    check("VERSION.json", False, str(e))

DIAGRAMADOR = [
    "app/diagramador/__init__.py", "app/diagramador/config.py", "app/diagramador/modelo.py",
    "app/diagramador/leitura.py", "app/diagramador/inline.py", "app/diagramador/limpeza.py",
    "app/diagramador/caminhos.py", "app/diagramador/arquivos.py",
    "app/diagramador/exportar_docx.py", "app/diagramador/exportar_epub.py", "app/diagramador/cli.py",
]
FORJA = ["ui/forja/forja.js", "ui/forja/forja.css",
         "ui/vendor/react.production.min.js", "ui/vendor/react-dom.production.min.js"]
required = [
    "app/server.py", "app/engine_manager.py", "app/hardware.py", "app/file_analysis.py",
    "app/workspace.py", "app/catalog.py", "app/autotune.py",
    "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
    "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py", "app/book/publicar.py",
    "app/book/similaridade.py", "app/book/livros_index.py",
    "config/models_registry.json", "config/personas/ficcao_360.md",
    "config/personas/tecnico_360.md", "config/personas/humanizacao.md",
    "tools/validar_modelo.py", "tools/smoke_modelo.py", "tools/calibrar_advanced.py",
    "ui/index.html", "ui/app.css", "ui/app.js",
    "runtime/python/python.exe",
    "engine/windows/cpu/llama-server.exe", "engine/windows/cuda/llama-server.exe",
    "engine/windows/cuda/llama-cli.exe",
    "models/Qwen3-4B-Q4_K_M.gguf", "models/Qwen3-8B-Q4_K_M.gguf",
    "models/Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf",
] + DIAGRAMADOR + FORJA
for rel in required:
    try:
        ok = (ROOT / rel).exists()
    except OSError:
        ok = False
    check(rel, ok, "")

for rel in ["app/server.py", "app/engine_manager.py", "app/hardware.py",
            "app/file_analysis.py", "app/workspace.py", "app/catalog.py", "app/autotune.py",
            "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
            "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py",
            "app/book/publicar.py", "app/book/similaridade.py", "app/book/livros_index.py",
            "tools/validar_modelo.py", "tools/smoke_modelo.py", "tools/calibrar_advanced.py"] + DIAGRAMADOR:
    p = ROOT / rel
    if p.exists():
        try:
            py_compile.compile(str(p), doraise=True); check("compile " + rel, True)
        except Exception as e:
            check("compile " + rel, False, str(e))

def has_all(rel, needles):
    p = ROOT / rel
    return p.exists() and all(x in p.read_text(encoding="utf-8", errors="replace") for x in needles)

def has_none(rel, needles):
    p = ROOT / rel
    if not p.exists():
        return False
    t = p.read_text(encoding="utf-8", errors="replace")
    return all(x not in t for x in needles)

check("planner: 18 generos", has_all("app/book/planner.py", ["terror", "suspense", "autoajuda", "biografia", "academico"]))
check("escrever: cenas + dedup + expansao", has_all("app/book/escrever.py", ["escrever_capitulo", "_corta_refrao", "EXPAND_MAX", "MAX_BIBLE = 2800"]))
check("revisar: auditar+compilar", has_all("app/book/revisar.py", ["def auditar", "def compilar"]))
check("publicar: PUBLICAR + tipografia", has_all("app/book/publicar.py", ["def publicar", "GENERO_ESCRITOR_PARA_DIAGRAMADOR"]))
check("file_analysis: pdf+docx", has_all("app/file_analysis.py", ["def analyze_pdf", "def analyze_docx"]))
check("livros_index: detalhe + plano com status", has_all("app/book/livros_index.py", ["def book_detail", "def read_book_file", "def _parse_plan", '"plan": plan']))

check("ui: sidebar + 4 views", has_all("ui/index.html", ["view-livros", "view-analise", "view-forja"]))
check("server: rota /api/forja", has_all("app/server.py", ["/api/forja", "def _forja_gerar"]))
check("forja.js: SEM chamada de nuvem", has_none("ui/forja/forja.js", ["api.anthropic"]))
check("server: criar/generos/revisar/publicar", has_all("app/server.py", ["/api/livros/criar", "/api/livros/generos", "def _livro_revisar", "def _livro_publicar"]))
check("ui: criar/revisar/publicar", has_all("ui/index.html", ["livroNovoForm", "livroRevisar", "livroPublicar"]))
check("server: rota run (SSE)+stop+handoff+n_cap", has_all("app/server.py", ["/run", "def _book_run_stream", "/api/livros/run/stop", "_BOOK_LOCK", "n_cap"]))
check("ui: controles de escrita + EventSource + capsel", has_all("ui/index.html", ["runOutline", "runEscrever", "runParar", "runCapSel"]) and has_all("ui/app.js", ["function runBook", "EventSource"]))
check("book_project: biblia por meta + intake", has_all("app/book/book_project.py", ["def _biblia", "def criar_livro", "voz_narrador", "personagens_chave", "choice=_choice"]))
check("engine: amostragem anti-loop + DRY", has_all("app/engine_manager.py", ["repeat_penalty", "min_p", "dry_multiplier"]))

# 0.9.15/0.9.16: export, tema, auto-continuar, capitulo especifico
check("app.js: exportar (.md/.txt/.csv)", has_all("ui/app.js", ["function updateBaixar", "_convToMd", "_mdTableToCsv"]))
check("forja.js: download do prompt", has_all("ui/forja/forja.js", ["function downloadResult"]))
check("app.css: tema NOTURNO fixo", has_all("ui/app.css", ["color-scheme: dark", 'data-theme="light"']))
check("chat: auto-continuar", has_all("ui/app.js", ["function streamPass", "AUTO_CONTINUE_MAX", "stopRequested"]) and has_all("ui/index.html", ["autoContinuar"]))

# 0.9.17: barra de progresso por cena
check("escrever: marcadores de progresso (_emit_prog / ::PROG::)", has_all("app/book/escrever.py", ["def _emit_prog", "::PROG:: ", 'phase="cena"', 'phase="fim"']))
check("ui: barra de progresso (updateRunProg + intercept)", has_all("ui/app.js", ["function updateRunProg", "::PROG:: ", "resetRunProg"]))
check("ui: elementos da barra", has_all("ui/index.html", ["runProgWrap", "runBarFill", "runProgLabel"]))
check("app.css: estilo da barra", has_all("ui/app.css", [".runBarFill", ".runProgWrap"]))

for mod in ("docx", "ebooklib", "lxml", "pypdf"):
    try:
        importlib.import_module(mod)
        check(f"runtime importa {mod}", True)
    except Exception as e:
        check(f"runtime importa {mod}", False, str(e))

try:
    reg = json.loads((ROOT / "config" / "models_registry.json").read_text(encoding="utf-8"))
    adv = [m for m in reg.get("models", []) if m.get("id") == "qwen3-30b-a3b-iq3"]
    check("registry: 30B status=validated", bool(adv) and adv[0].get("status") == "validated",
          adv[0].get("status") if adv else "ausente")
except Exception as e:
    check("registry AVANCADO", False, str(e))

mp = ROOT / "app" / "manifests" / "manifest_v0_9_17_final.json"
try:
    man = json.loads(mp.read_text(encoding="utf-8"))
    mism = []
    for rel, meta in man.get("files", {}).items():
        p = ROOT / rel
        if not p.exists():
            mism.append(rel + " (ausente)"); continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != meta.get("sha256"):
            mism.append(rel + " (hash)")
    check("integridade SHA256 (manifest)", not mism, "OK" if not mism else "; ".join(mism[:6]))
except Exception as e:
    check("integridade SHA256 (manifest)", False, str(e))

print()
print("=" * 72)
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.9.17 FINAL")
print("=" * 72)
fail = 0
for n, ok, d in checks:
    s = "OK" if ok else "FALHA"
    if not ok:
        fail += 1
    print(f"[{s:5}] {n}" + (f" — {d}" if d else ""))
print()
if fail:
    print(f"Resultado: {fail} falha(s).")
    raise SystemExit(1)
print("Resultado: V0.9.17 FINAL íntegra.")
raise SystemExit(0)
