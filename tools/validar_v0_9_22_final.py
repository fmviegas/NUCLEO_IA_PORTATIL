#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, importlib, json, os, py_compile, sys
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
    check("VERSION.json version=0.9.22", v.get("version") == "0.9.22", str(v.get("version")))
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
VCRT = [
    "engine/windows/cuda/vcruntime140.dll", "engine/windows/cuda/msvcp140.dll",
    "engine/windows/cpu/vcruntime140.dll", "engine/windows/cpu/msvcp140.dll",
]
# V0.9.21: camada plat + pasta linux/
PLAT_LINUX = [
    "app/plat.py",
    "linux/LEIA-ME.txt", "linux/PORTATIL_LINUX.md", "linux/montar_linux.py",
    "linux/nucleo.sh", "linux/calibrar.sh",
    "linux/engine/cpu/LEIA-ME.txt", "linux/engine/cuda/LEIA-ME.txt",
]
# V0.9.22: scripts de setup Linux
SETUP_LINUX = [
    "linux/setup/00_diagnostico.sh", "linux/setup/01_preparar.sh",
    "linux/setup/02_binarios.sh", "linux/setup/03_python.sh",
    "linux/setup/04_iniciar.sh", "linux/setup/LEIA-ME.txt",
]
required = [
    "app/server.py", "app/engine_manager.py", "app/hardware.py", "app/file_analysis.py",
    "app/workspace.py", "app/catalog.py", "app/autotune.py", "app/gguf_advisor.py",
    "app/calibration_manager.py", "app/benchmark.py", "app/chat.py", "app/maintenance_manager.py",
    "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
    "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py", "app/book/publicar.py",
    "app/book/similaridade.py", "app/book/livros_index.py",
    "config/models_registry.json", "config/personas/ficcao_360.md",
    "config/personas/tecnico_360.md", "config/personas/humanizacao.md",
    "tools/validar_modelo.py", "tools/smoke_modelo.py", "tools/calibrar_advanced.py",
    "tools/montar_portatil.py",
    "ui/index.html", "ui/app.css", "ui/app.js",
    "runtime/python/python.exe",
    "engine/windows/cpu/llama-server.exe", "engine/windows/cuda/llama-server.exe",
    "engine/windows/cuda/llama-cli.exe",
    "models/Qwen3-4B-Q4_K_M.gguf", "models/Qwen3-8B-Q4_K_M.gguf",
    "models/Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf",
    "models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
] + DIAGRAMADOR + FORJA + VCRT + PLAT_LINUX + SETUP_LINUX
for rel in required:
    try:
        ok = (ROOT / rel).exists()
    except OSError:
        ok = False
    check(rel, ok, "")

for rel in ["app/server.py", "app/engine_manager.py", "app/hardware.py",
            "app/file_analysis.py", "app/workspace.py", "app/catalog.py", "app/autotune.py",
            "app/benchmark.py", "app/chat.py", "app/maintenance_manager.py",
            "app/gguf_advisor.py", "app/calibration_manager.py", "app/plat.py",
            "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
            "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py",
            "app/book/publicar.py", "app/book/similaridade.py", "app/book/livros_index.py",
            "tools/validar_modelo.py", "tools/smoke_modelo.py", "tools/calibrar_advanced.py",
            "tools/montar_portatil.py", "linux/montar_linux.py"] + DIAGRAMADOR:
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

