#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import plat


class MaintenanceError(RuntimeError):
    pass


def _safe_presence(path: Path):
    try:
        if not path.exists():
            return False, "missing", None
        with open(path, "rb") as f:
            f.read(64)
        return True, "ok", None
    except OSError as exc:
        code = getattr(exc, "winerror", None)
        return False, "unreadable", code


def _directory_entry_exists(path: Path) -> bool:
    try:
        if path.exists():
            return True
    except OSError:
        pass
    try:
        return any(p.name.lower() == path.name.lower() for p in path.parent.iterdir())
    except OSError:
        return False


def _tail(path: Path, limit=80):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return text.splitlines()[-limit:]


class MaintenanceManager:
    CUDA_ZIPS = (
        "llama-b10516-bin-win-cuda-12.4-x64.zip",
        "cudart-llama-bin-win-cuda-12.4-x64.zip",
    )
    CPU_ZIPS = ("llama-b10516-bin-win-cpu-x64.zip",)

    def __init__(self, root: Path, engine):
        self.root = Path(root)
        self.engine = engine
        self.engine_root = plat.engine_root(self.root)
        self.downloads = self.root / "cache" / "downloads"
        self.log_dir = self.root / "logs" / "v0_6"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.maintenance_log = self.log_dir / "maintenance.log"
        self.lock = threading.RLock()

    def _log(self, text):
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.maintenance_log, "a", encoding="utf-8") as f:
                f.write(f"[{stamp}] {text}\n")
        except OSError:
            pass

    def _file_info(self, path: Path):
        ok, state, winerror = _safe_presence(path)
        return {
            "name": path.name,
            "path": str(path.relative_to(self.root)) if path.is_absolute() else str(path),
            "ok": ok,
            "state": state,
            "winerror": winerror,
        }

    def _backend_status(self, backend: str):
        folder = self.engine_root / backend
        required = plat.engine_bin_names()
        if backend == "cuda" and plat.IS_WINDOWS:
            required.append("ggml-cuda.dll")
        files = [self._file_info(folder / name) for name in required]
        ok = all(x["ok"] for x in files)
        unreadable = any(x["state"] == "unreadable" for x in files)
        return {
            "backend": backend,
            "ok": ok,
            "state": "ok" if ok else ("unreadable" if unreadable else "missing"),
            "files": files,
        }

    def _model_status(self):
        paths = []
        if self.engine.profile:
            for p in self.engine.profile.get("modes", {}).values():
                rel = p.get("model")
                if rel:
                    paths.append(self.root / rel)
        if not paths:
            paths = [
                self.root / "models" / "Qwen3-4B-Q4_K_M.gguf",
                self.root / "models" / "Qwen3-8B-Q4_K_M.gguf",
            ]

        unique = []
        seen = set()
        for p in paths:
            key = str(p).lower()
            if key not in seen:
                seen.add(key)
                unique.append(p)

        files = [self._file_info(p) for p in unique]
        return {
            "ok": bool(files) and all(x["ok"] for x in files),
            "files": files,
        }

    def _cache_status(self):
        names = list(self.CPU_ZIPS + self.CUDA_ZIPS)
        files = [self._file_info(self.downloads / name) for name in names]
        by_name = {f["name"]: f for f in files}
        return {
            "files": files,
            "can_repair_cpu": all(by_name[n]["ok"] for n in self.CPU_ZIPS),
            "can_repair_cuda": all(by_name[n]["ok"] for n in self.CUDA_ZIPS),
        }

    def snapshot(self):
        with self.lock:
            cpu = self._backend_status("cpu")
            cuda = self._backend_status("cuda")
            models = self._model_status()
            cache = self._cache_status()

            if cpu["ok"] and cuda["ok"] and models["ok"]:
                overall = "healthy"
                message = "Motores e modelos principais estão legíveis."
            elif cpu["ok"] and models["ok"]:
                overall = "degraded"
                message = "O NÚCLEO pode operar em CPU, mas o motor CUDA precisa de atenção."
            else:
                overall = "error"
                message = "Há componentes essenciais ausentes ou ilegíveis."

            active = self.engine.snapshot()
            if (
                active.get("status") == "ready"
                and active.get("backend") == "cpu"
                and active.get("backend_policy") != "cpu_forced"
                and self.engine.profile
                and any(
                    p.get("backend") == "cuda"
                    for p in self.engine.profile.get("modes", {}).values()
                )
            ):
                overall = "degraded"
                message = "A IA está funcionando em CPU por fallback; CUDA merece verificação."

            return {
                "overall": overall,
                "message": message,
                "cpu": cpu,
                "cuda": cuda,
                "models": models,
                "cache": cache,
                "engine": active,
                "actions": {
                    "can_restart": self.engine.has_profile(),
                    "can_use_cpu": cpu["ok"] and models["ok"] and self.engine.has_profile(),
                    "can_restore_profile_backend": self.engine.has_profile(),
                    "can_repair_cpu": cache["can_repair_cpu"],
                    "can_repair_cuda": cache["can_repair_cuda"],
                },
            }

    def logs(self):
        candidates = []
        for p in (self.root / "logs").glob("**/llama-server.log"):
            try:
                candidates.append((p.stat().st_mtime, p))
            except OSError:
                pass
        candidates.sort(reverse=True)
        engine_log = candidates[0][1] if candidates else None

        cal_candidates = []
        for p in (self.root / "logs").glob("**/calibration.log"):
            try:
                cal_candidates.append((p.stat().st_mtime, p))
            except OSError:
                pass
        cal_candidates.sort(reverse=True)
        cal_log = cal_candidates[0][1] if cal_candidates else None

        return {
            "engine_log": str(engine_log.relative_to(self.root)) if engine_log else None,
            "engine_tail": _tail(engine_log, 80) if engine_log else [],
            "calibration_log": str(cal_log.relative_to(self.root)) if cal_log else None,
            "calibration_tail": _tail(cal_log, 40) if cal_log else [],
            "maintenance_log": str(self.maintenance_log.relative_to(self.root)),
            "maintenance_tail": _tail(self.maintenance_log, 60),
        }

    def restart_engine(self):
        with self.lock:
            self._log("Reinício do motor solicitado pela interface.")
            try:
                snap = self.engine.restart()
                self._log(
                    f"Motor reiniciado: backend={snap.get('backend')} "
                    f"mode={snap.get('requested_mode')}"
                )
                return snap
            except Exception as exc:
                self._log(f"Falha ao reiniciar motor: {exc}")
                raise MaintenanceError(str(exc)) from exc

    def use_cpu(self):
        with self.lock:
            cpu = self._backend_status("cpu")
            if not cpu["ok"]:
                raise MaintenanceError("Motor CPU não está íntegro.")
            self._log("Fallback manual para CPU solicitado.")
            try:
                snap = self.engine.use_cpu()
                self._log("Motor reiniciado em CPU.")
                return snap
            except Exception as exc:
                self._log(f"Falha ao iniciar CPU: {exc}")
                raise MaintenanceError(str(exc)) from exc

    def restore_profile_backend(self):
        with self.lock:
            self._log("Retorno ao backend do perfil solicitado.")
            try:
                snap = self.engine.restore_profile_backend(restart=True)
                self._log(f"Backend do perfil restaurado: {snap.get('backend')}")
                return snap
            except Exception as exc:
                self._log(f"Falha ao restaurar backend do perfil: {exc}")
                raise MaintenanceError(str(exc)) from exc

    def _zip_names(self, backend):
        if backend == "cuda":
            return self.CUDA_ZIPS
        if backend == "cpu":
            return self.CPU_ZIPS
        raise MaintenanceError("Backend inválido para reparo.")

    def _validate_candidate(self, folder: Path, backend: str):
        required = plat.engine_bin_names()
        if backend == "cuda" and plat.IS_WINDOWS:
            required.append("ggml-cuda.dll")

        for name in required:
            ok, state, winerror = _safe_presence(folder / name)
            if not ok:
                detail = f" ({state}"
                if winerror:
                    detail += f", Windows {winerror}"
                detail += ")"
                raise MaintenanceError(f"Arquivo restaurado inválido: {name}{detail}")

        if os.name == "nt":
            cli = folder / "llama-cli.exe"
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                p = subprocess.run(
                    [str(cli), "--version"],
                    cwd=str(folder),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=25,
                    creationflags=flags,
                )
            except Exception as exc:
                raise MaintenanceError(
                    f"Motor restaurado não pôde ser executado: {exc}"
                ) from exc
            if p.returncode != 0:
                raise MaintenanceError(
                    f"llama-cli --version retornou código {p.returncode}."
                )

    def repair_backend(self, backend: str):
        backend = str(backend or "").lower()
        zip_names = self._zip_names(backend)

        with self.lock:
            cache = self._cache_status()
            key = f"can_repair_{backend}"
            if not cache.get(key):
                raise MaintenanceError(
                    f"Cache necessário para reparar {backend.upper()} não está íntegro."
                )

            previous_mode = self.engine.requested_mode or "auto"
            previous_forced = self.engine.forced_backend
            self._log(f"Iniciando reparo seguro do motor {backend.upper()}.")

            self.engine.stop(preserve_needs_calibration=False)

            parent = self.engine_root
            parent.mkdir(parents=True, exist_ok=True)
            target = parent / backend
            token = uuid.uuid4().hex[:10]
            candidate = parent / f".{backend}_repair_{token}"
            backup = parent / f"{backend}_backup_{time.strftime('%Y%m%d_%H%M%S')}"

            if candidate.exists():
                shutil.rmtree(candidate, ignore_errors=True)
            candidate.mkdir(parents=True)

            try:
                for zip_name in zip_names:
                    zpath = self.downloads / zip_name
                    with zipfile.ZipFile(zpath, "r") as z:
                        for info in z.infolist():
                            if info.is_dir():
                                continue
                            # Os ZIPs oficiais podem conter subpastas.
                            name = Path(info.filename).name
                            if not name:
                                continue
                            out = candidate / name
                            with z.open(info, "r") as src, open(out, "wb") as dst:
                                shutil.copyfileobj(src, dst, length=1024 * 1024)

                self._validate_candidate(candidate, backend)

                had_old = _directory_entry_exists(target)
                if had_old:
                    try:
                        target.rename(backup)
                    except Exception as exc:
                        raise MaintenanceError(
                            f"Não foi possível preservar a pasta {backend.upper()} atual: {exc}"
                        ) from exc

                try:
                    candidate.rename(target)
                except Exception as exc:
                    if had_old and backup.exists() and not target.exists():
                        try:
                            backup.rename(target)
                        except Exception:
                            pass
                    raise MaintenanceError(
                        f"Não foi possível ativar o motor restaurado: {exc}"
                    ) from exc

                try:
                    self._validate_candidate(target, backend)
                except Exception:
                    failed = parent / f"{backend}_falha_{token}"
                    try:
                        target.rename(failed)
                    except Exception:
                        pass
                    if had_old and backup.exists():
                        try:
                            backup.rename(target)
                        except Exception:
                            pass
                    raise

                self._log(
                    f"Reparo {backend.upper()} concluído. "
                    f"Backup anterior: {backup.name if had_old else 'não havia pasta anterior'}"
                )

                # Ao reparar CUDA, voltamos a permitir o backend do perfil.
                if backend == "cuda":
                    self.engine.forced_backend = None
                else:
                    self.engine.forced_backend = previous_forced

                try:
                    snap = self.engine.start(previous_mode)
                except Exception as exc:
                    self._log(
                        f"Motor foi reparado, mas não reiniciou automaticamente: {exc}"
                    )
                    raise MaintenanceError(
                        "Reparo concluído, porém o motor não reiniciou automaticamente. "
                        f"Detalhe: {exc}"
                    ) from exc

                return {
                    "backend": backend,
                    "backup_dir": str(backup.relative_to(self.root)) if had_old else None,
                    "engine": snap,
                    "status": self.snapshot(),
                }

            except Exception:
                shutil.rmtree(candidate, ignore_errors=True)
                # Se o reparo falhou antes da troca, tenta restaurar o estado anterior.
                try:
                    self.engine.forced_backend = previous_forced
                    if self.engine.has_profile() and self.engine.status != "ready":
                        self.engine.start(previous_mode)
                except Exception:
                    pass
                raise
