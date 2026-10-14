"""Shared helpers used by every ``tools/*.py`` module.

Every MCP tool function follows the same shape:

    with logger.track("Operation Name", target_path) as timer:
        result_data = service.do_thing(...)
    return ok(...)

and on failure, :class:`~workspace_mcp.models.schemas.WorkspaceError` is
caught once, centrally, by :func:`run_tool`, so individual tool functions
stay a few lines long and never need their own try/except.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.models.schemas import OperationStatus, Timer, WorkspaceError

T = TypeVar("T")


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def run_tool(
    logger: OperationLogger,
    *,
    operation: str,
    target_path: str,
    fn: Callable[[], T],
) -> dict[str, Any]:
    """Execute ``fn``, logging + converting the outcome into a plain dict.

    This is the single place that turns a :class:`WorkspaceError` into a
    client-safe payload instead of letting an exception propagate out of
    the MCP tool (which would surface as an opaque transport-level error).
    """
    timer = Timer()
    try:
        with logger.track(operation, target_path):
            result = fn()
    except WorkspaceError as exc:
        # logger.track() already wrote this failure to the log files;
        # here we just shape the client-facing response.
        return {
            "status": OperationStatus.ERROR.value,
            "operation": operation,
            "target_path": target_path,
            "message": exc.message,
            "error_code": exc.code,
            "duration_ms": timer.elapsed_ms(),
            **{k: _jsonable(v) for k, v in exc.details.items()},
        }
    return {
        "status": OperationStatus.SUCCESS.value,
        "operation": operation,
        "target_path": target_path,
        "duration_ms": timer.elapsed_ms(),
        "data": _jsonable(result),
    }


async def run_tool_async(
    logger: OperationLogger, *, operation: str, target_path: str, fn: Callable[[], Any]
) -> dict[str, Any]:
    """Async version for non-blocking process execution."""
    timer = Timer()
    try:
        with logger.track(operation, target_path):
            result = await fn()
    except WorkspaceError as exc:
        return {
            "status": OperationStatus.ERROR.value,
            "operation": operation,
            "target_path": target_path,
            "message": exc.message,
            "error_code": exc.code,
            "duration_ms": timer.elapsed_ms(),
            **{k: _jsonable(v) for k, v in exc.details.items()},
        }
    return {
        "status": OperationStatus.SUCCESS.value,
        "operation": operation,
        "target_path": target_path,
        "duration_ms": timer.elapsed_ms(),
        "data": _jsonable(result),
    }
