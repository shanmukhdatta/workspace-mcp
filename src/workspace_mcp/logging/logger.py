"""
Structured operation logging.

Every filesystem-affecting tool call is recorded twice:

1. As a JSON line in ``<logging_dir>/operations.jsonl`` (machine-readable,
   good for later analytics or feeding CLOUD.md generation).
2. As a human-readable line in ``<logging_dir>/operations.log`` in the
   format requested in the spec, e.g.::

       [2026-07-27T10:15:03Z] Created File | backend/main.py | Success | 120ms

Console logging uses the standard library ``logging`` module so operators
running the server see activity in real time as well.
"""

from __future__ import annotations

import json
import logging as _stdlib_logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from workspace_mcp.models.schemas import OperationStatus, Timer, WorkspaceError

_console_logger = _stdlib_logging.getLogger("workspace_mcp")
if not _console_logger.handlers:
    _handler = _stdlib_logging.StreamHandler()
    _handler.setFormatter(_stdlib_logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _console_logger.addHandler(_handler)
    _console_logger.setLevel(_stdlib_logging.INFO)


class OperationLogger:
    """Writes structured + human-readable logs and exposes a context manager
    that measures duration and records success/failure automatically.
    """

    def __init__(self, logging_dir: Path) -> None:
        self.logging_dir = Path(logging_dir)
        self.logging_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.logging_dir / "operations.jsonl"
        self.text_path = self.logging_dir / "operations.log"

    def record(
        self,
        *,
        operation: str,
        target_path: str,
        status: OperationStatus,
        duration_ms: float,
        message: str = "",
        error_code: Optional[str] = None,
    ) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "timestamp": ts,
            "operation": operation,
            "target_path": target_path,
            "status": status.value,
            "duration_ms": duration_ms,
            "message": message,
            "error_code": error_code,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

        human_status = "Success" if status == OperationStatus.SUCCESS else "FAILED"
        line = f"[{ts}] {operation} | {target_path} | {human_status} | {duration_ms}ms"
        if message and status != OperationStatus.SUCCESS:
            line += f" | {message}"
        with self.text_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

        if status == OperationStatus.SUCCESS:
            _console_logger.info(line)
        else:
            _console_logger.warning(line)

    @contextmanager
    def track(self, operation: str, target_path: str) -> Iterator[Timer]:
        """Context manager: times the block and logs success/failure.

        Any :class:`WorkspaceError` raised inside the block is logged with
        its message/code and then re-raised so the caller (the tool layer)
        can still convert it into a client-facing error payload.
        """
        timer = Timer()
        try:
            yield timer
        except WorkspaceError as exc:
            self.record(
                operation=operation,
                target_path=target_path,
                status=OperationStatus.ERROR,
                duration_ms=timer.elapsed_ms(),
                message=exc.message,
                error_code=exc.code,
            )
            raise
        except Exception as exc:  # pragma: no cover - defensive catch-all
            self.record(
                operation=operation,
                target_path=target_path,
                status=OperationStatus.ERROR,
                duration_ms=timer.elapsed_ms(),
                message=str(exc),
                error_code="UNEXPECTED_ERROR",
            )
            raise
        else:
            self.record(
                operation=operation,
                target_path=target_path,
                status=OperationStatus.SUCCESS,
                duration_ms=timer.elapsed_ms(),
            )

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the last ``limit`` structured log entries, newest last."""
        if not self.jsonl_path.exists():
            return []
        lines = self.jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:] if limit else lines
        return [json.loads(line) for line in tail]
