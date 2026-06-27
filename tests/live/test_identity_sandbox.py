"""Optional live Dotloop account smoke test."""

from __future__ import annotations

import os

import pytest

from dotloop_mcp.config import DotloopSettings
from dotloop_mcp.mcp_server import create_server


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("DOTLOOP_RUN_LIVE_TESTS") != "1",
    reason="Set DOTLOOP_RUN_LIVE_TESTS=1 to run live Dotloop tests.",
)
@pytest.mark.asyncio
async def test_live_account_smoke() -> None:
    """Read the live Dotloop account through the MCP public tool surface."""
    server = create_server(settings=DotloopSettings.from_env())
    result = await server.call_tool("dotloop_get_account", {})
    assert result


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("DOTLOOP_RUN_LIVE_TESTS") != "1",
    reason="Set DOTLOOP_RUN_LIVE_TESTS=1 to run live Dotloop tests.",
)
@pytest.mark.asyncio
async def test_live_profile_list_smoke() -> None:
    """Read live Dotloop profiles through the MCP public tool surface."""
    server = create_server(settings=DotloopSettings.from_env())
    result = await server.call_tool("dotloop_list_profiles", {})
    assert result
