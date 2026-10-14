"""Cursor-based audit event polling for IDE synchronization.

Native FastMCP supports SSE and streamable HTTP for MCP transport. This module
exposes a durable, bounded event cursor for workspace changes, not a file watcher.
"""
from __future__ import annotations

import json
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import WorkspaceError


class SyncService:
    def __init__(self, settings: WorkspaceSettings) -> None:
        self.audit = settings.resolved_logging_dir() / "operations.jsonl"

    def poll(self, cursor: int = 0, limit: int = 50) -> dict:
        if cursor < 0 or not 1 <= limit <= 200:
            raise WorkspaceError("Invalid cursor or limit.")
        events = []
        end = cursor
        if not self.audit.exists():
            return {"cursor": end, "events": events}
        # Read bytes, not text stream offsets; clients can resume across sessions.
        with self.audit.open("rb") as file:
            file.seek(0, 2)
            size = file.tell()
            if cursor > size:
                cursor = 0  # log rotated; begin again
            file.seek(cursor)
            for _ in range(limit):
                line = file.readline()
                if not line or not line.endswith(b"\n"):
                    break
                end = file.tell()
                try:
                    obj = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    continue
                events.append(obj)
        return {"cursor": end, "events": events}
