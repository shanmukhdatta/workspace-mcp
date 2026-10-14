"""MCP tools: validate_workspace, validate_path."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.tools._common import run_tool
from workspace_mcp.utils.pathsec import PathValidator


def register(
    mcp: FastMCP,
    settings: WorkspaceSettings,
    validator: PathValidator,
    logger: OperationLogger,
) -> None:
    @mcp.tool()
    def validate_workspace() -> dict[str, Any]:
        """Report the current workspace configuration and health: root
        directory, whether it exists/is writable, size limits, and
        allowed extensions.
        """

        def _do() -> dict[str, Any]:
            root = settings.workspace_root
            return {
                "workspace_root": str(root),
                "exists": root.exists(),
                "is_directory": root.is_dir() if root.exists() else False,
                "writable": _is_writable(root),
                "max_file_size_bytes": settings.max_file_size_bytes,
                "allowed_extensions": sorted(settings.allowed_extensions),
                "ignored_files": sorted(settings.ignored_files),
                "ignored_dirs": sorted(settings.ignored_dirs),
                "logging_dir": str(settings.resolved_logging_dir()),
                "backup_dir": str(settings.resolved_backup_dir()),
                "templates_dir": str(settings.resolved_templates_dir()),
                "allow_symlinks": settings.allow_symlinks,
                "require_overwrite_confirmation": settings.require_overwrite_confirmation,
            }

        return run_tool(logger, operation="Validate Workspace", target_path=".", fn=_do)

    @mcp.tool()
    def validate_path(path: str) -> dict[str, Any]:
        """Check whether a given relative path is valid and safe (no
        traversal, stays within the workspace, no symlink escape) without
        performing any read/write operation.

        Args:
            path: Path to validate, relative to the workspace root.
        """

        def _do() -> dict[str, Any]:
            resolved = validator.resolve(path)
            return {
                "input_path": path,
                "resolved_path": str(resolved),
                "relative_to_workspace": validator.relative_to_root(resolved),
                "exists": resolved.exists(),
                "is_file": resolved.is_file() if resolved.exists() else None,
                "is_directory": resolved.is_dir() if resolved.exists() else None,
                "is_protected": resolved.name in settings.protected_files,
            }

        return run_tool(logger, operation="Validate Path", target_path=path, fn=_do)


def _is_writable(path: Any) -> bool:
    import os

    try:
        return path.exists() and os.access(path, os.W_OK)
    except OSError:
        return False
