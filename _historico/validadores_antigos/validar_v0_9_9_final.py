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
    check("VERSION.json version=0.9.9", v.get("version") == "0.9.9", str(v.get("version")))
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

check("book_project: estrutura 00-08", has_all("app/book/book_project.py", ["00_GOVERNANCA", "08_PUBLICACAO", "criar_livro"]))
check("planner: 18 generos", has_all("app/book/planner.py", ["terror", "suspense", "autoajuda", "biografia", "academico"]))
check("outline: default modo=advanced", has_all("app/book/outline.py", ['default="advanced"']))
check("escrever: cenas + dedup", has_all("app/book/escrever.py", ["escrever_capitulo", "_corta_refrao"]))
check("revisar: redundancia semantica", has_all("app/book/revisar.py", ["def redundancia_semantica"]))
check("similaridade: TF-IDF por frase", has_all("app/book/similaridade.py", ["analisar_livro", "_variante_numerica"]))
check("publicar: PUBLICAR + tipografia", has_all("app/book/publicar.py", ["def publicar", "GENERO_ESCRITOR_PARA_DIAGRAMADOR"]))
check("file_analysis: pdf+docx", has_all("app/file_analysis.py", ["def analyze_pdf", "def analyze_docx", 'ext == ".doc"']))
check("livros_index: detalhe+leitor sandbox", has_all("app/book/livros_index.py", ["def book_detail", "def read_book_file"]))

# menu lateral + leitura (V0.9.7/0.9.8)
check("ui: sidebar + views", has_all("ui/index.html", ["class=\"sidebar\"", "navItem", "view-livros", "view-analise"]))
check("ui: leitor de livro + markdown", has_all("ui/app.js", ["function openLivro", "function renderMarkdown"]))
check("server: rotas livros detalhe/file", has_all("app/server.py", ["/api/livros/([\\w.-]+)", "/file"]))

# V0.9.9: Forja de Prompts
check("server: rota /api/forja", has_all("app/server.py", ["/api/forja", "def _forja_gerar"]))
check("ui: view Forja + scripts", has_all("ui/index.html", ["view-forja", "forja-root", "/forja/forja.js", "/vendor/react.production.min.js", "/forja/forja.css"]))
check("ui: navegacao forja + mount", has_all("ui/app.js", ['"forja"', "__mountForja"]))
check("forja.js: React + endpoint local", has_all("ui/forja/forja.js", ["React.createElement", "/api/forja", "__mountForja"]))
check("forja.js: SEM chamada de nuvem", has_none("ui/forja/forja.js", ["api.anthropic"]))
check("vendor: React UMD", has_all("ui/vendor/react.production.min.js", ["createElement"])
      and has_all("ui/vendor/react-dom.production.min.js", ["createRoot"]))

# deps de runtime importaveis
for mod in ("docx", "ebooklib", "lxml", "pypdf"):
    try:
        importlib.import_module(mod)
        check(f"runtime importa {mod}", True)
    except Exception as e:
        check(f"runtime importa {mod}", False, str(e))

# registry AVANCADO validado
try:
    reg = json.loads((ROOT / "config" / "models_registry.json").read_text(encoding="utf-8"))
    adv = [m for m in reg.get("models", []) if m.get("id") == "qwen3-30b-a3b-iq3"]
    check("registry: 30B status=validated", bool(adv) and adv[0].get("status") == "validated",
          adv[0].get("status") if adv else "ausente")
except Exception as e:
    check("registry AVANCADO", False, str(e))

mp = ROOT / "app" / "manifests" / "manifest_v0_9_9_final.json"
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
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.9.9 FINAL")
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
print("Resultado: V0.9.9 FINAL íntegra.")
raise SystemExit(0)
