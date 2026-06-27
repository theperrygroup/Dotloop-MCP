"""MCP server and tool registration tests."""

from __future__ import annotations

import socket
import subprocess
import sys
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path
from typing import Any

import anyio
import pytest
from pydantic import AnyUrl
from tests.conftest import FakeDotloopClient

from dotloop_mcp.config import DotloopServerSettings
from dotloop_mcp.coverage import COVERAGE_RESOURCE_URI, METHOD_COVERAGE_RESOURCE_URI
from dotloop_mcp.mcp_server import create_server
from dotloop_mcp.services import DotloopService
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextResourceContents

EXPECTED_TOOLS = {
    "dotloop_get_account",
    "dotloop_list_profiles",
    "dotloop_get_profile",
    "dotloop_list_loops",
    "dotloop_get_loop",
    "dotloop_get_loop_details",
    "dotloop_list_folders",
    "dotloop_get_folder",
    "dotloop_list_documents",
    "dotloop_get_document",
    "dotloop_download_document",
    "dotloop_list_participants",
    "dotloop_get_participant",
    "dotloop_list_task_lists",
    "dotloop_get_task_list",
    "dotloop_list_tasks",
    "dotloop_get_task",
    "dotloop_get_task_summary",
    "dotloop_get_all_tasks_in_loop",
    "dotloop_get_pending_tasks",
    "dotloop_get_completed_tasks",
    "dotloop_list_loop_activity",
    "dotloop_get_recent_activity",
    "dotloop_get_activity_summary",
    "dotloop_get_activity_by_type",
    "dotloop_get_activity_by_user",
    "dotloop_list_loop_templates",
    "dotloop_get_loop_template",
    "dotloop_find_template_by_name",
    "dotloop_get_template_summary",
    "dotloop_get_templates_by_type",
    "dotloop_get_default_templates",
    "dotloop_get_custom_templates",
}

