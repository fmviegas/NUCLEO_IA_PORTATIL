#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, importlib, json, os, py_compile, re, sys
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
    check("VERSION.json version=0.9.24", v.get("version") == "0.9.24", str(v.get("version")))
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
# V0.9.24: scripts de setup Linux
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
    "app/book/similaridade.py", "app/book/livros_index.py", "app/book/biblia_ctx.py",
    "app/book/fences.py",
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
    "app/exporters.py", "app/financeiro.py",
    "config/templates/financeiro/ControleFinanceiro.xlsx",
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
            "app/exporters.py", "app/financeiro.py",
            "app/book/book_project.py", "app/book/planner.py", "app/book/humanizar.py",
            "app/book/outline.py", "app/book/escrever.py", "app/book/revisar.py",
            "app/book/publicar.py", "app/book/similaridade.py", "app/book/livros_index.py",
            "app/book/biblia_ctx.py", "app/book/fences.py",
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

# --- V0.9.24: Forja NOVA (redesign escuro) + scripts de setup Linux ---
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
      and has_all("linux/setup/03_python.sh", [".venv", "pip install", "openpyxl"])
      and has_all("linux/setup/04_iniciar.sh", ["nucleo.sh", "plat"]))

# --- V0.9.24: exportar chat/analise para .docx e .xlsx ---
check("exporters: md_to_docx + md_to_xlsx + parse_md_tables",
      has_all("app/exporters.py", ["def md_to_docx", "def md_to_xlsx", "def parse_md_tables"]))
check("server: rota /api/export + _export_file",
      has_all("app/server.py", ['path == "/api/export"', "def _export_file", "Content-Disposition"]))
check("ui: menu export docx/xlsx + _exportServer",
      has_all("ui/index.html", ['data-exp="conv-docx"', 'data-exp="last-docx"', 'data-exp="xlsx"', 'id="baixarXlsx"'])
      and has_all("ui/app.js", ["function _exportServer", "/api/export", 'kind === "xlsx"']))
try:
    sys.path.insert(0, str(ROOT / "app"))
    import exporters as _exp
    _md = "# T\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    _d = _exp.md_to_docx(_md, "t"); _x = _exp.md_to_xlsx(_md, "t")
    ok = (isinstance(_d, (bytes, bytearray)) and isinstance(_x, (bytes, bytearray))
          and len(_d) > 500 and len(_x) > 500 and _d[:2] == b"PK" and _x[:2] == b"PK")
    check("exporters: gera docx/xlsx validos (zip PK)", ok, "" if ok else f"docx={len(_d)} xlsx={len(_x)}")
except Exception as e:
    check("exporters gera docx/xlsx", False, str(e))

# fix do exportador xlsx: tira markdown + moeda vira numero
check("exporters: _strip_md + moeda->numero", has_all("app/exporters.py", ["def _strip_md", "_strip_md(cell) if ri == 0"]))

# --- V0.9.24: biblia condensada por PRIORIDADE de campo (voz nunca sai) ---
try:
    sys.path.insert(0, str(ROOT / "app" / "book"))
    import biblia_ctx as _bc
    _big = ("# BIBLIA\nGenero: terror\nEpoca: " + "x. " * 900 +
            "\nPersonagens secundarios: " + "y. " * 900 +
            "\nTique verbal / palavra-assinatura: enfim\n"
            "NÃO usar (palavras/construções banidas): inabalavel\nTom / voz: [...]")
    _o = _bc.condensar(_big, 800)
    check("biblia_ctx: cabe no limite, mantem voz, tira placeholder",
          len(_o) <= 800 and "enfim" in _o and "inabalavel" in _o and "Tom / voz" not in _o,
          f"len={len(_o)}")
    check("escrever/outline usam biblia_ctx (sem corte seco)",
          has_all("app/book/escrever.py", ["biblia_ctx.condensar"])
          and has_all("app/book/outline.py", ["biblia_ctx.condensar"])
          and has_none("app/book/outline.py", ["biblia[:MAX_BIBLE_CHARS]"])
          and has_none("app/book/escrever.py", ["b[:MAX_BIBLE]"]))
except Exception as e:
    check("biblia_ctx", False, str(e))

# --- V0.9.24: cercas ``` soltas do modelo (escrever + publicar) ---
try:
    sys.path.insert(0, str(ROOT / "app" / "book"))
    import fences as _fc
    _P = "A media resume os dados em um unico numero bem simples e direto."
    _t, _n = _fc.sanear(_P + "\n\n```python\nx = 1\n\n" + _P, fiction=False)
    _ok_tec = _n == 1 and _t.count("```") == 2 and _t.rstrip().endswith(_P)
    _f, _ = _fc.sanear("```\n" + _P + "\n```", fiction=True)
    check("fences: fecha ``` aberto (tecnico) e tira cercas (ficcao)",
          _ok_tec and "```" not in _f and _fc.sanear(_t, False)[0] == _t)
    check("escrever/publicar usam fences.sanear",
          has_all("app/book/escrever.py", ["fences.sanear(txt", "fences.sanear(draft"])
          and has_all("app/book/publicar.py", ["def _sanear_capitulos", "fences.sanear("]))
except Exception as e:
    check("fences", False, str(e))

