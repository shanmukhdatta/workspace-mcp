"""
workspace_mcp
=============

A production-ready Model Context Protocol (MCP) server that lets an
MCP-compatible AI assistant (e.g. Claude Desktop) create and manage real
software projects directly on the local filesystem -- no ZIP files, no
copy/paste. Every operation is confined to a single configured workspace
directory and is validated, logged, and auditable.

See ``docs/ARCHITECTURE.md`` for a tour of the codebase.
"""

from __future__ import annotations

__version__ = "1.0.0"
