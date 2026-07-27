# API Documentation — MCP Tools

All 22 tools return a uniform JSON envelope:

**Success:**
```json
{
  "status": "success",
  "operation": "Created File",
  "target_path": "MyApp/backend/main.py",
  "duration_ms": 1.23,
  "data": { "...": "tool-specific payload" }
}
```

**Error:**
```json
{
  "status": "error",
  "operation": "Create File",
  "target_path": "../evil.py",
  "message": "Path traversal ('..') is not permitted.",
  "error_code": "PATH_TRAVERSAL",
  "duration_ms": 0.4
}
```

Every path parameter is **relative to the configured workspace root** — absolute paths and `..` are always rejected (`error_code: PATH_TRAVERSAL` / `WORKSPACE_VIOLATION`). See `error_code` values at the bottom of this document.

---

## Project Tools

### `create_project`
Create a new project with a conventional folder structure (`frontend`, `backend`, `database`, `docker`, `scripts`, `tests`, `docs`, `assets`, `config` by default) plus `.gitignore`, `Dockerfile`, `docker-compose.yml`, `README.md`, `CLOUD.md`, `PROJECT_TREE.md`.

| Param | Type | Default | Notes |
|---|---|---|---|
| `name` | string | *required* | Top-level project directory name |
| `structure` | list[string] \| null | `null` (default 9-folder scaffold) | Custom subfolder list |
| `description` | string | `""` | Used in README/CLOUD.md |
| `include_docker` | bool | `true` | Generate Dockerfile + docker-compose.yml |

### `delete_project`
Permanently delete an entire project directory.

| Param | Type | Default |
|---|---|---|
| `name` | string | *required* |
| `confirm` | bool | `false` — **must be `true`** |

### `rename_project`
Rename/move a project directory.

| Param | Type | Default |
|---|---|---|
| `old_name` | string | *required* |
| `new_name` | string | *required* |
| `overwrite` | bool | `false` |

---

## Directory Tools

### `create_directory`
Create a directory (and missing parents).

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `exist_ok` | bool | `true` |

### `delete_directory`
Delete a directory.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `confirm` | bool | `false` — **must be `true`** |
| `recursive` | bool | `true` |

The workspace root itself can never be deleted, even with `confirm=true`.

### `list_directory`
List a directory's immediate contents (name, type, size, modified time, extension).

| Param | Type | Default |
|---|---|---|
| `path` | string | `"."` (workspace root) |
| `include_hidden` | bool | `false` |

---

## File Tools

### `create_file`
Create a new file. Fails with `DUPLICATE_FILE` if it already exists, unless `overwrite=true`.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `content` | string | `""` |
| `overwrite` | bool | `false` |

### `read_file`
Read a file's full UTF-8 text content.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |

Returns `data.content` (string) and `data.info` (size, modified/created timestamps, extension, line count).

### `write_file`
Overwrite a file's entire content (creates it if missing). Existing files require `confirm=true`.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `content` | string | *required* |
| `confirm` | bool | `false` |

### `append_file`
Append text to an existing file (must already exist).

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `content` | string | *required* |

### `update_file`
Update part or all of an existing file. Use **either** `find`/`replace` **or** `new_content` — not both.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `find` | string \| null | `null` |
| `replace` | string \| null | `null` |
| `new_content` | string \| null | `null` |
| `count` | int | `-1` (replace all matches) |

### `move_file`
Move/rename a file to a new path.

| Param | Type | Default |
|---|---|---|
| `source_path` | string | *required* |
| `destination_path` | string | *required* |
| `overwrite` | bool | `false` |

### `rename_file`
Rename a file in place (same directory).

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `new_name` | string | *required* (filename only, not a path) |
| `overwrite` | bool | `false` |

### `delete_file`
Permanently delete a file.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |
| `confirm` | bool | `false` — **must be `true`** |

---

## Search Tools

### `search_files`
Glob search for filenames (e.g. `"*.py"`, `"**/*.test.ts"`).

