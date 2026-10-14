"""Project-level operations: create, delete, rename whole projects.

A "project" is simply a directory directly under the workspace root that
gets scaffolded with a conventional structure and starter documentation.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import (
    AlreadyExistsError,
    ConfirmationRequiredError,
    NotFoundError,
    ProjectInfo,
)
from workspace_mcp.services.directory_service import DirectoryService
from workspace_mcp.services.doc_service import DocService
from workspace_mcp.services.template_service import TemplateService
from workspace_mcp.utils.pathsec import PathValidator, sanitize_project_name

DEFAULT_STRUCTURE: list[str] = [
    "frontend",
    "backend",
    "database",
    "docker",
    "scripts",
    "tests",
    "docs",
    "assets",
    "config",
]

_GITIGNORE_TEMPLATE = """\
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Build output
dist/
build/

# Env / secrets
.env
.env.local

# Editor / OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# Logs
*.log
"""

_DOCKERFILE_TEMPLATE = """\
# TODO: replace with a real base image for this project.
FROM python:3.12-slim
WORKDIR /app
COPY . .
CMD ["echo", "Replace this Dockerfile with real build steps."]
"""

_DOCKER_COMPOSE_TEMPLATE = """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
"""


class ProjectService:
    def __init__(
        self,
        settings: WorkspaceSettings,
        validator: PathValidator,
        directory_service: DirectoryService,
        doc_service: DocService,
    ) -> None:
        self.settings = settings
        self.validator = validator
        self.directories = directory_service
        self.docs = doc_service

    def create_project(
        self,
        name: str,
        *,
        structure: Optional[list[str]] = None,
        description: str = "",
        include_docker: bool = True,
        template: Optional[str] = None,
        template_variables: Optional[dict[str, str]] = None,
    ) -> ProjectInfo:
        sanitize_project_name(name)
        if template:
            TemplateService(self.settings, self.validator).create(
                name, template, template_variables
            )
            from datetime import datetime, timezone
            dest = self.validator.resolve(name)
            return ProjectInfo(
                name=name,
                path=name,
                created=datetime.now(timezone.utc).isoformat(),
                structure=[p.name for p in dest.iterdir() if p.is_dir()],
            )
        project_path = self.validator.resolve(name)
        if project_path.exists():
            raise AlreadyExistsError(
                f"A project named '{name}' already exists in the workspace.", path=name
            )

        folders = structure if structure is not None else DEFAULT_STRUCTURE
        project_path.mkdir(parents=True)
        for folder in folders:
            self.directories.create_directory(f"{name}/{folder}")

        (project_path / ".gitignore").write_text(_GITIGNORE_TEMPLATE, encoding="utf-8")
        if include_docker:
            (project_path / "Dockerfile").write_text(_DOCKERFILE_TEMPLATE, encoding="utf-8")
            (project_path / "docker-compose.yml").write_text(_DOCKER_COMPOSE_TEMPLATE, encoding="utf-8")

        self.docs.generate_project_tree(name)
        self.docs.generate_readme(name, description=description, tech_stack=folders)
        self.docs.generate_cloud_log(
            name,
            goal=description or f"Scaffold the '{name}' project.",
            architecture_decisions=[f"Created default structure: {', '.join(folders)}"],
            files_created=[".gitignore"]
            + (["Dockerfile", "docker-compose.yml"] if include_docker else [])
            + ["README.md", "PROJECT_TREE.md"],
        )

        from datetime import datetime, timezone

        return ProjectInfo(
            name=name,
            path=self.validator.relative_to_root(project_path),
            created=datetime.now(timezone.utc).isoformat(),
            structure=folders,
        )

    def delete_project(self, name: str, *, confirm: bool = False) -> str:
        sanitize_project_name(name)
        project_path = self.validator.resolve(name)
        if not project_path.exists() or not project_path.is_dir():
            raise NotFoundError(f"No project named '{name}' exists.", path=name)
        if not confirm:
            raise ConfirmationRequiredError(
                f"Deleting project '{name}' requires confirm=True. This is "
                "irreversible and removes the entire project directory.",
                path=name,
            )
        shutil.rmtree(project_path)
        return name

    def rename_project(self, old_name: str, new_name: str, *, overwrite: bool = False) -> ProjectInfo:
        sanitize_project_name(old_name)
        sanitize_project_name(new_name)
        src = self.validator.resolve(old_name)
        dest = self.validator.resolve(new_name)
        if not src.exists() or not src.is_dir():
            raise NotFoundError(f"No project named '{old_name}' exists.", path=old_name)
        if dest.exists() and not overwrite:
            raise AlreadyExistsError(
                f"A project named '{new_name}' already exists.", path=new_name
            )
        src.replace(dest)

        from datetime import datetime, timezone

        structure = [
            p.name for p in dest.iterdir() if p.is_dir() and p.name not in self.settings.ignored_dirs
        ]
        return ProjectInfo(
            name=new_name,
            path=self.validator.relative_to_root(dest),
            created=datetime.now(timezone.utc).isoformat(),
            structure=structure,
        )
