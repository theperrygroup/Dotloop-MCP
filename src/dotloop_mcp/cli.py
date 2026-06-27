"""Command-line entrypoint for the Dotloop MCP server."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from dotloop_mcp.config import DotloopServerSettings
from dotloop_mcp.mcp_server import create_server


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Run the Dotloop MCP server.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("stdio", help="Run stdio transport.")

    http_parser = subparsers.add_parser("streamable-http", help="Run streamable HTTP transport.")
    http_parser.add_argument("--host", default=None)
    http_parser.add_argument("--port", type=int, default=None)
    http_parser.add_argument("--path", default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Dotloop MCP CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "stdio"

    if command == "stdio":
        server_settings = DotloopServerSettings.from_env()
        server = create_server(server_settings=server_settings)
        server.run(transport="stdio")
        return 0

    if command == "streamable-http":
        server_settings = DotloopServerSettings.from_env()
        server = create_server(
            server_settings=server_settings,
            host=args.host,
            port=args.port,
            streamable_http_path=args.path,
        )
        server.run(transport="streamable-http")
        return 0

    parser.error(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
