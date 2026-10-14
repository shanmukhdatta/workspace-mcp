"""Opt-in subprocess execution; never runs through a shell."""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator

MAX_OUTPUT = 65536
# Only conservative, commonly used developer CLIs. Operators must opt in.
SAFE_DEFAULT_COMMANDS = ("pytest", "ruff", "black", "mypy", "uv", "npm", "pip", "cargo")
BLOCKED_ARGUMENTS = ("-c", "--eval", "-e", "--prefix", "--global", "-g", "--cwd", "--directory")
BLOCKED_SHELL_METACHARS = ("\x00", "\n", "\r")


class TerminalService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator

    def _validate(self, argv: list[str], cwd: str) -> Path:
        if not self.settings.enable_terminal:
            raise WorkspaceError(
                "Terminal execution is disabled. Set WORKSPACE_MCP_ENABLE_TERMINAL=true after reviewing the security guide."
            )
        if not argv or len(argv) > 64 or not all(isinstance(a, str) and a for a in argv):
            raise WorkspaceError("Provide 1 to 64 non-empty command arguments.")
        exe = argv[0]
        allowed = set(self.settings.allowed_commands or SAFE_DEFAULT_COMMANDS)
        if exe not in allowed or "/" in exe or "\\" in exe:
            raise WorkspaceError("Executable is not in allowed_commands.", executable=exe)
        if any(len(arg) > 4096 or any(c in arg for c in BLOCKED_SHELL_METACHARS) for arg in argv):
            raise WorkspaceError("Invalid command argument.")
        # Blocks common CLI options that let commands escape cwd or evaluate inline code.
        if any(
            a in BLOCKED_ARGUMENTS or a.startswith("--prefix=") or a.startswith("--cwd=")
            for a in argv[1:]
        ):
            raise WorkspaceError("This command option is disallowed.")
        if exe == "uv" and len(argv) > 1 and argv[1] in ("tool", "pip", "python", "runx"):
            raise WorkspaceError("Unrestricted uv subcommands are disabled by this tool.")
        if (
            exe == "npm"
            and len(argv) > 1
            and argv[1] in ("exec", "run", "run-script", "config", "set")
        ):
            raise WorkspaceError("npm script execution/configuration requires an external sandbox.")
        path = self.validator.resolve(cwd)
        if not path.is_dir() or path == self.validator.workspace_root:
            raise WorkspaceError(
                "Command cwd must be an existing project directory, not the workspace root."
            )
        if shutil.which(exe) is None:
            raise WorkspaceError("Executable is not installed.", executable=exe)
        return path

    async def run_command(self, argv: list[str], cwd: str, timeout: int = 60) -> dict:
        path = self._validate(argv, cwd)
        if timeout < 1 or timeout > self.settings.command_timeout_seconds:
            raise WorkspaceError("Timeout outside configured range.")
        # Do not pass tokens and API keys to child processes by default.
        env = {
            key: value
            for key, value in os.environ.items()
            if not re.search(r"(TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL)", key, re.I)
        }
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=path,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                stdout, stderr = await process.communicate()
                timed_out = True
        except OSError as exc:
            raise WorkspaceError("Could not execute command.", detail=str(exc)) from exc
        return {
            "argv": argv,
            "cwd": self.validator.relative_to_root(path),
            "returncode": process.returncode,
            "timed_out": timed_out,
            "stdout": stdout[:MAX_OUTPUT].decode("utf-8", "replace"),
            "stderr": stderr[:MAX_OUTPUT].decode("utf-8", "replace"),
            "stdout_truncated": len(stdout) > MAX_OUTPUT,
            "stderr_truncated": len(stderr) > MAX_OUTPUT,
        }
