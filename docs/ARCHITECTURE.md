# Architecture Overview

## Layers

```
tools/          <-- thin @mcp.tool() wrappers; no business logic
services/       <-- business logic; raises WorkspaceError subclasses
utils/pathsec   <-- the ONLY place that resolves/validates filesystem paths
config/         <-- immutable settings, loaded once at startup
models/         <-- shared Pydantic schemas + exception hierarchy
logging/        <-- structured + human-readable operation logging
server.py       <-- wires all of the above into a FastMCP instance
```

Every arrow below is a "depends on", never the reverse — `utils` has no knowledge of `services`, `services` have no knowledge of `tools`, etc:

```
tools -> services -> utils/pathsec
tools -> logging
server.py -> config, utils, services, tools
```

## Why a single `PathValidator`?

Path traversal bugs are the single most common way a "sandboxed" filesystem tool stops being sandboxed. Rather than validating paths ad-hoc in each service method, every service is handed one `PathValidator` instance (constructed once, in `server.build_server()`, from the resolved `workspace_root`) and every filesystem-touching method starts with:

```python
path = self.validator.resolve(rel_path)
```

`resolve()` guarantees the returned `Path` is inside the workspace root or raises a typed `WorkspaceError`. See `utils/pathsec.py` docstring for the exact guarantees, and `tests/test_path_validation.py` for the adversarial test cases (traversal, absolute paths, NUL bytes, symlink escapes, reserved names).

## Why services return values / raise exceptions instead of dicts?

Keeping `services/*.py` exception-based (rather than returning `{"status": ..., ...}` dicts) means:

1. Services are usable directly from Python (tests, scripts, a future CLI) without needing to unpack a result envelope.
2. There is exactly one place — `tools/_common.py::run_tool` — that decides how errors are shown to an MCP client. Change the envelope shape once, and all 22 tools update.
3. `pytest.raises(SomeWorkspaceError)` reads more clearly than asserting on a dict's `error_code` key in every service-level test.

## Why FastMCP tools call a shared `run_tool()` helper?

Every tool function in `tools/*.py` is ~10 lines:

```python
@mcp.tool()
def create_file(path: str, content: str = "", overwrite: bool = False) -> dict[str, Any]:
    """..."""
    return run_tool(
        logger,
        operation="Created File",
        target_path=path,
        fn=lambda: file_service.create_file(path, content, overwrite=overwrite),
    )
```

`run_tool()`:
1. Starts a `Timer`.
2. Calls `fn()` inside `logger.track(...)`, which writes the JSON + text log line and re-raises on `WorkspaceError`.
3. Catches that re-raised error and shapes it into `{"status": "error", "error_code": ..., "message": ..., ...}`.
4. On success, wraps the return value into `{"status": "success", "data": ...}`.

This is why the docstring on each `@mcp.tool()` function is the *only* thing that differs meaningfully between tools — that docstring is what the MCP client (and the AI) sees as the tool's description and argument documentation, so it's written carefully for each tool.

## Data flow for `create_project`

```
AI calls create_project(name="TaskManager")
  -> tools/project_tools.py: create_project()
    -> services/project_service.py: ProjectService.create_project()
      -> utils/pathsec.py: sanitize_project_name(), validator.resolve()
      -> services/directory_service.py: create_directory() x9 (default structure)
      -> writes .gitignore, Dockerfile, docker-compose.yml
      -> services/doc_service.py: generate_project_tree(), generate_readme(), generate_cloud_log()
  <- ProjectInfo(name, path, created, structure)
  <- tools/_common.py: run_tool() wraps it as {"status": "success", "data": {...}}
  <- logging/logger.py: OperationLogger.track() has already written the log lines
```

## Extending the server

See `docs/EXTENSION_GUIDE.md` for a step-by-step guide to adding a new tool, and for the Phase 2 roadmap (terminal execution, Git integration, templates, backups).
