"""Persistent, project-scoped knowledge graph of facts and typed relations."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import NotFoundError, WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.validator = validator
        self.settings = settings
        self.db = settings.resolved_memory_dir() / "knowledge.sqlite3"

    def _validate_project(self, project: str) -> None:
        path = self.validator.resolve(project)
        if path.parent != self.validator.workspace_root or not path.is_dir():
            raise WorkspaceError("Memory project must be an existing top-level project.")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db)
        db.execute("""CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL,
            title TEXT NOT NULL, content TEXT NOT NULL, created TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS edges (
            id TEXT PRIMARY KEY, project TEXT NOT NULL,
            source TEXT NOT NULL, target TEXT NOT NULL, kind TEXT NOT NULL,
            created TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS facts_scope ON facts(project)")
        db.execute("CREATE INDEX IF NOT EXISTS edges_scope ON edges(project)")
        return db

    def remember(self, project: str, kind: str, title: str, content: str) -> dict:
        self._validate_project(project)
        if kind not in {"decision", "dependency", "api_contract", "architecture", "note", "todo"}:
            raise WorkspaceError("Unsupported knowledge type.")
        if not title.strip() or len(title) > 300 or len(content) > 20000:
            raise WorkspaceError("Invalid memory title/content.")
        fact = {"id": uuid.uuid4().hex, "project": project, "kind": kind,
                "title": title, "content": content, "created": utcnow()}
        with self._connect() as db:
            db.execute("INSERT INTO facts VALUES(:id,:project,:kind,:title,:content,:created)", fact)
        return fact

    def link(self, project: str, source: str, target: str, relation: str) -> dict:
        self._validate_project(project)
        if relation not in {"depends_on", "implements", "supersedes", "relates_to", "blocks"}:
            raise WorkspaceError("Unsupported relation.")
        with self._connect() as db:
            count = db.execute(
                "SELECT COUNT(*) FROM facts WHERE project=? AND id IN (?,?)",
                (project, source, target),
            ).fetchone()[0]
            if count != 2 or source == target:
                raise NotFoundError("Both distinct facts must belong to the same project.")
            edge = {"id": uuid.uuid4().hex, "project": project, "source": source,
                    "target": target, "kind": relation, "created": utcnow()}
            db.execute("INSERT INTO edges VALUES(:id,:project,:source,:target,:kind,:created)", edge)
        return edge

    def query(self, project: str, text: str = "", limit: int = 40) -> dict:
        self._validate_project(project)
        if not 1 <= limit <= 200:
            raise WorkspaceError("Limit must be between 1 and 200.")
        pattern = "%" + text.replace("%", "\\%").replace("_", "\\_") + "%"
        with self._connect() as db:
            facts = db.execute(
                """SELECT id,kind,title,content,created FROM facts
                WHERE project=? AND (title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\')
                ORDER BY created DESC LIMIT ?""", (project, pattern, pattern, limit)
            ).fetchall()
            edges = db.execute(
                "SELECT id,source,target,kind,created FROM edges WHERE project=? ORDER BY created DESC LIMIT ?",
                (project, limit),
            ).fetchall()
        return {"facts": [dict(zip(("id", "kind", "title", "content", "created"), row))
                          for row in facts],
                "relations": [dict(zip(("id", "source", "target", "kind", "created"), row))
                              for row in edges]}
