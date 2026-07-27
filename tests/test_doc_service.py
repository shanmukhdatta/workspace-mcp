from __future__ import annotations

import pytest

from workspace_mcp.models.schemas import NotFoundError
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.services.file_service import FileService


@pytest.fixture()
def scaffolded_project(directory_service: DirectoryService, file_service: FileService) -> str:
    directory_service.create_directory("Proj/backend")
    directory_service.create_directory("Proj/frontend")
    file_service.create_file("Proj/backend/main.py", "print('hi')\n")
    return "Proj"


class TestGenerateProjectTree:
    def test_generates_tree_file(self, doc_service: DocService, scaffolded_project: str, settings):
        rel = doc_service.generate_project_tree(scaffolded_project)
        tree_path = settings.workspace_root / rel
        content = tree_path.read_text()
        assert "backend" in content
        assert "frontend" in content
        assert "main.py" in content

    def test_missing_project_raises(self, doc_service: DocService):
        with pytest.raises(NotFoundError):
            doc_service.generate_project_tree("DoesNotExist")


class TestGenerateReadme:
    def test_readme_contains_all_sections(
        self, doc_service: DocService, scaffolded_project: str, settings
    ):
        rel = doc_service.generate_readme(
            scaffolded_project,
            description="An expense tracker.",
            features=["Track expenses", "Export CSV"],
            tech_stack=["FastAPI", "React"],
        )
        content = (settings.workspace_root / rel).read_text()
        for heading in [
            "## Features",
            "## Folder Structure",
            "## Installation",
            "## Usage",
            "## Dependencies",
            "## Configuration",
            "## Tech Stack",
            "## Future Improvements",
            "## License",
        ]:
            assert heading in content
        assert "An expense tracker." in content
        assert "Track expenses" in content


class TestGenerateCloudLog:
    def test_cloud_log_contains_all_sections(
        self, doc_service: DocService, scaffolded_project: str, settings
    ):
        rel = doc_service.generate_cloud_log(
            scaffolded_project,
            goal="Build an expense tracker",
            architecture_decisions=["Used FastAPI for backend"],
            files_created=["backend/main.py"],
        )
        content = (settings.workspace_root / rel).read_text()
        for heading in [
            "## Project Goal",
            "## Architecture Decisions",
            "## Folder Structure",
            "## Files Created",
            "## Files Updated",
            "## Implementation Notes",
            "## Important Decisions",
            "## Known Limitations",
            "## Future Work",
            "## Generation Timestamp",
        ]:
            assert heading in content
        assert "Build an expense tracker" in content
        assert "Used FastAPI for backend" in content