# --- features herdadas (V0.9.x) ---
check("planner: 18 generos", has_all("app/book/planner.py", ["terror", "suspense", "autoajuda", "biografia", "academico"]))
check("escrever: cenas + expansao + progresso", has_all("app/book/escrever.py", ["escrever_capitulo", "EXPAND_MAX", "MAX_BIBLE = 2800", "def _emit_prog"]))
check("publicar: pre-textuais", has_all("app/book/publicar.py", ["PRETEXTUAIS", "autor_detectado", "str(_dt.now().year)"]))
check("livros_index: plano com status", has_all("app/book/livros_index.py", ["def book_detail", "def _parse_plan", '"plan": plan']))
check("ui: 5 views (inclui diagnostico)", has_all("ui/index.html", ["view-livros", "view-analise", "view-forja", "view-diagnostico"]))
check("server: /api/forja + livros + run n_cap + hardware/diag", has_all("app/server.py", ["/api/forja", "def _book_run_stream", "n_cap", "/api/hardware/diagnostico"]))
check("server: CSP style inline (local)", has_all("app/server.py", ["style-src 'self' 'unsafe-inline'", "script-src 'self'"]))
check("ui: escrita+auto-continuar+export+capsel+progresso", has_all("ui/index.html", ["runCapSel", "runProgWrap", "autoContinuar"]) and has_all("ui/app.js", ["function updateRunProg", "function streamPass", "function updateBaixar"]))
check("app.css: tema NOTURNO fixo", has_all("ui/app.css", ["color-scheme: dark", 'data-theme="light"']))
check("gguf_advisor: classify + relatorio", has_all("app/gguf_advisor.py", ["def classify", "def build_report_text"]))
check("calib: barra anda por config (creep) + probe 30B", has_all("app/calibration_manager.py", ["_creep_from_config_line", "sonda real 30b"]))
check("server: /api/mode libera 'code'", has_all("app/server.py", ['"auto", "fast", "quality", "code"']))
check("engine: public_modes expoe 'code'", has_all("app/engine_manager.py", ['("fast", "quality", "code")']))
check("registry: coders 7B + 14B", has_all("config/models_registry.json", ["qwen25-coder-7b-q4km", "qwen25-coder-14b-q5km"]))
check("ui: botao CODIGO + gate", has_all("ui/index.html", ['data-mode="code"']) and has_all("ui/app.js", ["function gateModeButtons"]))
check("calibrar_advanced: generalizado (--mode)", has_all("tools/calibrar_advanced.py", ["--mode", "mode_key", "args.mode"]))
check("montar_portatil: monta + trava FAT32", has_all("tools/montar_portatil.py", ["def montar", "def coletar_arquivos", "FAT32"]))

# --- V0.9.21: camada plat.py (motor por SO) + pasta linux/ ---
check("plat: engine_root/engine_exe/EXE_SUFFIX", has_all("app/plat.py", ["def engine_root", "def engine_exe", "EXE_SUFFIX", "def engine_bin_names"]))
check("engine_manager usa plat (sem .exe fixo)",
      has_all("app/engine_manager.py", ["import plat", "plat.engine_exe(self.root"])
      and has_none("app/engine_manager.py", ['"engine" / "windows" / backend / "llama-server.exe"']))
check("chat usa plat", has_all("app/chat.py", ["import plat", "plat.engine_exe(ROOT"])
      and has_none("app/chat.py", ["engine/windows/cuda/llama-cli.exe"]))
check("autotune usa plat + detect_safe + sem trava SO",
      has_all("app/autotune.py", ["import plat", "plat.engine_exe(ROOT", "core.detect_safe()"])
      and has_none("app/autotune.py", ['"engine/windows/cuda/llama-cli.exe"', 'calibrada para Windows x64 nesta etapa']))
check("benchmark usa plat + detect_safe + sem trava SO",
      has_all("app/benchmark.py", ["import plat", "plat.engine_exe(", "core.detect_safe()"])
      and has_none("app/benchmark.py", ['"engine/windows/cpu/llama-bench.exe"', "calibrada para Windows x64."]))
check("maintenance usa plat (engine_root/bin_names)",
      has_all("app/maintenance_manager.py", ["import plat", "plat.engine_root(self.root)", "plat.engine_bin_names()"]))
check("hardware.detect_engine usa plat", has_all("app/hardware.py", ["import plat", "plat.engine_dir(ROOT"]))
check("montar_linux: inclui pasta linux + trava windows",
      has_all("linux/montar_linux.py", ["def montar", '"linux"', "linux/engine/", ".exe"]))
check("linux/nucleo.sh + calibrar.sh presentes",
      (ROOT / "linux/nucleo.sh").exists() and (ROOT / "linux/calibrar.sh").exists())

# --- V0.9.22: Forja NOVA (redesign escuro) + scripts de setup Linux ---
check("forja.js: motor local + mount + tema escuro",
      has_all("ui/forja/forja.js", ["/api/forja", "window.__mountForja", "React.createElement", "#0f0d0a", "#f4ede0"])
      and has_none("ui/forja/forja.js", ["fonts.googleapis", "window.claude", "#faf8f5", "#26201b", "import React"]))
