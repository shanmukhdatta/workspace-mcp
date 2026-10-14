"""MCP wrappers for extension capabilities. All use the shared result envelope."""

from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP
from workspace_mcp.logging.logger import OperationLogger
from workspace_mcp.services.terminal_service import TerminalService
from workspace_mcp.services.git_service import GitService
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.services.template_service import TemplateService
from workspace_mcp.services.index_service import IndexService
from workspace_mcp.services.memory_service import MemoryService
from workspace_mcp.services.agent_service import AgentService
from workspace_mcp.services.sync_service import SyncService
from workspace_mcp.tools._common import run_tool, run_tool_async


def register(
    mcp: FastMCP,
    terminal: TerminalService,
    git: GitService,
    backup: BackupService,
    templates: TemplateService,
    logger: OperationLogger,
    index: IndexService,
    memory: MemoryService,
    agents: AgentService,
    sync: SyncService,
) -> None:
    @mcp.tool()
    async def run_command(argv: list[str], cwd: str, timeout: int = 60) -> dict[str, Any]:
        """Run an explicitly allowed developer CLI without a shell (disabled by default)."""
        return await run_tool_async(
            logger,
            operation="Run Command",
            target_path=cwd,
            fn=lambda: terminal.run_command(argv, cwd, timeout),
        )

    @mcp.tool()
    def git_init(project: str) -> dict[str, Any]:
        """Initialize Git for an existing top-level project; opt-in required."""
        return run_tool(
            logger, operation="Git Init", target_path=project, fn=lambda: git.init(project)
        )

    @mcp.tool()
    def git_status(project: str) -> dict[str, Any]:
        """Show Git status for one project."""
        return run_tool(
            logger, operation="Git Status", target_path=project, fn=lambda: git.status(project)
        )

    @mcp.tool()
    def git_branch(project: str, name: str = "", create: bool = False) -> dict[str, Any]:
        """List, create or switch local Git branches; no remote operations."""
        return run_tool(
            logger,
            operation="Git Branch",
            target_path=project,
            fn=lambda: git.branch(project, name, create),
        )

    @mcp.tool()
    def git_log(project: str, limit: int = 10) -> dict[str, Any]:
        """Show bounded local Git commit history."""
        return run_tool(
            logger, operation="Git Log", target_path=project, fn=lambda: git.log(project, limit)
        )

    @mcp.tool()
    def git_diff(
        project: str, paths: list[str] | None = None, staged: bool = False
    ) -> dict[str, Any]:
        """Show Git patch, optionally only staged or explicit paths."""
        return run_tool(
            logger,
            operation="Git Diff",
            target_path=project,
            fn=lambda: git.diff(project, paths, staged),
        )

    @mcp.tool()
    def git_commit(
        project: str, message: str, paths: list[str], checkpoint: bool = True
    ) -> dict[str, Any]:
        """Stage only explicitly named project files and commit; optionally checkpoint beforehand."""
        return run_tool(
            logger,
            operation="Git Commit",
            target_path=project,
            fn=lambda: git.commit(project, message, paths, checkpoint),
        )

    @mcp.tool()
    def list_backups(path: str = "") -> dict[str, Any]:
        """List pre-mutation snapshots, optionally filtered by workspace-relative file path."""
        return run_tool(
            logger, operation="List Backups", target_path=path, fn=lambda: backup.list_backups(path)
        )

    @mcp.tool()
    def restore_backup(backup_id: str, confirm: bool = False) -> dict[str, Any]:
        """Restore a file from a recorded snapshot; requires explicit confirmation."""
        return run_tool(
            logger,
            operation="Restore Backup",
            target_path=backup_id,
            fn=lambda: backup.restore(backup_id, confirm=confirm),
        )

    @mcp.tool()
    def list_templates() -> dict[str, Any]:
        """List built-in and administrator-supplied project scaffold templates."""
        return run_tool(
            logger, operation="List Templates", target_path="", fn=templates.list_templates
        )

    @mcp.tool()
    def index_project(project: str, max_files: int = 5000) -> dict[str, Any]:
        """Incrementally index project source in SQLite; optional local semantic embeddings."""
        return run_tool(
            logger,
            operation="Index Project",
            target_path=project,
            fn=lambda: index.index(project, max_files),
        )

    @mcp.tool()
    def search_code(project: str, query: str, limit: int = 10) -> dict[str, Any]:
        """Search indexed code; reports lexical/semantic mode explicitly."""
        return run_tool(
            logger,
            operation="Search Code",
            target_path=project,
            fn=lambda: index.search(project, query, limit),
        )

    @mcp.tool()
    def remember_fact(project: str, kind: str, title: str, content: str) -> dict[str, Any]:
        """Store an architectural decision, dependency, API contract, TODO, or other fact."""
        return run_tool(
            logger,
            operation="Remember Fact",
            target_path=project,
            fn=lambda: memory.remember(project, kind, title, content),
        )

    @mcp.tool()
    def link_facts(project: str, source: str, target: str, relation: str) -> dict[str, Any]:
        """Create a knowledge-graph relation between two project facts."""
        return run_tool(
            logger,
            operation="Link Facts",
            target_path=project,
            fn=lambda: memory.link(project, source, target, relation),
        )

    @mcp.tool()
    def query_memory(project: str, text: str = "", limit: int = 40) -> dict[str, Any]:
        """Retrieve project facts and dependency relationships across sessions."""
        return run_tool(
            logger,
            operation="Query Memory",
            target_path=project,
            fn=lambda: memory.query(project, text, limit),
        )

    @mcp.tool()
    def agent_submit(
        project: str, role: str, goal: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Queue a task for a client-side architect/implementer/reviewer/tester/researcher agent."""
        return run_tool(
            logger,
            operation="Agent Submit",
            target_path=project,
            fn=lambda: agents.submit(project, role, goal, context),
        )

    @mcp.tool()
    def agent_claim(project: str, task_id: str, assignee: str) -> dict[str, Any]:
        """Claim queued work with an atomic transition to running."""
        return run_tool(
            logger,
            operation="Agent Claim",
            target_path=project,
            fn=lambda: agents.claim(project, task_id, assignee),
        )

    @mcp.tool()
    def agent_finish(
        project: str, task_id: str, assignee: str, result: str, succeeded: bool = True
    ) -> dict[str, Any]:
        """Record the assignee's outcome; does not generate or execute AI work."""
        return run_tool(
            logger,
            operation="Agent Finish",
            target_path=project,
            fn=lambda: agents.finish(project, task_id, assignee, result, succeeded),
        )

    @mcp.tool()
    def agent_tasks(project: str, status: str = "") -> dict[str, Any]:
        """List queued, running, completed, and failed tasks for a project."""
        return run_tool(
            logger,
            operation="Agent Tasks",
            target_path=project,
            fn=lambda: agents.list_tasks(project, status),
        )

    @mcp.tool()
    def sync_events(cursor: int = 0, limit: int = 50) -> dict[str, Any]:
        """Poll recent workspace operation events using a resumable byte cursor."""
        return run_tool(
            logger, operation="Sync Events", target_path="", fn=lambda: sync.poll(cursor, limit)
        )
