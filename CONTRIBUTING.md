# Contributing to Workspace MCP

Thank you for your interest in contributing to **Workspace MCP**! We welcome contributions from developers, researchers, and AI enthusiasts of all skill levels.

## How to Contribute

### 1. Reporting Bugs
If you find a bug or security issue:
- Search existing GitHub Issues to see if it has already been reported.
- If not, open a new issue with a clear title, reproduction steps, expected behavior, OS environment, Python version, and relevant log outputs.

### 2. Feature Requests
We welcome feature proposals for Phase 2 and Phase 3!
- Open a GitHub Discussion or Issue describing the feature, the problem it solves, and how it aligns with the Model Context Protocol ecosystem.

### 3. Pull Requests
1. **Fork the Repository**:
   ```bash
   git clone https://github.com/shanmukhdatta/workspace-mcp.git
   cd workspace-mcp
   ```
2. **Set up the Environment**:
   Using `uv` (recommended):
   ```bash
   uv sync --extra dev
   ```
   Or standard venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-new-tool
   ```
4. **Run Code Formatting & Type Checks**:
   ```bash
   black src/ tests/
   mypy src/
   pytest
   ```
5. **Submit your Pull Request**:
   Push your branch to GitHub and create a PR with a description of the changes made and tests added.

## Code Standards & Architecture

- **Path Security First**: All new file/directory operations MUST route through `PathValidator.resolve()` located in `src/workspace_mcp/utils/pathsec.py`.
- **Exception Hierarchy**: Service methods should raise subclasses of `WorkspaceError` (from `src/workspace_mcp/models/schemas.py`).
- **Tool Wrapper Design**: All `@mcp.tool()` implementations must use `run_tool()` in `src/workspace_mcp/tools/_common.py` to maintain a uniform JSON envelope and structured logging.
- **Type Annotations & Docstrings**: All public functions must have explicit type hints and detailed docstrings, as MCP tool docstrings are exposed directly to LLMs.

Thank you for helping make Workspace MCP the standard for AI-driven software development!
