"""Directory-level operations: create, delete, list."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import (
    AlreadyExistsError,
    ConfirmationRequiredError,
    DirectoryEntryInfo,
    EntryType,
    NotFoundError,
)
from workspace_mcp.utils.pathsec import PathValidator


class DirectoryService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator

    def create_directory(self, rel_path: str, *, exist_ok: bool = True) -> str:
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if path.exists() and path.is_dir() and not exist_ok:
            raise AlreadyExistsError(f"Directory '{rel_path}' already exists.", path=rel_path)
        if path.exists() and path.is_file():
            raise AlreadyExistsError(
                f"A file (not a directory) already exists at '{rel_path}'.", path=rel_path
            )
        path.mkdir(parents=True, exist_ok=True)
        return self.validator.relative_to_root(path)

    def delete_directory(
        self, rel_path: str, *, confirm: bool = False, recursive: bool = True
    ) -> str:
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if path == self.validator.workspace_root:
            raise ConfirmationRequiredError(
                "Refusing to delete the workspace root itself.", path=rel_path
            )
        if not path.exists() or not path.is_dir():
            raise NotFoundError(f"No directory found at '{rel_path}'.", path=rel_path)
        if self.settings.require_overwrite_confirmation and not confirm:
            raise ConfirmationRequiredError(
                f"Deleting directory '{rel_path}' requires confirm=True.", path=rel_path
            )
        if recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()
        return self.validator.relative_to_root(path)

    def list_directory(
        self, rel_path: str = ".", *, include_hidden: bool = False
    ) -> list[DirectoryEntryInfo]:
        path = self.validator.resolve(rel_path)
        if not path.exists() or not path.is_dir():
            raise NotFoundError(f"No directory found at '{rel_path}'.", path=rel_path)

        entries: list[DirectoryEntryInfo] = []
        for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if (
                child.name in self.settings.ignored_dirs
                or child.name in self.settings.ignored_files
            ):
                continue
            if not include_hidden and child.name.startswith("."):
                continue
            if child.is_symlink():
                etype = EntryType.SYMLINK
            elif child.is_dir():
                etype = EntryType.DIRECTORY
            elif child.is_file():
                etype = EntryType.FILE
            else:
                etype = EntryType.OTHER

            stat = child.stat()
            entries.append(
                DirectoryEntryInfo(
                    name=child.name,
                    path=self.validator.relative_to_root(child),
                    type=etype,
                    size_bytes=stat.st_size if etype == EntryType.FILE else None,
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    extension=child.suffix if etype == EntryType.FILE else None,
                )
            )
        return entries
