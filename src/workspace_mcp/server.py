"""
Entry point that assembles the FastMCP server.

Run directly:

    python -m workspace_mcp.server

or via the console-script installed by pyproject.toml:

    workspace-mcp

Configuration is resolved by :func:`workspace_mcp.config.settings.load_settings`
(file + environment variables) -- see docs/CONFIGURATION.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from workspace_mcp.config.settings import WorkspaceSettings, load_settings
from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.services.file_service import FileService
from workspace_mcp.services.project_service import ProjectService
from workspace_mcp.services.search_service import SearchService
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.services.terminal_service import TerminalService
from workspace_mcp.services.git_service import GitService
from workspace_mcp.services.template_service import TemplateService
from workspace_mcp.services.index_service import IndexService
from workspace_mcp.services.memory_service import MemoryService
from workspace_mcp.services.agent_service import AgentService
from workspace_mcp.services.sync_service import SyncService
from workspace_mcp.tools import extension_tools
from workspace_mcp.tools import (
    directory_tools,
    doc_tools,
    file_tools,
    project_tools,
    search_tools,
    validation_tools,
)
from workspace_mcp.utils.pathsec import PathValidator


def build_server(settings: WorkspaceSettings) -> FastMCP:
    """Wire settings -> validator -> services -> tools -> FastMCP instance."""
    settings.ensure_directories()

    validator = PathValidator(
        settings.workspace_root,
        allow_symlinks=settings.allow_symlinks,
        protected_files=settings.protected_files,
    )
    logger = OperationLogger(settings.resolved_logging_dir())

    directory_service = DirectoryService(settings, validator)
    file_service = FileService(settings, validator)
    doc_service = DocService(settings, validator)
    search_service = SearchService(settings, validator)
    project_service = ProjectService(settings, validator, directory_service, doc_service)

    mcp = FastMCP(
        "workspace-mcp",
        instructions=(
            "Tools for creating and managing real software projects directly "
            f"on disk inside the workspace at {settings.workspace_root}. "
            "Always create a project with create_project before adding files "
            "to it. All paths passed to any tool must be relative to the "
            "workspace root -- absolute paths and '..' are rejected."
        ),
    )

    project_tools.register(mcp, project_service, logger)
    directory_tools.register(mcp, directory_service, logger)
    file_tools.register(mcp, file_service, logger)
    search_tools.register(mcp, search_service, doc_service, logger)
    doc_tools.register(mcp, doc_service, logger)
    validation_tools.register(mcp, settings, validator, logger)
    extension_tools.register(
        mcp, TerminalService(settings, validator), GitService(settings, validator),
        BackupService(settings, validator), TemplateService(settings, validator), logger,
        IndexService(settings, validator), MemoryService(settings, validator),
        AgentService(settings, validator), SyncService(settings),
    )

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="workspace-mcp", description="Local Filesystem MCP Server")
    parser.add_argument(
        "--config", type=str, default=None, help="Path to a YAML/JSON config file."
    )
    parser.add_argument(
        "--workspace-root", type=str, default=None, help="Override the workspace root directory."
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport to run (default: stdio, used by Claude Desktop).",
    )
    parser.add_argument("action", nargs="?", choices=["index"], help="Optional command-line operation.")
    parser.add_argument("project", nargs="?", help="Project name for index operation.")
    args = parser.parse_args()

    settings = load_settings(args.config)
    if args.workspace_root:
        settings = settings.model_copy(update={"workspace_root": Path(args.workspace_root)})
        settings.ensure_directories()

    if args.action == "index":
        if not args.project:
            parser.error("index requires a project name.")
        import json

        validator = PathValidator(
            settings.workspace_root,
            allow_symlinks=settings.allow_symlinks,
            protected_files=settings.protected_files,
        )
        print(json.dumps(IndexService(settings, validator).index(args.project), indent=2))
        return

    mcp = build_server(settings)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
