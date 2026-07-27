"""End-to-end tests that go through the actual FastMCP tool layer
(`server.build_server` + `mcp.call_tool`) rather than the services directly,
to make sure errors surface as structured JSON, never as raw exceptions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.server import build_server


@pytest.fixture()
def mcp(tmp_path: Path):
    root = tmp_path / "AIProjects"
    root.mkdir()
    settings = WorkspaceSettings(workspace_root=root)
    return build_server(settings)


async def _call(mcp, name: str, args: dict):
    _, structured = await mcp.call_tool(name, args)
    return structured


class TestSuccessEnvelope:
    @pytest.mark.asyncio
    async def test_create_project_success_shape(self, mcp):
        result = await _call(mcp, "create_project", {"name": "Demo"})
        assert result["status"] == "success"
        assert result["operation"] == "Create Project"
        assert "duration_ms" in result
        assert result["data"]["name"] == "Demo"

    @pytest.mark.asyncio
    async def test_create_file_then_read(self, mcp):
        await _call(mcp, "create_project", {"name": "Demo"})
        await _call(mcp, "create_file", {"path": "Demo/app.py", "content": "x = 1\n"})
        result = await _call(mcp, "read_file", {"path": "Demo/app.py"})
        assert result["status"] == "success"
        assert result["data"]["content"] == "x = 1\n"


class TestErrorEnvelope:
    @pytest.mark.asyncio
    async def test_path_traversal_returns_structured_error(self, mcp):
        result = await _call(mcp, "create_file", {"path": "../evil.py", "content": "x"})
        assert result["status"] == "error"
        assert result["error_code"] == "PATH_TRAVERSAL"
        assert "message" in result

    @pytest.mark.asyncio
    async def test_missing_file_returns_structured_error(self, mcp):
        result = await _call(mcp, "read_file", {"path": "ghost.txt"})
        assert result["status"] == "error"
        assert result["error_code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_duplicate_project_returns_structured_error(self, mcp):
        await _call(mcp, "create_project", {"name": "Demo"})
        result = await _call(mcp, "create_project", {"name": "Demo"})
        assert result["status"] == "error"
        assert result["error_code"] == "ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_delete_without_confirm_returns_structured_error(self, mcp):
        await _call(mcp, "create_project", {"name": "Demo"})
        result = await _call(mcp, "delete_project", {"name": "Demo"})
        assert result["status"] == "error"
        assert result["error_code"] == "CONFIRMATION_REQUIRED"

    @pytest.mark.asyncio
    async def test_unsupported_extension_returns_structured_error(self, mcp):
        await _call(mcp, "create_project", {"name": "Demo"})
        result = await _call(
            mcp, "create_file", {"path": "Demo/virus.exe", "content": "MZ"}
        )
        assert result["status"] == "error"
        assert result["error_code"] == "UNSUPPORTED_EXTENSION"


class TestValidationTools:
    @pytest.mark.asyncio
    async def test_validate_workspace(self, mcp):
        result = await _call(mcp, "validate_workspace", {})
        assert result["status"] == "success"
        assert result["data"]["exists"] is True

    @pytest.mark.asyncio
    async def test_validate_path_safe(self, mcp):
        result = await _call(mcp, "validate_path", {"path": "Demo/app.py"})
        assert result["status"] == "success"
        assert result["data"]["exists"] is False

    @pytest.mark.asyncio
    async def test_validate_path_traversal_reported_as_error(self, mcp):
        result = await _call(mcp, "validate_path", {"path": "../escape.py"})
        assert result["status"] == "error"
        assert result["error_code"] == "PATH_TRAVERSAL"
