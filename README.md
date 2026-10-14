# 🚀 Workspace MCP 🛠️

> **The ultimate local filesystem bridge for Claude Desktop & Claude Code!** ⚡ Stop losing code to token limits — let Claude design, scaffold, build, and save full-stack software projects directly on your hard drive! 📁💻

[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.2.0-purple.svg?style=flat-square)](https://modelcontextprotocol.io)

---

## 🎯 Overview: Solving Claude's Token Limits 🛑

When using Claude to build multi-file projects, developers frequently run into **output token limits** and **context window cutoffs**:

1. ⚠️ **Truncated File Outputs**: Claude hits completion token limits mid-file, cutting off output and forcing you to repeatedly ask it to continue.
2. 🔄 **Lost Progress**: When a conversation gets too long or expires, un-saved code in the chat window disappears unless manually copy-pasted into your editor.
3. 🚫 **No Direct Disk Access**: Standard web and desktop chats cannot write files directly to your local computer.

### 🪄 How Workspace MCP Helps 🌟

Workspace MCP connects Claude directly to your local filesystem:

- 💾 **Incremental Local Disk Saves**: Every file and folder is saved immediately as Claude works. If Claude hits an output token limit on a long response, everything written up to that point remains 100% safely stored on disk.
- 🔁 **Resuming Work**: In a new chat prompt, simply ask Claude to read your project files and pick up right where it left off using `read_file`, `find_text`, or `update_file`.
- 📝 **Automatic Work Logs (`CLOUD.md`)**: Maintains an architectural work log tracking what was built, key decisions, and next steps for future chat sessions.

---

## 🧭 Capabilities Guide: What Workspace MCP Does 🛠️

Think of `workspace-mcp` as providing **file and project management hands** 🤲 to your AI assistant. The AI handles the reasoning (what code to write and how to structure it); `workspace-mcp` handles applying those changes directly to disk in a clean, organized folder layout.

### 🎨 The 4 Main Tool Categories

| Category | Description |
|---|---|
| 🗂️ **Project & Folder Management** | Create, rename, or remove project roots and subdirectories. |
| 📄 **File Operations** | Create, read, edit, move, rename, and delete individual files safely. |
| 🔍 **Search & Discovery** | Find text across files (`grep`), search by filename patterns (`glob`), or list directory trees. |
| 📊 **Auto-Documentation** | Automatically generate `README.md`, `PROJECT_TREE.md`, and `CLOUD.md` work logs. |

---

### 🗂️ 1. Project & Folder Management

- `create_project` 🏗️ — Initializes a project directory with a default scaffold.
- `create_directory` 📁 — Creates subfolders (e.g. `src/`, `docs/`) and missing parent folders automatically.
- `rename_project` ✏️ — Moves or renames an entire project directory.
- `delete_directory` 🗑️ — Recursively deletes a folder (requires explicit `confirm=true`).
- `delete_project` 💥 — Permanently removes an entire project directory (requires `confirm=true`).

*💡 Tip:* Always start a new application with `create_project` to keep files scoped inside a dedicated folder!

---

### 📄 2. File Operations

- `create_file` ✨ — Creates a new file with content (fails if the file already exists to prevent accidental overwrites).
- `write_file` 📝 — Overwrites a file completely or creates it if missing (requires `confirm=true` if overwriting).
- `update_file` 🔧 — Performs targeted string edits (`find`/`replace`) on existing files without replacing the entire file.
- `append_file` ➕ — Appends text to the end of a file without touching existing content.
- `read_file` 📖 — Reads a file's full UTF-8 text content.
- `move_file` 🚚 — Relocates a file to another directory.
- `rename_file` 🏷️ — Renames a file within its current folder.
- `delete_file` ❌ — Deletes a single file (requires `confirm=true`).

*💡 Tip:* Use `create_file` for brand new files, `update_file` for inline edits, and `write_file` when replacing an entire file!

---

### 🔍 3. Search & Discovery

- `find_text` 🔎 — Grep-like search across text files for literal strings (e.g. finding `TODO` comments or function usages).
- `search_files` 🎯 — Glob search for files matching a pattern (e.g. `**/*.py` or `*.ts`).
- `list_directory` 📋 — Lists files and subdirectories with sizes and metadata.

*💡 Tip:* Use `search_files` when looking for file types or names, and `find_text` when searching for specific code text across your project!

---

### 📊 4. Auto-Documentation & Validation

- `generate_readme` 📘 — Creates or updates a structured `README.md`.
- `generate_project_tree` 🌴 — Saves an ASCII visual tree map to `PROJECT_TREE.md`.
- `project_tree` 👁️ — Returns an ASCII visual tree in the tool response without saving to disk.
- `generate_cloud_log` ☁️ — Writes `CLOUD.md` documenting what was built and why.
- `validate_workspace` 🏥 — Checks workspace health, server configuration, and limits.
- `validate_path` 🛡️ — Verifies if a path is safe and valid before performing file operations.

---

### 🔄 Typical Workflow

```text
1. create_project        🏗️ → Initialize project directory
2. create_directory      📁 → Scaffold subfolders (src/, docs/)
3. create_file           ✨ → Write initial source files
4. update_file           🔧 → Edit and refine code incrementally
5. find_text/search_files🔎 → Locate references or check for TODOs
6. move_file/rename_file 🚚 → Organize file structure
7. generate_project_tree 🌴 → Save project tree map
8. generate_readme       📘 → Document setup and usage
9. generate_cloud_log    ☁️ → Save AI work log
10. validate_workspace   🏥 → Verify workspace state
```

---

## 🔌 Connecting to Claude Desktop 🤖

Claude Desktop manages MCP servers via its configuration file. Using `uv` allows Claude Desktop to run `workspace-mcp` automatically in the background without needing to start a server manually! ⚡

### 📂 Step 1: Locate `claude_desktop_config.json`

| OS | Config Path |
| --- | --- |
| **Windows 🪟** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **macOS 🍎** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Linux 🐧** | `~/.config/Claude/claude_desktop_config.json` |

### ⚙️ Step 2: Add Configuration

Add the following to your `claude_desktop_config.json`. Update the paths to point to your local installation of `workspace-mcp` and your desired `--workspace-root` directory:

#### Windows 🪟
```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/YourUsername/mcp/servers/workspace-mcp",
        "run",
        "workspace-mcp",
        "--workspace-root",
        "C:/Users/YourUsername/AIProjects"
      ]
    }
  }
}
```

#### macOS 🍎 / Linux 🐧
```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/user/workspace-mcp",
        "run",
        "workspace-mcp",
        "--workspace-root",
        "/home/user/AIProjects"
      ]
    }
  }
}
```

*💡 Note:* Requires [`uv`](https://github.com/astral-sh/uv) to be installed on your system PATH.

### 🔄 Step 3: Restart Claude Desktop 🔨

1. Fully close Claude Desktop (from system tray or menu bar).
2. Re-open Claude Desktop.
3. Click the hammer icon (🔨) in the chat bar to confirm that the **workspace-mcp** tools are active! 🎉

---

## 🎮 Usage & Master Prompt 👑

### 🌟 Comprehensive Master Prompt

Copy and paste this prompt into Claude Desktop to test all tool capabilities at once:

```text
Using the workspace MCP, create a new project called [project-name]. Set up the following structure: create a src/ directory, add starter files inside it ([file1], [file2]), and create a top-level README.md and .gitignore.

Once the files exist, append a notes section to the README, then update [file1] with the core logic for [feature].

Search the project for any TODO or FIXME comments using find_text. Find all files matching *.[ext] using search_files.

Rename [file2] to [new-name], then move it into a new docs/ directory.

Generate the project tree, generate a proper README, and generate a CLOUD.md log summarizing what was built.

Finally, validate the workspace configuration, and list the contents of the project root to confirm everything is in place.
```

### ⚡ Resuming Work After Token Limits

If Claude hits a completion limit mid-task:

1. Open a new chat session.
2. Prompt Claude:
   > "Check the files in `MyProject/src`, review `CLOUD.md` to see what was built so far, and finish implementing the main module."
3. Claude will use `list_directory`, `read_file`, and `update_file` to continue development seamlessly! 🚀

---

## 🛡️ Security Sandbox Architecture 🔒

Workspace MCP strictly isolates all operations to the configured `--workspace-root`:

```
Claude Desktop (Client 🤖)
       │
       ▼ Stdio Transport ⚡
Workspace MCP Server 🖥️
       │
       ▼
  Service Layer ⚙️ ──► PathValidator (os.path.realpath Sandbox 🛡️)
                               │
                               ▼
                     Sandboxed Workspace Root 📁
```

- 🛡️ **Path Security**: All input paths are resolved using `os.path.realpath` / `Path.resolve(strict=False)` to prevent `..` path traversal sequences and symlink escapes.
- 🚫 **Reserved Names**: Windows reserved filenames (`CON`, `NUL`, `AUX`, `COM1-9`) are rejected to preserve cross-platform compatibility.
- 🔐 **Confirmation Gating**: Destructive actions (`delete_file`, `delete_directory`, file overwrites) require explicit confirmation flags (`confirm=true` / `overwrite=true`).
- 📜 **Audit Logs**: Operations are logged to both `operations.jsonl` (machine-readable) and `operations.log` (human-readable text).

---

## 🧰 Tool Reference 📦

| Category | Tool | Description |
| --- | --- | --- |
| **Project 🏗️** | `create_project` | Scaffolds directory structure + `.gitignore`, `Dockerfile`, `README.md`, `CLOUD.md` |
| | `delete_project` | Removes project folder (requires `confirm=true`) |
| | `rename_project` | Renames or relocates a project directory |
| **Directory 📁** | `create_directory` | Creates subdirectories (including missing parents) |
| | `delete_directory` | Deletes directory recursively (requires `confirm=true`) |
| | `list_directory` | Lists directory files and metadata |
| **File 📄** | `create_file` | Creates a new file |
| | `read_file` | Reads UTF-8 text file content |
| | `write_file` | Overwrites file content (requires `confirm=true`) |
| | `append_file` | Appends text to end of file |
| | `update_file` | Performs `find`/`replace` string substitution or partial update |
| | `move_file` / `rename_file` | Relocates or renames a file |
| | `delete_file` | Deletes a file (requires `confirm=true`) |
| **Search 🔍** | `search_files` | Glob search for matching filenames |
| | `find_text` | Grep-like search across text files |
| | `project_tree` | Generates ASCII project tree string |
| **Docs 📘** | `generate_readme` | Creates/updates `README.md` |
| | `generate_cloud_log` | Creates `CLOUD.md` work log |
| | `generate_project_tree` | Saves `PROJECT_TREE.md` to disk |
| **Validation 🏥** | `validate_workspace` | Returns server health and settings |
| | `validate_path` | Validates relative path safety without modifying disk |

---

## ⚙️ Configuration Reference 🔧

Settings can be specified via command-line flags or environment variables (`WORKSPACE_MCP_*`):

| Option | Environment Variable | Default | Description |
| --- | --- | --- | --- |
| `--workspace-root` | `WORKSPACE_MCP_WORKSPACE_ROOT` | `./workspace` | Base sandboxed directory for all operations |
| `--config` | `WORKSPACE_MCP_CONFIG` | `None` | Path to YAML/JSON configuration file |
| `max_file_size_bytes` | `WORKSPACE_MCP_MAX_FILE_SIZE_BYTES` | `10485760` (10MB) | File size write limit |
| `require_overwrite_confirmation` | `WORKSPACE_MCP_REQUIRE_OVERWRITE_CONFIRMATION` | `true` | Enforces confirmation on file overwrite/delete |

---

## 📜 License ⚖️

Distributed under the [MIT License](LICENSE).

---

## 🧩 Extension branch — Roadmap capabilities

The [extension branch](https://github.com/shanmukhdatta/workspace-mcp/tree/extension)
contains additional tools built on the original Phase 1 service architecture.
They are under review in [PR #1](https://github.com/shanmukhdatta/workspace-mcp/pull/1);
the stable `main` release is unchanged until that PR is approved.

- **Commands:** `run_command` uses async subprocesses, an allowlist, timeouts
  and bounded output. Requires `WORKSPACE_MCP_ENABLE_TERMINAL=true` and a
  trusted workspace; a subprocess is **not** an OS sandbox.
- **Git:** `git_init`, `git_status`, `git_branch`, `git_diff`, `git_log`,
  `git_commit`; local operations only, disabled until
  `WORKSPACE_MCP_ENABLE_GIT=true`.
- **Recovery:** `list_backups` and `restore_backup` restore automatic file
  snapshots taken before mutations.
- **Scaffolds:** `list_templates` and optional `create_project(template=...)`
  support FastAPI/React, Next.js/Tailwind, Rust, and local text templates.
- **Code search:** `index_project`, `search_code`, and
  `workspace-mcp index MyProject`. Reports **lexical** by default; optional
  local embedding models enable **semantic** similarity.
- **Memory and collaboration:** `remember_fact`, `link_facts`,
  `query_memory`, `agent_submit`, `agent_claim`, `agent_finish`,
  `agent_tasks`, and `sync_events` for durable project context, agent
  task handoffs, and polling synchronization.

Review [ROADMAP.md](ROADMAP.md) and
[docs/EXTENSION_SECURITY.md](docs/EXTENSION_SECURITY.md) before use.
Autonomous model execution, billion-scale vector search, and full
bidirectional live IDE synchronization are **not** claimed as completed.
