# Changelog

All notable changes to **Workspace MCP** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-27

### Added
- **Initial Production Release (Phase 1)** of Model Context Protocol (MCP) server for local codebase exploration and project generation.
- **22 Production-Ready MCP Tools**:
  - **Project Tools**: `create_project`, `delete_project`, `rename_project`.
  - **Directory Tools**: `create_directory`, `delete_directory`, `list_directory`.
  - **File Tools**: `create_file`, `read_file`, `write_file`, `append_file`, `update_file`, `move_file`, `rename_file`, `delete_file`.
  - **Search Tools**: `search_files` (glob), `find_text` (grep-like literal search), `project_tree` (ASCII visualizer).
  - **Documentation Tools**: `generate_readme`, `generate_cloud_log` (AI work log), `generate_project_tree`.
  - **Validation Tools**: `validate_workspace`, `validate_path`.
- **Strict Path Security & Sandboxing Engine**:
  - Resolution via `Path.resolve(strict=False)` preventing `..` traversal and symlink escapes.
  - OS-reserved filename validation (`NUL`, `CON`, `AUX`, `COM1-9`, etc.).
  - Confirmation-gated destructive file overwrites and deletions.
- **Pydantic v2 & Pydantic-Settings Configuration System**:
  - Support for YAML/JSON config files (`workspace_mcp.config.yaml`).
  - Environment variable configuration override (`WORKSPACE_MCP_*`).
- **Structured Operations Logging**:
  - Dual output: Machine-readable JSONL (`operations.jsonl`) and Human-readable text log (`operations.log`).
- **Client Configuration & Examples**:
  - Pre-configured `claude_desktop_config.json` templates for macOS, Linux, and Windows.
  - Comprehensive test suite (80+ unit and integration tests using `pytest` and `pytest-asyncio`).