check("forja.css: utilitarios do tema escuro", has_all("ui/forja/forja.css", ["#0f0d0a", "#ff7a18"]))
check("forja.nucleo.tsx: fonte adaptada (repo)",
      (not (ROOT / "forja-de-prompts" / "forja.nucleo.tsx").exists())
      or has_all("forja-de-prompts/forja.nucleo.tsx", ["/api/forja", "window.__mountForja", "const { useState"]))
check("linux/setup: diagnostico (FS/CRLF) + preparar (sed/chmod)",
      has_all("linux/setup/00_diagnostico.sh", ["findmnt", "CRLF", "exfat"])
      and has_all("linux/setup/01_preparar.sh", ["sed -i", "chmod +x"]))
check("linux/setup: binarios (download/build) + python(venv) + iniciar",
      has_all("linux/setup/02_binarios.sh", ["--build", "engine/", "llama-server"])
      and has_all("linux/setup/03_python.sh", [".venv", "pip install"])
      and has_all("linux/setup/04_iniciar.sh", ["nucleo.sh", "plat"]))

# import + identidade de caminho no Windows (nao muda comportamento)
try:
    sys.path.insert(0, str(ROOT / "app"))
    import plat as _plat
    if _plat.IS_WINDOWS:
        esperado = ROOT / "engine" / "windows" / "cuda" / "llama-server.exe"
        got = _plat.engine_exe(ROOT, "cuda", "llama-server")
        check("plat: identidade Windows (engine/windows/...exe)", got == esperado,
              "" if got == esperado else f"{got} != {esperado}")
    else:
        esperado = ROOT / "linux" / "engine" / "cuda" / "llama-server"
        got = _plat.engine_exe(ROOT, "cuda", "llama-server")
        check("plat: caminho Linux (linux/engine/...)", got == esperado)
    check("plat: sufixo coerente com SO",
          _plat.EXE_SUFFIX == (".exe" if os.name == "nt" else ""))
except Exception as e:
    check("plat import/identidade", False, str(e))

# import dos modulos que passaram a depender de plat
try:
    sys.path.insert(0, str(ROOT / "app"))
    for m in ("plat", "hardware", "engine_manager", "chat", "maintenance_manager", "autotune", "benchmark"):
        importlib.import_module(m)
    check("import modulos com plat (7)", True)
except Exception as e:
    check("import modulos com plat", False, str(e))

# --- advisor / catalog / runtime (herdado) ---
try:
    sys.path.insert(0, str(ROOT / "app"))
    import gguf_advisor as _adv
    d = _adv.classify(15.88, 4.0, True)
    nomes = {vv: [m["nome"] for m in d["grupos"][vv]] for vv in ("folga", "limite", "nao_roda")}
    ok = ("Qwen3-4B" in nomes["folga"] and any("30B-A3B" in n for n in nomes["limite"]))
    check("gguf_advisor: NUCLEO 4B=folga, 30B=limite", ok, "" if ok else str(nomes))
except Exception as e:
    check("gguf_advisor import/classify", False, str(e))

try:
    sys.path.insert(0, str(ROOT / "app"))
    import catalog as _cat
    reg = _cat.load_registry(str(ROOT))
    coder = [m for m in reg["models"] if m["id"] == "qwen25-coder-7b-q4km"]
    check("catalog: coder-7B present", bool(coder) and coder[0].get("present"),
          "" if coder and coder[0].get("present") else "ausente")
except Exception as e:
    check("catalog: coder-7B", False, str(e))

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

mp = ROOT / "app" / "manifests" / "manifest_v0_9_22_final.json"
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
    check("manifest inclui forja + linux/setup",
          "ui/forja/forja.js" in man.get("files", {})
          and "linux/setup/00_diagnostico.sh" in man.get("files", {}))
except Exception as e:
    check("integridade SHA256 (manifest)", False, str(e))

print()
print("=" * 72)
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.9.22 FINAL")
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
print("Resultado: V0.9.22 FINAL íntegra.")
raise SystemExit(0)
