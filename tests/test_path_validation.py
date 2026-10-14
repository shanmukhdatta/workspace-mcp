from __future__ import annotations

import os
from pathlib import Path

import pytest

from workspace_mcp.models.schemas import (
    InvalidPathError,
    PathTraversalError,
    ProtectedFileError,
    SymlinkEscapeError,
    WorkspaceViolationError,
)
from workspace_mcp.utils.pathsec import PathValidator, sanitize_name


class TestResolveHappyPath:
    def test_resolve_simple_relative_path(self, validator: PathValidator):
        resolved = validator.resolve("MyApp/backend/main.py")
        assert resolved == validator.workspace_root / "MyApp" / "backend" / "main.py"

    def test_resolve_root(self, validator: PathValidator):
        assert validator.resolve(".") == validator.workspace_root
        assert validator.resolve("") == validator.workspace_root

    def test_backslash_separators_are_normalized(self, validator: PathValidator):
        resolved = validator.resolve("MyApp\\backend\\main.py")
        assert resolved == validator.workspace_root / "MyApp" / "backend" / "main.py"


class TestPathTraversal:
    def test_dotdot_is_rejected(self, validator: PathValidator):
        with pytest.raises(PathTraversalError):
            validator.resolve("../escape.py")

    def test_nested_dotdot_is_rejected(self, validator: PathValidator):
        with pytest.raises(PathTraversalError):
            validator.resolve("MyApp/../../escape.py")

    def test_absolute_posix_path_is_rejected(self, validator: PathValidator):
        with pytest.raises(WorkspaceViolationError):
            validator.resolve("/etc/passwd")

    def test_absolute_windows_path_is_rejected(self, validator: PathValidator):
        with pytest.raises(WorkspaceViolationError):
            validator.resolve("C:\\Windows\\System32\\config.sys")

    def test_nul_byte_is_rejected(self, validator: PathValidator):
        with pytest.raises(InvalidPathError):
            validator.resolve("MyApp/file\x00.py")


class TestSymlinkEscape:
    def test_symlink_pointing_outside_workspace_is_rejected(
        self, validator: PathValidator, tmp_path: Path
    ):
        outside_target = tmp_path / "outside.txt"
        outside_target.write_text("secret")
        link = validator.workspace_root / "link_to_outside.txt"
        try:
            os.symlink(outside_target, link)
        except OSError as e:
            pytest.skip(f"Symlinks not supported/permitted: {e}")
        with pytest.raises(SymlinkEscapeError):
            validator.resolve("link_to_outside.txt")

    def test_symlink_inside_workspace_rejected_when_disabled(self, validator: PathValidator):
        target_dir = validator.workspace_root / "real_dir"
        target_dir.mkdir()
        link = validator.workspace_root / "link_inside.txt"
        try:
            os.symlink(target_dir, link)
        except OSError as e:
            pytest.skip(f"Symlinks not supported/permitted: {e}")
        # allow_symlinks defaults to False in the fixture
        with pytest.raises(SymlinkEscapeError):
            validator.resolve("link_inside.txt")

    def test_symlink_inside_workspace_allowed_when_enabled(self, validator: PathValidator):
        validator.allow_symlinks = True
        target_dir = validator.workspace_root / "real_dir2"
        target_dir.mkdir()
        link = validator.workspace_root / "link_inside2.txt"
        try:
            os.symlink(target_dir, link)
        except OSError as e:
            pytest.skip(f"Symlinks not supported/permitted: {e}")
        resolved = validator.resolve("link_inside2.txt")
        assert resolved.exists()


class TestProtectedFiles:
    def test_protected_file_is_flagged(self, validator: PathValidator):
        protected_path = validator.workspace_root / "workspace_mcp.config.json"
        protected_path.write_text("{}")
        with pytest.raises(ProtectedFileError):
            validator.assert_not_protected(protected_path)


class TestSanitizeName:
    @pytest.mark.parametrize("name", ["..", ".", "", "a/b", "a\\b", "CON", "con.txt"])
    def test_rejects_invalid_names(self, name: str):
        with pytest.raises(InvalidPathError):
            sanitize_name(name)

    @pytest.mark.parametrize("name", ["MyApp", "my-app_2.0", "file.name.ext", "Expense Tracker"])
    def test_accepts_valid_names(self, name: str):
        assert sanitize_name(name) == name

    def test_rejects_unsupported_characters(self):
        with pytest.raises(InvalidPathError):
            sanitize_name("bad;name")


class TestRelativeToRoot:
    def test_relative_to_root_roundtrip(self, validator: PathValidator):
        resolved = validator.resolve("MyApp/backend/main.py")
        assert validator.relative_to_root(resolved) == os.path.join("MyApp", "backend", "main.py")
