from __future__ import annotations

import pytest

from workspace_mcp.models.schemas import (
    AlreadyExistsError,
    ConfirmationRequiredError,
    NotFoundError,
)
from workspace_mcp.services.project_service import DEFAULT_STRUCTURE, ProjectService


class TestCreateProject:
    def test_create_project_default_structure(self, project_service: ProjectService):
        info = project_service.create_project("ExpenseTracker")
        assert info.name == "ExpenseTracker"
        assert set(info.structure) == set(DEFAULT_STRUCTURE)

    def test_create_project_generates_docs(self, project_service: ProjectService, settings):
        project_service.create_project("ExpenseTracker")
        project_dir = settings.workspace_root / "ExpenseTracker"
        assert (project_dir / "README.md").exists()
        assert (project_dir / "CLOUD.md").exists()
        assert (project_dir / "PROJECT_TREE.md").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "Dockerfile").exists()
        assert (project_dir / "docker-compose.yml").exists()

    def test_create_project_custom_structure(self, project_service: ProjectService, settings):
        project_service.create_project("Minimal", structure=["src", "tests"])
        project_dir = settings.workspace_root / "Minimal"
        assert (project_dir / "src").is_dir()
        assert (project_dir / "tests").is_dir()
        assert not (project_dir / "frontend").exists()

    def test_duplicate_project_raises(self, project_service: ProjectService):
        project_service.create_project("Dup")
        with pytest.raises(AlreadyExistsError):
            project_service.create_project("Dup")

    def test_no_docker_option(self, project_service: ProjectService, settings):
        project_service.create_project("NoDocker", include_docker=False)
        project_dir = settings.workspace_root / "NoDocker"
        assert not (project_dir / "Dockerfile").exists()


class TestDeleteProject:
    def test_delete_requires_confirm(self, project_service: ProjectService):
        project_service.create_project("ToDelete")
        with pytest.raises(ConfirmationRequiredError):
            project_service.delete_project("ToDelete")
        project_service.delete_project("ToDelete", confirm=True)
        with pytest.raises(NotFoundError):
            project_service.delete_project("ToDelete", confirm=True)

    def test_delete_missing_project_raises_not_found(self, project_service: ProjectService):
        with pytest.raises(NotFoundError):
            project_service.delete_project("Nonexistent", confirm=True)


class TestRenameProject:
    def test_rename_moves_directory(self, project_service: ProjectService, settings):
        project_service.create_project("OldName")
        info = project_service.rename_project("OldName", "NewName")
        assert info.name == "NewName"
        assert (settings.workspace_root / "NewName").exists()
        assert not (settings.workspace_root / "OldName").exists()

    def test_rename_missing_project_raises(self, project_service: ProjectService):
        with pytest.raises(NotFoundError):
            project_service.rename_project("Ghost", "Other")

    def test_rename_onto_existing_without_overwrite_raises(self, project_service: ProjectService):
        project_service.create_project("A")
        project_service.create_project("B")
        with pytest.raises(AlreadyExistsError):
            project_service.rename_project("A", "B")
