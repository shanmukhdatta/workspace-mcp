# Quick Start

This walks through going from zero to "the AI just built a project on my disk" in a few minutes.

## 1. Install

Follow `docs/INSTALL.md` first. You should be able to run:

```bash
workspace-mcp --workspace-root ~/AIProjects
```

and see it start without errors (`Ctrl+C` to stop — normal MCP servers over stdio don't print much).

## 2. Connect Claude Desktop

Follow `docs/CLIENT_CONFIG.md` to add `workspace-mcp` to your `claude_desktop_config.json`, then fully restart Claude Desktop.

## 3. Confirm the tools show up

In a new Claude Desktop conversation, click the tools/plug icon and confirm you see tools like `create_project`, `create_file`, `list_directory`, etc. (22 total).

## 4. Ask for a project

Try a prompt like:

> Using the filesystem workspace tools, create a project called "TaskManager" with a FastAPI backend and a React frontend. Add a basic FastAPI app with a health check endpoint in backend/main.py, and a minimal React entry point in frontend/src/App.jsx. Then generate the README and CLOUD.md describing what you built.

Claude will call `create_project`, then a series of `create_file` calls, then `generate_readme` / `generate_cloud_log`. Check `~/AIProjects/TaskManager` on disk afterward — it will contain the real files, not just chat output.

## 5. Inspect the audit trail

Every operation is logged to:

```
~/AIProjects/.workspace_mcp/logs/operations.log      # human-readable
~/AIProjects/.workspace_mcp/logs/operations.jsonl    # structured
```

## 6. Try the safety rails

Ask Claude to overwrite a file it already created without saying "confirm" — it should get a `CONFIRMATION_REQUIRED` error back and ask you before retrying with `confirm=True`. Ask it to write outside the workspace (e.g. `../outside.txt`) and it will get a `PATH_TRAVERSAL` error instead of touching your filesystem.

See `docs/API.md` for the full list of tools and their arguments, and `examples/example_prompts.md` for more sample prompts.
