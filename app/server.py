#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import mimetypes
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
UI_DIR = ROOT / "ui"
sys.path.insert(0, str(APP_DIR))
# fontes locais da Forja (ui/forja/fonts): o registro do Windows nem sempre
# conhece .woff2 → sem isto saem como application/octet-stream
mimetypes.add_type("font/woff2", ".woff2")

from engine_manager import EngineError, EngineManager
from sessions import SessionStore
from calibration_manager import CalibrationError, CalibrationManager
from maintenance_manager import MaintenanceError, MaintenanceManager
from workspace import WorkspaceError, WorkspaceStore

def _load_app_version() -> str:
    try:
        data = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8-sig"))
        return str(data.get("version") or "0.0.0")
    except Exception:
        return "0.0.0"


APP_VERSION = _load_app_version()
HOST = "127.0.0.1"
# Trabalho de escrita de livro (OUTLINE/ESCREVER) — um por vez. O motor é único,
# então o job assume o motor via subprocesso enquanto o chat fica pausado.
_BOOK_LOCK = threading.Lock()
_BOOK_JOB = {"proc": None}
SESSION_ROUTE_RE = re.compile(r"^/api/session/([a-f0-9]{16})(?:/(save))?$")
FILE_ROUTE_RE = re.compile(r"^/api/files/([a-f0-9]{16})(?:/([a-f0-9]{12}))?$")


def free_port(preferred=18080):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return int(s.getsockname()[1])


# Forja: início de uma sequência de tags "--nome" (precedida de espaço ou
# início de linha, pra não pegar hífens de palavras como "teal-orange").
_FORJA_TAG_START_RE = re.compile(r"(?:^|(?<=\s))--(?=[A-Za-z])")
_FORJA_TAG_SPLIT_RE = re.compile(r"\s+(?=--)")
FORJA_MAX_TAGS = 8


def _forja_limpar_tags(text: str, max_tags: int = FORJA_MAX_TAGS) -> tuple[str, bool]:
    """Modelos pequenos entram em loop na linha de tags do prompt
    ("--extreme detail in the fabric --extreme detail in the clothing ...").
    Cada tag muda um pouco, então repeat_penalty/DRY não seguram. Aqui, em
    cada linha com tags: mantém só a primeira tag de cada nome (1ª palavra),
    põe --ar na frente, corta em `max_tags` e descarta lixo ("---").
    Devolve (texto, houve_corte)."""
    out, trimmed = [], False
    for line in text.split("\n"):
        m = _FORJA_TAG_START_RE.search(line)
        if not m:
            out.append(line)
            continue
        desc = line[:m.start()].rstrip().rstrip(",").rstrip()
        raw = [t.strip() for t in _FORJA_TAG_SPLIT_RE.split(line[m.start():].strip())]
        seen, tags = set(), []
        for t in raw:
            if not re.match(r"^--[A-Za-z]", t):
                trimmed = True
                continue
            key = t[2:].split()[0].lower()
            if key in seen:
                trimmed = True
                continue
            seen.add(key)
            tags.append(t.rstrip(","))
        tags.sort(key=lambda t: 0 if t[2:].split()[0].lower() == "ar" else 1)
        if len(tags) > max_tags:
            tags, trimmed = tags[:max_tags], True
        if desc:
            out.append(desc)
        if tags:
            out.append(" ".join(tags))
    return "\n".join(out), trimmed


class NucleoHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, engine, sessions, calibration, maintenance, workspace):
        super().__init__(address, handler)
        self.engine = engine
        self.sessions = sessions
        self.calibration = calibration
        self.maintenance = maintenance
        self.workspace = workspace


