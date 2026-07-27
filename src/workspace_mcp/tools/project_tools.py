"""MCP tools: create_project, delete_project, rename_project."""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.project_service import ProjectService
from workspace_mcp.tools._common import run_tool


def register(mcp: FastMCP, project_service: ProjectService, logger: OperationLogger) -> None:
    @mcp.tool()
    def create_project(
        name: str,
        structure: Optional[list[str]] = None,
        description: str = "",
        include_docker: bool = True,
    ) -> dict[str, Any]:
        """Create a new project inside the workspace with a conventional
        folder structure (frontend/backend/database/docker/scripts/tests/
        docs/assets/config by default) plus .gitignore, Dockerfile,
        docker-compose.yml, README.md, CLOUD.md and PROJECT_TREE.md.

        Args:
            name: Project (top-level directory) name. Letters, numbers,
                spaces, '.', '-', '_' only.
            structure: Optional custom list of subfolder names, replacing
                the default 9-folder scaffold.
            description: One-paragraph description used in README/CLOUD.md.
            include_docker: Whether to generate Dockerfile + docker-compose.yml.
        """
        return run_tool(
            logger,
            operation="Create Project",
            target_path=name,
            fn=lambda: project_service.create_project(
                name,
                structure=structure,
                description=description,
                include_docker=include_docker,
            ),
        )

    @mcp.tool()
    def delete_project(name: str, confirm: bool = False) -> dict[str, Any]:
        """Permanently delete an entire project directory and everything in it.

        Args:
            name: Project name to delete.
            confirm: Must be explicitly set to True; this is irreversible.
        """
        return run_tool(
            logger,
            operation="Delete Project",
            target_path=name,
            fn=lambda: project_service.delete_project(name, confirm=confirm),
        )

    @mcp.tool()
    def rename_project(old_name: str, new_name: str, overwrite: bool = False) -> dict[str, Any]:
        """Rename (move) a project directory within the workspace.

        Args:
            old_name: Current project name.
            new_name: New project name.
            overwrite: If True, replace an existing project at new_name.
        """
        return run_tool(
            logger,
            operation="Rename Project",
            target_path=f"{old_name} -> {new_name}",
            fn=lambda: project_service.rename_project(old_name, new_name, overwrite=overwrite),
        )