TOOL_CALLS: tuple[tuple[str, dict[str, object]], ...] = (
    ("dotloop_get_account", {}),
    ("dotloop_list_profiles", {}),
    ("dotloop_get_profile", {"profile_id": 10}),
    (
        "dotloop_list_loops",
        {"profile_id": 10, "batch_size": 25, "batch_number": 2, "include_details": True},
    ),
    ("dotloop_get_loop", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_loop_details", {"profile_id": 10, "loop_id": 20}),
    (
        "dotloop_list_folders",
        {"profile_id": 10, "loop_id": 20, "include_documents": True},
    ),
    (
        "dotloop_get_folder",
        {"profile_id": 10, "loop_id": 20, "folder_id": 30, "include_archived": True},
    ),
    ("dotloop_list_documents", {"profile_id": 10, "loop_id": 20, "folder_id": 30}),
    ("dotloop_get_document", {"profile_id": 10, "loop_id": 20, "document_id": 40}),
    ("dotloop_download_document", {"profile_id": 10, "loop_id": 20, "document_id": 40}),
    ("dotloop_list_participants", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_participant", {"profile_id": 10, "loop_id": 20, "participant_id": 50}),
    ("dotloop_list_task_lists", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_task_list", {"profile_id": 10, "loop_id": 20, "tasklist_id": 60}),
    ("dotloop_list_tasks", {"profile_id": 10, "loop_id": 20, "tasklist_id": 60}),
    ("dotloop_get_task", {"profile_id": 10, "loop_id": 20, "tasklist_id": 60, "task_id": 70}),
    ("dotloop_get_task_summary", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_all_tasks_in_loop", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_pending_tasks", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_get_completed_tasks", {"profile_id": 10, "loop_id": 20}),
    ("dotloop_list_loop_activity", {"profile_id": 10, "loop_id": 20, "batch_size": 10}),
    ("dotloop_get_recent_activity", {"profile_id": 10, "loop_id": 20, "limit": 5}),
    ("dotloop_get_activity_summary", {"profile_id": 10, "loop_id": 20}),
    (
        "dotloop_get_activity_by_type",
        {"profile_id": 10, "loop_id": 20, "activity_type": "Document", "batch_size": 10},
    ),
    (
        "dotloop_get_activity_by_user",
        {"profile_id": 10, "loop_id": 20, "user_name": "Ada", "batch_size": 10},
    ),
    ("dotloop_list_loop_templates", {"profile_id": 10}),
    ("dotloop_get_loop_template", {"profile_id": 10, "template_id": 80}),
    ("dotloop_find_template_by_name", {"profile_id": 10, "template_name": "Buyer"}),
    ("dotloop_get_template_summary", {"profile_id": 10}),
    ("dotloop_get_templates_by_type", {"profile_id": 10, "template_type": "default"}),
    ("dotloop_get_default_templates", {"profile_id": 10}),
    ("dotloop_get_custom_templates", {"profile_id": 10}),
)


def _server() -> Any:
    return create_server(
        server_settings=DotloopServerSettings(),
        service=DotloopService(FakeDotloopClient()),
    )


def _unused_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return int(server_socket.getsockname()[1])


async def _wait_for_local_port(port: int) -> None:
    for _ in range(50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(0.1)
            if client_socket.connect_ex(("127.0.0.1", port)) == 0:
                return
        await anyio.sleep(0.1)
    raise AssertionError(f"Timed out waiting for local port {port}.")


async def _call_tool(
    server: Any,
    tools: Mapping[str, Any],
    name: str,
    args: dict[str, object] | None = None,
) -> dict[str, Any]:
    assert name in tools
    result = await server.call_tool(name, args or {})
    if isinstance(result, dict):
        return result
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
        structured_result = result[1].get("result")
        if isinstance(structured_result, dict):
            return structured_result
        return result[1]
    raise AssertionError(f"Unexpected tool result: {result!r}")


@pytest.mark.asyncio
async def test_registered_tools_and_resource() -> None:
    server = _server()

    tools = {tool.name: tool for tool in await server.list_tools()}
    resources = await server.list_resources()
    resource_contents = list(await server.read_resource(COVERAGE_RESOURCE_URI))
    method_resource_contents = list(await server.read_resource(METHOD_COVERAGE_RESOURCE_URI))
    resource_uris = {str(resource.uri) for resource in resources}

    assert EXPECTED_TOOLS.issubset(tools)
    assert {COVERAGE_RESOURCE_URI, METHOD_COVERAGE_RESOURCE_URI}.issubset(resource_uris)
    assert "Dotloop MCP API Coverage Matrix" in resource_contents[0].content
    assert "Dotloop Library Method Coverage" in method_resource_contents[0].content


@pytest.mark.asyncio
async def test_representative_tools_call_through_public_surface() -> None:
    server = _server()
    tools = {tool.name: tool for tool in await server.list_tools()}

    account = await _call_tool(server, tools, "dotloop_get_account")
    profiles = await _call_tool(server, tools, "dotloop_list_profiles")
    loop = await _call_tool(server, tools, "dotloop_get_loop", {"profile_id": 10, "loop_id": 20})
    document = await _call_tool(
        server,
        tools,
        "dotloop_download_document",
        {"profile_id": 10, "loop_id": 20, "document_id": 40},
    )
    template = await _call_tool(
        server,
        tools,
        "dotloop_find_template_by_name",
        {"profile_id": 10, "template_name": "Buyer"},
    )

    assert account["data"]["firstName"] == "Ada"
    assert profiles["data"][0]["id"] == 10
    assert loop["data"]["id"] == 20
    assert document["contentType"] == "application/pdf"
    assert template["data"]["name"] == "Buyer"


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "arguments"), TOOL_CALLS)
async def test_all_read_tools_call_through_public_surface(
    name: str,
    arguments: dict[str, object],
) -> None:
    server = _server()
    tools = {tool.name: tool for tool in await server.list_tools()}

    result = await _call_tool(server, tools, name, arguments)

    assert result


@pytest.mark.asyncio
async def test_stdio_client_can_list_and_call_representative_tool() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tests.mcp.fake_stdio_server"],
        cwd=Path.cwd(),
    )

    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            coverage_resource = await session.read_resource(AnyUrl(COVERAGE_RESOURCE_URI))
            result = await session.call_tool("dotloop_get_account", {})

    tool_names = {tool.name for tool in tools.tools}
    coverage_content = coverage_resource.contents[0]

    assert "dotloop_get_account" in tool_names
    assert isinstance(coverage_content, TextResourceContents)
    assert "Dotloop MCP API Coverage Matrix" in coverage_content.text
    assert result.structuredContent == {"result": {"data": {"id": 1, "firstName": "Ada"}}}


@pytest.mark.asyncio
async def test_streamable_http_client_can_list_and_call_representative_tool() -> None:
    port = _unused_local_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tests.mcp.fake_streamable_http_server",
            "--port",
            str(port),
        ],
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        await _wait_for_local_port(port)
        async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (
            read_stream,
            write_stream,
            _get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                method_coverage_resource = await session.read_resource(
                    AnyUrl(METHOD_COVERAGE_RESOURCE_URI)
                )
                result = await session.call_tool("dotloop_get_account", {})

        tool_names = {tool.name for tool in tools.tools}
        method_coverage_content = method_coverage_resource.contents[0]

        assert "dotloop_get_account" in tool_names
        assert isinstance(method_coverage_content, TextResourceContents)
        assert "Dotloop Library Method Coverage" in method_coverage_content.text
        assert result.structuredContent == {"result": {"data": {"id": 1, "firstName": "Ada"}}}
    finally:
        process.terminate()
        with suppress(subprocess.TimeoutExpired):
            process.communicate(timeout=5)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
