# Developer Guide

## Setting up for development

```bash
git clone <this-repo> workspace-mcp
cd workspace-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest                     # full suite
pytest -k path_validation  # just the security tests
pytest -v                  # verbose, one line per test
```

The suite (`tests/`) covers:

- `test_path_validation.py` — traversal, absolute paths, NUL bytes, symlink escapes, reserved names, sanitize_name()
- `test_workspace_restriction.py` — cross-workspace isolation
- `test_file_service.py` — create/read/write/append/update/move/rename/delete, size + extension limits
- `test_directory_service.py` — create/list/delete, hidden-entry filtering, root-deletion guard
- `test_project_service.py` — scaffolding, custom structure, duplicate/rename/delete flows
- `test_doc_service.py` — README/CLOUD.md/PROJECT_TREE.md content
- `test_search_service.py` — glob search, text search, extension filters, case sensitivity
- `test_error_handling.py` — end-to-end through the real FastMCP tool layer (`mcp.call_tool`), asserting the JSON error envelope shape

## Code style

- Format with `black` (line length 100, configured in `pyproject.toml`): `black src tests`
- Type-check with `mypy`: `mypy src`
- Every public function/class has a docstring; keep that up whenever you add one.

## Project conventions

- **Never touch the filesystem without going through `PathValidator.resolve()`.** If you're writing a new service method and you're tempted to do `Path(workspace_root) / rel_path` directly, don't — use `self.validator.resolve(rel_path)` instead.
- **Raise, don't return, errors from services.** Use the existing exception hierarchy in `models/schemas.py` (`WorkspaceError` subclasses) or add a new subclass if none fits — don't invent a new dict-based error shape.
- **Tools stay thin.** A `@mcp.tool()` function should be a docstring plus one `run_tool(...)` call. If you find yourself writing `if`/`try` logic inside a tool function, that logic belongs in the service layer instead.
- **Every destructive operation needs a `confirm`/`overwrite` parameter** gated by `settings.require_overwrite_confirmation`, following the pattern in `file_service.delete_file` / `write_file`.
- **Log everything.** Wrap new service calls in `logger.track(operation_name, target_path)` via `run_tool()` — don't call `print()` or the stdlib logger directly from tools/services.

## Adding a new dependency

Add it to `[project.dependencies]` (or `[project.optional-dependencies].dev`) in `pyproject.toml`, then `pip install -e .` again.

## Debugging a running server

Logs are always written to `<workspace_root>/.workspace_mcp/logs/operations.log` (human-readable) and `operations.jsonl` (structured), regardless of which MCP client is driving the server — tail them in another terminal while testing:

```bash
tail -f ~/AIProjects/.workspace_mcp/logs/operations.log
```

## Manually exercising a tool without an MCP client

```python
import asyncio
from workspace_mcp.config.settings import WorkspaceSettings
from workspace_mcp.server import build_server

settings = WorkspaceSettings(workspace_root="/tmp/test-workspace")
mcp = build_server(settings)

async def main():
    _, result = await mcp.call_tool("create_project", {"name": "Demo"})
    print(result)

asyncio.run(main())
```
