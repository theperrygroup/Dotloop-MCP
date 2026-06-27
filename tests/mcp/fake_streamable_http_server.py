"""Fake streamable HTTP server used by MCP client smoke tests."""

from __future__ import annotations

import argparse

from tests.conftest import FakeDotloopClient

from dotloop_mcp.config import DotloopServerSettings
from dotloop_mcp.mcp_server import create_server
from dotloop_mcp.services import DotloopService


def build_parser() -> argparse.ArgumentParser:
    """Build the fake server argument parser."""
    parser = argparse.ArgumentParser(description="Run fake Dotloop MCP streamable HTTP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--path", default="/mcp")
    return parser


def main() -> None:
    """Run a fake Dotloop MCP server over streamable HTTP."""
    args = build_parser().parse_args()
    server = create_server(
        server_settings=DotloopServerSettings(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path=args.path,
        ),
        service=DotloopService(FakeDotloopClient()),
    )
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
