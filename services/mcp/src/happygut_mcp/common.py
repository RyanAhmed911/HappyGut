"""Shared pieces for the HappyGut MCP servers: read-only tool annotations, bearer auth, the runner."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .foodgraph import BearerAuth

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
# For tools that read the patient's records from the HappyGut API (still read-only, but not a closed world).
READ_ONLY_REMOTE = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)


def run(build: Callable[[], MCPServer], doc: str, default_port: int) -> None:
    """stdio by default; ``--http`` serves Streamable HTTP behind MCP_BEARER_TOKEN."""
    parser = argparse.ArgumentParser(description=doc.split("\n\n")[0])
    parser.add_argument("--http", action="store_true", help="serve Streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=default_port)
    args = parser.parse_args()
    server = build()
    if not args.http:
        server.run("stdio")
        return
    import uvicorn

    uvicorn.run(BearerAuth(server.streamable_http_app(), os.environ.get("MCP_BEARER_TOKEN", "")), host=args.host, port=args.port)