| Param | Type | Default |
|---|---|---|
| `pattern` | string | *required* |
| `root` | string | `"."` |
| `max_results` | int | `200` |

### `find_text`
Grep-like search for a literal string inside text files.

| Param | Type | Default |
|---|---|---|
| `query` | string | *required* |
| `root` | string | `"."` |
| `extensions` | list[string] \| null | `null` (all) |
| `case_sensitive` | bool | `false` |
| `max_results` | int | `200` |

Binary/undecodable files and files over 2 MB are silently skipped. Returns a list of `{path, line_number, line_text}`.

### `project_tree`
Render an ASCII tree of a directory **without** saving it to disk (compare to `generate_project_tree`, which writes `PROJECT_TREE.md`).

| Param | Type | Default |
|---|---|---|
| `path` | string | `"."` |

---

## Documentation Tools

### `generate_readme`
(Re)generate `README.md` with sections: description, features, folder structure, installation, usage, dependencies, configuration, tech stack, future improvements, license.

| Param | Type | Default |
|---|---|---|
| `project_path` | string | *required* |
| `description` | string | `""` |
| `features` | list[string] \| null | `null` |
| `installation` | string | `""` |
| `usage` | string | `""` |
| `dependencies` | list[string] \| null | `null` |
| `configuration` | string | `""` |
| `tech_stack` | list[string] \| null | `null` |
| `future_improvements` | list[string] \| null | `null` |
| `license_name` | string | `"MIT"` |

### `generate_cloud_log`
(Re)generate `CLOUD.md`, the AI work log.

| Param | Type | Default |
|---|---|---|
| `project_path` | string | *required* |
| `goal` | string | `""` |
| `architecture_decisions` | list[string] \| null | `null` |
| `files_created` | list[string] \| null | `null` |
| `files_updated` | list[string] \| null | `null` |
| `implementation_notes` | list[string] \| null | `null` |
| `important_decisions` | list[string] \| null | `null` |
| `known_limitations` | list[string] \| null | `null` |
| `future_work` | list[string] \| null | `null` |

### `generate_project_tree`
(Re)generate `PROJECT_TREE.md` on disk.

| Param | Type | Default |
|---|---|---|
| `project_path` | string | *required* |

---

## Validation Tools

### `validate_workspace`
Report workspace configuration/health: root path, existence, writability, size limits, allowed extensions, ignored files/dirs, logging/backup/template dirs, symlink policy, confirmation policy. No parameters.

### `validate_path`
Check whether a relative path is valid/safe **without** performing any read/write.

| Param | Type | Default |
|---|---|---|
| `path` | string | *required* |

Returns `resolved_path`, `relative_to_workspace`, `exists`, `is_file`, `is_directory`, `is_protected`.

---

## Error codes (`error_code` field)

| Code | Meaning |
|---|---|
| `PATH_TRAVERSAL` | Input contained `..` |
| `WORKSPACE_VIOLATION` | Resolved path (or absolute input) escapes the workspace root |
| `SYMLINK_ESCAPE` | A symlink resolves outside the workspace, or symlinks are disabled |
| `INVALID_PATH` | Empty/reserved/NUL-containing/illegal-character path segment |
| `NOT_FOUND` | Target file/directory/project doesn't exist |
| `ALREADY_EXISTS` | Target already exists and no overwrite flag was given |
| `DUPLICATE_FILE` | `create_file`/`move_file`/`rename_file` target already exists |
| `PERMISSION_DENIED` | OS-level permission error |
| `FILE_TOO_LARGE` | Content exceeds `max_file_size_bytes` |
| `UNSUPPORTED_EXTENSION` | Extension not in `allowed_extensions` |
| `CONFIRMATION_REQUIRED` | Destructive op called without `confirm`/`overwrite=true` |
| `PROTECTED_FILE` | Target is in `protected_files` (server config files) |
| `UNEXPECTED_ERROR` | An unhandled exception (should be rare; please report) |
