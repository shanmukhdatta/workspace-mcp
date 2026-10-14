"""MCP tools: create_directory, delete_directory, list_directory."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.tools._common import run_tool


def register(mcp: FastMCP, directory_service: DirectoryService, logger: OperationLogger) -> None:
    @mcp.tool()
    def create_directory(path: str, exist_ok: bool = True) -> dict[str, Any]:
        """Create a directory (and any missing parents) inside the workspace.

        Args:
            path: Path relative to the workspace root, e.g. "MyApp/backend/api".
            exist_ok: If False, error when the directory already exists.
        """
        return run_tool(
            logger,
            operation="Create Directory",
            target_path=path,
            fn=lambda: directory_service.create_directory(path, exist_ok=exist_ok),
        )

    @mcp.tool()
    def delete_directory(
        path: str, confirm: bool = False, recursive: bool = True
    ) -> dict[str, Any]:
        """Delete a directory inside the workspace.

        Args:
            path: Path relative to the workspace root.
            confirm: Must be explicitly True; this is irreversible.
            recursive: If True (default), delete all contents too. If
                False, only succeeds when the directory is empty.
        """
        return run_tool(
            logger,
            operation="Delete Directory",
            target_path=path,
            fn=lambda: directory_service.delete_directory(
                path, confirm=confirm, recursive=recursive
            ),
        )

    @mcp.tool()
    def list_directory(path: str = ".", include_hidden: bool = False) -> dict[str, Any]:
        """List the immediate contents of a directory inside the workspace.

        Args:
            path: Path relative to the workspace root (default: workspace root).
            include_hidden: If True, include dotfiles/dotfolders.
        """
        return run_tool(
            logger,
            operation="List Directory",
            target_path=path,
            fn=lambda: directory_service.list_directory(path, include_hidden=include_hidden),
        )
