"""MCP wrappers for extension capabilities. All use the shared result envelope."""
from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP
from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.terminal_service import TerminalService
from workspace_mcp.services.git_service import GitService
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.services.template_service import TemplateService
from workspace_mcp.tools._common import run_tool, run_tool_async


def register(mcp: FastMCP, terminal: TerminalService, git: GitService,
             backup: BackupService, templates: TemplateService, logger: OperationLogger) -> None:
    @mcp.tool()
    async def run_command(argv: list[str], cwd: str, timeout: int = 60) -> dict[str, Any]:
        """Run an explicitly allowed developer CLI without a shell (disabled by default)."""
        return await run_tool_async(logger, operation="Run Command", target_path=cwd,
                                    fn=lambda: terminal.run_command(argv, cwd, timeout))

    @mcp.tool()
    def git_init(project: str) -> dict[str, Any]:
        """Initialize Git for an existing top-level project; opt-in required."""
        return run_tool(logger, operation="Git Init", target_path=project, fn=lambda: git.init(project))

    @mcp.tool()
    def git_status(project: str) -> dict[str, Any]:
        """Show Git status for one project."""
        return run_tool(logger, operation="Git Status", target_path=project, fn=lambda: git.status(project))

    @mcp.tool()
    def git_branch(project: str, name: str = "", create: bool = False) -> dict[str, Any]:
        """List, create or switch local Git branches; no remote operations."""
        return run_tool(logger, operation="Git Branch", target_path=project,
                        fn=lambda: git.branch(project, name, create))

    @mcp.tool()
    def git_log(project: str, limit: int = 10) -> dict[str, Any]:
        """Show bounded local Git commit history."""
        return run_tool(logger, operation="Git Log", target_path=project, fn=lambda: git.log(project, limit))

    @mcp.tool()
    def git_diff(project: str, paths: list[str] | None = None, staged: bool = False) -> dict[str, Any]:
        """Show Git patch, optionally only staged or explicit paths."""
        return run_tool(logger, operation="Git Diff", target_path=project,
                        fn=lambda: git.diff(project, paths, staged))

    @mcp.tool()
    def git_commit(project: str, message: str, paths: list[str],
                   checkpoint: bool = True) -> dict[str, Any]:
        """Stage only explicitly named project files and commit; optionally checkpoint beforehand."""
        return run_tool(logger, operation="Git Commit", target_path=project,
                        fn=lambda: git.commit(project, message, paths, checkpoint))

    @mcp.tool()
    def list_backups(path: str = "") -> dict[str, Any]:
        """List pre-mutation snapshots, optionally filtered by workspace-relative file path."""
        return run_tool(logger, operation="List Backups", target_path=path,
                        fn=lambda: backup.list_backups(path))

    @mcp.tool()
    def restore_backup(backup_id: str, confirm: bool = False) -> dict[str, Any]:
        """Restore a file from a recorded snapshot; requires explicit confirmation."""
        return run_tool(logger, operation="Restore Backup", target_path=backup_id,
                        fn=lambda: backup.restore(backup_id, confirm=confirm))

    @mcp.tool()
    def list_templates() -> dict[str, Any]:
        """List built-in and administrator-supplied project scaffold templates."""
        return run_tool(logger, operation="List Templates", target_path="",
                        fn=templates.list_templates)
