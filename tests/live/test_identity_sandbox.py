"""Optional live Dotloop read smoke tests."""

from __future__ import annotations

import os

import pytest

from dotloop_mcp.config import DotloopConfigurationError, DotloopSettings, load_dotloop_env_file
from dotloop_mcp.mcp_server import create_server


def _load_live_env() -> str | None:
    """Load optional local live-test env and return a safe error string."""
    try:
        load_dotloop_env_file()
    except DotloopConfigurationError as exc:
        return str(exc)
    return None


_LIVE_ENV_ERROR = _load_live_env()


def _live_run_flag_enabled() -> bool:
    """Whether live tests were explicitly enabled."""
    return os.getenv("DOTLOOP_RUN_LIVE_TESTS") == "1"


def _optional_live_value_present(name: str) -> bool:
    """Whether an optional live-test target is configured."""
    return bool(os.getenv(name))


def _required_live_int(name: str) -> int:
    """Read a required live-test integer env value."""
    raw_value = os.getenv(name)
    if raw_value is None:
        pytest.fail(f"{name} is required for this live read smoke.")
    try:
        return int(raw_value)
    except ValueError:
        pytest.fail(f"{name} must be an integer.")


def _live_settings() -> DotloopSettings:
    """Load live Dotloop settings, failing loudly only after explicit opt-in."""
    if _LIVE_ENV_ERROR is not None:
        raise DotloopConfigurationError(_LIVE_ENV_ERROR)
    return DotloopSettings.from_env()


_SKIP_LIVE_DISABLED = pytest.mark.skipif(
    not _live_run_flag_enabled(),
    reason="Set DOTLOOP_RUN_LIVE_TESTS=1 to run live Dotloop tests.",
)


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.asyncio
async def test_live_account_smoke() -> None:
    """Read the live Dotloop account through the MCP public tool surface."""
    server = create_server(settings=_live_settings())
    result = await server.call_tool("dotloop_get_account", {})
    assert result


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.asyncio
async def test_live_profile_list_smoke() -> None:
    """Read live Dotloop profiles through the MCP public tool surface."""
    server = create_server(settings=_live_settings())
    result = await server.call_tool("dotloop_list_profiles", {})
    assert result


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.skipif(
    not _optional_live_value_present("DOTLOOP_LIVE_PROFILE_ID"),
    reason="Set DOTLOOP_LIVE_PROFILE_ID to run profile-specific live reads.",
)
@pytest.mark.asyncio
async def test_live_profile_get_smoke() -> None:
    """Read one live Dotloop profile through the MCP public tool surface."""
    profile_id = _required_live_int("DOTLOOP_LIVE_PROFILE_ID")
    server = create_server(settings=_live_settings())
    result = await server.call_tool("dotloop_get_profile", {"profile_id": profile_id})
    assert result


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.skipif(
    not _optional_live_value_present("DOTLOOP_LIVE_PROFILE_ID"),
    reason="Set DOTLOOP_LIVE_PROFILE_ID to run profile-specific live reads.",
)
@pytest.mark.asyncio
async def test_live_loop_list_smoke() -> None:
    """List live Dotloop loops for a configured profile."""
    profile_id = _required_live_int("DOTLOOP_LIVE_PROFILE_ID")
    server = create_server(settings=_live_settings())
    result = await server.call_tool("dotloop_list_loops", {"profile_id": profile_id})
    assert result


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.skipif(
    not (
        _optional_live_value_present("DOTLOOP_LIVE_PROFILE_ID")
        and _optional_live_value_present("DOTLOOP_LIVE_LOOP_ID")
    ),
    reason="Set DOTLOOP_LIVE_PROFILE_ID and DOTLOOP_LIVE_LOOP_ID to run loop live reads.",
)
@pytest.mark.asyncio
async def test_live_loop_get_smoke() -> None:
    """Read one live Dotloop loop through the MCP public tool surface."""
    profile_id = _required_live_int("DOTLOOP_LIVE_PROFILE_ID")
    loop_id = _required_live_int("DOTLOOP_LIVE_LOOP_ID")
    server = create_server(settings=_live_settings())
    result = await server.call_tool(
        "dotloop_get_loop",
        {"profile_id": profile_id, "loop_id": loop_id},
    )
    assert result


@pytest.mark.live
@_SKIP_LIVE_DISABLED
@pytest.mark.skipif(
    not (
        _optional_live_value_present("DOTLOOP_LIVE_PROFILE_ID")
        and _optional_live_value_present("DOTLOOP_LIVE_LOOP_ID")
        and _optional_live_value_present("DOTLOOP_LIVE_DOCUMENT_ID")
    ),
    reason=(
        "Set DOTLOOP_LIVE_PROFILE_ID, DOTLOOP_LIVE_LOOP_ID, and "
        "DOTLOOP_LIVE_DOCUMENT_ID to run document metadata live reads."
    ),
)
@pytest.mark.asyncio
async def test_live_document_metadata_smoke() -> None:
    """Read live Dotloop document metadata through the MCP public tool surface."""
    profile_id = _required_live_int("DOTLOOP_LIVE_PROFILE_ID")
    loop_id = _required_live_int("DOTLOOP_LIVE_LOOP_ID")
    document_id = _required_live_int("DOTLOOP_LIVE_DOCUMENT_ID")
    server = create_server(settings=_live_settings())
    result = await server.call_tool(
        "dotloop_get_document",
        {"profile_id": profile_id, "loop_id": loop_id, "document_id": document_id},
    )
    assert result
