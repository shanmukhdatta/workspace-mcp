"""Search utilities: glob-based filename search and text/content search."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import NotFoundError, SearchMatch
from workspace_mcp.utils.pathsec import PathValidator

# Hard safety cap independent of config, to keep a single find_text call
# from scanning gigabytes of binary data if a project is huge.
_MAX_BYTES_TO_SCAN_PER_FILE = 2 * 1024 * 1024  # 2 MB


class SearchService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator

    def _is_ignored(self, path: Path) -> bool:
        return any(part in self.settings.ignored_dirs for part in path.parts)

    def search_files(self, pattern: str, rel_root: str = ".", *, max_results: int = 200) -> list[str]:
        """Glob search for filenames matching ``pattern`` (e.g. ``"*.py"``)."""
        root = self.validator.resolve(rel_root)
        if not root.exists() or not root.is_dir():
            raise NotFoundError(f"No directory found at '{rel_root}'.", path=rel_root)

        results: list[str] = []
        for match in root.rglob(pattern):
            if self._is_ignored(match.relative_to(root)):
                continue
            if match.name in self.settings.ignored_files:
                continue
            results.append(self.validator.relative_to_root(match))
            if len(results) >= max_results:
                break
        return results

    def find_text(
        self,
        query: str,
        rel_root: str = ".",
        *,
        extensions: Optional[list[str]] = None,
        case_sensitive: bool = False,
        max_results: int = 200,
    ) -> list[SearchMatch]:
        """Grep-like search for ``query`` inside text files under ``rel_root``."""
        root = self.validator.resolve(rel_root)
        if not root.exists() or not root.is_dir():
            raise NotFoundError(f"No directory found at '{rel_root}'.", path=rel_root)

        ext_filter = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions} if extensions else None
        needle = query if case_sensitive else query.lower()

        matches: list[SearchMatch] = []
        for file_path in root.rglob("*"):
            if len(matches) >= max_results:
                break
            if not file_path.is_file() or file_path.is_symlink():
                continue
            if self._is_ignored(file_path.relative_to(root)):
                continue
            if file_path.name in self.settings.ignored_files:
                continue
            if ext_filter is not None and file_path.suffix.lower() not in ext_filter:
                continue
            try:
                if file_path.stat().st_size > _MAX_BYTES_TO_SCAN_PER_FILE:
                    continue
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # skip binaries / unreadable files silently

            haystack_lines = text.splitlines()
            for i, line in enumerate(haystack_lines, start=1):
                hay = line if case_sensitive else line.lower()
                if needle in hay:
                    matches.append(
                        SearchMatch(
                            path=self.validator.relative_to_root(file_path),
                            line_number=i,
                            line_text=line.strip()[:300],
                        )
                    )
                    if len(matches) >= max_results:
                        break
        return matches
