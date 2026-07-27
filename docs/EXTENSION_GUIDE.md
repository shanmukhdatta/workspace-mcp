# Extension Guide

This server is Phase 1 of a larger AI Development Workspace project. It was deliberately layered (`config → utils/pathsec → services → tools → server`) so later phases can be added without reworking existing code. This guide covers both "how to add a tool today" and the intended shape of future phases.

## Adding a brand-new tool to an existing category

Example: adding a `copy_file` tool alongside `move_file`.

1. **Service method** (`services/file_service.py`): add `copy_file(self, src_rel, dest_rel, *, overwrite=False) -> FileInfo`, following the same pattern as `move_file` (resolve both paths, check protection/overwrite, do the OS operation, return `self._info(dest)`). Raise existing `WorkspaceError` subclasses; add a new one to `models/schemas.py` only if none fits.
2. **Tool wrapper** (`tools/file_tools.py`): add
   ```python
   @mcp.tool()
   def copy_file(source_path: str, destination_path: str, overwrite: bool = False) -> dict[str, Any]:
       """Copy a file to a new location within the workspace, leaving the original in place.

       Args:
           source_path: Path to copy from, relative to the workspace root.
           destination_path: Path to copy to, relative to the workspace root.
           overwrite: If True, replace an existing file at the destination.
       """
       return run_tool(
           logger,
           operation="Copy File",
           target_path=f"{source_path} -> {destination_path}",
           fn=lambda: file_service.copy_file(source_path, destination_path, overwrite=overwrite),
       )
   ```
3. **Test** (`tests/test_file_service.py`): add a `TestCopyFile` class exercising success + `NotFoundError`/`DuplicateFileError` paths.
4. Nothing else changes — `server.py` already registers all tools in `file_tools.register(...)`, logging/error-envelope handling comes for free from `run_tool()`.

## Adding a brand-new category of tools

1. Create `services/<name>_service.py` with a class taking `(settings, validator)` in `__init__`, same as every existing service.
2. Create `tools/<name>_tools.py` with a `register(mcp, <name>_service, logger)` function containing your `@mcp.tool()` functions.
3. In `server.py::build_server()`, instantiate the service and call `<name>_tools.register(mcp, <name>_service, logger)` alongside the existing registrations.
4. Add a test module under `tests/`.

## Roadmap: future phases

### Phase 2 — Terminal execution
A `TerminalService` that runs allow-listed commands (e.g. `pip install`, `npm install`, `pytest`) with the working directory locked to a path inside the workspace (reuse `PathValidator.resolve()` for the cwd), streaming output back through a new `run_command` tool. Needs its own confirmation/allow-list config (`allowed_commands`, `command_timeout_seconds`) in `WorkspaceSettings`.

### Phase 2 — Git integration
A `GitService` wrapping `git init/add/commit/branch/diff/log`, again scoped to a single project directory inside the workspace. Should reuse `OperationLogger` for an auditable commit history separate from git's own log.

### Phase 2 — Project templates
`templates_dir` already exists in configuration but is unused. Intended shape: `create_project(..., template="fastapi-react")` copies a pre-built folder from `templates_dir/fastapi-react/` instead of the built-in default structure, with placeholder substitution (e.g. `{{project_name}}`) applied to file contents during the copy.

### Phase 2 — Backups on overwrite/delete
`backup_dir` already exists in configuration but is unused. Intended shape: before `write_file`/`delete_file` mutate an existing file, copy the current content to `backup_dir/<timestamp>/<relative_path>` so destructive operations are recoverable even after `confirm=true`.

### Phase 3 — Project memory / multi-agent workflows
A `MemoryService` persisting structured facts about a project (decisions, TODOs, architecture notes) separately from `CLOUD.md`'s prose log, queryable by future planning/multi-agent tools. Should live under `.workspace_mcp/memory/<project>.json`, mirroring how `logging_dir` is organized today.

### Phase 3 — Plugins
A `plugins/` entry-point mechanism (Python `entry_points` in `pyproject.toml`) letting third parties add `tools/*.py`-shaped modules that `server.py` discovers and registers dynamically, instead of requiring a fork of this repo.

None of the above require changing `utils/pathsec.py`, `models/schemas.py`, `logging/logger.py`, or the `run_tool()` envelope — that stability is the point of the layered design.
