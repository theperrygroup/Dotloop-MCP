"""Server construction and CLI tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, cast

import httpx
import pytest
from tests.conftest import FakeDotloopClient

from dotloop_mcp import cli as cli_module
from dotloop_mcp import hosted_reference as hosted_module
from dotloop_mcp import mcp_server as server_module
from dotloop_mcp.config import (
    DotloopAppOAuthSettings,
    DotloopConfigurationError,
    DotloopHostedOAuthSettings,
    DotloopMcpAuthSettings,
    DotloopServerSettings,
    DotloopSettings,
)
from dotloop_mcp.coverage import (
    API_COVERAGE_MARKDOWN,
    COVERAGE_RESOURCE_URI,
    METHOD_COVERAGE_MARKDOWN,
    METHOD_COVERAGE_RESOURCE_URI,
)
from dotloop_mcp.mcp_registration import register_server_surface
from dotloop_mcp.mcp_tools import DotloopToolAdapter
from dotloop_mcp.services import DotloopService
from mcp.server.fastmcp import FastMCP


class RunnableServer:
    """Small fake for CLI transport dispatch."""

    def __init__(self) -> None:
        self.transports: list[str] = []

    def run(self, transport: str) -> None:
        self.transports.append(transport)


class ConstructedFakeDotloopClient(FakeDotloopClient):
    """Fake DotloopClient replacement that records constructor kwargs."""

    calls: ClassVar[list[dict[str, object]]] = []

    def __init__(self, api_key: str, base_url: str, timeout: int) -> None:
        super().__init__()
        self.calls.append({"api_key": api_key, "base_url": base_url, "timeout": timeout})


def test_cli_runs_default_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_server = RunnableServer()
    calls: list[dict[str, object]] = []

    def fake_create_server(**kwargs: object) -> RunnableServer:
        calls.append(kwargs)
        return fake_server

    monkeypatch.setattr(cli_module, "create_server", fake_create_server)

    assert cli_module.main([]) == 0
    assert fake_server.transports == ["stdio"]
    assert isinstance(calls[0]["server_settings"], DotloopServerSettings)


def test_cli_runs_streamable_http_with_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_server = RunnableServer()
    calls: list[dict[str, object]] = []

    def fake_create_server(**kwargs: object) -> RunnableServer:
        calls.append(kwargs)
        return fake_server

    monkeypatch.setattr(cli_module, "create_server", fake_create_server)

    assert (
        cli_module.main(
            ["streamable-http", "--host", "0.0.0.0", "--port", "9000", "--path", "/custom"]
        )
        == 0
    )

    assert fake_server.transports == ["streamable-http"]
    assert calls[0]["host"] == "0.0.0.0"
    assert calls[0]["port"] == 9000
    assert calls[0]["streamable_http_path"] == "/custom"


def test_hosted_reference_requires_mcp_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(DotloopServerSettings, "from_env", lambda: DotloopServerSettings())

    with pytest.raises(DotloopConfigurationError, match="DOTLOOP_MCP_AUTH_ENABLED"):
        hosted_module.main([])


def test_hosted_reference_runs_streamable_http_with_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_server = RunnableServer()
    calls: list[dict[str, object]] = []
    settings = DotloopServerSettings(
        mcp_auth=DotloopMcpAuthSettings(
            enabled=True,
            issuer_url="http://127.0.0.1/auth",
            resource_server_url="http://127.0.0.1/mcp",
            jwks_url="http://127.0.0.1/jwks",
        )
    )

    def fake_create_server(**kwargs: object) -> RunnableServer:
        calls.append(kwargs)
        return fake_server

    monkeypatch.setattr(DotloopServerSettings, "from_env", lambda: settings)
    monkeypatch.setattr(hosted_module, "create_server", fake_create_server)

    assert hosted_module.main(["--host", "0.0.0.0", "--port", "9000", "--path", "/custom"]) == 0

    assert fake_server.transports == ["streamable-http"]
    server_settings = calls[0]["server_settings"]
    assert isinstance(server_settings, DotloopServerSettings)
    assert server_settings.transport == "streamable-http"
    assert server_settings.host == "0.0.0.0"
    assert server_settings.port == 9000
    assert server_settings.streamable_http_path == "/custom"


@pytest.mark.asyncio
async def test_create_server_constructs_client_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ConstructedFakeDotloopClient.calls.clear()
    monkeypatch.setattr(server_module, "DotloopClient", ConstructedFakeDotloopClient)

    server = server_module.create_server(
        DotloopSettings(
            access_token="token-value",
            base_url="https://example.test/public/v2",
            timeout=17,
        ),
        server_settings=DotloopServerSettings(log_level="WARNING"),
        host="0.0.0.0",
        port=9000,
        streamable_http_path="/custom",
    )
    result = cast(
        tuple[object, dict[str, Any]],
        await server.call_tool("dotloop_get_account", {}),
    )
    structured_result = result[1]
    payload = cast(dict[str, Any], structured_result["result"])

    assert ConstructedFakeDotloopClient.calls == [
        {
            "api_key": "token-value",
            "base_url": "https://example.test/public/v2",
            "timeout": 17,
        }
    ]
    assert payload["data"]["firstName"] == "Ada"


@pytest.mark.asyncio
async def test_create_server_uses_dotloop_app_oauth_client_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ConstructedFakeDotloopClient.calls.clear()

    class FakeCredentialProvider:
        def build_client_factory(self) -> object:
            return lambda: ConstructedFakeDotloopClient(
                api_key="oauth-token",
                base_url="https://example.test/public/v2",
                timeout=19,
            )

    monkeypatch.setattr(
        server_module,
        "build_dotloop_app_credential_provider",
        lambda _: FakeCredentialProvider(),
    )

    server = server_module.create_server(
        server_settings=DotloopServerSettings(
            app_oauth=DotloopAppOAuthSettings(
                enabled=True,
                client_id="client-id",
                client_secret="client-secret",
                redirect_url="https://dotloop.example.com/oauth/dotloop/callback",
                token_secret_arn="secret-id",
                base_url="https://example.test/public/v2",
                timeout=19,
            )
        )
    )
    await server.call_tool("dotloop_get_account", {})

    assert ConstructedFakeDotloopClient.calls == [
        {
            "api_key": "oauth-token",
            "base_url": "https://example.test/public/v2",
            "timeout": 19,
        }
    ]


@pytest.mark.asyncio
async def test_create_server_can_boot_with_unavailable_dotloop_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("DOTLOOP_API_KEY", raising=False)

    server = server_module.create_server(
        server_settings=DotloopServerSettings(allow_missing_access_token=True),
    )
    tools = {tool.name for tool in await server.list_tools()}
    resource_contents = list(await server.read_resource(COVERAGE_RESOURCE_URI))

    assert "dotloop_get_account" in tools
    assert "Dotloop MCP API Coverage Matrix" in resource_contents[0].content
    with pytest.raises(DotloopConfigurationError, match="access token"):
        server_module.create_server(server_settings=DotloopServerSettings())
    with pytest.raises(Exception, match="Dotloop access token is not configured"):
        await server.call_tool("dotloop_get_account", {})


@pytest.mark.asyncio
async def test_create_server_mounts_hosted_oauth_routes() -> None:
    server = server_module.create_server(
        server_settings=DotloopServerSettings(
            transport="streamable-http",
            mcp_auth=DotloopMcpAuthSettings(
                enabled=True,
                issuer_url="http://127.0.0.1:8000",
                resource_server_url="http://127.0.0.1:8000/mcp",
                jwks_url="http://127.0.0.1:8000/.well-known/jwks.json",
            ),
            hosted_oauth=DotloopHostedOAuthSettings(
                enabled=True,
                public_consent_enabled=True,
            ),
        ),
        service=DotloopService(FakeDotloopClient()),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.streamable_http_app()),
        base_url="http://127.0.0.1:8000",
    ) as client:
        metadata_response = await client.get("/.well-known/oauth-authorization-server")
        jwks_response = await client.get("/.well-known/jwks.json")
        protected_resource_response = await client.get("/.well-known/oauth-protected-resource/mcp")

    assert metadata_response.status_code == 200
    assert metadata_response.json()["issuer"] == "http://127.0.0.1:8000"
    assert jwks_response.status_code == 200
    assert protected_resource_response.status_code == 200


@pytest.mark.asyncio
async def test_coverage_resource_uses_static_fallback(tmp_path: Path) -> None:
    server = FastMCP("Test Dotloop MCP")
    register_server_surface(
        server,
        DotloopToolAdapter(DotloopService(FakeDotloopClient())),
        project_root=tmp_path,
    )

    resource_contents = list(await server.read_resource(COVERAGE_RESOURCE_URI))
    method_resource_contents = list(await server.read_resource(METHOD_COVERAGE_RESOURCE_URI))

    assert resource_contents[0].content == API_COVERAGE_MARKDOWN
    assert method_resource_contents[0].content == METHOD_COVERAGE_MARKDOWN
