# CLOUD.md — AI Work Log

> This document explains exactly what was generated for the `workspace-mcp` server itself and why.

## Project Goal

Build a production-ready Phase-1 MCP server that lets an MCP-compatible AI assistant create and manage software projects directly on the local filesystem, eliminating the need for ZIP-file downloads, while being extensible for future phases (terminal execution, Git integration, project memory, plugins, multi-agent workflows).

## Architecture Decisions

- **Layered architecture** (`config → utils/pathsec → services → tools → server`) so security logic lives in exactly one place (`utils/pathsec.py`) and every service/tool routes through it — there is no code path that touches the filesystem without going through `PathValidator.resolve()`.
- **Services vs. tools split**: `services/*.py` contain pure business logic and raise typed `WorkspaceError` subclasses; `tools/*.py` are thin `@mcp.tool()` wrappers that catch those exceptions once (via `tools/_common.py::run_tool`) and convert them into a uniform JSON envelope (`status`, `operation`, `target_path`, `duration_ms`, `data` or `error_code`/`message`). This means adding a new tool never requires re-implementing error handling.
- **Pydantic Settings for configuration** (`config/settings.py`), layering hard-coded defaults → optional YAML/JSON file → `WORKSPACE_MCP_*` environment variables, so the same server binary works unchanged across dev/CI/production.
- **Path security via `Path.resolve(strict=False)` + `relative_to()`**, not string-prefix matching, because prefix checks are trivially defeated by `..` sequences and symlinks. Symlinks are detected on the *unresolved* candidate path (walking up to the workspace root) since a fully-resolved path can never itself report as a symlink.
- **Confirmation-gated destructive operations**: overwrite (`write_file`, `create_file` without `overwrite=True`) and delete (`delete_file`, `delete_directory`, `delete_project`) all require an explicit `confirm=True`/`overwrite=True` flag by default, controlled by `require_overwrite_confirmation`.
- **Dual logging**: a JSON-lines file (`operations.jsonl`) for machine consumption and a human-readable text log (`operations.log`) in the exact format requested (`[timestamp] Operation | Path | Status | Duration`), both written from a single `OperationLogger.track()` context manager so every tool gets identical logging for free.

## Folder Structure

```
workspace-mcp/
├── src/workspace_mcp/
│   ├── server.py
│   ├── config/settings.py
│   ├── models/schemas.py
│   ├── utils/pathsec.py
│   ├── logging/logger.py
│   ├── services/
│   │   ├── project_service.py
│   │   ├── directory_service.py
│   │   ├── file_service.py
│   │   ├── search_service.py
│   │   └── doc_service.py
│   └── tools/
│       ├── _common.py
│       ├── project_tools.py
│       ├── directory_tools.py
│       ├── file_tools.py
│       ├── search_tools.py
│       ├── doc_tools.py
│       └── validation_tools.py
├── tests/
├── docs/
└── examples/
```

## Files Created

- `src/workspace_mcp/**` — full server implementation (config, models, utils, logging, services, tools, server.py)
- `tests/**` — conftest.py + 8 test modules (path validation, workspace restriction, file/directory/project/doc/search services, end-to-end error handling)
- `pyproject.toml`, `workspace_mcp.config.example.yaml`
- `docs/**` — Install, Quick Start, Configuration, Client Config, Developer Guide, API, Architecture, Extension Guide
- `examples/**` — Claude Desktop config JSON, sample prompts
- `README.md`, `CLOUD.md`, `PROJECT_TREE.md`, `.gitignore`

## Files Updated

- `utils/pathsec.py` — fixed symlink-detection logic mid-development: the initial implementation checked `resolved.is_symlink()` *after* calling `Path.resolve()`, which always returns `False` because resolution already follows symlinks to their target. Fixed by detecting symlinks on the *unresolved* candidate path (and its ancestors) before resolution, then applying policy to the resolved target.

## Implementation Notes

- All 22 MCP tools were exercised through the **real** `FastMCP.call_tool()` API (not just unit-tested service calls) to confirm the end-to-end JSON envelope, including a live path-traversal rejection and a confirmation-gated overwrite.
- Extensionless files (`Dockerfile`, `LICENSE`, etc.) are always allowed regardless of `allowed_extensions`, since the spec's own example project structure includes them.
- `update_file` supports two mutually exclusive modes: literal `find`/`replace` (bounded by `count`) or a full `new_content` rewrite, covering both small edits and full regenerations.
- `find_text` caps per-file scan size at 2 MB and silently skips undecodable (binary) files rather than erroring, so a single large binary asset can't break a project-wide text search.

## Important Decisions

- Filenames are restricted to a conservative allow-list (letters, numbers, space, `. - _ ( ) [ ]`) and Windows-reserved device names (`CON`, `NUL`, `COM1`, ...) are rejected on every platform, so projects generated on Linux remain portable to Windows.
- The workspace root itself can never be deleted through `delete_directory`, even with `confirm=True`, as a hard safety backstop independent of the confirmation flag.

## Known Limitations

- `read_file` only supports UTF-8 text files; binary file read/write is out of scope for Phase 1.
- No file-versioning/backup-on-overwrite yet, even though `backup_dir` is already part of the configuration schema — the directory is created but not yet used. This is called out explicitly for Phase 2.
- No terminal/process-execution tools, Git tools, or template-directory-backed scaffolds yet.

## Future Work

- Wire `backup_dir` into `write_file`/`delete_file` so overwritten/deleted content is preserved for recovery.
- Add a `templates/` mechanism so `create_project` can scaffold from named templates instead of only the built-in default structure.
- Phase 2: terminal execution tools, Git integration, project "memory", plugin system, multi-agent workflows (see `docs/EXTENSION_GUIDE.md`).

## Generation Timestamp

2026-07-27
