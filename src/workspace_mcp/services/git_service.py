"""Git operations scoped to one validated project; no network subcommands."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import WorkspaceError
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.utils.pathsec import PathValidator


class GitService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator
        self.backups = BackupService(settings, validator)

    def _project(self, project: str) -> Path:
        path = self.validator.resolve(project)
        if path == self.validator.workspace_root or path.parent != self.validator.workspace_root or not path.is_dir():
            raise WorkspaceError("Git project must name an existing top-level workspace project.")
        if (path / ".git").is_symlink():
            raise WorkspaceError("Refusing to use symlinked .git directory.")
        return path

    def _run(self, project: str, args: list[str], *, initialized: bool = True) -> dict:
        if not self.settings.enable_git:
            raise WorkspaceError("Git tools are disabled; set WORKSPACE_MCP_ENABLE_GIT=true.")
        path = self._project(project)
        if initialized and not (path / ".git").is_dir():
            raise WorkspaceError("Project is not a Git repository; run git_init first.")
        try:
            proc = subprocess.run(
                ["git", "-C", str(path), *args],
                capture_output=True, text=True, errors="replace",
                timeout=self.settings.command_timeout_seconds, stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise WorkspaceError("Git command failed.", detail=str(exc)) from exc
        return {"returncode": proc.returncode, "stdout": proc.stdout[:65536],
                "stderr": proc.stderr[:65536], "truncated": len(proc.stdout) > 65536 or len(proc.stderr) > 65536}

    def init(self, project: str) -> dict:
        return self._run(project, ["init"], initialized=False)

    def status(self, project: str) -> dict:
        return self._run(project, ["status", "--short", "--branch"])

    def log(self, project: str, limit: int = 10) -> dict:
        if not 1 <= limit <= 100:
            raise WorkspaceError("limit must be between 1 and 100.")
        return self._run(project, ["log", "--oneline", f"-{limit}"])

    def branch(self, project: str, name: str = "", create: bool = False) -> dict:
        if not name and not create:
            return self._run(project, ["branch", "--list"])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.\-/]{0,100}", name) or ".." in name or name.endswith((".", "/", ".lock")):
            raise WorkspaceError("Invalid Git branch name.")
        return self._run(project, ["branch", name] if create else ["switch", name])

    def _paths(self, project: str, paths: list[str]) -> list[str]:
        root = self._project(project)
        if not paths:
            raise WorkspaceError("Provide explicit relative file paths.")
        result = []
        for p in paths:
            resolved = self.validator.resolve(f"{project}/{p}")
            self.validator.assert_not_protected(resolved)
            if resolved == root or not resolved.is_relative_to(root):
                raise WorkspaceError("Git path must remain inside selected project.")
            result.append(resolved.relative_to(root).as_posix())
        return result

    def diff(self, project: str, paths: list[str] | None = None, staged: bool = False) -> dict:
        args = ["diff", "--no-ext-diff", "--no-textconv"]
        if staged:
            args.append("--cached")
        if paths:
            args += ["--", *self._paths(project, paths)]
        return self._run(project, args)

    def commit(self, project: str, message: str, paths: list[str], checkpoint: bool = True) -> dict:
        if not message.strip() or len(message) > 500:
            raise WorkspaceError("Commit message must be 1 to 500 characters.")
        validated = self._paths(project, paths)
        if checkpoint:
            for p in validated:
                target = self.validator.resolve(f"{project}/{p}")
                if target.is_file():
                    self.backups.snapshot(target)
        added = self._run(project, ["add", "--", *validated])
        if added["returncode"] != 0:
            return added
        # Git hooks can execute local scripts. Git will not run hooks for MCP commits.
        return self._run(project, ["-c", "core.hooksPath=/dev/null", "commit", "-m", message])
