"""Reference hosted entrypoint for Dotloop MCP deployments."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import replace

from dotloop_mcp.config import DotloopConfigurationError, DotloopServerSettings
from dotloop_mcp.mcp_server import create_server


def build_parser() -> argparse.ArgumentParser:
    """Build the hosted entrypoint argument parser."""
    parser = argparse.ArgumentParser(description="Run the hosted Dotloop MCP server.")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--path", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the hosted streamable HTTP server.

    Raises:
        DotloopConfigurationError: If hosted MCP URL auth is not configured.
    """
    args = build_parser().parse_args(argv)
    server_settings = DotloopServerSettings.from_env()
    server_settings = replace(
        server_settings,
        transport="streamable-http",
        host=args.host or server_settings.host,
        port=args.port or server_settings.port,
        streamable_http_path=args.path or server_settings.streamable_http_path,
    )
    if not server_settings.mcp_auth.enabled:
        raise DotloopConfigurationError("Hosted Dotloop MCP requires DOTLOOP_MCP_AUTH_ENABLED=1.")

    server = create_server(server_settings=server_settings)
    server.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
