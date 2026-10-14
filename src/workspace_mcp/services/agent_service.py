"""Persistent task coordination between clients/agents; does not invoke an LLM."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator


class AgentService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.validator = validator
        self.db = settings.resolved_memory_dir() / "agent_tasks.sqlite3"

    def _project(self, project: str) -> None:
        path = self.validator.resolve(project)
        if not path.is_dir() or path.parent != self.validator.workspace_root:
            raise WorkspaceError("Agent workflow requires an existing project.")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db, timeout=20)
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, project TEXT NOT NULL, role TEXT NOT NULL,
            goal TEXT NOT NULL, context TEXT NOT NULL, status TEXT NOT NULL,
            assignee TEXT, result TEXT, created TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS tasks_project ON tasks(project,status)")
        return db

    def submit(self, project: str, role: str, goal: str, context: dict | None = None) -> dict:
        self._project(project)
        if role not in {"architect", "implementer", "reviewer", "tester", "researcher"}:
            raise WorkspaceError("Invalid role.")
        if not goal.strip() or len(goal) > 4000:
            raise WorkspaceError("Task goal is required and must be <=4000 chars.")
        encoded = json.dumps(context or {}, ensure_ascii=False)
        if len(encoded) > 10000:
            raise WorkspaceError("Task context too large.")
        task_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                "INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    task_id,
                    project,
                    role,
                    goal,
                    encoded,
                    "queued",
                    None,
                    None,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return {"task_id": task_id, "status": "queued", "role": role}

    def claim(self, project: str, task_id: str, assignee: str) -> dict:
        self._project(project)
        if not assignee.strip() or len(assignee) > 200:
            raise WorkspaceError("Invalid assignee.")
        with self._connect() as db:
            row = db.execute(
                """UPDATE tasks SET assignee=?,status='running'
                WHERE project=? AND id=? AND status='queued' RETURNING id""",
                (assignee, project, task_id),
            ).fetchone()
            if row is None:
                raise WorkspaceError("Task not found or already claimed.")
        return {"task_id": task_id, "status": "running", "assignee": assignee}

    def finish(
        self, project: str, task_id: str, assignee: str, result: str, succeeded: bool = True
    ) -> dict:
        self._project(project)
        if len(result) > 20000:
            raise WorkspaceError("Result too long.")
        status = "completed" if succeeded else "failed"
        with self._connect() as db:
            updated = db.execute(
                "UPDATE tasks SET result=?,status=? WHERE project=? AND id=? AND assignee=? AND status='running'",
                (result, status, project, task_id, assignee),
            ).rowcount
            if not updated:
                raise WorkspaceError("Only the assignee can finish a running task.")
        return {"task_id": task_id, "status": status}

    def list_tasks(self, project: str, status: str = "") -> list[dict]:
        self._project(project)
        if status and status not in {"queued", "running", "completed", "failed"}:
            raise WorkspaceError("Invalid task status.")
        with self._connect() as db:
            cursor = db.execute(
                """SELECT id,role,goal,context,status,assignee,result,created FROM tasks
                WHERE project=? AND (?='' OR status=?) ORDER BY created DESC LIMIT 100""",
                (project, status, status),
            )
            return [
                dict(
                    zip(
                        (
                            "id",
                            "role",
                            "goal",
                            "context",
                            "status",
                            "assignee",
                            "result",
                            "created",
                        ),
                        row,
                    )
                )
                for row in cursor.fetchall()
            ]
