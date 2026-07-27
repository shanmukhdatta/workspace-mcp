# Workspace MCP Architecture & Visual Assets

This directory contains visual architecture diagrams, banners, and media assets for Workspace MCP.

## System Flow Architecture

```
+-------------------------------------------------------------------------+
|                              IDE / AI CLIENT                            |
|     (Claude Desktop, Claude Code, Antigravity IDE, VS Code, Ollama)     |
+-------------------------------------------------------------------------+
                                     |
                         MCP Protocol (Stdio / SSE)
                                     v
+-------------------------------------------------------------------------+
|                          WORKSPACE MCP SERVER                           |
|                      (FastMCP Entry Point: server.py)                   |
+-------------------------------------------------------------------------+
       |                             |                            |
       v                             v                            v
+--------------+             +---------------+            +---------------+
| Config Layer |             |  Tools Layer  |            | Logging Engine|
| (settings.py)|             | (22 MCP Tools)|            | (logger.py)   |
+--------------+             +---------------+            +---------------+
                                     |
                                     v
                             +---------------+
                             | Services Layer|
                             |  (Business    |
                             |     Logic)    |
                             +---------------+
                                     |
                                     v
                        +-------------------------+
                        | Security Sandbox Engine |
                        | (utils/pathsec.py)      |
                        +-------------------------+
                                     |
                        Safe Realpath Resolution
                                     v
                        +-------------------------+
                        |  Local Filesystem Root  |
                        |   (Sandboxed Storage)   |
                        +-------------------------+
```
