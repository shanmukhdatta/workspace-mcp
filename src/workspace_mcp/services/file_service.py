"""File-level operations: create, read, write, append, update, move, rename,
delete -- all funneled through :class:`~workspace_mcp.utils.pathsec.PathValidator`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.services.backup_service import BackupService
from workspace_mcp.models.schemas import (
    AlreadyExistsError,
    ConfirmationRequiredError,
    DuplicateFileError,
    FileInfo,
    FileTooLargeError,
    NotFoundError,
    UnsupportedExtensionError,
)
from workspace_mcp.utils.pathsec import PathValidator, sanitize_name


class FileService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator
        self.backups = BackupService(settings, validator)

    def _backup(self, path: Path) -> None:
        if self.settings.enable_backups and path.is_file():
            self.backups.snapshot(path)

    # ------------------------------------------------------------------ #

    def _check_extension(self, path: Path) -> None:
        if not self.settings.allowed_extensions:
            return
        suffix = path.suffix.lower()
        # Files with no extension (e.g. "Dockerfile", "LICENSE") are allowed.
        if suffix == "":
            return
        if suffix not in {e.lower() for e in self.settings.allowed_extensions}:
            raise UnsupportedExtensionError(
                f"Extension '{suffix}' is not in the allowed_extensions list.",
                extension=suffix,
                path=str(path),
            )

    def _check_size(self, content: str | bytes) -> None:
        size = len(content.encode("utf-8")) if isinstance(content, str) else len(content)
        if size > self.settings.max_file_size_bytes:
            raise FileTooLargeError(
                f"Content is {size} bytes, exceeding the "
                f"{self.settings.max_file_size_bytes}-byte limit.",
                size_bytes=size,
                limit_bytes=self.settings.max_file_size_bytes,
            )

    @staticmethod
    def _info(path: Path) -> FileInfo:
        stat = path.stat()
        text_lines: Optional[int] = None
        try:
            text_lines = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
        except OSError:
            text_lines = None
        return FileInfo(
            path=str(path),
            size_bytes=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            created=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
            extension=path.suffix,
            line_count=text_lines,
        )

    # -- public operations --------------------------------------------- #

    def create_file(self, rel_path: str, content: str = "", *, overwrite: bool = False) -> FileInfo:
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if path.exists() and not overwrite:
            raise DuplicateFileError(
                f"A file already exists at '{rel_path}'. Pass overwrite=True "
                "to replace it, or use write_file/update_file instead.",
                path=rel_path,
            )
        self._check_extension(path)
        self._check_size(content)
        self._backup(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return self._info(path)

    def read_file(self, rel_path: str) -> tuple[str, FileInfo]:
        path = self.validator.resolve(rel_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError(f"No file found at '{rel_path}'.", path=rel_path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedExtensionError(
                f"'{rel_path}' does not look like a UTF-8 text file and "
                "cannot be read through this tool.",
                path=rel_path,
            ) from exc
        return text, self._info(path)

    def write_file(self, rel_path: str, content: str, *, confirm: bool = False) -> FileInfo:
        """Full overwrite of a file's contents (creates it if missing)."""
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if path.exists() and self.settings.require_overwrite_confirmation and not confirm:
            raise ConfirmationRequiredError(
                f"'{rel_path}' already exists. Pass confirm=True to "
                "overwrite it (this replaces the entire file content).",
                path=rel_path,
            )
        self._check_extension(path)
        self._check_size(content)
        self._backup(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return self._info(path)

    def append_file(self, rel_path: str, content: str) -> FileInfo:
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if not path.exists():
            raise NotFoundError(
                f"Cannot append: no file exists at '{rel_path}'. Use " "create_file first.",
                path=rel_path,
            )
        self._check_extension(path)
        existing = path.read_text(encoding="utf-8")
        self._check_size(existing + content)
        self._backup(path)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(content)
        return self._info(path)

    def update_file(
        self,
        rel_path: str,
        *,
        find: Optional[str] = None,
        replace: Optional[str] = None,
        new_content: Optional[str] = None,
        count: int = -1,
    ) -> FileInfo:
        """Update a file either by literal find/replace, or full replacement.

        Exactly one mode must be used:
        - ``find`` + ``replace`` (optionally bounded by ``count``), or
        - ``new_content`` for a full rewrite.
        """
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if not path.exists():
            raise NotFoundError(f"No file found at '{rel_path}'.", path=rel_path)

        if new_content is not None:
            updated = new_content
        elif find is not None:
            original = path.read_text(encoding="utf-8")
            if find not in original:
                raise NotFoundError(
                    f"The text to find was not present in '{rel_path}'.",
                    path=rel_path,
                )
            updated = original.replace(find, replace or "", count if count >= 0 else -1)
        else:
            raise NotFoundError(  # reused as a generic "bad args" signal
                "update_file requires either (find, replace) or new_content.",
                path=rel_path,
            )

        self._check_size(updated)
        self._backup(path)
        path.write_text(updated, encoding="utf-8")
        return self._info(path)

    def move_file(self, src_rel: str, dest_rel: str, *, overwrite: bool = False) -> FileInfo:
        src = self.validator.resolve(src_rel)
        dest = self.validator.resolve(dest_rel)
        self.validator.assert_not_protected(src)
        if not src.exists():
            raise NotFoundError(f"No file found at '{src_rel}'.", path=src_rel)
        if dest.exists() and not overwrite:
            raise DuplicateFileError(f"Destination '{dest_rel}' already exists.", path=dest_rel)
        self._check_extension(dest)
        self._backup(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.replace(dest)
        return self._info(dest)

    def rename_file(self, rel_path: str, new_name: str, *, overwrite: bool = False) -> FileInfo:
        sanitize_name(new_name, kind="file name")
        src = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(src)
        if not src.exists():
            raise NotFoundError(f"No file found at '{rel_path}'.", path=rel_path)
        dest = src.with_name(new_name)
        self.validator.resolve(str(dest.relative_to(self.validator.workspace_root)))
        if dest.exists() and not overwrite:
            raise DuplicateFileError(
                f"'{new_name}' already exists in that directory.", path=new_name
            )
        self._backup(dest)
        src.replace(dest)
        return self._info(dest)

    def delete_file(self, rel_path: str, *, confirm: bool = False) -> str:
        path = self.validator.resolve(rel_path)
        self.validator.assert_not_protected(path)
        if not path.exists() or not path.is_file():
            raise NotFoundError(f"No file found at '{rel_path}'.", path=rel_path)
        if self.settings.require_overwrite_confirmation and not confirm:
            raise ConfirmationRequiredError(
                f"Deleting '{rel_path}' requires confirm=True.", path=rel_path
            )
        self._backup(path)
        path.unlink()
        return self.validator.relative_to_root(path)
