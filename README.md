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

## 💡 Capabilities Guide — What is this, really?

Think of **workspace-mcp** as giving an AI assistant *hands* inside a project folder on disk. Without it, an AI can only talk to you about code — you'd have to copy-paste files back and forth manually. With it, the AI can directly create, read, edit, organize, and document real files and folders, the same way a developer would using a file explorer and a terminal.

It does **not** write your logic for you by magic, and it's **not** a game engine, compiler, or database. It's a **file and project management layer**. The "intelligence" (writing the actual logic, API code, etc.) still comes from the AI reasoning about your request — **workspace-mcp** is what lets that reasoning turn into real files on your machine, cleanly organized.

---

### The Core Idea: 4 Categories of Power

Every tool in **workspace-mcp** falls into one of these four buckets:

| Category | What it means in plain English |
|---|---|
| 🗂️ **Project & Folder Management** | Creating, renaming, deleting entire projects or folders |
| 📄 **File Operations** | Creating, reading, editing, moving, renaming, deleting individual files |
| 🔍 **Search & Discovery** | Finding files or text across a whole project without manually digging |
| 📝 **Auto-Documentation** | Generating README, project trees, and work logs automatically |

---

### 1. 🗂️ Project & Folder Management

This is the "scaffolding" layer — setting up the skeleton before anything gets built.

- **`create_project`** — Starts a brand-new project folder with a sensible structure. This is usually the *first* thing you do.
- **`create_directory`** — Adds a subfolder inside a project (e.g. `src/`, `assets/`, `docs/`). Creates parent folders automatically if they don't exist yet.
- **`rename_project`** — Renames (moves) an entire project.
- **`delete_directory`** — Removes a folder and everything inside it. Permanent — use with care.
- **`delete_project`** — Wipes an entire project. Also permanent.

> 💡 **Beginner tip:** Always start a new piece of work with `create_project`. It keeps everything organized instead of scattering files around loosely.

---

### 2. 📄 File Operations

This is where actual content gets written.

- **`create_file`** — Makes a brand-new file with content (fails if the file already exists — this is a safety net against accidentally overwriting work).
- **`write_file`** — Overwrites a file's *entire* content, or creates it if it doesn't exist yet. Use this when you want a clean slate.
- **`update_file`** — Edits *part* of an existing file (like changing one function) without touching the rest.
- **`append_file`** — Adds text to the *end* of a file, without touching what's already there (great for logs or growing notes).
- **`read_file`** — Reads a file's full content back to you.
- **`move_file`** — Moves a file to a different folder (can rename it at the same time).
- **`rename_file`** — Renames a file, keeping it in the same folder.
- **`delete_file`** — Permanently deletes a single file.

> 💡 **Beginner tip:** `create_file` vs `write_file` vs `update_file` is the most common confusion:
> - Brand new file → `create_file`
> - Replace everything in an existing file → `write_file`
> - Change just one part → `update_file`

---

### 3. 🔍 Search & Discovery

Once a project has more than a couple of files, you need to *find* things instead of remembering where everything is.

- **`find_text`** — Searches file *contents* for a literal string (like grep). Great for finding all `TODO` comments, or every place a function is used.
- **`search_files`** — Finds files by *name pattern* (e.g. all `.js` files, or anything named `test_*`).
- **`list_directory`** — Shows what's immediately inside a folder (like `ls`).

> 💡 **Beginner tip:** Use `search_files` when you know *what kind* of file you want but not *where* it is. Use `find_text` when you know *what text* you're looking for but not *which file* it's in.

---

### 4. 📝 Auto-Documentation & Introspection

This is the layer that keeps a project understandable — for you, teammates, or your future self.

- **`generate_readme`** — Auto-writes a proper `README.md` for the project (sections like setup, usage, structure).
- **`generate_project_tree`** — Creates a saved `PROJECT_TREE.md` — a visual ASCII map of every file and folder.
- **`project_tree`** — Same idea, but just *shows* it to you without saving it to disk.
- **`generate_cloud_log`** — Creates `CLOUD.md`, a plain-English log explaining what the AI actually built and *why* — useful for tracking AI-assisted work over time.
- **`validate_path`** — Checks if a given file path is valid and safe before you use it.
- **`validate_workspace`** — Reports on the overall health of the workspace (root location, config, etc.).

> 💡 **Beginner tip:** Run `generate_readme` + `generate_project_tree` + `generate_cloud_log` near the *end* of a work session — they document what was just built, so it's most accurate then.

---

### 🔄 A Typical Full Workflow

```
1. create_project        → set up "my-app/"
2. create_directory      → add "src/", "docs/"
3. create_file           → write starter files
4. update_file           → refine logic as you go
5. find_text/search_files→ check for TODOs, locate files
6. move_file/rename_file → tidy up structure
7. generate_project_tree → snapshot the layout
8. generate_readme       → document it
9. generate_cloud_log    → log what was done
10. validate_workspace   → sanity-check everything
```

---

### 🧠 Key Mental Model to Remember

> **workspace-mcp doesn't think for you — it acts on disk for you.**
>
> The AI still does the reasoning (what code to write, how to structure a game or API, etc.). Workspace-mcp is the hands that turn that reasoning into an organized, documented, real project folder — instead of a wall of code pasted into a chat window that you'd have to assemble yourself.

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

### 🌟 Full-Potential Master Prompt (Unleash All 22 Tools)

To exercise the complete capabilities of Workspace MCP in Claude Desktop, copy and paste this master prompt:

```text
Using the workspace MCP, create a new project called [project-name]. Set up the following structure: create a src/ directory, add starter files inside it ([file1], [file2]), and create a top-level README.md and .gitignore.

Once the files exist, append a notes section to the README, then update [file1] with the core logic for [feature].

Search the project for any TODO or FIXME comments using find_text. Find all files matching *.[ext] using search_files.

Rename [file2] to [new-name], then move it into a new docs/ directory.

Generate the project tree, generate a proper README, and generate a CLOUD.md log summarizing what was built.

Finally, validate the workspace configuration, and list the contents of the project root to confirm everything is in place.
```

#### 🔍 What Tools This Master Prompt Exercises:
1. `create_project` / `create_directory` — Initializes project and directory hierarchy.
2. `create_file` — Creates `src/[file1]`, `src/[file2]`, top-level `README.md`, `.gitignore`.
3. `append_file` & `update_file` — Appends notes section to `README.md` and updates `[file1]` with feature logic.
4. `find_text` & `search_files` — Searches code for `TODO`/`FIXME` comments and matches extensions (`*.py`, `*.ts`, etc.).
5. `rename_file` & `move_file` — Renames `[file2]` to `[new-name]` and moves it into `docs/`.
6. `generate_project_tree`, `generate_readme`, `generate_cloud_log` — Formats and writes documentation artifacts (`PROJECT_TREE.md`, `README.md`, `CLOUD.md`).
7. `validate_workspace` & `list_directory` — Verifies workspace configuration health and lists root contents.

---

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
