"""MCP tools: generate_readme, generate_cloud_log, generate_project_tree."""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.tools._common import run_tool


def register(mcp: FastMCP, doc_service: DocService, logger: OperationLogger) -> None:
    @mcp.tool()
    def generate_readme(
        project_path: str,
        description: str = "",
        features: Optional[list[str]] = None,
        installation: str = "",
        usage: str = "",
        dependencies: Optional[list[str]] = None,
        configuration: str = "",
        tech_stack: Optional[list[str]] = None,
        future_improvements: Optional[list[str]] = None,
        license_name: str = "MIT",
    ) -> dict[str, Any]:
        """(Re)generate README.md for a project with the standard sections:
        description, features, folder structure, installation, usage,
        dependencies, configuration, tech stack, future improvements, license.

        Args:
            project_path: Path to the project directory, relative to the workspace root.
        """
        return run_tool(
            logger,
            operation="Generate README",
            target_path=project_path,
            fn=lambda: doc_service.generate_readme(
                project_path,
                description=description,
                features=features,
                installation=installation,
                usage=usage,
                dependencies=dependencies,
                configuration=configuration,
                tech_stack=tech_stack,
                future_improvements=future_improvements,
                license_name=license_name,
            ),
        )

    @mcp.tool()
    def generate_cloud_log(
        project_path: str,
        goal: str = "",
        architecture_decisions: Optional[list[str]] = None,
        files_created: Optional[list[str]] = None,
        files_updated: Optional[list[str]] = None,
        implementation_notes: Optional[list[str]] = None,
        important_decisions: Optional[list[str]] = None,
        known_limitations: Optional[list[str]] = None,
        future_work: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """(Re)generate CLOUD.md -- the AI work log explaining exactly what
        was generated in this project and why: goal, architecture decisions,
        files created/updated, implementation notes, known limitations,
        and future work.

        Args:
            project_path: Path to the project directory, relative to the workspace root.
        """
        return run_tool(
            logger,
            operation="Generate CLOUD.md",
            target_path=project_path,
            fn=lambda: doc_service.generate_cloud_log(
                project_path,
                goal=goal,
                architecture_decisions=architecture_decisions,
                files_created=files_created,
                files_updated=files_updated,
                implementation_notes=implementation_notes,
                important_decisions=important_decisions,
                known_limitations=known_limitations,
                future_work=future_work,
            ),
        )

    @mcp.tool()
    def generate_project_tree(project_path: str) -> dict[str, Any]:
        """(Re)generate PROJECT_TREE.md, a saved visual ASCII tree of the project.

        Args:
            project_path: Path to the project directory, relative to the workspace root.
        """
        return run_tool(
            logger,
            operation="Generate PROJECT_TREE.md",
            target_path=project_path,
            fn=lambda: doc_service.generate_project_tree(project_path),
        )
