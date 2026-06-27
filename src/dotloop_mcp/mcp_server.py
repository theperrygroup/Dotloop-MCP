"""FastMCP server construction for Dotloop."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from dotloop import DotloopClient

from dotloop_mcp.config import DotloopServerSettings, DotloopSettings
from dotloop_mcp.logging import configure_logging
from dotloop_mcp.mcp_registration import register_server_surface
from dotloop_mcp.mcp_tools import DotloopToolAdapter
from dotloop_mcp.services import DotloopService
from mcp.server.fastmcp import FastMCP

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_server(
    settings: DotloopSettings | None = None,
    *,
    server_settings: DotloopServerSettings | None = None,
    client: Any | None = None,
    service: DotloopService | None = None,
    host: str | None = None,
    port: int | None = None,
    streamable_http_path: str | None = None,
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

    Returns:
        Registered FastMCP server.
    """
    resolved_server_settings = server_settings or DotloopServerSettings.from_env()
    configure_logging(resolved_server_settings.log_level)

    if service is None:
        if client is None:
            resolved_settings = settings or DotloopSettings.from_env()
            client = DotloopClient(
                api_key=resolved_settings.access_token,
                base_url=resolved_settings.base_url,
                timeout=resolved_settings.timeout,
            )
        service = DotloopService(client)

    adapter = DotloopToolAdapter(service)
    mcp = FastMCP(
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
        log_level=cast(
            Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            resolved_server_settings.log_level,
        ),
    )
    register_server_surface(mcp, adapter, project_root=_PROJECT_ROOT)
    return mcp
