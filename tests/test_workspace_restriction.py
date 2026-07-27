from __future__ import annotations

from pathlib import Path

import pytest

from workspace_mcp.models.schemas import PathTraversalError, WorkspaceViolationError
from workspace_mcp.services.file_service import FileService
from workspace_mcp.utils.pathsec import PathValidator


def test_two_sibling_workspaces_cannot_see_each_other(tmp_path: Path):
    ws_a = tmp_path / "ws_a"
    ws_b = tmp_path / "ws_b"
    ws_a.mkdir()
    ws_b.mkdir()

    validator_a = PathValidator(ws_a)
    (ws_b / "secret.txt").write_text("nope")

    # Even a crafted relative path can't reach ws_b from ws_a's validator,
    # because absolute-looking components are rejected and traversal is too.
    with pytest.raises((PathTraversalError, WorkspaceViolationError)):
        validator_a.resolve(f"../{ws_b.name}/secret.txt")


def test_file_service_cannot_write_outside_workspace(file_service: FileService):
    with pytest.raises(PathTraversalError):
        file_service.create_file("../outside.txt", "content")
