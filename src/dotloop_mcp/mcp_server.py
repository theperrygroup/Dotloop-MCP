"""FastMCP server construction for Dotloop."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from dotloop import DotloopClient
from starlette.applications import Starlette

from dotloop_mcp.app_oauth import build_dotloop_app_credential_provider
from dotloop_mcp.auth import DotloopMcpJwtVerifier, build_mcp_auth_settings
from dotloop_mcp.battle_fixtures import BattleFixtureDotloopClient
from dotloop_mcp.battle_recording import ToolCallRecorder
from dotloop_mcp.config import DotloopConfigurationError, DotloopServerSettings, DotloopSettings
from dotloop_mcp.hosted_oauth import DotloopHostedOAuthApplication
from dotloop_mcp.logging import configure_logging
from dotloop_mcp.mcp_registration import register_server_surface
from dotloop_mcp.mcp_tools import DotloopToolAdapter
from dotloop_mcp.services import DotloopService, UnavailableDotloopService
from mcp.server.auth.provider import TokenVerifier
from mcp.server.fastmcp import FastMCP

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DotloopFastMCP(FastMCP):
    """FastMCP subclass that mounts hosted OAuth issuer routes when configured."""

    _hosted_oauth_application: DotloopHostedOAuthApplication | None = None

    def streamable_http_app(self) -> Starlette:
        """Return the streamable HTTP app with hosted OAuth routes mounted."""
        app = super().streamable_http_app()
        if self._hosted_oauth_application is None:
            return app

        existing_paths = {getattr(route, "path", None) for route in app.routes}
        for route in self._hosted_oauth_application.routes():
            if route.path not in existing_paths:
                app.routes.append(route)
        return app


def create_server(
    settings: DotloopSettings | None = None,
    *,
    server_settings: DotloopServerSettings | None = None,
    client: Any | None = None,
    service: DotloopService | None = None,
    host: str | None = None,
    port: int | None = None,
    streamable_http_path: str | None = None,
    token_verifier: TokenVerifier | None = None,
) -> FastMCP:
    """Create a registered Dotloop FastMCP server.

    Args:
        settings: Optional local Dotloop settings.
        server_settings: Optional server bootstrap settings.
        client: Optional Dotloop client or test double.
        service: Optional prebuilt service adapter.
        host: Optional host override.
        port: Optional port override.
        streamable_http_path: Optional streamable HTTP path override.
        token_verifier: Optional inbound MCP auth verifier override.

    Returns:
        Registered FastMCP server.
    """
    resolved_server_settings = server_settings or DotloopServerSettings.from_env()
    configure_logging(resolved_server_settings.log_level)

    dotloop_credential_provider = None
    if service is None:
        if resolved_server_settings.battle_fixture_mode:
            service = DotloopService(BattleFixtureDotloopClient())
        elif client is None:
            if resolved_server_settings.app_oauth.enabled:
                dotloop_credential_provider = build_dotloop_app_credential_provider(
                    resolved_server_settings.app_oauth
                )
                client = dotloop_credential_provider.build_client_factory()
            else:
                try:
                    resolved_settings = settings or DotloopSettings.from_env()
                except DotloopConfigurationError:
                    if not resolved_server_settings.allow_missing_access_token:
                        raise
                    service = UnavailableDotloopService(
                        "Dotloop access token is not configured for this hosted MCP deployment."
                    )
                else:
                    client = DotloopClient(
                        api_key=resolved_settings.access_token,
                        base_url=resolved_settings.base_url,
                        timeout=resolved_settings.timeout,
                    )
        if service is None:
            service = DotloopService(client)

    adapter = DotloopToolAdapter(
        service,
        recorder=ToolCallRecorder.from_path(resolved_server_settings.battle_record_path),
    )
    mcp_auth = resolved_server_settings.mcp_auth
    auth_settings = build_mcp_auth_settings(mcp_auth) if mcp_auth.enabled else None
    resolved_token_verifier = None
    hosted_oauth_application = None
    if mcp_auth.enabled:
        if resolved_server_settings.hosted_oauth.enabled:
            hosted_oauth_application = DotloopHostedOAuthApplication(
                auth_settings=mcp_auth,
                hosted_settings=resolved_server_settings.hosted_oauth,
                dotloop_credential_provider=dotloop_credential_provider,
            )
            resolved_token_verifier = token_verifier or hosted_oauth_application.token_verifier()
        else:
            resolved_token_verifier = token_verifier or DotloopMcpJwtVerifier(mcp_auth)
    mcp = DotloopFastMCP(
        "Dotloop MCP",
        instructions=(
            "Use the Dotloop read tools for account, profile, loop, loop detail, folder, "
            "document, participant, task, activity, and template inspection. This server is "
            "read-first: do not claim support for creating, updating, deleting, uploading, "
            "or changing Dotloop resources through v1 tools."
        ),
        host=host or resolved_server_settings.host,
        port=port or resolved_server_settings.port,
        streamable_http_path=streamable_http_path or resolved_server_settings.streamable_http_path,
        json_response=True,
        auth=auth_settings,
        token_verifier=resolved_token_verifier,
        log_level=cast(
            Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            resolved_server_settings.log_level,
        ),
    )
    mcp._hosted_oauth_application = hosted_oauth_application
    register_server_surface(mcp, adapter, project_root=_PROJECT_ROOT)
    return mcp
