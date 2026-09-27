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
    check("VERSION.json version=0.9.4", v.get("version") == "0.9.4", str(v.get("version")))
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
required = [
    "app/server.py", "app/engine_manager.py", "app/hardware.py", "app/file_analysis.py",
    "app/workspace.py", "app/catalog.py", "app/autotune.py",
    "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
    "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py", "app/book/publicar.py",
    "config/models_registry.json", "config/personas/ficcao_360.md",
    "config/personas/tecnico_360.md", "config/personas/humanizacao.md",
    "tools/validar_modelo.py", "tools/smoke_modelo.py",
    "ui/index.html", "ui/app.css", "ui/app.js",
    "runtime/python/python.exe",
    "engine/windows/cpu/llama-server.exe", "engine/windows/cuda/llama-server.exe",
    "models/Qwen3-4B-Q4_K_M.gguf", "models/Qwen3-8B-Q4_K_M.gguf",
    "models/Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf",
] + DIAGRAMADOR
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
            "app/book/publicar.py",
            "tools/validar_modelo.py", "tools/smoke_modelo.py"] + DIAGRAMADOR:
    p = ROOT / rel
    if p.exists():
        try:
            py_compile.compile(str(p), doraise=True); check("compile " + rel, True)
        except Exception as e:
            check("compile " + rel, False, str(e))

def has_all(rel, needles):
    p = ROOT / rel
    return p.exists() and all(x in p.read_text(encoding="utf-8", errors="replace") for x in needles)

check("book_project: estrutura 00-08", has_all("app/book/book_project.py", ["00_GOVERNANCA", "08_PUBLICACAO", "criar_livro"]))
check("planner: metas de genero", has_all("app/book/planner.py", ["GENRE_TARGETS", "plan_chapters"]))
check("humanizar: linter A1-A12", has_all("app/book/humanizar.py", ["negar_e_reafirmar", "analyze_text"]))
check("outline: lotes + ritmo por ato", has_all("app/book/outline.py", ["_batch_message", "_ritmo_por_ato"]))
check("escrever: cenas + dedup", has_all("app/book/escrever.py", ["escrever_capitulo", "_corta_refrao"]))
check("revisar: auditoria+compilar", has_all("app/book/revisar.py", ["def auditar", "def compilar"]))
check("engine: catalogo+reaper", has_all("app/engine_manager.py", ["_resolve_model_path", "_reap_orphan_servers"]))
check("file_analysis: leitura semantica", has_all("app/file_analysis.py", ["_extract_form_block", "_classify_structure"]))

# V0.9.3: modo AVANCADO
check("escrever: default modo=advanced", has_all("app/book/escrever.py", ['default="advanced"']))
check("outline: default modo=advanced", has_all("app/book/outline.py", ['default="advanced"']))
check("validar_modelo: aceita qwen3moe", has_all("tools/validar_modelo.py", ["qwen3moe"]))

# V0.9.4: etapa PUBLICAR (diagramador)
check("publicar: etapa PUBLICAR", has_all("app/book/publicar.py", ["def publicar", "carregar_multiplos", "08_PUBLICACAO"]))
check("publicar: remove titulo duplicado", has_all("app/book/publicar.py", ["_remover_titulos_duplicados"]))
check("diagramador: exporta docx", has_all("app/diagramador/exportar_docx.py", ["def diagramar_docx"]))
check("diagramador: exporta epub", has_all("app/diagramador/exportar_epub.py", ["def exportar_epub"]))

# deps de publicacao importaveis no runtime portatil
for mod in ("docx", "ebooklib", "lxml"):
    try:
        importlib.import_module(mod)
        check(f"runtime importa {mod}", True)
    except Exception as e:
        check(f"runtime importa {mod}", False, str(e))

# registry: entrada AVANCADO validada
try:
    reg = json.loads((ROOT / "config" / "models_registry.json").read_text(encoding="utf-8"))
    adv = [m for m in reg.get("models", []) if m.get("id") == "qwen3-30b-a3b-iq3"]
    check("registry: 30B status=validated", bool(adv) and adv[0].get("status") == "validated",
          adv[0].get("status") if adv else "ausente")
except Exception as e:
    check("registry AVANCADO", False, str(e))

mp = ROOT / "app" / "manifests" / "manifest_v0_9_4_final.json"
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
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.9.4 FINAL")
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
print("Resultado: V0.9.4 FINAL íntegra.")
raise SystemExit(0)
