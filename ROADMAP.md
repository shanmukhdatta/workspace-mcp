# Workspace MCP Roadmap

This document outlines the multi-phase vision for **Workspace MCP**, evolving it into a comprehensive AI-driven development environment platform.

---

## 🎯 Phase 1: Core Filesystem & Codebase Scaffolding (Current Release - v1.0.0)

- [x] **22 FastMCP Tools** for complete project, directory, file, search, doc, and path validation operations.
- [x] **Strict Security Sandbox** preventing path traversal (`..`), symlink escapes, absolute path overrides, and reserved Windows device names.
- [x] **Layered Configuration System** (Defaults → YAML/JSON File → `WORKSPACE_MCP_*` Environment Variables).
- [x] **Dual Structured Logging** (`operations.jsonl` machine logs + `operations.log` human audit log).
- [x] **Automated Documentation Engine** (`README.md`, `CLOUD.md` AI work log, `PROJECT_TREE.md`).
- [x] **Cross-Platform Support** (Windows, macOS, Linux) with Claude Desktop, VS Code, Antigravity IDE, Ollama integration.

---

## 🚀 Phase 2: Terminal Execution, Git Integration & Project Memory (In Development)

- [ ] **Terminal Execution Tools**:
  - `run_command`: Execute CLI tools, test suites, package managers (`npm`, `pip`, `uv`, `pytest`, `cargo`).
  - Non-blocking async process runner with timeout and output capture capabilities.
- [ ] **Git Version Control Integration**:
  - `git_init`, `git_status`, `git_commit`, `git_branch`, `git_diff`, `git_log`.
  - Automatic commit checkpoints prior to major AI refactoring sessions.
- [ ] **Backup & Versioning Engine**:
  - Auto-backup overwritten/deleted files into `backup_dir` before mutation, enabling single-click rollback.
- [ ] **Project Scaffolding Templates**:
  - Dynamic template registry (`template_dir`) supporting parameterized project bootstrapping (e.g. FastAPI + React, Next.js + Tailwind, Rust CLI).
- [ ] **Semantic Vector Search & Indexing**:
  - Embedding indexer (`uv run workspace-mcp index`) for instant semantic code discovery across million-line codebases.

---

## 🌟 Phase 3: Multi-Agent Workflows & Intelligent Workspace Systems (Future Vision)

- [ ] **Multi-Agent Task Orchestration**:
  - Standardized agent communication protocols for delegating architecture, implementation, and review tasks to sub-agents.
- [ ] **Persistent Codebase Memory**:
  - Architectural Knowledge Graph tracking dependencies, decisions, API contracts, and structural changes across sessions.
- [ ] **Real-Time Workspace Synchronization**:
  - WebSockets / SSE transport extensions for live IDE code synchronization and real-time visual progress monitoring.
