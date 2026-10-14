"""Contract and regression tests for extension capabilities."""
from __future__ import annotations

import asyncio
import json
import shutil

import pytest

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import ConfirmationRequiredError, WorkspaceError
from workspace_mcp.services.agent_service import AgentService
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.services.git_service import GitService
from workspace_mcp.services.index_service import IndexService
from workspace_mcp.services.memory_service import MemoryService
from workspace_mcp.services.sync_service import SyncService
from workspace_mcp.services.template_service import TemplateService
from workspace_mcp.services.terminal_service import TerminalService


def test_backup_overwrite_delete_and_restore(file_service, settings, validator):
    file_service.create_file("demo.txt", "first")
    file_service.write_file("demo.txt", "second", confirm=True)
    file_service.delete_file("demo.txt", confirm=True)
    backup = BackupService(settings, validator)
    rows = backup.list_backups("demo.txt")
    assert len(rows) == 2
    assert [r["size"] for r in rows] == [6, 5]
    with pytest.raises(ConfirmationRequiredError):
        backup.restore(rows[0]["backup_id"])
    backup.restore(rows[0]["backup_id"], confirm=True)
    assert file_service.read_file("demo.txt")[0] == "second"


def test_config_rejects_external_support_dirs(workspace_root, tmp_path):
    settings = WorkspaceSettings(workspace_root=workspace_root, backup_dir=tmp_path / "elsewhere")
    with pytest.raises(ValueError):
        settings.ensure_directories()


def test_protected_subtrees(file_service):
    with pytest.raises(WorkspaceError):
        file_service.create_file(".workspace_mcp/memory/notes.txt", "not permitted")


def test_templates_builtins_and_duplicate(settings, validator):
    service = TemplateService(settings, validator)
    assert {"rust-cli", "fastapi-react", "nextjs-tailwind"}.issubset(service.list_templates())
    created = service.create("RustDemo", "rust-cli")
    assert created["files"] >= 2
    assert 'name = "rustdemo"' in (settings.workspace_root / "RustDemo/Cargo.toml").read_text()
    with pytest.raises(WorkspaceError):
        service.create("RustDemo", "rust-cli")


def test_custom_template_symlink_blocked(settings, validator):
    folder = settings.resolved_templates_dir() / "custom"
    folder.mkdir()
    (folder / "README.md").write_text("Hello {{project_name}}")
    t = TemplateService(settings, validator)
    assert t.create("Demo", "custom")["files"] == 1
    assert (settings.workspace_root / "Demo/README.md").read_text() == "Hello Demo"


def test_index_incremental_and_query(settings, validator):
    project = settings.workspace_root / "Demo"
    project.mkdir()
    (project / "alpha.py").write_text("def fibonacci_sequence():\n    return [0, 1, 1, 2]\n")
    index = IndexService(settings, validator)
    first = index.index("Demo")
    assert first["updated_files"] == 1
    assert first["mode"] == "lexical"
    assert index.index("Demo")["unchanged_files"] == 1
    matches = index.search("Demo", "fibonacci_sequence")
    assert matches["results"][0]["path"] == "alpha.py"
    assert not index.search("Demo", "unrelatedTokenXYZ")["results"]


def test_memory_graph_and_project_isolation(settings, validator):
    (settings.workspace_root / "P1").mkdir()
    (settings.workspace_root / "P2").mkdir()
    memory = MemoryService(settings, validator)
    a = memory.remember("P1", "decision", "Use SQLite", "Persist facts")
    b = memory.remember("P1", "dependency", "DB adapter", "Needs storage")
    edge = memory.link("P1", a["id"], b["id"], "depends_on")
    assert edge["source"] == a["id"]
    assert len(memory.query("P1", "SQLite")["facts"]) == 1
    assert not memory.query("P2")["facts"]
    with pytest.raises(WorkspaceError):
        memory.link("P2", a["id"], b["id"], "depends_on")


def test_agent_lifecycle(settings, validator):
    (settings.workspace_root / "Demo").mkdir()
    agents = AgentService(settings, validator)
    task = agents.submit("Demo", "reviewer", "Verify schema", {"target": "api"})
    assert agents.claim("Demo", task["task_id"], "agent-1")["status"] == "running"
    with pytest.raises(WorkspaceError):
        agents.claim("Demo", task["task_id"], "agent-2")
    with pytest.raises(WorkspaceError):
        agents.finish("Demo", task["task_id"], "agent-2", "no")
    assert agents.finish("Demo", task["task_id"], "agent-1", "done")["status"] == "completed"
    assert len(agents.list_tasks("Demo", "completed")) == 1


def test_terminal_gate_validation(settings, validator):
    (settings.workspace_root / "Demo").mkdir()
    terminal = TerminalService(settings, validator)
    with pytest.raises(WorkspaceError):
        asyncio.run(terminal.run_command(["pytest", "--version"], "Demo"))
    enabled = settings.model_copy(update={"enable_terminal": True})
    terminal = TerminalService(enabled, validator)
    with pytest.raises(WorkspaceError):
        asyncio.run(terminal.run_command(["sh", "-c", "echo"], "Demo"))
    with pytest.raises(WorkspaceError):
        asyncio.run(terminal.run_command(["pytest", "--version"], "../"))
    if shutil.which("pytest"):
        result = asyncio.run(terminal.run_command(["pytest", "--version"], "Demo"))
        assert result["returncode"] == 0
        assert "pytest" in result["stdout"]


def test_git_gated_and_local(settings, validator):
    (settings.workspace_root / "Demo").mkdir()
    git = GitService(settings, validator)
    with pytest.raises(WorkspaceError):
        git.init("Demo")
    enabled = settings.model_copy(update={"enable_git": True})
    git = GitService(enabled, validator)
    if shutil.which("git"):
        assert git.init("Demo")["returncode"] == 0
        assert git.status("Demo")["returncode"] == 0
    with pytest.raises(WorkspaceError):
        git.branch("Demo", "../bad", create=True)


def test_sync_polling(settings):
    source = settings.resolved_logging_dir() / "operations.jsonl"
    source.write_text(json.dumps({"operation": "Created File", "target_path": "Demo/a.py"}) + "\n")
    sync = SyncService(settings)
    first = sync.poll()
    assert len(first["events"]) == 1
    assert first["cursor"] > 0
    assert sync.poll(first["cursor"])["events"] == []
