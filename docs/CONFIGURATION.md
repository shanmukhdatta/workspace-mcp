# Configuration Guide

Configuration is resolved by `workspace_mcp.config.settings.load_settings()` in this priority order (highest wins):

1. **Environment variables**, prefixed `WORKSPACE_MCP_` (e.g. `WORKSPACE_MCP_WORKSPACE_ROOT`).
2. **`--workspace-root` CLI flag** (overrides just that one field, applied after file+env).
3. **Config file** (YAML or JSON), located via:
   - `--config <path>` CLI flag, or
   - `WORKSPACE_MCP_CONFIG_FILE` env var, or
   - `./workspace_mcp.config.yaml` / `./workspace_mcp.config.json` in the current directory.
4. **Hard-coded defaults** in `WorkspaceSettings`.

See `workspace_mcp.config.example.yaml` for a fully-commented example.

## All settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `workspace_root` | path | `~/AIProjects` | The single directory the server may read/write. |
| `max_file_size_bytes` | int | `5242880` (5 MB) | Hard cap on any single file write. |
| `allowed_extensions` | set[str] | ~40 common code/text extensions | Files with other extensions are rejected. Extensionless files (Dockerfile, LICENSE) are always allowed. |
| `ignored_files` | set[str] | `.DS_Store`, `Thumbs.db`, ... | Filenames skipped by `list_directory`/`search_files`/`find_text`. |
| `ignored_dirs` | set[str] | `__pycache__`, `.git`, `node_modules`, `.venv`, ... | Directories never listed or descended into by search/list operations (still creatable/writable directly by path). |
| `logging_dir` | path | `.workspace_mcp/logs` (under workspace root) | Where `operations.log` / `operations.jsonl` are written. |
| `backup_dir` | path | `.workspace_mcp/backups` | Reserved for future backup-on-overwrite (Phase 2). |
| `templates_dir` | path | `.workspace_mcp/templates` | Reserved for future named project templates (Phase 2). |
| `allow_symlinks` | bool | `false` | If true, symlinks that resolve *inside* the workspace are followed. Symlinks resolving *outside* are always rejected regardless. |
| `require_overwrite_confirmation` | bool | `true` | If true, overwrite/delete operations need `confirm=True`/`overwrite=True`. |
| `protected_files` | set[str] | server's own config filenames | Names that can never be targeted by write/delete tools. |

## Environment variable examples

```bash
export WORKSPACE_MCP_WORKSPACE_ROOT="/home/user/AIProjects"
export WORKSPACE_MCP_MAX_FILE_SIZE_BYTES=10485760
export WORKSPACE_MCP_ALLOW_SYMLINKS=false
export WORKSPACE_MCP_REQUIRE_OVERWRITE_CONFIRMATION=true
```

Pydantic Settings parses `set[str]`-typed fields like `allowed_extensions` from a JSON array string when passed via environment variable, e.g.:

```bash
export WORKSPACE_MCP_ALLOWED_EXTENSIONS='[".py", ".ts", ".md"]'
```

## Changing the workspace at runtime

The workspace root is fixed for the lifetime of one server process (it's baked into the `PathValidator` at startup). To point the AI at a different directory, restart the server with a different `--workspace-root`/config — this is intentional, since letting an MCP tool call itself change the sandbox boundary would defeat the sandbox.
