#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import atexit
import json
import os
import shutil
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))

import hardware
import plat
try:
    import catalog  # V0.7 Fase 3: resolução de modelo por id (opcional)
except Exception:
    catalog = None


class EngineError(RuntimeError):
    pass


def _safe_exists(path: Path):
    try:
        return path.exists(), None
    except OSError as exc:
        return False, exc


def _free_port(preferred: int = 18081) -> int:
    def available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    if available(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _nvidia_memory():
    exe = shutil.which("nvidia-smi.exe") or shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        p = subprocess.run(
            [exe, "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=8
        )
        rows = []
        for line in p.stdout.splitlines():
            vals = [x.strip() for x in line.split(",")]
            if len(vals) >= 2:
                try:
                    rows.append((float(vals[0]), float(vals[1])))
                except ValueError:
                    pass
        return max(rows, key=lambda x: x[1]) if rows else None
    except Exception:
        return None


class EngineManager:
    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.app_dir = self.root / "app"
        self.profile_dir = self.root / "profiles" / "machines"
        self.log_dir = self.root / "logs" / "v0_6"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.hw = None
        self.machine_id = None
        self.machine_id_v2 = None
        self.detection_confidence = None
        self.profile = None

        self.requested_mode = "auto"
        self.active_key = None
        self.active_profile = None
        self.backend_actual = None
        self.backend_reason = None
        self.process = None
        self.log_handle = None
        self.port = None
        self.status = "stopped"
        self.last_error = None
        self.last_tps = None
        self.forced_backend = None
        self._help_cache = {}
        self.api_key = secrets.token_urlsafe(24)
        self.server_auth_enabled = False
        self.parallel_slots = None
        self.lock = threading.RLock()
        self.stop_event = threading.Event()

        self._detect_machine()
        self.reload_profile()
        if not self.profile:
            self.status = "needs_calibration"

        # V0.6.5.3: limpa llama-server órfãos deixados por um encerramento
        # sujo anterior, evitando 401 (chave efêmera) e conflito de porta.
        try:
            self._reap_orphan_servers()
        except Exception:
            pass

        atexit.register(self.stop)

    def _detect_machine(self):
        if os.name != "nt":
            profiles = list(self.profile_dir.glob("*.json"))
            if profiles:
                data = json.loads(profiles[0].read_text(encoding="utf-8-sig"))
                self.machine_id = data.get("machine_id", "test")
            else:
                self.machine_id = "test"
            self.hw = None
            return

        # V0.7 Fase 1: detecção à prova de crash (nunca deixa o app sem HW).
        detect = getattr(hardware, "detect_safe", hardware.detect_windows)
        self.hw = detect()
        self.machine_id = hardware.machine_id(self.hw)
        try:
            self.machine_id_v2 = hardware.machine_id_v2(self.hw)
            self.detection_confidence = hardware.detection_confidence(self.hw)
        except Exception:
            self.machine_id_v2 = None
            self.detection_confidence = None
        if self.detection_confidence and self.detection_confidence.get("level") == "low":
            # Não bloqueia; apenas registra para evitar recalibração indevida.
            self.last_error = (
                "Confiança de detecção baixa: "
                + ", ".join(self.detection_confidence.get("reasons", []))
            )

    def profile_path(self) -> Path:
        return self.profile_dir / f"{self.machine_id}.json"

    def reload_profile(self) -> bool:
        with self.lock:
            path = self.profile_path()
            if not path.exists():
                self.profile = None
                return False
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(data, dict):
                    raise ValueError("Perfil inválido.")
                self.profile = data
                return True
            except Exception as exc:
                self.profile = None
                self.last_error = f"Não foi possível ler o perfil: {exc}"
                return False

    def has_profile(self) -> bool:
        return isinstance(self.profile, dict) and bool(self.profile.get("modes"))

    def public_modes(self):
        if not self.profile:
            return {}
        modes = self.profile.get("modes", {})
        result = {}
        for key in ("fast", "quality", "code"):
            if key not in modes:
                continue
            p = modes[key]
            result[key] = {
                "key": key,
                "name": p.get("mode_name", key.upper()),
                "model": Path(p.get("model", "")).name,
                "model_id": p.get("model_id"),
                "backend": p.get("backend", "cpu"),
                "reference_tps": p.get("observed_chat_generation_tps")
                    or p.get("generation_tps"),
                "gpu_layers": p.get("gpu_layers", 0),
                "context_size": p.get("context_size", 4096),
                "vram_headroom_mib": p.get("observed_vram_headroom_mib"),
            }
        return result

    def _select_key(self, requested: str) -> str:
        if not self.has_profile():
            raise EngineError("Esta máquina precisa ser calibrada antes de iniciar a IA.")

        modes = self.profile.get("modes", {})
        if requested == "auto":
            chosen = self.profile.get("recommended_auto", "fast")
            if chosen not in modes:
                chosen = "fast" if "fast" in modes else next(iter(modes))

            if chosen == "quality" and "fast" in modes:
                mem = _nvidia_memory()
                q = modes["quality"]
                required = q.get("observed_vram_used_mib")
                reserve = int(self.profile.get("policy", {}).get(
                    "minimum_vram_headroom_mib", 400))
                if mem and required:
                    used_now, total = mem
                    free_now = total - used_now
                    if free_now < float(required) + reserve:
                        chosen = "fast"
            return chosen

        if requested not in modes:
            raise EngineError(f"Modo indisponível: {requested}")
        return requested

    def _help_text(self, exe: Path) -> str:
        key = str(exe).lower()
        if key in self._help_cache:
            return self._help_cache[key]
        try:
            p = subprocess.run(
                [str(exe), "--help"],
                cwd=str(exe.parent),
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    if os.name == "nt" else 0,
            )
            text = p.stdout + "\n" + p.stderr
        except Exception:
            text = ""
        self._help_cache[key] = text
        return text

    def _supports(self, exe: Path, option: str) -> bool:
        return option in self._help_text(exe)

    def _server_exe(self, backend: str) -> Path:
        # Resolucao por SO (Windows: engine/windows/...exe; Linux: linux/engine/...).
        return plat.engine_exe(self.root, backend, "llama-server")

    def _simulate_no_nvidia(self) -> bool:
        """V0.7 Fase 2 — modo de simulação para testar o fallback CPU-only sem
        uma segunda máquina. Ativado por variável de ambiente
        NUCLEO_SIMULATE_NO_NVIDIA=1 OU pela presença do arquivo
        state\\SIMULATE_NO_NVIDIA. Relido a cada início (toggle a quente)."""
        val = os.environ.get("NUCLEO_SIMULATE_NO_NVIDIA", "").strip().lower()
        if val in ("1", "true", "sim", "yes", "on"):
            return True
        try:
            if (self.root / "state" / "SIMULATE_NO_NVIDIA").exists():
                return True
        except Exception:
            pass
        return False

    def _cuda_available(self) -> bool:
        """True somente se vale a pena tentar o backend CUDA: há GPU NVIDIA
        detectada e a simulação de 'sem NVIDIA' não está ativa."""
        if self._simulate_no_nvidia():
            return False
        try:
            return bool(getattr(self.hw, "nvidia_detected", False))
        except Exception:
            return False

    def _resolve_model_path(self, profile: dict) -> Path:
        """V0.7 Fase 3: resolve o arquivo do modelo pelo `model_id` (catálogo);
        cai para o campo legado `model` (perfis v2) se o id/registro faltar."""
        mid = profile.get("model_id")
        if mid and catalog is not None:
            try:
                m = catalog.get_model(mid, root=self.root)
                if m and m.get("file"):
                    cand = self.root / "models" / m["file"]
                    if cand.exists():
                        return cand
            except Exception:
                pass
        return self.root / profile.get("model", "")

    def _build_command(self, profile: dict, backend_override: str | None = None):
        backend = backend_override or profile.get("backend", "cpu")
        exe = self._server_exe(backend)
        model = self._resolve_model_path(profile)
        threads = int(
            profile.get("cpu_threads", 4)
            if backend == profile.get("backend")
            else profile.get("fallback_cpu_threads", profile.get("cpu_threads", 4))
        )
        ngl = int(profile.get("gpu_layers", 0)) if backend == "cuda" else 0
        ctx = int(profile.get("context_size", 4096))
        port = self.port or _free_port()

        cmd = [
            str(exe),
            "--model", str(model),
            "--threads", str(threads),
            "--n-gpu-layers", str(ngl),
            "--ctx-size", str(ctx),
            "--host", "127.0.0.1",
            "--port", str(port),
        ]

        if self._supports(exe, "--reasoning"):
            cmd += ["--reasoning", "off"]
        elif self._supports(exe, "--chat-template-kwargs"):
            cmd += ["--chat-template-kwargs", '{"enable_thinking":false}']

        api_key_enabled = self._supports(exe, "--api-key")
        if api_key_enabled:
            cmd += ["--api-key", self.api_key]

        parallel_slots = None
        if self._supports(exe, "--parallel"):
            cmd += ["--parallel", "1"]
            parallel_slots = 1

        if self._supports(exe, "--no-webui"):
            cmd += ["--no-webui"]

        return {
            "cmd": cmd,
            "exe": exe,
            "model": model,
            "threads": threads,
            "gpu_layers": ngl,
            "context_size": ctx,
            "backend": backend,
            "port": port,
            "api_key_enabled": api_key_enabled,
            "parallel_slots": parallel_slots,
        }

    def _validate_runtime(self, built):
        for label, path in [("motor", built["exe"]), ("modelo", built["model"])]:
            ok, err = _safe_exists(path)
            if not ok:
                if err and getattr(err, "winerror", None) == 1392:
                    raise EngineError(
                        f"O {label} está ilegível (Windows 1392): {path}"
                    )
                raise EngineError(f"{label.capitalize()} ausente: {path}")

    def _wait_health(self, timeout=120):
        url = f"http://127.0.0.1:{self.port}/health"
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            if self.process and self.process.poll() is not None:
                raise EngineError(
                    f"llama-server encerrou com código {self.process.returncode}. "
                    f"Veja logs\\v0_6\\llama-server.log"
                )
            try:
                headers = {}
                if self.server_auth_enabled:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=2) as r:
                    if r.status == 200:
                        return
            except Exception as exc:
                last = exc
            time.sleep(0.25)
        raise EngineError(f"llama-server não ficou pronto a tempo: {last}")

    def start(self, requested_mode: str = "auto"):
        with self.lock:
            if not self.has_profile():
                self.status = "needs_calibration"
                raise EngineError("Esta máquina precisa ser calibrada.")

            self.requested_mode = requested_mode
            key = self._select_key(requested_mode)
            p = dict(self.profile["modes"][key])

            # V0.7 Fase 2: sem NVIDIA (real ou simulado) => CPU direto.
            cuda_ok = self._cuda_available()
            desired_backend = (
                "cpu" if (self.forced_backend == "cpu" or not cuda_ok)
                else p.get("backend", "cpu")
            )
            if (
                self.process
                and self.process.poll() is None
                and self.active_key == key
                and self.backend_actual == desired_backend
            ):
                self.status = "ready"
                return self.snapshot()

            self.stop(preserve_needs_calibration=False)
            # V0.6.5.3: antes de reservar porta e subir nova engine, encerra
            # qualquer llama-server órfão deste projeto (nosso já foi parado).
            try:
                self._reap_orphan_servers()
            except Exception:
                pass
            self.status = "starting"
            self.last_error = None
            self.port = _free_port(18081)

            if self.forced_backend == "cpu":
                attempts = ["cpu"]
                self.backend_reason = "CPU forçado (manutenção)"
            elif not cuda_ok:
                attempts = ["cpu"]
                self.backend_reason = (
                    "simulação sem NVIDIA" if self._simulate_no_nvidia()
                    else "sem GPU NVIDIA detectada"
                )
            else:
                attempts = [p.get("backend", "cpu")]
                if attempts[0] == "cuda":
                    attempts.append("cpu")
                self.backend_reason = "conforme perfil"

            errors = []
            for backend in attempts:
                try:
                    built = self._build_command(p, backend_override=backend)
                    self._validate_runtime(built)

                    log_path = self.log_dir / "llama-server.log"
                    self.log_handle = open(log_path, "a", encoding="utf-8", errors="replace")
                    self.log_handle.write(
                        f"\n\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"mode={requested_mode} profile={key} backend={backend} ===\n"
                    )
                    self.log_handle.flush()

                    creationflags = 0
                    if os.name == "nt":
                        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

                    self.process = subprocess.Popen(
                        built["cmd"],
                        cwd=str(built["exe"].parent),
                        stdout=self.log_handle,
                        stderr=subprocess.STDOUT,
                        creationflags=creationflags,
                    )
                    self.backend_actual = backend
                    self.active_key = key
                    self.active_profile = p
                    self.server_auth_enabled = bool(built.get("api_key_enabled"))
                    self.parallel_slots = built.get("parallel_slots")
                    self._wait_health()
                    self.status = "ready"
                    return self.snapshot()

                except Exception as exc:
                    errors.append(f"{backend}: {exc}")
                    self._terminate_process_only()
                    if self.log_handle:
                        try:
                            self.log_handle.close()
                        except Exception:
                            pass
                        self.log_handle = None

            self.status = "error"
            self.last_error = " | ".join(errors)
            raise EngineError(self.last_error)

    def _reap_orphan_servers(self):
        """V0.6.5.3 — encerra llama-server órfãos deste projeto.

        Quando o backend Python encerra de forma suja, o llama-server pode
        continuar rodando com a chave efêmera antiga e segurando a porta,
        causando 'HTTP 401 Invalid API Key' na próxima sessão. Aqui varremos
        os processos llama-server cujo executável está sob a pasta engine\\
        DESTE projeto e encerramos os que não são o nosso processo atual.

        Escopo restrito ao próprio projeto: nunca toca em um llama-server
        iniciado a partir de outro caminho. Windows apenas; no-op fora dele
        e em qualquer falha (best-effort).
        """
        if os.name != "nt":
            return []
        engine_root = str((self.root / "engine").resolve()).lower()
        keep_pid = None
        try:
            if self.process and self.process.poll() is None:
                keep_pid = int(self.process.pid)
        except Exception:
            keep_pid = None

        ps = (
            "$ErrorActionPreference='SilentlyContinue';"
            "Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" |"
            " ForEach-Object { \"$($_.ProcessId)|$($_.ExecutablePath)\" }"
        )
        reaped = []
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=15, creationflags=creationflags,
            ).stdout
        except Exception:
            return []

        for line in (out or "").splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            pid_str, _, exe_path = line.partition("|")
            try:
                pid = int(pid_str.strip())
            except ValueError:
                continue
            exe_path = (exe_path or "").strip().lower()
            if not exe_path or not exe_path.startswith(engine_root):
                continue
            if keep_pid is not None and pid == keep_pid:
                continue
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F", "/T"],
                    capture_output=True, text=True, timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                reaped.append(pid)
            except Exception:
                pass

        if reaped:
            try:
                with open(self.log_dir / "orphan_reap.log", "a",
                          encoding="utf-8", errors="replace") as fh:
                    fh.write(
                        f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"reaped llama-server orfaos: {reaped}\n"
                    )
            except Exception:
                pass
        return reaped

    def _terminate_process_only(self):
        proc = self.process
        self.process = None
        if not proc:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        except Exception:
            pass

    def stop(self, preserve_needs_calibration=True):
        with self.lock:
            self.stop_event.set()
            self._terminate_process_only()
            if self.log_handle:
                try:
                    self.log_handle.close()
                except Exception:
                    pass
                self.log_handle = None
            self.backend_actual = None
            self.active_key = None
            self.active_profile = None
            self.port = None
            self.server_auth_enabled = False
            self.parallel_slots = None
            if preserve_needs_calibration and not self.has_profile():
                self.status = "needs_calibration"
            else:
                self.status = "stopped"

    def switch_mode(self, mode: str):
        with self.lock:
            self.stop_event.set()
        return self.start(mode)

    def restart(self):
        mode = self.requested_mode or "auto"
        self.stop(preserve_needs_calibration=False)
        return self.start(mode)

    def use_cpu(self):
        self.forced_backend = "cpu"
        mode = self.requested_mode or "auto"
        self.stop(preserve_needs_calibration=False)
        return self.start(mode)

    def restore_profile_backend(self, restart=True):
        self.forced_backend = None
        if restart and self.has_profile():
            mode = self.requested_mode or "auto"
            self.stop(preserve_needs_calibration=False)
            return self.start(mode)
        return self.snapshot()

    def request_stop_generation(self):
        self.stop_event.set()

    def _system_prompt(self):
        model = Path(self.active_profile.get("model", "")).name if self.active_profile else ""
        mode = (
            self.active_profile.get("mode_name", self.active_key)
            if self.active_profile else self.active_key
        )
        return (
            "Você é o assistente local do produto NÚCLEO IA PORTÁTIL. "
            "Responda em português do Brasil por padrão. "
            f"Modo atual: {mode}. Modelo-base: {model}. "
            "Diferencie sempre o produto NÚCLEO IA PORTÁTIL do modelo-base. "
            "Não exponha cadeia de pensamento, rascunhos internos nem blocos "
            "Start thinking/End thinking. Seja claro, útil e tecnicamente correto. "
            "Quando houver contexto de arquivos, priorize achados e conclusões; "
            "evite repetir metadados, colunas vazias ou listas longas sem necessidade; "
            "termine a resposta de forma completa e objetiva."
        )

    def stream_chat(self, messages: list[dict], max_tokens: int = 1536):
        if self.status != "ready" or not self.port:
            raise EngineError("Motor de IA não está pronto.")

        self.stop_event.clear()
        clean = []
        for m in messages[-40:]:
            role = m.get("role")
            content = str(m.get("content", "")).strip()
            if role in ("user", "assistant") and content:
                clean.append({"role": role, "content": content})

        prompt_messages = [{"role": "system", "content": self._system_prompt()}] + clean

        # V0.6.5.1: evita o corte seco observado em análises de planilha.
        # O limite antigo era fixo em 1024 tokens. Agora usamos um teto maior,
        # mas respeitamos aproximadamente o contexto ativo sem depender de um
        # tokenizer adicional (minimalismo funcional).
        context_size = 4096
        try:
            if self.active_profile:
                context_size = int(self.active_profile.get("context_size") or 4096)
        except (TypeError, ValueError):
            context_size = 4096

        prompt_chars = sum(len(str(m.get("content", ""))) for m in prompt_messages)
        # Estimativa conservadora para PT-BR/dados estruturados.
        estimated_input_tokens = max(1, int(prompt_chars / 3.2)) + (len(prompt_messages) * 8)
        safety_tokens = 320
        available_output = max(256, context_size - estimated_input_tokens - safety_tokens)
        effective_max_tokens = max(256, min(int(max_tokens), int(available_output)))

        payload = {
            "messages": prompt_messages,
            "max_tokens": effective_max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": 0.7,
            # Amostragem sã + anti-repetição. Sem isto o llama-server roda com
            # penalidade de repetição desligada (padrão 1.0) e modelos pequenos
            # entram em loop de frase (ex.: repetir a mesma linha até o fim).
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.05,
            "repeat_penalty": 1.15,
            "repeat_last_n": 256,
            # DRY: mata loop de trecho LITERAL (o que penalty comum não pega bem).
            # Chaves extras são ignoradas por builds que não suportam DRY.
            "dry_multiplier": 0.8,
            "dry_base": 1.75,
            "dry_allowed_length": 3,
            "dry_penalty_last_n": 1024,
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.server_auth_enabled:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST",
        )

        started = time.perf_counter()
        usage = None
        finish_reason = None
        response = None
        try:
            response = urllib.request.urlopen(req, timeout=600)
            for raw in response:
                if self.stop_event.is_set():
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    break
                try:
                    obj = json.loads(chunk)
                except json.JSONDecodeError:
                    continue

                if isinstance(obj.get("usage"), dict):
                    usage = obj["usage"]

                choices = obj.get("choices") or []
                if choices and isinstance(choices[0], dict):
                    choice = choices[0]
                    if choice.get("finish_reason") is not None:
                        finish_reason = choice.get("finish_reason")
                    delta = choice.get("delta") or {}
                    text = delta.get("content")
                    if isinstance(text, str) and text:
                        yield {"type": "delta", "text": text}

            elapsed = max(0.001, time.perf_counter() - started)
            measured = None
            if usage:
                comp = usage.get("completion_tokens")
                if isinstance(comp, (int, float)) and comp > 0:
                    measured = round(float(comp) / elapsed, 2)
                    self.last_tps = measured
            yield {
                "type": "done",
                "stopped": self.stop_event.is_set(),
                "tps": measured,
                "finish_reason": finish_reason,
                "truncated": finish_reason in ("length", "max_tokens"),
                "max_tokens": effective_max_tokens,
            }

        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:1200]
            raise EngineError(f"llama-server HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            if self.stop_event.is_set():
                yield {"type": "done", "stopped": True, "tps": None}
            else:
                raise EngineError(f"Falha durante a geração: {exc}") from exc
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

    def _hardware_summary(self):
        if self.hw is not None:
            gpu = None
            vram = None
            for g in self.hw.gpus:
                if g.vendor == "NVIDIA":
                    gpu = g.name
                    vram = g.vram_gb
                    break
            return {
                "manufacturer": self.hw.manufacturer,
                "computer_model": self.hw.model,
                "cpu": self.hw.cpu,
                "ram_total_gb": self.hw.ram_total_gb,
                "gpu": gpu,
                "gpu_vram_gb": vram,
            }

        if self.profile:
            h = self.profile.get("hardware_summary", {})
            return {
                "manufacturer": h.get("manufacturer"),
                "computer_model": h.get("model"),
                "cpu": h.get("cpu"),
                "ram_total_gb": h.get("ram_total_gb"),
                "gpu": h.get("nvidia_gpu"),
                "gpu_vram_gb": (
                    round(float(h.get("vram_total_mib")) / 1024, 2)
                    if h.get("vram_total_mib") else None
                ),
            }

        return {
            "manufacturer": None, "computer_model": None, "cpu": None,
            "ram_total_gb": None, "gpu": None, "gpu_vram_gb": None,
        }

    def snapshot(self):
        p = self.active_profile or {}
        mem = _nvidia_memory() if self.backend_actual == "cuda" else None
        h = self._hardware_summary()

        return {
            "status": self.status,
            "profile_available": self.has_profile(),
            "machine_id": self.machine_id,
            "machine_id_v2": self.machine_id_v2,
            "detection_confidence": self.detection_confidence,
            "requested_mode": self.requested_mode,
            "active_profile": self.active_key,
            "active_mode_name": p.get("mode_name"),
            "model": Path(p.get("model", "")).name if p else None,
            "model_id": (p.get("model_id") if p else None),
            "backend": self.backend_actual,
            "backend_policy": ("cpu_forced" if self.forced_backend == "cpu" else "profile"),
            "backend_reason": self.backend_reason,
            "cuda_available": self._cuda_available(),
            "simulate_no_nvidia": self._simulate_no_nvidia(),
            "engine_auth": self.server_auth_enabled,
            "parallel_slots": self.parallel_slots,
            "threads": (
                p.get("cpu_threads")
                if self.backend_actual == p.get("backend")
                else p.get("fallback_cpu_threads")
            ) if p else None,
            "gpu_layers": p.get("gpu_layers", 0) if self.backend_actual == "cuda" else 0,
            "context_size": p.get("context_size") if p else None,
            "reference_tps": (
                p.get("observed_chat_generation_tps") or p.get("generation_tps")
            ) if p else None,
            "last_tps": self.last_tps,
            "manufacturer": h["manufacturer"],
            "computer_model": h["computer_model"],
            "cpu": h["cpu"],
            "ram_total_gb": h["ram_total_gb"],
            "gpu": h["gpu"],
            "gpu_vram_gb": h["gpu_vram_gb"],
            "vram_used_mib": mem[0] if mem else None,
            "vram_total_mib": mem[1] if mem else None,
            "modes": self.public_modes(),
            "auto_recommends": (
                self.profile.get("recommended_auto", "fast")
                if self.profile else None
            ),
            "error": self.last_error,
        }
