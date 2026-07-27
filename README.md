# Workspace MCP

> **The local filesystem bridge for Claude Desktop & Claude Code.** Stop losing code to token limits — let Claude design, build, and save full-stack software projects directly on your hard drive.

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](pyproject.toml)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![CI Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](.github/workflows/ci.yml)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 The Token Limit Problem & How Workspace MCP Solves It

When asking **Claude (Claude Desktop or Claude Code)** to build large applications, complex features, or multi-file repositories, developers constantly hit **output token exhaustion** and **context window limits**:

1. **Truncated Code Outputs**: Claude hits completion token caps mid-file, cutting off code generation and forcing you to prompt *"continue writing line 150..."* repeatedly.
2. **Context Loss Across Conversations**: Once a chat gets long or expires, generated code lost in chat history must be manually copy-pasted and assembled.
3. **No Direct Local File Storage**: Standard web or desktop chats cannot write directly to your disk.

### 💡 The Solution: Direct Local Storage
With **Workspace MCP**, Claude writes files **directly to your local filesystem** progressively as it works:

- **Incremental File Saving**: Every file, directory, and configuration is written immediately to disk. If Claude reaches a token output limit on a response, **everything written so far is 100% saved on your computer**.
- **Seamless Resume**: Simply tell Claude in a fresh prompt or new conversation: *"Check the existing files in my project and continue building..."*. Claude uses `read_file`, `find_text`, or `update_file` to inspect local code and pick up exactly where it left off.
- **Automated Work Logging (`CLOUD.md`)**: Claude maintains an automated work log documenting architectural decisions, created files, and next steps so future Claude sessions never lose context.

---

## 🔌 How to Connect to Claude Desktop

### Why Use `uv` for Automatic Server Execution?
By configuring Claude Desktop with `uv`, **Claude Desktop automatically launches and manages Workspace MCP in the background**. 

You do **not** need to manually open a terminal, activate virtual environments, or run server commands before opening Claude. `uv` handles installation, dependencies, and execution automatically whenever Claude Desktop starts up.

### Step 1: Open `claude_desktop_config.json`

Open the configuration file for your operating system:

| Operating System | Config File Location |
| --- | --- |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` <br> *(e.g. `C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json`)* |
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

### Step 2: Add the Automatic `uv` Configuration

Paste the following JSON block into your `claude_desktop_config.json` file. Update the directory paths to match your local installation of `workspace-mcp` and your desired `--workspace-root` folder:

#### Windows Configuration:
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

#### macOS / Linux Configuration:
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

> 💡 **Prerequisite**: Make sure `uv` is installed on your system ([install uv](https://github.com/astral-sh/uv)).

### Step 3: Restart & Verify in Claude Desktop

1. Fully quit Claude Desktop (exit from system tray / menu bar).
2. Re-open Claude Desktop.
3. Click the **hammer icon (🔨)** in the lower-right corner of the chat box.
4. You will see **22 Workspace MCP tools** active and ready to use!

---

## 🛠️ How We Use It (Workflow & Prompts)

### Workflow 1: Building Full Applications
Ask Claude Desktop to scaffold a complete project:

> *"Claude, create a new project called `TaskManager` with a FastAPI backend, React frontend, Docker setup, and document everything in `README.md` and `CLOUD.md`."*

Claude automatically invokes `create_project`, creates the directory structure, writes `main.py` and `App.jsx`, and generates documentation directly inside your local `AIProjects/TaskManager` folder.

### Workflow 2: Resuming Work After Token Limits
If Claude stops mid-task due to token completion limits:

1. Open a new or existing chat with Claude.
2. Prompt Claude:
   > *"Check the files in `TaskManager/backend`, read `CLOUD.md` to see what was built, and finish implementing the database models."*
3. Claude executes `list_directory`, `read_file`, and `write_file` to inspect your local code and seamlessly complete the feature.

---

## 🛡️ Security & Sandboxing Architecture

```
+-------------------------------------------------------------------+
|                           CLAUDE DESKTOP                          |
+-------------------------------------------------------------------+
                                  |
                      MCP Stdio Transport (JSON-RPC)
                                  v
