# Example MCP Client Configuration

## Claude Desktop

Claude Desktop's config file lives at:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add (or merge into) the `mcpServers` object:

```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "workspace-mcp",
      "args": ["--workspace-root", "/home/user/AIProjects"]
    }
  }
}
```

If `workspace-mcp` isn't on your `PATH` (e.g. it's only installed inside a venv), point directly at the venv's Python and run the module instead:

```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "/home/user/workspace-mcp/.venv/bin/python",
      "args": ["-m", "workspace_mcp.server", "--workspace-root", "/home/user/AIProjects"]
    }
  }
}
```

On Windows, use the venv's `python.exe`:

```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "D:\\workspace-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "workspace_mcp.server", "--workspace-root", "D:\\AIProjects"]
    }
  }
}
```

**Fully quit and restart Claude Desktop** (not just close the window) after editing this file.

## Any other MCP client (generic stdio)

Any MCP client that supports launching a stdio server just needs the same `command` + `args` shown above. `workspace-mcp` speaks the standard MCP stdio transport by default; pass `--transport sse` or `--transport streamable-http` if your client needs an HTTP-based transport instead (see `workspace-mcp --help`).

## Verifying the connection

After restarting your client, look for `workspace-mcp` in its tool/connector list, with 22 tools available: `create_project`, `delete_project`, `rename_project`, `create_directory`, `delete_directory`, `list_directory`, `create_file`, `read_file`, `write_file`, `append_file`, `update_file`, `move_file`, `rename_file`, `delete_file`, `search_files`, `find_text`, `project_tree`, `generate_readme`, `generate_cloud_log`, `generate_project_tree`, `validate_workspace`, `validate_path`.
