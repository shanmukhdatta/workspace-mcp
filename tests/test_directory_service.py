from __future__ import annotations

import pytest

from workspace_mcp.models.schemas import (
    AlreadyExistsError,
    ConfirmationRequiredError,
    NotFoundError,
)
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.services.file_service import FileService


class TestCreateDirectory:
    def test_create_directory_creates_nested_path(self, directory_service: DirectoryService):
        rel = directory_service.create_directory("a/b/c")
        assert rel.replace("\\", "/") == "a/b/c"

    def test_create_directory_exist_ok_true_is_idempotent(
        self, directory_service: DirectoryService
    ):
        directory_service.create_directory("a")
        directory_service.create_directory("a")  # should not raise

    def test_create_directory_exist_ok_false_raises_if_present(
        self, directory_service: DirectoryService
    ):
        directory_service.create_directory("a")
        with pytest.raises(AlreadyExistsError):
            directory_service.create_directory("a", exist_ok=False)


class TestListDirectory:
    def test_list_directory_returns_entries(
        self, directory_service: DirectoryService, file_service: FileService
    ):
        directory_service.create_directory("proj/sub")
        file_service.create_file("proj/readme.txt", "hi")
        entries = directory_service.list_directory("proj")
        names = {e.name for e in entries}
        assert names == {"sub", "readme.txt"}

    def test_list_missing_directory_raises(self, directory_service: DirectoryService):
        with pytest.raises(NotFoundError):
            directory_service.list_directory("does/not/exist")

    def test_hidden_entries_excluded_by_default(self, directory_service: DirectoryService):
        directory_service.create_directory(".hidden")
        directory_service.create_directory("visible")
        entries = directory_service.list_directory(".")
        names = {e.name for e in entries}
        assert "visible" in names
        assert ".hidden" not in names


class TestDeleteDirectory:
    def test_delete_requires_confirm(self, directory_service: DirectoryService):
        directory_service.create_directory("to_delete")
        with pytest.raises(ConfirmationRequiredError):
            directory_service.delete_directory("to_delete")
        directory_service.delete_directory("to_delete", confirm=True)
        with pytest.raises(NotFoundError):
            directory_service.list_directory("to_delete")

    def test_cannot_delete_workspace_root(self, directory_service: DirectoryService):
        with pytest.raises(ConfirmationRequiredError):
            directory_service.delete_directory(".", confirm=True)
