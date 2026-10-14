"""Parameterized project templates inside a protected server-owned registry."""

from __future__ import annotations

import re
from pathlib import Path

from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.models.schemas import AlreadyExistsError, NotFoundError, WorkspaceError
from workspace_mcp.utils.pathsec import PathValidator, sanitize_project_name, sanitize_name

# Built-ins are deliberately small starting points, not claims of complete applications.
BUILTINS = {
    "fastapi-react": {
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI(title='{{project_name}}')\n\n@app.get('/health')\ndef health():\n    return {'ok': True}\n",
        "backend/requirements.txt": "fastapi>=0.115\nuvicorn>=0.30\n",
        "frontend/package.json": '{"name":"{{project_slug}}","private":true,"scripts":{"dev":"vite --host 127.0.0.1"},"dependencies":{"react":"^18.3.1","react-dom":"^18.3.1","vite":"^5.4.0"}}\n',
        "README.md": "# {{project_name}}\n\nFastAPI backend + React starter. Add the frontend entry point before using the Vite script.\n",
    },
    "nextjs-tailwind": {
        "package.json": '{"name":"{{project_slug}}","private":true,"scripts":{"dev":"next dev","build":"next build"},"dependencies":{"next":"^15.0.0","react":"^19.0.0","react-dom":"^19.0.0","tailwindcss":"^4.0.0"}}\n',
        "app/page.tsx": "export default function Home() { return <main><h1>{{project_name}}</h1></main> }\n",
        "app/layout.tsx": "import type { ReactNode } from 'react';\nexport default function RootLayout({children}: {children: ReactNode}) { return <html lang='en'><body>{children}</body></html> }\n",
        "README.md": "# {{project_name}}\n\nNext.js starter. Configure Tailwind integration before styling.\n",
    },
    "rust-cli": {
        "Cargo.toml": '[package]\nname = "{{project_slug}}"\nversion = "0.1.0"\nedition = "2021"\n',
        "src/main.rs": 'fn main() { println!("Hello from {{project_name}}!"); }\n',
        "README.md": "# {{project_name}}\n\nRun using cargo run.\n",
    },
}


class TemplateService:
    def __init__(self, settings: WorkspaceSettings, validator: PathValidator) -> None:
        self.settings = settings
        self.validator = validator

    def list_templates(self) -> list[str]:
        custom = [
            p.name
            for p in self.settings.resolved_templates_dir().iterdir()
            if p.is_dir() and not p.is_symlink()
        ]
        return sorted(set(BUILTINS) | set(custom))

    def create(self, name: str, template: str, variables: dict[str, str] | None = None) -> dict:
        sanitize_project_name(name)
        sanitize_name(template, kind="template")
        dest = self.validator.resolve(name)
        if dest.exists():
            raise AlreadyExistsError("Project already exists.", path=name)
        vals = {"project_name": name, "project_slug": re.sub(r"[^a-z0-9_-]", "-", name.lower())}
        for key, val in (variables or {}).items():
            if (
                not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,40}", key)
                or not isinstance(val, str)
                or len(val) > 4000
            ):
                raise WorkspaceError("Invalid template parameter.")
            vals[key] = val
        registry = self.settings.resolved_templates_dir()
        folder = registry / template
        if template in BUILTINS:
            content = BUILTINS[template]
        elif (
            folder.is_dir()
            and not folder.is_symlink()
            and folder.resolve().is_relative_to(registry.resolve())
        ):
            content = {}
            for p in folder.rglob("*"):
                if p.is_symlink():
                    raise WorkspaceError("Symlink is forbidden inside templates.")
                if not p.is_file():
                    continue
                if len(content) >= 200:
                    raise WorkspaceError("Template has too many files.")
                if p.stat().st_size > self.settings.max_file_size_bytes:
                    raise WorkspaceError("Template file too large.")
                content[p.relative_to(folder).as_posix()] = p.read_text(encoding="utf-8")
        else:
            raise NotFoundError("Unknown template.", template=template)

        def render(s: str) -> str:
            def replace(m: re.Match[str]) -> str:
                key = m.group(1)
                if key not in vals:
                    raise WorkspaceError("Missing template parameter.", parameter=key)
                return vals[key]

            return re.sub(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", replace, s)

        rendered = {}
        for rel, value in content.items():
            rel = render(rel)
            path = self.validator.resolve(f"{name}/{rel}")
            if not path.is_relative_to(dest) or path == dest:
                raise WorkspaceError("Unsafe template path.")
            rendered[path] = render(value)
            if len(rendered[path].encode()) > self.settings.max_file_size_bytes:
                raise WorkspaceError("Rendered template file too large.")
        # Perform all validation before the first file is written.
        dest.mkdir()
        try:
            for path, value in rendered.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value, encoding="utf-8")
        except Exception:
            import shutil

            shutil.rmtree(dest)
            raise
        return {"project": name, "template": template, "files": len(rendered)}