+-------------------------------------------------------------------+
|                        WORKSPACE MCP SERVER                       |
|                       (uv run workspace-mcp)                      |
+-------------------------------------------------------------------+
        |                         |                         |
        v                         v                         v
+----------------+       +------------------+      +----------------+
| Pydantic Config|       |   22 FastMCP     |      | Dual Logging   |
| (settings.py)  |       |   Tool Handlers  |      | Engine         |
+----------------+       +------------------+      +----------------+
                                  |
                                  v
                         +------------------+
                         | Service Layer    |
                         +------------------+
                                  |
                                  v
                         +------------------+
                         | PathValidator    |
                         | Realpath Sandbox |
                         +------------------+
                                  |
                      Verified Safe Local Path
                                  v
                         +------------------+
                         | Local Hard Drive |
                         | (Workspace Root) |
                         +------------------+
```

### Security Sandbox Features
- **Strict Single-Root Isolation**: Claude can **only** read, write, or search within your configured `--workspace-root`.
- **Anti-Traversal Verification**: All paths are checked using `os.path.realpath` / `Path.resolve()` to prevent `..` relative path escapes and symlink exploits.
- **Confirmation Protection**: Destructive operations (file deletions, full overwrites) require confirmation flags to safeguard against accidental code loss.
- **Dual Audit Trail**: Logs every tool call to `operations.jsonl` (JSON) and `operations.log` (text) inside your workspace log folder.

---

## 🧰 MCP Tools Reference

Workspace MCP provides **22 production tools** organized into 6 functional groups:

| Category | Tool | Description |
| --- | --- | --- |
| **Project** | `create_project` | Scaffolds directory structure + `.gitignore`, `Dockerfile`, `README.md`, `CLOUD.md` |
| | `delete_project` | Permanently deletes a project folder (requires `confirm=true`) |
| | `rename_project` | Renames or moves a project directory |
| **Directory** | `create_directory` | Creates directories (including missing parent folders) |
| | `delete_directory` | Deletes directory recursively (requires `confirm=true`) |
| | `list_directory` | Lists directory contents, sizes, and file metadata |
| **File Operations** | `create_file` | Creates a new file with content |
| | `read_file` | Reads UTF-8 text file content |
| | `write_file` | Overwrites file content completely (requires `confirm=true`) |
| | `append_file` | Appends code/text to an existing file |
| | `update_file` | Targeted string substitution (`find`/`replace`) or partial rewrite |
| | `move_file` / `rename_file` | Relocates or renames a file |
| | `delete_file` | Permanently deletes a file (requires `confirm=true`) |
| **Search** | `search_files` | Glob file search (e.g. `**/*.py`, `src/**/*.ts`) |
| | `find_text` | Grep-like search across text files for code references |
| | `project_tree` | Generates ASCII project structure visual string |
| **Docs** | `generate_readme` | Auto-generates/updates `README.md` |
| | `generate_cloud_log` | Auto-generates `CLOUD.md` AI work log |
| | `generate_project_tree` | Saves `PROJECT_TREE.md` diagram to disk |
| **Validation** | `validate_workspace` | Inspects active server limits and workspace configuration |
| | `validate_path` | Checks if a path is safe and valid without modifying disk |

---

## ⚙️ Configuration Reference

Configure settings via command-line flags or environment variables (`WORKSPACE_MCP_*`):

| Flag / Option | Environment Variable | Default | Description |
| --- | --- | --- | --- |
| `--workspace-root` | `WORKSPACE_MCP_WORKSPACE_ROOT` | `./workspace` | Target directory for all local project files |
| `--config` | `WORKSPACE_MCP_CONFIG` | `None` | Optional path to YAML/JSON configuration file |
| `max_file_size_bytes` | `WORKSPACE_MCP_MAX_FILE_SIZE_BYTES` | `10485760` (10MB) | Max bytes allowed for single file write |
| `require_overwrite_confirmation` | `WORKSPACE_MCP_REQUIRE_OVERWRITE_CONFIRMATION` | `true` | Requires `confirm=true` on overwrite/delete |

---

## 📄 License & Contributing

Distributed under the [MIT License](LICENSE). Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
