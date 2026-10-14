# Workspace MCP Roadmap

## Phase 1 — Existing stable release

- [x] Original 22 FastMCP filesystem, directory, search, documentation and validation tools.
- [x] PathValidator, layered settings and dual audit logging.
- [x] Platform integrations via MCP transport and documentation.

## Phase 2 — Extension branch implementation

- [x] **Opt-in terminal runner**: `run_command(argv, cwd, timeout)` via
  asyncio subprocess with a validated working directory, bounded output, timeout,
  and an allowlist. **Security limit:** child processes themselves are not OS
  sandboxed; command execution remains disabled by default.
- [x] **Opt-in Git tools**: `git_init`, `git_status`, `git_branch`,
  `git_diff`, `git_log`, `git_commit`. Commits can snapshot named files first.
- [x] **Backup engine**: pre-mutation file backups with SHA-256 manifests,
  `list_backups` and confirmed `restore_backup`.
- [x] **Template registry**: built-in FastAPI/React, Next.js and Rust starters
  plus safe parameterized local templates.
- [x] **Incremental SQLite code index** with CLI `workspace-mcp index` and
  `search_code`, lexical mode by default and optional genuine local embeddings.
- [ ] **Million-line performance guarantee**: needs benchmark measurements,
  streaming index optimizations and production-scale testing.

## Phase 3 — Extension branch foundations

- [x] **Multi-agent task protocol**: durable submit/claim/finish/status queue,
  with standard roles. Client agents are responsible for executing tasks.
- [ ] **Automatic agent spawning and orchestration**: not implemented; requires
  model provider integrations, budgets, cancellation and strong isolation.
- [x] **Persistent codebase knowledge graph**: decision, dependency, API
  contract and architecture facts, with typed relationships in SQLite.
- [x] **Incremental workspace event polling** using persistent audit-log cursors,
  supported over the server's existing MCP transports.
- [ ] **Bidirectional real-time WebSockets/SSE file synchronization**,
  authenticated subscriptions, conflict handling, and IDE UI progress:
  beyond the current polling/event foundation.

See [Extension Security and Rollout](docs/EXTENSION_SECURITY.md).
**Branch status:** implementation is not equivalent to production validation.
The `extension` PR must pass automated and IDE tests before merging.