class Handler(BaseHTTPRequestHandler):
    server_version = f"NucleoIA/{APP_VERSION}"

    def log_message(self, fmt, *args):
        log_dir = ROOT / "logs" / "v0_6_5"
        log_dir.mkdir(parents=True, exist_ok=True)
        line = "%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            fmt % args,
        )
        try:
            with open(log_dir / "interface-http.log", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    @property
    def engine(self):
        return self.server.engine

    @property
    def sessions(self):
        return self.server.sessions

    @property
    def calibration(self):
        return self.server.calibration

    @property
    def maintenance(self):
        return self.server.maintenance

    @property
    def workspace(self):
        return self.server.workspace

    def _origin_allowed(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        try:
            p = urllib.parse.urlsplit(origin)
            return p.hostname in ("127.0.0.1", "localhost", "::1")
        except Exception:
            return False

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            # style-src permite 'unsafe-inline': a UI (barra de progresso, chips) e a
            # Forja usam estilos/animações inline (<style>, style={{}}). App LOCAL
            # (127.0.0.1, um usuário); script-src segue estrito 'self' (defesa anti-XSS).
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        )

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Nucleo-IA", APP_VERSION)
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self, max_bytes=2_000_000):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length > max_bytes:
            raise ValueError("Requisição grande demais.")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        if not self._origin_allowed():
            return self._json(403, {
                "ok": False,
                "error": {"code": "ORIGIN_BLOCKED", "message": "Origem não permitida."},
            })

        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path

        if path == "/api/status":
            return self._json(200, {
                "ok": True,
                "product": "NÚCLEO IA PORTÁTIL",
                "version": APP_VERSION,
                "data": self.engine.snapshot(),
            })

        if path == "/api/modes":
            return self._json(200, {
                "ok": True,
                "data": {
                    "modes": self.engine.public_modes(),
                    "auto_recommends": (
                        self.engine.profile.get("recommended_auto", "fast")
                        if self.engine.profile else None
                    ),
                },
            })

        if path == "/api/calibrate/status":
            return self._json(200, {
                "ok": True,
                "data": self.calibration.snapshot(),
            })

        if path == "/api/maintenance/status":
            return self._json(200, {
                "ok": True,
                "data": self.maintenance.snapshot(),
            })

        if path == "/api/maintenance/logs":
            return self._json(200, {
                "ok": True,
                "data": self.maintenance.logs(),
            })

        file_match = FILE_ROUTE_RE.fullmatch(path)
        if file_match and not file_match.group(2):
            return self._json(200, {
                "ok": True,
                "data": self.workspace.list_files(file_match.group(1)),
            })

        if path == "/api/sessions":
            qs = urllib.parse.parse_qs(parsed.query)
            try:
                limit = int((qs.get("limit") or ["20"])[0])
            except ValueError:
                limit = 20
            return self._json(200, {
                "ok": True,
                "data": self.sessions.list_recent(limit=limit),
            })

        if path == "/api/session/last":
            return self._json(200, {
                "ok": True,
                "data": self.sessions.last_nonempty(),
            })

        match = SESSION_ROUTE_RE.fullmatch(path)
        if match and not match.group(2):
            data = self.sessions.get(match.group(1))
            if data is None:
                return self._json(404, {
                    "ok": False,
                    "error": {"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."},
                })
            return self._json(200, {"ok": True, "data": data})

        if path == "/api/hardware/diagnostico":
            try:
                data = self._hardware_diagnostico()
            except Exception as exc:  # noqa
                return self._json(200, {"ok": False, "error": {"code": "DIAG_ERROR", "message": str(exc)}})
            return self._json(200, {"ok": True, "data": data})

        if path == "/api/financeiro":
            try:
                import financeiro
                return self._json(200, {"ok": True, "data": {
                    "modelo_presente": financeiro.TEMPLATE.exists(), "aviso": financeiro.MSG_SEM_MODELO}})
            except Exception as exc:  # noqa
                return self._json(200, {"ok": False, "error": {"code": "FIN_INFO", "message": str(exc)}})

        if path in ("/api/financeiro/anos", "/api/financeiro/dados", "/api/financeiro/analise"):
            # módulo financeiro (fase B): dados locais por ano em workspace/financeiro/
            try:
                import financeiro_dados as FD
                qs = urllib.parse.parse_qs(parsed.query)
                if path.endswith("/anos"):
                    import datetime as _dt
                    return self._json(200, {"ok": True, "data": {"anos": FD.anos(), "atual": _dt.date.today().year}})
                ano = int((qs.get("ano") or ["0"])[0])
                if path.endswith("/dados"):
                    return self._json(200, {"ok": True, "data": FD.carregar(ano)})
                return self._json(200, {"ok": True, "data": {"prompt": FD.prompt_analise(ano)}})
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": {"code": "FIN_BAD", "message": str(exc)}})
            except Exception as exc:  # noqa
                return self._json(200, {"ok": False, "error": {"code": "FIN_FAIL", "message": str(exc)}})

        if path == "/api/livros":
            try:
                from book.livros_index import list_books
                data = list_books(ROOT)
            except Exception as exc:  # read-only; nunca derruba a UI
                return self._json(200, {"ok": True, "data": [], "note": str(exc)})
            return self._json(200, {"ok": True, "data": data})

        if path == "/api/livros/generos":
            try:
                from book import planner as _pl
                gens = [{"id": g, "family": "ficcao" if _pl.is_fiction(g) else "tecnico",
                         "range": list(_pl.GENRE_TARGETS[g])}
                        for g in sorted(_pl.GENRE_TARGETS)]
            except Exception as exc:
                return self._json(200, {"ok": True, "data": [], "note": str(exc)})
            return self._json(200, {"ok": True, "data": gens})

        m_livro = re.fullmatch(r"/api/livros/([\w.-]+)", path)
        if m_livro:
            try:
                from book.livros_index import book_detail
                data = book_detail(ROOT, m_livro.group(1))
            except Exception as exc:
                return self._json(200, {"ok": False, "error": {"code": "LIVRO_ERROR", "message": str(exc)}})
            if data is None:
                return self._json(404, {"ok": False, "error": {"code": "LIVRO_NOT_FOUND", "message": "Livro não encontrado."}})
            return self._json(200, {"ok": True, "data": data})

        m_livro_file = re.fullmatch(r"/api/livros/([\w.-]+)/file", path)
        if m_livro_file:
            rel = (urllib.parse.parse_qs(parsed.query).get("rel") or [""])[0]
            try:
                from book.livros_index import read_book_file
                data = read_book_file(ROOT, m_livro_file.group(1), rel)
            except Exception as exc:
                return self._json(200, {"ok": False, "error": {"code": "FILE_ERROR", "message": str(exc)}})
            if data is None:
                return self._json(404, {"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": "Arquivo não encontrado ou não permitido."}})
            return self._json(200, {"ok": True, "data": data})

        m_run = re.fullmatch(r"/api/livros/([\w.-]+)/run", path)
        if m_run:
            qs = urllib.parse.parse_qs(parsed.query)
            acao = (qs.get("acao") or ["outline"])[0]
            modo = (qs.get("modo") or ["advanced"])[0]
            n_cap = None
            try:
                raw_n = (qs.get("n") or [""])[0].strip()
                if raw_n:
                    n_cap = int(raw_n)
                    if n_cap < 1:
                        n_cap = None
            except (ValueError, TypeError):
                n_cap = None
            return self._book_run_stream(m_run.group(1), acao, modo, n_cap)

        return self._serve_static(path)

    def do_POST(self):
        if not self._origin_allowed():
            return self._json(403, {
                "ok": False,
                "error": {"code": "ORIGIN_BLOCKED", "message": "Origem não permitida."},
            })

        path = urllib.parse.urlsplit(self.path).path
        try:
            file_match = FILE_ROUTE_RE.fullmatch(path)
            if file_match and not file_match.group(2):
                sid = file_match.group(1)
                if self.sessions.get(sid) is None:
                    return self._json(404, {
                        "ok": False,
                        "error": {"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."},
                    })
                parsed = urllib.parse.urlsplit(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                filename = (qs.get("name") or ["arquivo"])[0]
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0:
                    raise ValueError("Arquivo vazio.")
                if length > 50 * 1024 * 1024:
                    raise ValueError("Arquivo excede o limite de 50 MB.")
                content = self.rfile.read(length)
                item = self.workspace.upload(sid, filename, content)
                return self._json(201, {"ok": True, "data": item})

            if path == "/api/mode":
                body = self._read_json()
                mode = str(body.get("mode", "")).lower()
                if mode not in ("auto", "fast", "quality", "code"):
                    raise ValueError("Modo inválido.")
                snap = self.engine.switch_mode(mode)
                return self._json(200, {"ok": True, "data": snap})

            if path == "/api/stop":
                self.engine.request_stop_generation()
                return self._json(200, {"ok": True})

            if path == "/api/chat":
                return self._chat_stream()

            if path == "/api/forja":
                return self._forja_gerar()

            if path == "/api/export":
                return self._export_file()

            if path == "/api/financeiro/gerar":
                return self._financeiro_gerar()

            if path == "/api/financeiro/dados":
                body = self._read_json(max_bytes=4_000_000)
                try:
                    import financeiro_dados as FD
                    salvo = FD.salvar(body.get("ano"), body.get("dados") or {})
                except (ValueError, TypeError) as exc:
                    return self._json(400, {"ok": False, "error": {"code": "FIN_BAD", "message": str(exc)}})
                return self._json(200, {"ok": True, "data": salvo})

            if path == "/api/livros/run/stop":
                p = _BOOK_JOB.get("proc")
                if p and p.poll() is None:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                    return self._json(200, {"ok": True, "data": {"stopping": True}})
                return self._json(200, {"ok": True, "data": {"stopping": False}})

            m_rev = re.fullmatch(r"/api/livros/([\w.-]+)/revisar", path)
            if m_rev:
                return self._livro_revisar(m_rev.group(1))
            m_pub = re.fullmatch(r"/api/livros/([\w.-]+)/publicar", path)
            if m_pub:
                return self._livro_publicar(m_pub.group(1))

            if path == "/api/livros/criar":
                body = self._read_json()
                genero = str(body.get("genero") or "").strip()
                titulo = str(body.get("titulo") or "").strip()
                autor = str(body.get("autor") or "").strip()
                slug = str(body.get("slug") or "").strip()
                def _optint(v):
                    try:
                        return int(v) if v else None
                    except (TypeError, ValueError):
                        return None
                meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
                meta = {str(k): str(v) for k, v in meta.items() if isinstance(v, (str, int, float))}
                try:
                    from book.book_project import criar_livro
                    book = criar_livro(slug=slug, genero=genero, titulo=titulo, autor=autor,
                                       total=_optint(body.get("total")), wpc=_optint(body.get("wpc")),
                                       meta=meta)
                    return self._json(201, {"ok": True, "data": {"slug": book.name}})
                except FileExistsError as exc:
                    return self._json(200, {"ok": False, "error": {"code": "EXISTS", "message": str(exc)}})
                except ValueError as exc:
                    return self._json(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": str(exc)}})
                except Exception as exc:  # noqa
                    return self._json(200, {"ok": False, "error": {"code": "ERROR", "message": str(exc)}})

            if path == "/api/session/new":
                return self._json(201, {
                    "ok": True,
                    "data": self.sessions.create(),
                })

            match = SESSION_ROUTE_RE.fullmatch(path)
            if match and match.group(2) == "save":
                body = self._read_json()
                snap = self.engine.snapshot()
                saved = self.sessions.save(
                    match.group(1),
                    body.get("messages") if isinstance(body.get("messages"), list) else [],
                    mode=str(body.get("mode") or snap.get("requested_mode") or "auto"),
                    active_profile=snap.get("active_profile"),
                    model=snap.get("model"),
                )
                return self._json(200, {"ok": True, "data": saved})

            if path == "/api/calibrate":
                data = self.calibration.start()
                return self._json(202, {"ok": True, "data": data})

            if path == "/api/calibrate/cancel":
                data = self.calibration.cancel()
                return self._json(200, {"ok": True, "data": data})

            if path.startswith("/api/maintenance/") and self.calibration.is_running():
                raise MaintenanceError(
                    "Aguarde a calibração terminar antes de executar manutenção."
                )

            if path == "/api/maintenance/restart":
                data = self.maintenance.restart_engine()
                return self._json(200, {"ok": True, "data": data})

            if path == "/api/maintenance/use-cpu":
                data = self.maintenance.use_cpu()
                return self._json(200, {"ok": True, "data": data})

            if path == "/api/maintenance/profile-backend":
                data = self.maintenance.restore_profile_backend()
                return self._json(200, {"ok": True, "data": data})

            if path == "/api/maintenance/repair":
                body = self._read_json()
                backend = str(body.get("backend", "")).lower()
                if backend not in ("cpu", "cuda"):
                    raise ValueError("Backend inválido para reparo.")
                data = self.maintenance.repair_backend(backend)
                return self._json(200, {"ok": True, "data": data})

            if path == "/api/shutdown":
                self._json(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return

            return self._json(404, {
                "ok": False,
                "error": {"code": "NOT_FOUND", "message": "Endpoint inexistente."},
            })

        except ValueError as exc:
            return self._json(400, {
                "ok": False,
                "error": {"code": "BAD_REQUEST", "message": str(exc)},
            })
        except FileNotFoundError as exc:
            return self._json(404, {
                "ok": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": str(exc)},
            })
        except WorkspaceError as exc:
            return self._json(400, {
                "ok": False,
                "error": {"code": "WORKSPACE_ERROR", "message": str(exc)},
            })
        except CalibrationError as exc:
            return self._json(409, {
                "ok": False,
                "error": {"code": "CALIBRATION_ERROR", "message": str(exc)},
            })
        except MaintenanceError as exc:
            return self._json(409, {
                "ok": False,
                "error": {"code": "MAINTENANCE_ERROR", "message": str(exc)},
            })
        except EngineError as exc:
            return self._json(503, {
                "ok": False,
                "error": {"code": "ENGINE_ERROR", "message": str(exc)},
            })
        except Exception as exc:
            return self._json(500, {
                "ok": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(exc)},
            })

    def do_DELETE(self):
        if not self._origin_allowed():
            return self._json(403, {
                "ok": False,
                "error": {"code": "ORIGIN_BLOCKED", "message": "Origem não permitida."},
            })

        path = urllib.parse.urlsplit(self.path).path

        file_match = FILE_ROUTE_RE.fullmatch(path)
        if file_match and file_match.group(2):
            try:
                deleted = self.workspace.delete_file(
                    file_match.group(1), file_match.group(2)
                )
            except WorkspaceError as exc:
                return self._json(400, {
                    "ok": False,
                    "error": {"code": "WORKSPACE_ERROR", "message": str(exc)},
                })
            if not deleted:
                return self._json(404, {
                    "ok": False,
                    "error": {"code": "FILE_NOT_FOUND", "message": "Arquivo não encontrado."},
                })
            return self._json(200, {"ok": True})

        match = SESSION_ROUTE_RE.fullmatch(path)
        if not match or match.group(2):
            return self._json(404, {
                "ok": False,
                "error": {"code": "NOT_FOUND", "message": "Endpoint inexistente."},
            })
        try:
            deleted = self.sessions.delete(match.group(1))
        except ValueError as exc:
            return self._json(400, {
                "ok": False,
                "error": {"code": "BAD_REQUEST", "message": str(exc)},
            })
        if not deleted:
            return self._json(404, {
                "ok": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."},
            })
        self.workspace.delete_session(match.group(1))
        return self._json(200, {"ok": True})

    def _chat_stream(self):
        body = self._read_json()
        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages deve conter ao menos uma mensagem.")

        session_id = str(body.get("session_id") or "").lower()
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                question = str(msg.get("content") or "")
                break

        enriched = [dict(m) for m in messages if isinstance(m, dict)]
        if session_id:
            try:
                file_context = self.workspace.context_for_question(session_id, question)
            except WorkspaceError:
                file_context = ""
            if file_context:
                for msg in reversed(enriched):
                    if msg.get("role") == "user":
                        msg["content"] = (
                            str(msg.get("content") or "")
                            + "\n\n"
                            + file_context
                        )
                        break

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "close")
        self.send_header("X-Nucleo-IA", APP_VERSION)
        self._security_headers()
        self.end_headers()

        def emit(obj):
            data = "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
            self.wfile.write(data.encode("utf-8"))
            self.wfile.flush()

        try:
            for event in self.engine.stream_chat(enriched):
                emit(event)
        except EngineError as exc:
            try:
                emit({"type": "error", "message": str(exc)})
            except Exception:
                pass
        except (BrokenPipeError, ConnectionResetError):
            self.engine.request_stop_generation()
        except Exception as exc:
            try:
                emit({"type": "error", "message": str(exc)})
            except Exception:
                pass

    def _export_file(self):
        """Exporta conteúdo (Markdown/texto) para .docx ou .xlsx e devolve o
        binário para download. Usado pelo Chat e pela Análise de Arquivos.
        Corpo: {formato: 'docx'|'xlsx', content: str, titulo?: str}."""
        try:
            body = self._read_json(max_bytes=12_000_000)
        except ValueError as exc:
            return self._json(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": str(exc)}})
        fmt = str(body.get("formato") or body.get("format") or "").lower()
        content = str(body.get("content") or "")
        titulo = str(body.get("titulo") or "NUCLEO").strip() or "NUCLEO"
        if fmt not in ("docx", "xlsx"):
            return self._json(400, {"ok": False, "error": {"code": "BAD_FORMAT", "message": "Formato deve ser docx ou xlsx."}})
        if not content.strip():
            return self._json(400, {"ok": False, "error": {"code": "EMPTY", "message": "Nada para exportar."}})
        try:
            import exporters
            if fmt == "docx":
                data = exporters.md_to_docx(content, titulo)
                ctype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                data = exporters.md_to_xlsx(content, titulo)
                ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except Exception as exc:  # noqa
            return self._json(200, {"ok": False, "error": {"code": "EXPORT_FAIL", "message": str(exc)}})
        safe = re.sub(r"[^A-Za-z0-9_.\-]+", "_", titulo)[:60].strip("_") or "NUCLEO"
        fname = f"{safe}.{fmt}"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Nucleo-IA", APP_VERSION)
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _financeiro_gerar(self):
        """Devolve a planilha do usuário PREENCHIDA com os dados de um ano — versão
        'fiel' ou 'aprimorada' (app/financeiro.py + financeiro_dados.py).
        Corpo: {versao: 'fiel'|'aprimorada', ano: int}. O modelo é de terceiros e
        fica só na máquina do usuário: NÃO há download do modelo em branco."""
        try:
            body = self._read_json()
        except ValueError as exc:
            return self._json(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": str(exc)}})
        versao = str(body.get("versao") or "").lower()
        try:
            import financeiro
            if not body.get("ano"):
                raise ValueError("informe o ano: só a planilha preenchida com os seus dados é gerada")
            import financeiro_dados as FD
            data, fname = FD.exportar(body.get("ano"), versao)
        except ValueError as exc:
            return self._json(400, {"ok": False, "error": {"code": "BAD_VERSION", "message": str(exc)}})
        except FileNotFoundError as exc:
            return self._json(409, {"ok": False, "error": {"code": "FIN_SEM_MODELO", "message": str(exc)}})
        except Exception as exc:  # noqa
            return self._json(200, {"ok": False, "error": {"code": "FIN_FAIL", "message": str(exc)}})
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Nucleo-IA", APP_VERSION)
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _forja_gerar(self):
        """Geração de prompt da Forja usando o MOTOR LOCAL (não-streaming).
        O 'system' da Forja é dobrado no turno do usuário porque o engine
        prepende seu próprio system e só aceita roles user/assistant.

        Engenharia reversa de imagem: quando o corpo traz `image` (data-URL
        base64), troca o motor pro modo 'vision' (Gemma 3 4B + mmproj),
        gera com a imagem de fato anexada, e restaura o modo anterior do
        chat ao final — mesmo padrão de handoff usado por _book_run_stream."""
        body = self._read_json(max_bytes=15_000_000)
        system = str(body.get("system") or "").strip()
        user = str(body.get("user") or "").strip()
        image = body.get("image")
        try:
            max_tokens = int(body.get("max_tokens") or 1200)
        except (TypeError, ValueError):
            max_tokens = 1200
        max_tokens = max(256, min(max_tokens, 2000))
        if not user and not system:
            return self._json(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": "Prompt vazio."}})
        if image is not None and (
            not isinstance(image, str) or not image.startswith("data:image/") or ";base64," not in image
        ):
            return self._json(400, {"ok": False, "error": {"code": "BAD_REQUEST", "message": "Imagem inválida."}})
        combined = (system + "\n\n" + user).strip()
        message = {"role": "user", "content": combined}
        if image:
            message["images"] = [image]

        prev_mode = None
        switched = False
        if image:
            prev_mode = self.engine.requested_mode
            try:
                self.engine.switch_mode("vision")
                switched = True
            except EngineError as exc:
                return self._json(200, {"ok": False, "error": {"code": "VISION_UNAVAILABLE", "message": str(exc)}})

        try:
            parts = []
            truncated = False
            for ev in self.engine.stream_chat([message], max_tokens=max_tokens):
                if not isinstance(ev, dict):
                    continue
                if ev.get("type") == "delta" and ev.get("text"):
                    parts.append(ev["text"])
                elif ev.get("type") == "done":
                    truncated = bool(ev.get("truncated"))
            text, tags_trimmed = _forja_limpar_tags("".join(parts).strip())
            return self._json(200, {"ok": True, "text": text.strip(),
                                    "truncated": truncated, "tags_trimmed": tags_trimmed})
        except EngineError as exc:
            return self._json(200, {"ok": False, "error": {"code": "ENGINE_ERROR", "message": str(exc)}})
        finally:
            if switched:
                try:
                    self.engine.start(prev_mode or "auto")
                except Exception:
                    pass

    def _livro_dir(self, slug):
        base = (ROOT / "workspace" / "livros").resolve()
        d = (base / slug).resolve()
        if base not in d.parents or not d.is_dir():
            return None
        return d

    def _livro_revisar(self, slug):
        """REVISAR (determinístico, sem IA): auditoria + humanização + redundância
        semântica + compila o manuscrito. Roda em processo (não usa o motor)."""
        d = self._livro_dir(slug)
        if d is None:
            return self._json(404, {"ok": False, "error": {"code": "LIVRO_NOT_FOUND", "message": "Livro não encontrado."}})
        try:
            from book import revisar as R
            rev = d / "07_REVISAO"
            rev.mkdir(parents=True, exist_ok=True)
            (rev / "AUDITORIA.md").write_text(R.auditar(d), encoding="utf-8")
            (rev / "PASSE_HUMANIZACAO.md").write_text(R.humanizar_tudo(d), encoding="utf-8")
            (rev / "REDUNDANCIA_SEMANTICA.md").write_text(R.redundancia_semantica(d), encoding="utf-8")
            man = R.compilar(d)
            return self._json(200, {"ok": True, "data": {
                "manuscrito": man.name,
                "reports": ["AUDITORIA.md", "PASSE_HUMANIZACAO.md", "REDUNDANCIA_SEMANTICA.md"],
            }})
        except Exception as exc:  # noqa
            return self._json(200, {"ok": False, "error": {"code": "REVISAR_ERROR", "message": str(exc)}})

    def _livro_publicar(self, slug):
        """PUBLICAR (diagramador, sem IA): gera .docx + .epub em 08_PUBLICACAO."""
        d = self._livro_dir(slug)
        if d is None:
            return self._json(404, {"ok": False, "error": {"code": "LIVRO_NOT_FOUND", "message": "Livro não encontrado."}})
        try:
            from book import publicar as P
            docx, epub = P.publicar(d)
            return self._json(200, {"ok": True, "data": {
                "docx": docx.name if docx else None,
                "epub": epub.name if epub else None,
            }})
        except Exception as exc:  # noqa
            return self._json(200, {"ok": False, "error": {"code": "PUBLICAR_ERROR", "message": str(exc)}})

    def _hardware_diagnostico(self):
        """Detecta o hardware (sem psutil) e classifica GGUF em folga/limite/não-roda."""
        import hardware as hw_mod
        import catalog as cat
        import gguf_advisor as adv
        hw = hw_mod.detect_safe()
        caps = cat.caps_from_hardware(hw)
        gpu_nome = "nenhuma NVIDIA"
        for g in getattr(hw, "gpus", []) or []:
            if getattr(g, "vendor", "") == "NVIDIA":
                gpu_nome = getattr(g, "name", None) or "NVIDIA"
                break
        gguf = adv.classify(caps["ram_gb"], caps["vram_gb"], caps["cuda_available"])
        hardware_info = {
            "cpu": getattr(hw, "cpu", "?"),
            "physical_cores": getattr(hw, "physical_cores", None),
            "logical_threads": getattr(hw, "logical_threads", None),
            "ram_total_gb": round(float(getattr(hw, "ram_total_gb", 0) or 0), 2),
            "ram_available_gb": round(float(getattr(hw, "ram_available_gb", 0) or 0), 2),
            "gpu_nome": gpu_nome,
            "nvidia_detected": bool(getattr(hw, "nvidia_detected", False)),
        }
        data = {"hardware": hardware_info, "gguf": gguf}
        data["relatorio_txt"] = adv.build_report_text(data)
        return data

    def _book_run_stream(self, slug, acao, modo, n_cap=None):
        """Roda OUTLINE/ESCREVER como subprocesso e transmite o stdout via SSE.
        Handoff do motor: pausa o motor do chat, o subprocesso sobe o seu, e ao
        final o motor do chat é religado. Um job por vez (_BOOK_LOCK)."""
        d = self._livro_dir(slug)

        def open_sse():
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store")
            self.send_header("Connection", "close")
            self.send_header("X-Nucleo-IA", APP_VERSION)
            self._security_headers()
            self.end_headers()

        def emit(o):
            self.wfile.write(("data: " + json.dumps(o, ensure_ascii=False) + "\n\n").encode("utf-8"))
            self.wfile.flush()

        if d is None:
            open_sse(); emit({"type": "error", "message": "Livro não encontrado."}); emit({"type": "done", "code": -1}); return
        if acao not in ("outline", "escrever"):
            open_sse(); emit({"type": "error", "message": "Ação inválida."}); emit({"type": "done", "code": -1}); return
        if modo not in ("auto", "fast", "quality", "advanced"):
            modo = "advanced"
        if not _BOOK_LOCK.acquire(blocking=False):
            open_sse(); emit({"type": "error", "message": "Já há um trabalho de escrita em andamento."}); emit({"type": "done", "code": -1}); return

        open_sse()
        proc = None
        try:
            script = "outline.py" if acao == "outline" else "escrever.py"
            if acao == "outline":
                args = ["gerar", "--dir", str(d), "--modo", modo]
            elif n_cap:
                args = ["capitulo", "--n", str(n_cap), "--dir", str(d), "--modo", modo, "--partes", "4"]
            else:
                args = ["proximo", "--dir", str(d), "--modo", modo, "--partes", "4"]
            cmd = [sys.executable, "-u", str(APP_DIR / "book" / script)] + args
            emit({"type": "start", "acao": acao, "modo": modo})
            try:
                self.engine.stop()
                emit({"type": "log", "line": "⏸ motor do chat pausado (liberando recursos para a escrita)"})
            except Exception as exc:  # noqa
                emit({"type": "log", "line": "aviso ao pausar motor: %s" % exc})
            env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", bufsize=1, env=env,
                                    creationflags=flags)
            _BOOK_JOB["proc"] = proc
            for line in proc.stdout:
                emit({"type": "log", "line": line.rstrip("\r\n")})
            proc.wait()
            emit({"type": "done", "code": proc.returncode})
        except (BrokenPipeError, ConnectionResetError):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        except Exception as exc:  # noqa
            try:
                emit({"type": "error", "message": str(exc)}); emit({"type": "done", "code": -1})
            except Exception:
                pass
        finally:
            p = _BOOK_JOB.get("proc")
            if p and p.poll() is None:
                try:
                    p.terminate(); p.wait(timeout=15)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
            _BOOK_JOB["proc"] = None
            try:
                self.engine.start("auto")
            except Exception:
                pass
            try:
                _BOOK_LOCK.release()
            except Exception:
                pass

    def _serve_static(self, path):
        if path in ("", "/"):
            target = UI_DIR / "index.html"
        else:
            rel = path.lstrip("/")
            target = (UI_DIR / rel).resolve()
            try:
                target.relative_to(UI_DIR.resolve())
            except ValueError:
                return self._json(403, {"ok": False, "error": {"message": "Acesso negado."}})

        if not target.is_file():
            return self._json(404, {"ok": False, "error": {"message": "Arquivo não encontrado."}})

        ctype, _ = mimetypes.guess_type(target.name)
        ctype = ctype or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""),
        )
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Nucleo-IA", APP_VERSION)
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)



