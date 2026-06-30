"""Fake streamable HTTP server used by MCP client smoke tests."""

from __future__ import annotations

import argparse

from tests.conftest import FakeDotloopClient

from dotloop_mcp.config import DotloopMcpAuthSettings, DotloopServerSettings
from dotloop_mcp.mcp_server import create_server
from dotloop_mcp.services import DotloopService
from mcp.server.auth.provider import AccessToken


class AllowTokenVerifier:
    """Test verifier for authenticated streamable HTTP smoke tests."""

    def __init__(self, resource_url: str, issuer_url: str) -> None:
        self._resource_url = resource_url
        self._issuer_url = issuer_url

    async def verify_token(self, token: str) -> AccessToken | None:
        if token != "good-token":
            return None
        return AccessToken(
            token="[validated]",
            client_id="test-client",
            scopes=["dotloop:read"],
            resource=self._resource_url,
            subject="user-123",
            claims={"iss": self._issuer_url},
        )


def build_parser() -> argparse.ArgumentParser:
    """Build the fake server argument parser."""
    parser = argparse.ArgumentParser(description="Run fake Dotloop MCP streamable HTTP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--auth", action="store_true")
    return parser


def main() -> None:
    """Run a fake Dotloop MCP server over streamable HTTP."""
    args = build_parser().parse_args()
    resource_url = f"http://127.0.0.1:{args.port}{args.path}"
    issuer_url = f"http://127.0.0.1:{args.port}/auth"
    auth_settings = (
        DotloopMcpAuthSettings(
            enabled=True,
            issuer_url=issuer_url,
            resource_server_url=resource_url,
            jwks_url=f"http://127.0.0.1:{args.port}/jwks",
            required_scopes=("dotloop:read",),
        )
        if args.auth
        else DotloopMcpAuthSettings()
    )
    server = create_server(
        server_settings=DotloopServerSettings(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path=args.path,
            mcp_auth=auth_settings,
        ),
        service=DotloopService(FakeDotloopClient()),
        token_verifier=AllowTokenVerifier(resource_url, issuer_url) if args.auth else None,
    )
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
