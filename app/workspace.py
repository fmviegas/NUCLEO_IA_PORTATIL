#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from file_analysis import (
    MAX_FILE_BYTES,
    SUPPORTED_EXTENSIONS,
    FileAnalysisError,
    analyze_file,
    context_for_analysis,
)

SESSION_RE = re.compile(r"^[a-f0-9]{16}$")
FILE_RE = re.compile(r"^[a-f0-9]{12}$")
MAX_FILES_PER_SESSION = 5
MAX_TOTAL_BYTES_PER_SESSION = 50 * 1024 * 1024


class WorkspaceError(RuntimeError):
    pass


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _safe_filename(name):
    name = Path(str(name or "arquivo")).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        name = "arquivo"
    stem = Path(name).stem[:90] or "arquivo"
    ext = Path(name).suffix.lower()[:10]
    return stem + ext


class WorkspaceStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.workspace_root = self.root / "workspace" / "sessions"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def _sid(self, session_id):
        sid = str(session_id or "").lower()
        if not SESSION_RE.fullmatch(sid):
            raise WorkspaceError("ID de sessão inválido.")
        return sid

    def _fid(self, file_id):
        fid = str(file_id or "").lower()
        if not FILE_RE.fullmatch(fid):
            raise WorkspaceError("ID de arquivo inválido.")
        return fid

    def _dir(self, session_id):
        return self.workspace_root / self._sid(session_id)

    def _meta_path(self, session_id):
        return self._dir(session_id) / "files.json"

    def _load(self, session_id):
        path = self._meta_path(session_id)
        if not path.exists():
            return {"schema": 1, "session_id": self._sid(session_id), "files": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return {"schema": 1, "session_id": self._sid(session_id), "files": []}
        return data if isinstance(data, dict) else {"schema": 1, "session_id": self._sid(session_id), "files": []}

    def _save(self, session_id, data):
        folder = self._dir(session_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = self._meta_path(session_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def list_files(self, session_id):
        with self.lock:
            data = self._load(session_id)
            out = []
            for item in data.get("files") or []:
                clean = dict(item)
                clean.pop("stored_name", None)
                clean.pop("analysis", None)
                out.append(clean)
            return out

    def upload(self, session_id, filename, content: bytes):
        sid = self._sid(session_id)
        safe = _safe_filename(filename)
        ext = Path(safe).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise WorkspaceError("Formato não suportado. Use XLSX, CSV, TXT, MD ou JSON.")
        if not content:
            raise WorkspaceError("Arquivo vazio.")
        if len(content) > MAX_FILE_BYTES:
            raise WorkspaceError("Arquivo excede o limite de 25 MB.")

        with self.lock:
            data = self._load(sid)
            files = data.get("files") or []
            if len(files) >= MAX_FILES_PER_SESSION:
                raise WorkspaceError("Limite de 5 arquivos por conversa atingido.")
            current_total = sum(int(x.get("size") or 0) for x in files)
            if current_total + len(content) > MAX_TOTAL_BYTES_PER_SESSION:
                raise WorkspaceError("Arquivos desta conversa excedem o limite total de 50 MB.")

            fid = uuid.uuid4().hex[:12]
            folder = self._dir(sid)
            uploads = folder / "uploads"
            uploads.mkdir(parents=True, exist_ok=True)
            stored_name = f"{fid}_{safe}"
            path = uploads / stored_name
            path.write_bytes(content)

            try:
                analysis = analyze_file(path)
            except Exception:
                try:
                    path.unlink()
                except OSError:
                    pass
                raise

            item = {
                "id": fid,
                "name": safe,
                "stored_name": stored_name,
                "extension": ext,
                "size": len(content),
                "uploaded_at": _now_iso(),
                "analysis": analysis,
                "summary": self._public_summary(analysis),
            }
            files.append(item)
            data["files"] = files
            self._save(sid, data)

            public = dict(item)
            public.pop("stored_name", None)
            public.pop("analysis", None)
            return public

    def _public_summary(self, analysis):
        typ = analysis.get("type")
        if typ == "xlsx":
            return {
                "type": "xlsx",
                "sheet_count": analysis.get("sheet_count", 0),
                "row_count": analysis.get("row_count", 0),
                "formula_count": analysis.get("formula_count", 0),
                "sheets": [
                    {"name": s.get("name"), "row_count": s.get("row_count", 0)}
                    for s in (analysis.get("sheets") or [])[:12]
                ],
            }
        if analysis.get("kind") == "table":
            return {
                "type": typ,
                "row_count": analysis.get("row_count", 0),
                "column_count": len(analysis.get("columns") or []),
                "columns": [c.get("name") for c in (analysis.get("columns") or [])[:20]],
            }
        if typ == "pdf":
            return {
                "type": "pdf",
                "page_count": analysis.get("page_count"),
                "pages_with_text": analysis.get("pages_with_text"),
                "word_count": analysis.get("word_count"),
                "scanned_guess": analysis.get("scanned_guess"),
                "note": analysis.get("note", ""),
            }
        if typ == "docx":
            return {
                "type": "docx",
                "paragraph_count": analysis.get("paragraph_count"),
                "table_count": analysis.get("table_count"),
                "word_count": analysis.get("word_count"),
            }
        return {
            "type": typ,
            "line_count": analysis.get("line_count"),
            "word_count": analysis.get("word_count"),
            "json_shape": analysis.get("json_shape"),
        }

    def delete_file(self, session_id, file_id):
        sid = self._sid(session_id)
        fid = self._fid(file_id)
        with self.lock:
            data = self._load(sid)
            files = data.get("files") or []
            target = next((x for x in files if x.get("id") == fid), None)
            if not target:
                return False
            path = self._dir(sid) / "uploads" / target["stored_name"]
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            data["files"] = [x for x in files if x.get("id") != fid]
            self._save(sid, data)
            return True

    def delete_session(self, session_id):
        folder = self._dir(session_id)
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)

    def context_for_question(self, session_id, question, max_total_chars=7000):
        with self.lock:
            data = self._load(session_id)
            files = data.get("files") or []
            if not files:
                return ""

            q = str(question or "").lower()
            # Prioritize explicitly named files, then newest.
            ranked = sorted(
                files,
                key=lambda x: (
                    1 if str(x.get("name", "")).lower() in q else 0,
                    str(x.get("uploaded_at", "")),
                ),
                reverse=True,
            )
            chunks = []
            remaining = max_total_chars
            for item in ranked[:3]:
                if remaining < 1200:
                    break
                chunk = context_for_analysis(
                    item.get("analysis") or {},
                    item.get("name") or "arquivo",
                    question,
                    max_chars=min(4200, remaining),
                )
                chunks.append(chunk)
                remaining -= len(chunk) + 80

            if not chunks:
                return ""

            intro = (
                "[CONTEXTO LOCAL DE ARQUIVOS — gerado por ferramentas determinísticas]\n"
                "Use os valores calculados abaixo como evidência. "
                "O NÚCLEO REALIZA cálculos determinísticos (soma, média, mínimo, "
                "máximo, contagem) sobre os dados extraídos; nunca afirme que não "
                "pode calcular. O que ele NÃO faz é recalcular o motor de fórmulas "
                "do Excel. "
                "Não invente linhas/células que não estejam presentes. "
                "Se a pergunta exigir um cálculo que este contexto não fornece, diga isso. "
                "Em XLSX, fórmulas são lidas e comparadas, mas NÃO recalculadas. "
                "Quando a planilha for um formulário/calculadora, use os pares "
                "rótulo→valor e as seções fornecidas; não trate células vazias "
                "estruturais como dados faltantes. "
                "Responda de forma objetiva: destaque achados, valores importantes, "
                "possíveis inconsistências e uma conclusão. Não liste colunas totalmente "
                "vazias nem repita todos os metadados sem necessidade.\n\n"
            )
            return (intro + "\n\n---\n\n".join(chunks))[:max_total_chars]