def existing_instance_url(port=18080):
    """Reabre uma instância já ativa em vez de carregar um segundo modelo."""
    url = f"http://{HOST}:{port}/api/status"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=0.8) as r:
            data = json.loads(r.read().decode("utf-8"))
        payload = data.get("data") if isinstance(data, dict) else None
        if (
            data.get("ok") is True
            and isinstance(payload, dict)
            and payload.get("machine_id")
            and data.get("version")
        ):
            return f"http://{HOST}:{port}/"
    except Exception:
        return None
    return None


def main():
    if os.name != "nt":
        print(f"NÚCLEO IA PORTÁTIL {APP_VERSION} foi preparado para Windows x64.")
        return 2

    existing = existing_instance_url(18080)
    if existing:
        print("O NÚCLEO já está em execução. Reabrindo a interface...")
        webbrowser.open(existing, new=2)
        return 0

    print("=" * 72)
    print(f"          NÚCLEO IA PORTÁTIL — V{APP_VERSION}")
    print("=" * 72)
    print("Interface Local — Arquivos e Análise Local.")
    print("Minimalismo funcional: sem frameworks e sem banco de dados.")
    print()

    try:
        engine = EngineManager(ROOT)
        sessions = SessionStore(ROOT)
        calibration = CalibrationManager(ROOT, engine)
        maintenance = MaintenanceManager(ROOT, engine)
        workspace = WorkspaceStore(ROOT)
    except Exception as exc:
        print("Não foi possível carregar o NÚCLEO:")
        print(exc)
        return 3

    if engine.has_profile():
        try:
            print("Iniciando motor em modo AUTO...")
            engine.start("auto")
        except Exception as exc:
            engine.status = "error"
            engine.last_error = str(exc)
            print("Aviso: motor não iniciou:", exc)
    else:
        engine.status = "needs_calibration"
        print("Nova máquina detectada: aguardando calibração pela interface.")

    port = free_port(18080)
    httpd = NucleoHTTPServer((HOST, port), Handler, engine, sessions, calibration, maintenance, workspace)
    url = f"http://{HOST}:{port}/"

    stop_once = threading.Event()

    def shutdown_handler(*_):
        if stop_once.is_set():
            return
        stop_once.set()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown_handler)

    print("Interface:", url)
    print("Histórico:", ROOT / "sessions")
    print("Acesso de rede: somente 127.0.0.1 (este computador)")
    print("Feche esta janela ou pressione Ctrl+C para encerrar.")
    print()

    threading.Timer(0.8, lambda: webbrowser.open(url, new=2)).start()

    try:
        httpd.serve_forever(poll_interval=0.4)
    finally:
        engine.stop()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
