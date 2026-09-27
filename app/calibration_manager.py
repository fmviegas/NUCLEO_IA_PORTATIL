#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path


class CalibrationError(RuntimeError):
    pass


class CalibrationManager:
    def __init__(self, root: Path, engine):
        self.root = Path(root)
        self.app_dir = self.root / "app"
        self.engine = engine
        self.lock = threading.RLock()
        self.proc = None
        self.thread = None
        self.cancel_requested = False
        self.started_at = None
        self.finished_at = None
        self.state = "idle"
        self.stage = "idle"
        self.progress = 0
        self.message = "Calibração não iniciada."
        self.error = None
        self.output = deque(maxlen=12)
        self.result = None
        self.started_monotonic = None
        self.stage_started_monotonic = None
        self.last_output_monotonic = None
        self.current_probe = None

        self.log_dir = self.root / "logs" / "v0_6"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / "calibration.log"

    @staticmethod
    def classify_line(line: str):
        s = line.strip()
        low = s.lower()

        if "machine id:" in low or low.startswith("cpu:") or low.startswith("ram:"):
            return "hardware", 10, "Hardware identificado."

        if "4b — cpu:" in low or "4b - cpu:" in low:
            return "cpu_4b", 20, "Testando CPU com o modelo RÁPIDO."
        if "4b — cuda:" in low or "4b - cuda:" in low:
            return "cuda_4b", 33, "Testando aceleração CUDA do modelo RÁPIDO."
        if "4b — sonda ram/vram" in low or "4b - sonda ram/vram" in low:
            return "memory_4b", 43, "Medindo RAM e VRAM do modelo RÁPIDO."

        if "8b — cpu:" in low or "8b - cpu:" in low:
            return "cpu_8b", 50, "Testando CPU com o modelo QUALIDADE."
        if "8b — cuda:" in low or "8b - cuda:" in low:
            return "cuda_8b", 63, "Testando aceleração CUDA do modelo QUALIDADE."
        if "8b — sonda ram/vram" in low or "8b - sonda ram/vram" in low:
            return "memory_8b", 74, "Medindo RAM e VRAM do modelo QUALIDADE."

        probe = re.search(r"sonda real\s+(4b|8b)\s*-\s*(\d+)\s+gpu layers", low)
        if probe:
            model_key = probe.group(1)
            layers = int(probe.group(2))
            if model_key == "4b":
                return (
                    "stability_4b", 82,
                    f"Validando RÁPIDO — {layers} GPU layers.",
                    {"model": "4B", "gpu_layers": layers},
                )
            return (
                "stability_8b", 90,
                f"Validando QUALIDADE — {layers} GPU layers.",
                {"model": "8B", "gpu_layers": layers},
            )

        if "sonda real 4b" in low:
            return "stability_4b", 82, "Validando estabilidade real do modo RÁPIDO.", None
        if "sonda real 8b" in low:
            return "stability_8b", 90, "Validando estabilidade real do modo QUALIDADE.", None
        if "sonda real 30b" in low or "sonda real advanced" in low:
            return "stability_30b", 92, "Validando modo AVANÇADO (carrega ~12 GB, pode levar 1–2 min).", None

        if "perfil v0.5 salvo:" in low:
            return "saving", 97, "Salvando o perfil desta máquina."
        if "modo auto recomendado:" in low:
            return "saving", 98, "Finalizando recomendação AUTO."

        if "executando benchmark base v0.4" in low:
            return "benchmark", 15, "Iniciando benchmark desta máquina."

        return None

    def is_running(self):
        with self.lock:
            return self.state == "running"

    def snapshot(self):
        with self.lock:
            now = time.monotonic()
            elapsed = (
                int(now - self.started_monotonic)
                if self.started_monotonic is not None and self.state == "running"
                else None
            )
            stage_elapsed = (
                int(now - self.stage_started_monotonic)
                if self.stage_started_monotonic is not None and self.state == "running"
                else None
            )
            last_activity = (
                int(now - self.last_output_monotonic)
                if self.last_output_monotonic is not None and self.state == "running"
                else None
            )
            return {
                "state": self.state,
                "stage": self.stage,
                "progress": self.progress,
                "message": self.message,
                "error": self.error,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "elapsed_seconds": elapsed,
                "stage_elapsed_seconds": stage_elapsed,
                "last_activity_seconds": last_activity,
                "current_probe": self.current_probe,
                "machine_id": self.engine.machine_id,
                "profile_available": self.engine.has_profile(),
                "output_tail": list(self.output),
                "result": self.result,
            }

    def start(self):
        with self.lock:
            if self.state == "running":
                raise CalibrationError("Já existe uma calibração em andamento.")

            script = self.app_dir / "autotune.py"
            if not script.exists():
                raise CalibrationError("app\\autotune.py não foi encontrado.")

            benchmark = self.app_dir / "benchmark.py"
            if not benchmark.exists():
                raise CalibrationError("app\\benchmark.py não foi encontrado.")

            self.cancel_requested = False
            self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self.finished_at = None
            self.state = "running"
            self.stage = "preparing"
            self.progress = 5
            self.message = "Preparando a calibração."
            self.error = None
            self.output.clear()
            self.result = None
            self.started_monotonic = time.monotonic()
            self.stage_started_monotonic = self.started_monotonic
            self.last_output_monotonic = self.started_monotonic
            self.current_probe = None

            # A calibração precisa da GPU/CPU livres.
            self.engine.stop(preserve_needs_calibration=True)
            self.engine.status = "calibrating"

            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            child_env = os.environ.copy()
            child_env["PYTHONIOENCODING"] = "utf-8"
            child_env["PYTHONUTF8"] = "1"

            self.proc = subprocess.Popen(
                [sys.executable, "-u", str(script)],
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
                env=child_env,
            )

            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            return self.snapshot()

    # Uma config de benchmark concluída imprime algo como
    #   "  CPU t=4... tg=9.73 | pp=34.4"  /  "  CUDA ngl=18... tg=12.91 | pp=..."
    _RE_CONFIG = re.compile(r"(cpu\s*t=\d+|cuda\s*ngl=\d+|\bngl=\d+|\bt=\d+)", re.IGNORECASE)

    def _creep_from_config_line(self, line):
        """Barra 'anda' um pouco a cada config medida dentro de uma fase longa,
        para a calibração não parecer travada entre os cabeçalhos de fase."""
        low = line.lower()
        if "tg=" not in low:
            return
        m = self._RE_CONFIG.search(low)
        if not m:
            return
        with self.lock:
            if self.state != "running":
                return
            if self.progress < 96:
                self.progress = min(96, self.progress + 1)
            cfg = m.group(1).upper().replace("CPU ", "CPU ").replace("CUDA ", "CUDA ")
            self.message = f"Medindo desempenho… ({cfg})"
            if self.last_output_monotonic is None:
                self.last_output_monotonic = time.monotonic()

    def _set_progress_from_line(self, line):
        classified = self.classify_line(line)
        if not classified:
            self._creep_from_config_line(line)
            return
        if len(classified) == 4:
            stage, progress, message, probe = classified
        else:
            stage, progress, message = classified
            probe = None
        with self.lock:
            if stage != self.stage:
                self.stage_started_monotonic = time.monotonic()
            if progress >= self.progress:
                self.stage = stage
                self.progress = progress
                self.message = message
                self.current_probe = probe

    def _restart_previous_if_possible(self):
        try:
            self.engine.reload_profile()
            if self.engine.has_profile():
                self.engine.start("auto")
            else:
                self.engine.status = "needs_calibration"
        except Exception as exc:
            self.engine.status = "error"
            self.engine.last_error = str(exc)

    def _run(self):
        return_code = None
        try:
            with open(self.log_path, "a", encoding="utf-8", errors="replace") as log:
                log.write(
                    f"\n\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"machine={self.engine.machine_id} ===\n"
                )
                log.flush()

                while True:
                    line = self.proc.stdout.readline() if self.proc and self.proc.stdout else ""
                    if line:
                        clean = line.rstrip()
                        with self.lock:
                            self.output.append(clean)
                            self.last_output_monotonic = time.monotonic()
                        log.write(line)
                        log.flush()
                        self._set_progress_from_line(clean)
                    elif self.proc and self.proc.poll() is not None:
                        break
                    else:
                        time.sleep(0.05)

                return_code = self.proc.wait() if self.proc else 1

            with self.lock:
                cancelled = self.cancel_requested

            if cancelled:
                with self.lock:
                    self.state = "cancelled"
                    self.stage = "cancelled"
                    self.message = "Calibração cancelada."
                    self.error = None
                    self.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                self._restart_previous_if_possible()
                return

            if return_code != 0:
                raise CalibrationError(
                    f"AutoTune encerrou com código {return_code}. "
                    f"Veja logs\\v0_6\\calibration.log"
                )

            if not self.engine.reload_profile():
                raise CalibrationError(
                    "O AutoTune terminou, mas o perfil desta máquina não foi encontrado."
                )

            # Volta automaticamente para o NÚCLEO em AUTO.
            snap = self.engine.start("auto")
            modes = self.engine.public_modes()

            result = {
                "recommended": self.engine.profile.get("recommended_auto", "fast"),
                "active_profile": snap.get("active_profile"),
                "modes": modes,
            }

            with self.lock:
                self.state = "finished"
                self.stage = "finished"
                self.progress = 100
                self.message = "Calibração concluída."
                self.error = None
                self.result = result
                self.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        except Exception as exc:
            with self.lock:
                self.state = "error"
                self.stage = "error"
                self.message = "Não foi possível concluir a calibração."
                self.error = str(exc)
                self.finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self._restart_previous_if_possible()
        finally:
            with self.lock:
                self.proc = None

    def cancel(self):
        with self.lock:
            if self.state != "running" or not self.proc:
                return self.snapshot()
            self.cancel_requested = True
            proc = self.proc

        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    timeout=15,
                )
            else:
                proc.terminate()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

        return self.snapshot()
