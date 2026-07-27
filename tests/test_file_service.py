from __future__ import annotations

import pytest

from workspace_mcp.models.schemas import (
    ConfirmationRequiredError,
    DuplicateFileError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedExtensionError,
)
from workspace_mcp.services.file_service import FileService
from workspace_mcp.config.settings import WorkspaceSettings


class TestCreateFile:
    def test_create_file_writes_content(self, file_service: FileService):
        info = file_service.create_file("app.py", "print('hi')\n")
        assert info.size_bytes > 0
        assert info.extension == ".py"

    def test_create_file_creates_parent_dirs(self, file_service: FileService):
        file_service.create_file("nested/deep/dir/app.py", "x = 1\n")
        text, _ = file_service.read_file("nested/deep/dir/app.py")
        assert text == "x = 1\n"

    def test_duplicate_create_without_overwrite_fails(self, file_service: FileService):
        file_service.create_file("app.py", "a")
        with pytest.raises(DuplicateFileError):
            file_service.create_file("app.py", "b")

    def test_duplicate_create_with_overwrite_succeeds(self, file_service: FileService):
        file_service.create_file("app.py", "a")
        info = file_service.create_file("app.py", "b", overwrite=True)
        text, _ = file_service.read_file("app.py")
        assert text == "b"

    def test_unsupported_extension_rejected(self, file_service: FileService):
        with pytest.raises(UnsupportedExtensionError):
            file_service.create_file("virus.exe", "MZ")

    def test_file_too_large_rejected(self, file_service: FileService):
        file_service.settings.max_file_size_bytes = 10
        with pytest.raises(FileTooLargeError):
            file_service.create_file("big.txt", "x" * 100)


class TestReadFile:
    def test_read_missing_file_raises_not_found(self, file_service: FileService):
        with pytest.raises(NotFoundError):
            file_service.read_file("nope.txt")

    def test_read_returns_content_and_info(self, file_service: FileService):
        file_service.create_file("a.txt", "hello\nworld\n")
        text, info = file_service.read_file("a.txt")
        assert text == "hello\nworld\n"
        assert info.line_count == 2


class TestWriteFile:
    def test_write_new_file_no_confirm_needed(self, file_service: FileService):
        file_service.write_file("new.txt", "content")
        text, _ = file_service.read_file("new.txt")
        assert text == "content"

    def test_write_existing_file_requires_confirm(self, file_service: FileService):
        file_service.create_file("existing.txt", "v1")
        with pytest.raises(ConfirmationRequiredError):
            file_service.write_file("existing.txt", "v2")
        file_service.write_file("existing.txt", "v2", confirm=True)
        text, _ = file_service.read_file("existing.txt")
        assert text == "v2"


class TestAppendFile:
    def test_append_to_missing_file_raises(self, file_service: FileService):
        with pytest.raises(NotFoundError):
            file_service.append_file("missing.txt", "x")

    def test_append_adds_to_end(self, file_service: FileService):
        file_service.create_file("log.txt", "line1\n")
        file_service.append_file("log.txt", "line2\n")
        text, _ = file_service.read_file("log.txt")
        assert text == "line1\nline2\n"


class TestUpdateFile:
    def test_find_replace(self, file_service: FileService):
        file_service.create_file("config.py", "DEBUG = True\n")
        file_service.update_file("config.py", find="True", replace="False")
        text, _ = file_service.read_file("config.py")
        assert text == "DEBUG = False\n"

    def test_find_not_present_raises(self, file_service: FileService):
        file_service.create_file("config.py", "DEBUG = True\n")
        with pytest.raises(NotFoundError):
            file_service.update_file("config.py", find="NOPE", replace="x")

    def test_full_rewrite(self, file_service: FileService):
        file_service.create_file("config.py", "old\n")
        file_service.update_file("config.py", new_content="new\n")
        text, _ = file_service.read_file("config.py")
        assert text == "new\n"


class TestMoveRenameDelete:
    def test_move_file(self, file_service: FileService):
        file_service.create_file("src.txt", "data")
        file_service.move_file("src.txt", "dest/moved.txt")
        text, _ = file_service.read_file("dest/moved.txt")
        assert text == "data"
        with pytest.raises(NotFoundError):
            file_service.read_file("src.txt")

    def test_rename_file(self, file_service: FileService):
        file_service.create_file("old.txt", "data")
        file_service.rename_file("old.txt", "new.txt")
        text, _ = file_service.read_file("new.txt")
        assert text == "data"

    def test_delete_requires_confirm(self, file_service: FileService):
        file_service.create_file("temp.txt", "x")
        with pytest.raises(ConfirmationRequiredError):
            file_service.delete_file("temp.txt")
        file_service.delete_file("temp.txt", confirm=True)
        with pytest.raises(NotFoundError):
            file_service.read_file("temp.txt")
