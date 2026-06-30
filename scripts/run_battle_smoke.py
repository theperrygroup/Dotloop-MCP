"""Run a tiny fixture-mode MCP battle smoke and write a call log."""

from __future__ import annotations

import anyio

from dotloop_mcp.mcp_server import create_server


async def _run_smoke() -> None:
    server = create_server()
    tools = {tool.name for tool in await server.list_tools()}
    if "dotloop_get_account" not in tools:
        raise RuntimeError("dotloop_get_account is not registered.")
    await server.call_tool("dotloop_get_account", {})


def main() -> int:
    """Run the smoke check."""
    anyio.run(_run_smoke)
    print("Battle fixture smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
