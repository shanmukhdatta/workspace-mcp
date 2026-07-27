# Installation Guide

## Requirements

- Python 3.11 or newer
- pip (or `uv`/`pipx`, if you prefer)

## 1. Get the code

```bash
git clone <this-repo> workspace-mcp
cd workspace-mcp
```

## 2. Create a virtual environment

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install the package

```bash
pip install -e .
```

This installs `workspace-mcp` in editable mode and registers the `workspace-mcp` console script (see `pyproject.toml`'s `[project.scripts]`).

For development (running the test suite, linting):

```bash
pip install -e ".[dev]"
```

## 4. Choose your workspace directory

Pick a single directory the AI is allowed to create projects in. It will be created automatically if it doesn't exist.

- Windows: `D:\AIProjects`
- Linux/macOS: `/home/<you>/AIProjects`

## 5. Verify it runs

```bash
workspace-mcp --workspace-root /home/<you>/AIProjects --transport stdio
```

The process will sit waiting for an MCP client to connect over stdio (this is normal — it's not a web server). Press `Ctrl+C` to stop it.

If you'd rather use a config file instead of `--workspace-root`, copy `workspace_mcp.config.example.yaml` to `workspace_mcp.config.yaml`, edit `workspace_root`, and run:

```bash
workspace-mcp --config workspace_mcp.config.yaml
```

## 6. Connect it to an MCP client

See `docs/CLIENT_CONFIG.md` for wiring this into Claude Desktop, or `docs/QUICKSTART.md` for a fast end-to-end walkthrough.

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

You should see 80+ passing tests covering path security, every service, and end-to-end MCP error handling.
