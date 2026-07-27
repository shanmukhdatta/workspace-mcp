from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.services.file_service import FileService
from workspace_mcp.services.project_service import ProjectService
from workspace_mcp.services.search_service import SearchService
from workspace_mcp.utils.pathsec import PathValidator


@pytest.fixture()
def workspace_root(tmp_path: Path) -> Path:
    root = tmp_path / "AIProjects"
    root.mkdir()
    return root


@pytest.fixture()
def settings(workspace_root: Path) -> WorkspaceSettings:
    s = WorkspaceSettings(
        workspace_root=workspace_root,
        require_overwrite_confirmation=True,
    )
    s.ensure_directories()
    return s


@pytest.fixture()
def validator(settings: WorkspaceSettings) -> PathValidator:
    return PathValidator(
        settings.workspace_root,
        allow_symlinks=settings.allow_symlinks,
        protected_files=settings.protected_files,
    )


@pytest.fixture()
def directory_service(settings: WorkspaceSettings, validator: PathValidator) -> DirectoryService:
    return DirectoryService(settings, validator)


@pytest.fixture()
def file_service(settings: WorkspaceSettings, validator: PathValidator) -> FileService:
    return FileService(settings, validator)


@pytest.fixture()
def doc_service(settings: WorkspaceSettings, validator: PathValidator) -> DocService:
    return DocService(settings, validator)


@pytest.fixture()
def search_service(settings: WorkspaceSettings, validator: PathValidator) -> SearchService:
    return SearchService(settings, validator)


@pytest.fixture()
def project_service(
    settings: WorkspaceSettings,
    validator: PathValidator,
    directory_service: DirectoryService,
    doc_service: DocService,
) -> ProjectService:
    return ProjectService(settings, validator, directory_service, doc_service)