# --- V0.9.24: progresso intra-cena (barra anda enquanto o modelo escreve) ---
check("progresso intra-cena: escrever emite 'gerando' + outline on_delta + UI",
      has_all("app/book/escrever.py", ["def _prog_ao_vivo", 'phase="gerando"', "on_delta=_prog_ao_vivo("])
      and has_all("app/book/outline.py", ["def _run_engine(eng, msg: str, max_tokens: int, on_delta=None)"])
      and has_all("ui/app.js", ['p.phase === "gerando"', "runProgPreview"])
      and has_all("ui/index.html", ['id="runProgPreview"']))

# --- V0.9.24: menu FINANCEIRO (Controle Financeiro .xlsx fiel/aprimorada) ---
try:
    sys.path.insert(0, str(ROOT / "app"))
    import financeiro as _fin, zipfile as _zf, io as _io, re as _re
    _fb, _ = _fin.gerar("fiel")
    _ab, _ = _fin.gerar("aprimorada")
    _z = _zf.ZipFile(_io.BytesIO(_ab))
    _wbx = _z.read("xl/workbook.xml").decode("utf-8")
    _jan = _z.read("xl/worksheets/sheet5.xml").decode("utf-8")
    check("financeiro: fiel = modelo byte a byte",
          _fb == (ROOT / "config/templates/financeiro/ControleFinanceiro.xlsx").read_bytes())
    check("financeiro: aprimorada integra (17 abas, listas, destaques, protecao, treemaps)",
          _z.testzip() is None and _wbx.count("<sheet ") == 17 and "<dataValidations" in _jan
          and "<conditionalFormatting" in _jan and "<sheetProtection" in _jan
          and sum(1 for n in _z.namelist() if _re.search(r"charts/chartEx\d+\.xml$", n)) == 12)
    check("financeiro: rotas + menu",
          has_all("app/server.py", ['path == "/api/financeiro"', 'path == "/api/financeiro/gerar"', "def _financeiro_gerar"])
          and has_all("ui/index.html", ['data-view="financeiro"', 'id="view-financeiro"'])
          and has_all("ui/app.js", ["function loadFinanceiro", "function baixarFinanceiro"]))
except Exception as e:
    check("financeiro", False, str(e))

# --- V0.9.24: epigrafe como pre-textual proprio (DOCX + EPUB) ---
try:
    sys.path.insert(0, str(ROOT / "app"))
    from diagramador.leitura import linhas_epigrafe as _le, _classe_pre_textual as _cpt
    from diagramador.modelo import Bloco as _B
    _l = _le([_B("p", "Citacao qualquer."), _B("p", "— Autor, *Obra*"), _B("hr", ""),
              _B("quote", "Outra."), _B("list", "", ["Outro Autor"])])
    check("epigrafe: leitura (texto/autoria/sep) + arquivo reconhecido",
          [t for t, _ in _l] == ["texto", "autoria", "sep", "texto", "autoria"]
          and _cpt("x/epigrafe.md") == "epigrafe" and _cpt("x/00-Epígrafe.md") == "epigrafe")
    check("epigrafe: DOCX/EPUB/publicar",
          has_all("app/diagramador/exportar_docx.py", ["def _pagina_epigrafe", "if livro.epigrafe:"])
          and has_all("app/diagramador/exportar_epub.py", ['file_name="epigrafe.xhtml"', "spine.append(epigrafe_item)"])
          and has_all("app/book/publicar.py", ['"epigrafe.md"']))
except Exception as e:
    check("epigrafe", False, str(e))

# --- V0.9.24: fontes da Forja locais (offline) ---
_fdir = ROOT / "ui" / "forja" / "fonts"
_fcss = (ROOT / "ui" / "forja" / "fonts.css")
_furls = re.findall(r"url\('fonts/([^']+)'\)", _fcss.read_text(encoding="utf-8")) if _fcss.exists() else []
check("forja: fontes locais (fonts.css + woff2 + licencas OFL + index + mime)",
      len(_furls) == 10 and all((_fdir / u).is_file() and (_fdir / u).read_bytes()[:4] == b"wOF2" for u in _furls)
      and len(list(_fdir.glob("OFL-*.txt"))) == 3
      and has_all("ui/index.html", ['href="/forja/fonts.css"'])
      and has_all("app/server.py", ['mimetypes.add_type("font/woff2", ".woff2")']),
      f"{len(_furls)} faces")

# --- V0.9.24: gerador de planilhas REMOVIDO (nao ficou como o usuario queria) ---
check("planilhas removido (sem rota/aba/modulo)",
      not (ROOT / "app/planilhas.py").exists()
      and has_none("app/server.py", ["/api/planilhas", "_planilha_gerar"])
      and has_none("ui/index.html", ['data-view="planilhas"', 'id="view-planilhas"'])
      and has_none("ui/app.js", ["loadPlanilhas", "/api/planilhas"]))

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

for mod in ("docx", "ebooklib", "lxml", "pypdf", "openpyxl"):
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

mp = ROOT / "app" / "manifests" / "manifest_v0_9_24_final.json"
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
print("        NÚCLEO IA PORTÁTIL — VALIDAÇÃO V0.9.24 FINAL")
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
print("Resultado: V0.9.24 FINAL íntegra.")
raise SystemExit(0)
