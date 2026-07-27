"""MCP tools: create_file, read_file, write_file, append_file, update_file,
move_file, rename_file, delete_file.
"""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.file_service import FileService
from workspace_mcp.tools._common import run_tool


def register(mcp: FastMCP, file_service: FileService, logger: OperationLogger) -> None:
    @mcp.tool()
    def create_file(path: str, content: str = "", overwrite: bool = False) -> dict[str, Any]:
        """Create a new file with the given content inside the workspace.

        Fails with DUPLICATE_FILE if the file already exists unless
        overwrite=True is passed.

        Args:
            path: Path relative to the workspace root, e.g. "MyApp/backend/main.py".
            content: Full text content of the file.
            overwrite: If True, replace an existing file at this path.
        """
        return run_tool(
            logger,
            operation="Created File",
            target_path=path,
            fn=lambda: file_service.create_file(path, content, overwrite=overwrite),
        )

    @mcp.tool()
    def read_file(path: str) -> dict[str, Any]:
        """Read the full text content of a file inside the workspace.

        Args:
            path: Path relative to the workspace root.
        """
        def _do() -> dict[str, Any]:
            text, info = file_service.read_file(path)
            return {"content": text, "info": info.model_dump(mode="json")}

        return run_tool(logger, operation="Read File", target_path=path, fn=_do)

    @mcp.tool()
    def write_file(path: str, content: str, confirm: bool = False) -> dict[str, Any]:
        """Overwrite a file's entire content (creating it if it doesn't exist).

        If the file already exists, confirm=True is required (unless the
        server's require_overwrite_confirmation setting is disabled).

        Args:
            path: Path relative to the workspace root.
            content: New full text content of the file.
            confirm: Must be True to overwrite an existing file.
        """
        return run_tool(
            logger,
            operation="Write File",
            target_path=path,
            fn=lambda: file_service.write_file(path, content, confirm=confirm),
        )

    @mcp.tool()
    def append_file(path: str, content: str) -> dict[str, Any]:
        """Append text to the end of an existing file.

        Args:
            path: Path relative to the workspace root. The file must already exist.
            content: Text to append.
        """
        return run_tool(
            logger,
            operation="Append File",
            target_path=path,
            fn=lambda: file_service.append_file(path, content),
        )

    @mcp.tool()
    def update_file(
        path: str,
        find: Optional[str] = None,
        replace: Optional[str] = None,
        new_content: Optional[str] = None,
        count: int = -1,
    ) -> dict[str, Any]:
        """Update part or all of an existing file.

        Use EITHER (find, replace) for a literal text substitution, OR
        new_content for a full rewrite -- do not pass both.

        Args:
            path: Path relative to the workspace root. Must already exist.
            find: Literal text to search for (mutually exclusive with new_content).
            replace: Replacement text for every match of `find` (default: "").
            new_content: Full replacement content for the file.
            count: Max number of `find` occurrences to replace (-1 = all).
        """
        return run_tool(
            logger,
            operation="Update File",
            target_path=path,
            fn=lambda: file_service.update_file(
                path, find=find, replace=replace, new_content=new_content, count=count
            ),
        )

    @mcp.tool()
    def move_file(source_path: str, destination_path: str, overwrite: bool = False) -> dict[str, Any]:
        """Move (or move+rename) a file to a new location within the workspace.

        Args:
            source_path: Current path, relative to the workspace root.
            destination_path: New path, relative to the workspace root.
            overwrite: If True, replace an existing file at the destination.
        """
        return run_tool(
            logger,
            operation="Move File",
            target_path=f"{source_path} -> {destination_path}",
            fn=lambda: file_service.move_file(source_path, destination_path, overwrite=overwrite),
        )

    @mcp.tool()
    def rename_file(path: str, new_name: str, overwrite: bool = False) -> dict[str, Any]:
        """Rename a file in place (keeping it in the same directory).

        Args:
            path: Current path, relative to the workspace root.
            new_name: New filename (not a full path) -- e.g. "app.py".
            overwrite: If True, replace an existing file with that name.
        """
        return run_tool(
            logger,
            operation="Rename File",
            target_path=path,
            fn=lambda: file_service.rename_file(path, new_name, overwrite=overwrite),
        )

    @mcp.tool()
    def delete_file(path: str, confirm: bool = False) -> dict[str, Any]:
        """Permanently delete a file inside the workspace.

        Args:
            path: Path relative to the workspace root.
            confirm: Must be explicitly True; this is irreversible.
        """
        return run_tool(
            logger,
            operation="Delete File",
            target_path=path,
            fn=lambda: file_service.delete_file(path, confirm=confirm),
        )
