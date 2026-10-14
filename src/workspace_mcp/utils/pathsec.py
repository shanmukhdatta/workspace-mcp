"""
Path validation and security.

This module is the single choke point every filesystem operation must pass
through. It is intentionally small, dependency-free, and heavily tested
(see ``tests/test_path_validation.py``) because a bug here is a security
bug for the whole server.

Guarantees provided by :meth:`PathValidator.resolve`:

1. The returned path is *always* a descendant of the workspace root
   (or the workspace root itself), verified via ``os.path.realpath``
   -- not string prefix matching, which is spoofable.
2. ``..`` segments, absolute paths that try to "escape" via a relative
   input, and NUL bytes are rejected before any filesystem call is made.
3. Symlinks are resolved and re-checked; a symlink that points outside the
   workspace is rejected unless ``allow_symlinks`` is explicitly enabled
   AND the resolved target is still inside the workspace (i.e. internal
   symlinks are fine, escaping ones never are).
4. Reserved / protected file names cannot be targeted for write or delete.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from workspace_mcp.models.schemas import (
    InvalidPathError,
    PathTraversalError,
    ProtectedFileError,
    SymlinkEscapeError,
    WorkspaceViolationError,
)

# Windows reserved device names -- rejected on every platform for portability
# of projects the server generates.
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}

# A conservative, portable filename allow-list: letters, numbers, space,
# dot, dash, underscore, plus common bracket/paren characters. Anything
# else (including control characters) is rejected.
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9 ._\-()\[\]]+$")


def _reject_nul(value: str) -> None:
    if "\x00" in value:
        raise InvalidPathError("Path contains a NUL byte.", path=value)


def sanitize_name(name: str, *, kind: str = "path segment") -> str:
    """Validate a single filename/dirname/project-name component.

    Raises :class:`InvalidPathError` if the name is empty, is ``.``/``..``,
    contains path separators, is a Windows-reserved device name, or contains
    characters outside the safe allow-list.
    """
    _reject_nul(name)
    if not name or name in (".", ".."):
        raise InvalidPathError(f"Invalid {kind}: {name!r}", value=name)
    if "/" in name or "\\" in name:
        raise InvalidPathError(f"{kind} must not contain path separators: {name!r}", value=name)
    stem = name.split(".")[0].upper()
    if stem in _WINDOWS_RESERVED:
        raise InvalidPathError(f"{kind} uses a reserved device name: {name!r}", value=name)
    if not _SAFE_SEGMENT_RE.match(name):
        raise InvalidPathError(
            f"{kind} contains unsupported characters: {name!r}. "
            "Use letters, numbers, spaces, '.', '-', '_', '(' or ')'.",
            value=name,
        )
    return name


class PathValidator:
    """Resolves and validates untrusted, user/AI-supplied relative paths."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        allow_symlinks: bool = False,
        protected_files: Optional[set[str]] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.allow_symlinks = allow_symlinks
        self.protected_files = protected_files or set()

    # -- public API -------------------------------------------------- #

    def resolve(self, relative_path: str, *, must_exist: bool = False) -> Path:
        """Resolve ``relative_path`` against the workspace root safely.

        Args:
            relative_path: A path supplied by the caller. May use ``/`` or
                ``\\`` separators. Must NOT be an absolute path outside the
                workspace, and must not contain ``..`` that escapes it.
            must_exist: If True, raise :class:`workspace_mcp.models.schemas.NotFoundError`-
                compatible ``InvalidPathError`` is not raised here; existence
                is the caller's responsibility, but symlink-target checks
                only run for paths that already exist.

        Returns:
            An absolute, resolved :class:`pathlib.Path` guaranteed to be
            inside ``self.workspace_root``.
        """
        if relative_path is None:
            raise InvalidPathError("Path must not be empty.")
        _reject_nul(relative_path)

        raw = relative_path.strip().replace("\\", "/")
        if raw in ("", "."):
            candidate = self.workspace_root
        else:
            # Reject absolute-looking inputs (POSIX '/' or Windows 'C:\')
            # outright -- everything must be relative to the workspace.
            if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
                raise WorkspaceViolationError(
                    "Absolute paths are not allowed; provide a path relative "
                    "to the workspace root.",
                    path=relative_path,
                )
            parts = [p for p in raw.split("/") if p not in ("", ".")]
            if any(p == ".." for p in parts):
                raise PathTraversalError(
                    "Path traversal ('..') is not permitted.", path=relative_path
                )
            for p in parts:
                sanitize_name(p, kind="path segment")
            candidate = self.workspace_root.joinpath(*parts)

        resolved = self._safe_realpath(candidate)

        if self._contains_symlink(candidate):
            # `resolved` is already the fully-realpath'd target (Path.resolve()
            # follows symlinks), so the containment check here doubles as the
            # "does this symlink escape the workspace" check.
            self._check_symlink(resolved, original=relative_path)
        else:
            self._assert_inside_root(resolved, original=relative_path)

        return resolved

    def assert_not_protected(self, path: Path) -> None:
        # Server-private children must remain unreachable through file tools.
        rel = path.relative_to(self.workspace_root)
        if ".workspace_mcp" in rel.parts or path.name in self.protected_files:
            raise ProtectedFileError(
                f"'{path.name}' is a protected server file and cannot be "
                "modified or deleted through the MCP tools.",
                path=str(path),
            )

    def relative_to_root(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.workspace_root))
        except ValueError:
            return str(path)

    # -- internals ----------------------------------------------------- #

    def _safe_realpath(self, candidate: Path) -> Path:
        """Resolve symlinks/`..` without requiring the path to exist.

        ``Path.resolve(strict=False)`` already does this correctly on
        modern Python (it resolves as much of the path as exists and
        normalizes the rest), so we simply delegate to it.
        """
        return candidate.resolve(strict=False)

    def _assert_inside_root(self, resolved: Path, *, original: str) -> None:
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise WorkspaceViolationError(
                "Resolved path escapes the configured workspace root.",
                path=original,
                resolved=str(resolved),
                workspace_root=str(self.workspace_root),
            ) from exc

    def _contains_symlink(self, candidate: Path) -> bool:
        """True if ``candidate`` or any of its existing ancestors (up to the
        workspace root) is itself a symlink. Must be called on the
        *unresolved* candidate path -- a resolved/realpath'd path can never
        report ``is_symlink() == True`` since resolution already follows
        symlinks to their target.
        """
        p = candidate
        while True:
            if p.is_symlink():
                return True
            if p == self.workspace_root or p.parent == p:
                return False
            p = p.parent

    def _check_symlink(self, resolved_target: Path, *, original: str) -> None:
        """Apply symlink policy given the fully-resolved (realpath) target."""
        try:
            resolved_target.relative_to(self.workspace_root)
        except ValueError as exc:
            raise SymlinkEscapeError(
                "This path is a symlink that resolves outside the "
                "workspace root; refusing to follow it.",
                path=original,
                target=str(resolved_target),
            ) from exc
        if not self.allow_symlinks:
            raise SymlinkEscapeError(
                "Symlinks are disabled by configuration "
                "(allow_symlinks=False), even though this one points "
                "inside the workspace.",
                path=original,
            )


def sanitize_project_name(name: str) -> str:
    """Stricter validator specifically for top-level project names."""
    return sanitize_name(name, kind="project name")
