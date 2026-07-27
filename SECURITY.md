# Security Policy for Workspace MCP

Security is a primary design pillar of **Workspace MCP**. Because this server grants LLMs and AI assistants direct filesystem access, security controls are strictly enforced to prevent path traversal, arbitrary file writes, symlink attacks, and unauthorized system access.

## Supported Versions

| Version | Supported          | Security Maintenance |
| ------- | ------------------ | -------------------- |
| 1.0.x   | :white_check_mark: | Active               |
| < 1.0   | :x:                | Deprecated           |

## Security Guarantees & Features

1. **Sandboxed Workspace**: All file/directory operations are strictly bound within the resolved `workspace_root` directory.
2. **Anti-Traversal Validation**: Every path input is resolved via `os.path.realpath` / `Path.resolve(strict=False)`. Relative `..` traversal sequences and leading slashes are validated and rejected if they step outside the root (`PATH_TRAVERSAL` / `WORKSPACE_VIOLATION`).
3. **Symlink Escape Protection**: Unresolved candidate paths and their parent directories are checked against symlink resolution policies. Symlinks that point outside the workspace root are blocked (`SYMLINK_ESCAPE`).
4. **OS Reserved Device Filtering**: Filenames like `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, and `LPT1-9` are rejected across all operating systems to prevent OS device lockup or escape vulnerabilities.
5. **Confirmation Gating**: Destructive file/directory deletions and full overwrites require explicit confirmation parameters (`confirm=True` / `overwrite=True`).
6. **File Size Limits**: File read/write bounds are capped (default 10 MB per write, 2 MB for search scans) to prevent Denial of Service (DoS) through resource exhaustion.

## Reporting a Vulnerability

If you discover a security vulnerability or path traversal bypass in Workspace MCP:

1. **Do NOT open a public GitHub issue.**
2. Send a detailed report directly to `shanmukhdatta@gmail.com`.
3. Include reproduction steps, sample payload / path string, and expected vs actual behavior.
4. We will acknowledge receipt of your report within 24-48 hours and work with you to release a patch promptly.
