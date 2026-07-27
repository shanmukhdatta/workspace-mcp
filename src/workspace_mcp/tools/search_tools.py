"""MCP tools: search_files, find_text, project_tree."""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.services.search_service import SearchService
from workspace_mcp.tools._common import run_tool


def register(
    mcp: FastMCP,
    search_service: SearchService,
    doc_service: DocService,
    logger: OperationLogger,
) -> None:
    @mcp.tool()
    def search_files(pattern: str, root: str = ".", max_results: int = 200) -> dict[str, Any]:
        """Find files by glob pattern (e.g. "*.py", "**/*.test.ts").

        Args:
            pattern: Glob pattern, evaluated relative to `root`.
            root: Directory to search under, relative to the workspace root.
            max_results: Cap on number of matches returned.
        """
        return run_tool(
            logger,
            operation="Search Files",
            target_path=f"{root} ({pattern})",
            fn=lambda: search_service.search_files(pattern, root, max_results=max_results),
        )

    @mcp.tool()
    def find_text(
        query: str,
        root: str = ".",
        extensions: Optional[list[str]] = None,
        case_sensitive: bool = False,
        max_results: int = 200,
    ) -> dict[str, Any]:
        """Search file contents for a literal text string (grep-like).

        Args:
            query: Literal text to search for.
            root: Directory to search under, relative to the workspace root.
            extensions: Optional list like [".py", ".ts"] to restrict the search.
            case_sensitive: Whether the match is case sensitive.
            max_results: Cap on number of matching lines returned.
        """
        return run_tool(
            logger,
            operation="Find Text",
            target_path=f"{root} ('{query}')",
            fn=lambda: search_service.find_text(
                query,
                root,
                extensions=extensions,
                case_sensitive=case_sensitive,
                max_results=max_results,
            ),
        )

    @mcp.tool()
    def project_tree(path: str = ".") -> dict[str, Any]:
        """Render a visual ASCII tree of a directory's contents (not saved to disk).

        Args:
            path: Directory to render, relative to the workspace root.
        """
        def _do() -> dict[str, str]:
            resolved = search_service.validator.resolve(path)
            return {"tree": doc_service.render_tree(resolved)}

        return run_tool(logger, operation="Render Project Tree", target_path=path, fn=_do)
