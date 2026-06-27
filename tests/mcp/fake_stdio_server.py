"""Fake stdio server used by MCP client smoke tests."""

from __future__ import annotations

from tests.conftest import FakeDotloopClient

from dotloop_mcp.config import DotloopServerSettings
from dotloop_mcp.mcp_server import create_server
from dotloop_mcp.services import DotloopService


def main() -> None:
    """Run a fake Dotloop MCP server over stdio."""
    server = create_server(
        server_settings=DotloopServerSettings(),
        service=DotloopService(FakeDotloopClient()),
    )
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
