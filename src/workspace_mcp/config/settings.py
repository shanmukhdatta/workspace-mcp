"""
Configuration for the workspace MCP server.

Configuration can come from (in increasing priority order):

1. Hard-coded defaults below.
2. A YAML/JSON config file (``--config`` / ``WORKSPACE_MCP_CONFIG_FILE``).
3. Environment variables prefixed with ``WORKSPACE_MCP_`` (e.g.
   ``WORKSPACE_MCP_WORKSPACE_ROOT=/home/user/AIProjects``).

The resulting :class:`WorkspaceSettings` object is treated as immutable for
the lifetime of the process and is the single source of truth every
service/tool consults for limits, allow-lists, and directory locations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ALLOWED_EXTENSIONS: set[str] = {
    # code
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".kt", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".cs",
    ".rb", ".php", ".sh", ".bash", ".ps1", ".sql", ".graphql", ".proto",
    # web / markup
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    # data / config
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".env.example",
    ".xml", ".csv", ".txt", ".md", ".mdx", ".rst",
    # containers / build
    ".dockerfile", ".gitignore", ".gitattributes", ".editorconfig",
    ".lock", ".mod", ".sum",
    # images/docs commonly generated alongside docs (kept conservative)
    ".svg",
}

DEFAULT_IGNORED_FILES: set[str] = {
    ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", ".env.local",
}

DEFAULT_IGNORED_DIRS: set[str] = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".idea", ".vscode",
}


class WorkspaceSettings(BaseSettings):
    """Immutable server configuration.

    All paths other than ``workspace_root`` are resolved *relative to*
    ``workspace_root`` unless given as absolute paths, and are created on
    first use if missing.
    """

    model_config = SettingsConfigDict(
        env_prefix="WORKSPACE_MCP_",
        extra="ignore",
        case_sensitive=False,
    )

    workspace_root: Path = Field(
        default=Path.home() / "AIProjects",
        description="The single directory the server is allowed to touch.",
    )
    max_file_size_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5 MB
        description="Hard cap on any single file the server will write.",
    )
    allowed_extensions: set[str] = Field(default_factory=lambda: set(DEFAULT_ALLOWED_EXTENSIONS))
    ignored_files: set[str] = Field(default_factory=lambda: set(DEFAULT_IGNORED_FILES))
    ignored_dirs: set[str] = Field(default_factory=lambda: set(DEFAULT_IGNORED_DIRS))

    # New capabilities are gated independently; unsafe process execution is off by default.
    enable_terminal: bool = False
    enable_git: bool = False
    enable_backups: bool = True
    max_backup_file_size_bytes: int = 25 * 1024 * 1024
    command_timeout_seconds: int = Field(default=120, ge=1, le=1800)
    allowed_commands: set[str] = Field(default_factory=set)
    semantic_model_path: str = ""
    logging_dir: Path = Field(default=Path(".workspace_mcp/logs"))
    index_dir: Path = Field(default=Path(".workspace_mcp/index"))
    memory_dir: Path = Field(default=Path(".workspace_mcp/memory"))
    sync_dir: Path = Field(default=Path(".workspace_mcp/sync"))
    backup_dir: Path = Field(default=Path(".workspace_mcp/backups"))
    templates_dir: Path = Field(default=Path(".workspace_mcp/templates"))

    allow_symlinks: bool = Field(
        default=False,
        description="If False (recommended), any symlink whose target "
        "resolves outside the workspace is rejected.",
    )
    require_overwrite_confirmation: bool = Field(
        default=True,
        description="If True, write_file/delete_* require explicit "
        "confirm=True instead of silently clobbering existing content.",
    )
    protected_files: set[str] = Field(
        default_factory=lambda: {
            "workspace_mcp.config.json",
            "workspace_mcp.config.yaml",
            ".workspace_mcp",
        }
    )

    @field_validator("workspace_root", "logging_dir", "backup_dir", "templates_dir", "index_dir", "memory_dir", "sync_dir", mode="before")
    @classmethod
    def _expand(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = Path(v)
        if isinstance(v, Path):
            return Path(os.path.expandvars(str(v))).expanduser()
        return v

    def resolved_index_dir(self) -> Path:
        return self._resolve_under_root(self.index_dir)

    def resolved_memory_dir(self) -> Path:
        return self._resolve_under_root(self.memory_dir)

    def resolved_sync_dir(self) -> Path:
        return self._resolve_under_root(self.sync_dir)

    def resolved_logging_dir(self) -> Path:
        return self._resolve_under_root(self.logging_dir)

    def resolved_backup_dir(self) -> Path:
        return self._resolve_under_root(self.backup_dir)

    def resolved_templates_dir(self) -> Path:
        return self._resolve_under_root(self.templates_dir)

    def _resolve_under_root(self, p: Path) -> Path:
        root = self.workspace_root.resolve()
        resolved = (p if p.is_absolute() else root / p).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Server support directory must be inside workspace root.")
        return resolved

    def ensure_directories(self) -> None:
        """Create workspace root and all support directories if missing."""
        for d in (
            self.workspace_root,
            self.resolved_logging_dir(),
            self.resolved_backup_dir(),
            self.resolved_templates_dir(),
            self.resolved_index_dir(),
            self.resolved_memory_dir(),
            self.resolved_sync_dir(),
        ):
            d.mkdir(parents=True, exist_ok=True)


def _load_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == ".json":
        return json.loads(text) or {}
    raise ValueError(f"Unsupported config file extension: {path.suffix}")


def load_settings(config_file: Optional[str | Path] = None) -> WorkspaceSettings:
    """Build a :class:`WorkspaceSettings`, layering file config under env vars.

    Args:
        config_file: Optional explicit path to a YAML/JSON config file. If
            omitted, ``WORKSPACE_MCP_CONFIG_FILE`` env var is checked, and
            finally ``./workspace_mcp.config.yaml`` / ``.json`` in the
            current working directory.
    """
    candidates: list[Path] = []
    if config_file:
        candidates.append(Path(config_file))
    env_path = os.environ.get("WORKSPACE_MCP_CONFIG_FILE")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path.cwd() / "workspace_mcp.config.yaml")
    candidates.append(Path.cwd() / "workspace_mcp.config.json")

    file_data: dict[str, Any] = {}
    for candidate in candidates:
        if candidate.exists():
            file_data = _load_file(candidate)
            break

    # Environment variables (handled by pydantic-settings) take precedence
    # over file values because we only use file_data to seed defaults that
    # BaseSettings() itself will then override with any matching env var.
    settings = WorkspaceSettings(**file_data)
    settings.ensure_directories()
    return settings
