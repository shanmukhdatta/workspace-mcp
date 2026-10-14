# Extension security, operations and rollout

The `extension` branch adds optional capabilities alongside the existing 22
filesystem tools. The default `main` behavior remains the baseline.

## Terminal and Git

Terminal execution is **disabled by default**. Enable it only on machines and
workspaces containing trusted code:

```bash
WORKSPACE_MCP_ENABLE_TERMINAL=true
WORKSPACE_MCP_ALLOWED_COMMANDS='["pytest","ruff","black","mypy"]'
WORKSPACE_MCP_COMMAND_TIMEOUT_SECONDS=120
```

Pass arguments as an array, e.g. `["pytest","-q"]`, with `cwd="Demo"`.
No shell is used; execution has a timeout, capped stdout/stderr, and a
validated workspace cwd. The service strips likely token/password environment
variables. However, **a child process is not a filesystem sandbox**.
Even allowlisted tools can execute untrusted project scripts or plugins or
write outside the workspace. For strong isolation use a disposable VM or
locked-down container; do not enable terminal execution for untrusted repos.

Git is also disabled by default:

```bash
WORKSPACE_MCP_ENABLE_GIT=true
```

Only local `init/status/branch/diff/log/add/commit` are available. `git_commit`
requires explicit project-relative paths and disables Git hooks for the commit.
No Git `push`, `fetch`, remote management, or reset functionality is exposed.
All commands run on top-level workspace projects; Git output is bounded.
Configure your local Git author name/email before committing.

## Backups and restoration

Existing files are snapshotted before `create_file(overwrite=True)`,
`write_file`, `append_file`, `update_file`, `move_file` overwrite,
`rename_file` overwrite and `delete_file`. Backups are protected under
`.workspace_mcp/backups/<id>/` with a SHA-256 manifest.
Use `list_backups` and `restore_backup(id, confirm=True)`.
Restoring an existing file also snapshots that file beforehand.

Scope limitation: directory and whole-project deletion are NOT snapshotted.
For critical projects, make Git commits or separate backups before deleting a
directory or project. Backups are not atomic with every operation, so crashes,
disk exhaustion and concurrent writers remain operational risks. The backup
file size threshold is configurable.

## Templates and indexing

`list_templates` lists built-ins and folders in `templates_dir` (default
`.workspace_mcp/templates`). Pass `template="rust-cli"`,
`"nextjs-tailwind"`, or `"fastapi-react"` to `create_project`, optionally
with `template_variables={"company": "Example"}`. Templates are minimal
starters, not guaranteed production-ready dependencies or applications.
Administrator-provided templates are text-only, capped in count/size, and
cannot use symlinks. Review custom templates before installation.

Run `workspace-mcp index MyProject --workspace-root ...` or call
`index_project("MyProject")`. Indexed content is stored in SQLite under
`.workspace_mcp/index`. Without a configured local embedding model,
`search_code` explicitly reports `mode="lexical"`, not semantic.
To enable genuine embedding similarity, install `sentence-transformers`
in the server environment and set
`WORKSPACE_MCP_SEMANTIC_MODEL_PATH=/absolute/local/model/directory`.
Indexing is bounded by `max_files`; millions of lines require performance
testing, batching, and incremental-index improvements.

## Persistent memory, agent coordination and synchronization

`remember_fact`, `link_facts`, and `query_memory` maintain a persistent
project-scoped SQLite knowledge graph. Records are local plaintext and
should not contain credentials.

`agent_submit`, `agent_claim`, `agent_finish`, and `agent_tasks` implement
a persistent task hand-off queue. Agents must poll and execute tasks in their
own clients; this is not an autonomous LLM spawning system.

`sync_events` exposes a resumable audit-log cursor for IDE polling.
It is not yet bidirectional WebSocket synchronization or a filesystem
watcher. The pre-existing MCP server supports SSE and streamable-HTTP
transport; configure transport and authentication appropriate to your host.
Never expose a command-capable MCP server directly to the public Internet.

## Rollout

1. Run the existing tests and new extension tests on Python 3.11/3.12.
2. Verify the baseline 22 tools continue to work in Claude Desktop and IDE.
3. Exercise backup/restore, Git and command gates in a disposable workspace.
4. Confirm auth and isolation before enabling network transports.
5. Review the draft PR, then merge only after CI and local operational checks.
