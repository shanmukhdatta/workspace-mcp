# Frequently Asked Questions (FAQ)

### Q: What is Workspace MCP?
**A:** Workspace MCP is an official Model Context Protocol (MCP) server that empowers AI assistants (such as Claude Desktop, Claude Code, Antigravity IDE, VS Code, Cursor, and Ollama) to browse, create, edit, search, and manage software projects directly on your local filesystem without requiring ZIP downloads or manual file copy-pasting.

### Q: How does Workspace MCP protect my local machine from unsafe AI actions?
**A:** Security is central to Workspace MCP. The server operates under a strict single-directory sandbox specified by `--workspace-root`. All file and directory operations pass through a central `PathValidator` that uses `os.path.realpath` / `Path.resolve()` to verify paths. Any attempt to use relative `..` sequences, absolute system paths, symlink escapes, or OS-reserved device filenames (`CON`, `NUL`, etc.) is immediately blocked with a structured error envelope.

### Q: What happens if an AI assistant tries to overwrite or delete a file?
**A:** Workspace MCP enforces confirmation gating for destructive operations. By default, file overwrites (`write_file`), file deletions (`delete_file`), and directory/project deletions (`delete_directory`, `delete_project`) fail unless an explicit confirmation flag (`confirm=true` or `overwrite=true`) is passed. Furthermore, the workspace root directory itself can *never* be deleted under any circumstances.

### Q: Can I use Workspace MCP with local LLMs via Ollama?
**A:** Yes! Any AI tool or framework that supports the Model Context Protocol (e.g. Continue.dev, VS Code MCP extensions, LangChain / LlamaIndex MCP clients, or local MCP-compatible frontends) can connect to Workspace MCP over stdio or SSE transport while calling Ollama models locally.

### Q: How do I configure Claude Desktop to use Workspace MCP?
**A:** You simply add a JSON snippet to your `claude_desktop_config.json` file. See the [Claude Desktop Config Guide](README.md#-claude-desktop-configuration-guide) in `README.md` or `docs/CLIENT_CONFIG.md` for platform-specific file paths and exact configuration blocks.

### Q: Does Workspace MCP require internet access or remote APIs?
**A:** No. Workspace MCP runs completely locally on your machine. It does not send any telemetry, codebase files, or credentials to external servers.

### Q: What operating systems are supported?
**A:** Windows 10/11, macOS (Intel & Apple Silicon), and Linux (Ubuntu, Debian, Fedora, Arch, etc.).

### Q: How does logging work?
**A:** Every tool call generates an entry in two log files inside your configured `log_dir`:
1. `operations.jsonl`: Machine-readable JSONLines format containing timestamp, operation, target path, status, duration, and error codes.
2. `operations.log`: Human-readable text format (`[TIMESTAMP] OPERATION | PATH | STATUS | DURATION`).
