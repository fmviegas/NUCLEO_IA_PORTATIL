#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

SESSION_ID_RE = re.compile(r"^[a-f0-9]{16}$")
MAX_TITLE = 64
MAX_MESSAGES = 500


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _safe_title(text: str) -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return "Nova conversa"
    if len(text) <= MAX_TITLE:
        return text
    return text[: MAX_TITLE - 1].rstrip() + "…"


class SessionStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.sessions_root = self.root / "sessions"
        self.sessions_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._cleanup_stale_files()

    def _cleanup_stale_files(self):
        """Remove apenas sessões vazias antigas e .tmp abandonados."""
        now = datetime.now().timestamp()
        try:
            for tmp in self.sessions_root.glob("*/*/*.json.tmp"):
                try:
                    if now - tmp.stat().st_mtime > 3600:
                        tmp.unlink()
                except OSError:
                    pass

            for path in self.sessions_root.glob("*/*/*.json"):
                try:
                    if now - path.stat().st_mtime <= 86400:
                        continue
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    if isinstance(data, dict) and not (data.get("messages") or []):
                        path.unlink()
                except (OSError, json.JSONDecodeError):
                    pass
        except OSError:
            pass

    def _validate_id(self, session_id: str) -> str:
        sid = str(session_id or "").lower()
        if not SESSION_ID_RE.fullmatch(sid):
            raise ValueError("ID de sessão inválido.")
        return sid

    def _path_for_new(self, session_id: str) -> Path:
        now = datetime.now()
        folder = self.sessions_root / f"{now.year:04d}" / f"{now.month:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{session_id}.json"

    def _find_path(self, session_id: str) -> Path | None:
        sid = self._validate_id(session_id)
        matches = list(self.sessions_root.glob(f"*/*/{sid}.json"))
        return matches[0] if matches else None

    def _atomic_write(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        tmp.write_text(encoded, encoding="utf-8")
        os.replace(tmp, path)

    def create(self) -> dict:
        with self.lock:
            sid = uuid.uuid4().hex[:16]
            now = _now_iso()
            data = {
                "schema": 1,
                "id": sid,
                "created_at": now,
                "updated_at": now,
                "title": "Nova conversa",
                "mode": "auto",
                "active_profile": None,
                "model": None,
                "messages": [],
            }
            self._atomic_write(self._path_for_new(sid), data)
            return data

    def get(self, session_id: str) -> dict | None:
        with self.lock:
            path = self._find_path(session_id)
            if not path:
                return None
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                return None
            return data if isinstance(data, dict) else None

    def save(
        self,
        session_id: str,
        messages: list,
        mode: str = "auto",
        active_profile: str | None = None,
        model: str | None = None,
    ) -> dict:
        with self.lock:
            path = self._find_path(session_id)
            if not path:
                raise FileNotFoundError("Sessão não encontrada.")

            current = self.get(session_id) or {}
            clean = []
            for msg in messages[-MAX_MESSAGES:]:
                if not isinstance(msg, dict):
                    continue
                role = str(msg.get("role", ""))
                content = str(msg.get("content", "")).strip()
                if role not in ("user", "assistant") or not content:
                    continue
                clean.append({"role": role, "content": content})

            title = current.get("title") or "Nova conversa"
            if title == "Nova conversa":
                first_user = next(
                    (m["content"] for m in clean if m["role"] == "user"),
                    "",
                )
                title = _safe_title(first_user)

            data = {
                "schema": 1,
                "id": self._validate_id(session_id),
                "created_at": current.get("created_at") or _now_iso(),
                "updated_at": _now_iso(),
                "title": title,
                "mode": mode if mode in ("auto", "fast", "quality") else "auto",
                "active_profile": active_profile,
                "model": model,
                "messages": clean,
            }
            self._atomic_write(path, data)
            return data

    def delete(self, session_id: str) -> bool:
        with self.lock:
            path = self._find_path(session_id)
            if not path:
                return False
            path.unlink()
            # Remove empty year/month folders, never anything above sessions/.
            try:
                if not any(path.parent.iterdir()):
                    path.parent.rmdir()
                if path.parent.parent != self.sessions_root and not any(path.parent.parent.iterdir()):
                    path.parent.parent.rmdir()
            except OSError:
                pass
            return True

    def list_recent(self, limit: int = 20, include_empty: bool = False) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        items = []
        with self.lock:
            paths = list(self.sessions_root.glob("*/*/*.json"))
            paths.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

            for path in paths:
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(data, dict):
                    continue
                count = len(data.get("messages") or [])
                if not include_empty and count == 0:
                    continue
                items.append({
                    "id": data.get("id"),
                    "title": data.get("title") or "Nova conversa",
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "mode": data.get("mode", "auto"),
                    "model": data.get("model"),
                    "message_count": count,
                })
                if len(items) >= limit:
                    break
        return items

    def last_nonempty(self) -> dict | None:
        recent = self.list_recent(limit=1, include_empty=False)
        if not recent:
            return None
        return self.get(recent[0]["id"])
