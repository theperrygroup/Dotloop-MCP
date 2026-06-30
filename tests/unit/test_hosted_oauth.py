"""Unit tests for built-in hosted OAuth issuer routes."""

from __future__ import annotations

import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from starlette.applications import Starlette

from dotloop_mcp.app_oauth import (
    DotloopApiToken,
    DotloopAppCredentialProvider,
    DotloopAppOAuthClient,
    InMemoryDotloopApiTokenStore,
)
from dotloop_mcp.config import (
    DotloopAppOAuthSettings,
    DotloopHostedOAuthSettings,
    DotloopMcpAuthSettings,
)
from dotloop_mcp.hosted_oauth import DotloopHostedOAuthApplication


def _auth_settings() -> DotloopMcpAuthSettings:
    return DotloopMcpAuthSettings(
        enabled=True,
        issuer_url="http://127.0.0.1:8000",
        resource_server_url="http://127.0.0.1:8000/mcp",
        jwks_url="http://127.0.0.1:8000/.well-known/jwks.json",
        required_scopes=("dotloop:read",),
    )


def _hosted_settings(*, public_consent: bool = True) -> DotloopHostedOAuthSettings:
    return DotloopHostedOAuthSettings(
        enabled=True,
        public_consent_enabled=public_consent,
        authorization_code_seconds=300,
        access_token_seconds=3600,
        refresh_token_seconds=3600,
    )


def _dotloop_app_settings() -> DotloopAppOAuthSettings:
    return DotloopAppOAuthSettings(
        enabled=True,
        client_id="dotloop-client-id",
        client_secret="dotloop-client-secret",
        authorize_url="https://auth.dotloop.com/oauth/authorize",
        token_url="https://auth.dotloop.com/oauth/token",
        redirect_url="http://127.0.0.1:8000/oauth/dotloop/callback",
        token_secret_arn="secret-id",
        token_refresh_leeway_seconds=60,
        token_request_timeout_seconds=5,
    )


def _dotloop_provider(
    *,
    token: DotloopApiToken | None = None,
    http_client: httpx.Client | None = None,
) -> DotloopAppCredentialProvider:
    settings = _dotloop_app_settings()
    return DotloopAppCredentialProvider(
        settings=settings,
        store=InMemoryDotloopApiTokenStore(token),
        oauth_client=DotloopAppOAuthClient(
            settings=settings,
            http_client=http_client,
            time_provider=lambda: 100,
        ),
        time_provider=lambda: 100,
    )


def _client(application: DotloopHostedOAuthApplication) -> httpx.AsyncClient:
    app = Starlette(routes=list(application.routes()))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


@pytest.mark.asyncio
async def test_hosted_oauth_metadata_and_jwks() -> None:
    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(),
    )
    async with _client(application) as client:
        metadata_response = await client.get("/.well-known/oauth-authorization-server")
        jwks_response = await client.get("/.well-known/jwks.json")

    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["issuer"] == "http://127.0.0.1:8000"
    assert metadata["authorization_endpoint"] == "http://127.0.0.1:8000/oauth/authorize"
    assert metadata["token_endpoint"] == "http://127.0.0.1:8000/oauth/token"
    assert metadata["registration_endpoint"] == "http://127.0.0.1:8000/oauth/register"
    assert metadata["jwks_uri"] == "http://127.0.0.1:8000/.well-known/jwks.json"
    assert metadata["scopes_supported"] == ["dotloop:read"]
    assert jwks_response.status_code == 200
    assert jwks_response.json()["keys"][0]["kid"] == "dotloop-hosted-current"


@pytest.mark.asyncio
async def test_hosted_oauth_authorization_code_and_refresh_flow() -> None:
    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(),
    )
    redirect_uri = "http://127.0.0.1:7777/callback"
    async with _client(application) as client:
        register_response = await client.post(
            "/oauth/register",
            json={
                "redirect_uris": [redirect_uri],
                "scope": "dotloop:read",
                "token_endpoint_auth_method": "none",
            },
        )
        client_id = register_response.json()["client_id"]
        verifier = "test-verifier"

        authorize_response = await client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": _pkce_challenge(verifier),
                "code_challenge_method": "S256",
                "scope": "dotloop:read",
                "state": "state-123",
            },
            follow_redirects=False,
        )

        assert authorize_response.status_code == 302
        redirect = authorize_response.headers["location"]
        parsed_redirect = urlsplit(redirect)
        query = parse_qs(parsed_redirect.query)
        assert parsed_redirect.scheme == "http"
        assert parsed_redirect.netloc == "127.0.0.1:7777"
        assert query["state"] == ["state-123"]
        code = query["code"][0]

        token_response = await client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code": code,
                "code_verifier": verifier,
            },
        )

        assert token_response.status_code == 200
        token_payload = token_response.json()
        assert token_payload["token_type"] == "Bearer"
        assert token_payload["scope"] == "dotloop:read"
        access_token = await application.token_verifier().verify_token(
            token_payload["access_token"]
        )
        assert access_token is not None
        assert access_token.client_id == client_id
        assert access_token.subject == "dotloop-hosted-user"
        assert access_token.resource == "http://127.0.0.1:8000/mcp"

        refresh_response = await client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": token_payload["refresh_token"],
            },
        )

    assert refresh_response.status_code == 200
    refreshed_token = await application.token_verifier().verify_token(
        refresh_response.json()["access_token"]
    )
    assert refreshed_token is not None


@pytest.mark.asyncio
async def test_hosted_oauth_public_consent_gate() -> None:
    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(public_consent=False),
    )

    async with _client(application) as client:
        response = await client.get("/oauth/authorize")

    assert response.status_code == 403
    assert "authorization is not enabled" in response.text


@pytest.mark.asyncio
async def test_hosted_oauth_redirects_to_dotloop_when_api_token_missing() -> None:
    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(public_consent=False),
        dotloop_credential_provider=_dotloop_provider(),
    )
    redirect_uri = "http://127.0.0.1:7777/callback"
    async with _client(application) as client:
        register_response = await client.post(
            "/oauth/register",
            json={"redirect_uris": [redirect_uri], "scope": "dotloop:read"},
        )
        client_id = register_response.json()["client_id"]

        response = await client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": "challenge",
                "scope": "dotloop:read",
                "state": "mcp-state",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    redirect = response.headers["location"]
    parsed_redirect = urlsplit(redirect)
    query = parse_qs(parsed_redirect.query)
    assert parsed_redirect.scheme == "https"
    assert parsed_redirect.netloc == "auth.dotloop.com"
    assert parsed_redirect.path == "/oauth/authorize"
    assert query["client_id"] == ["dotloop-client-id"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8000/oauth/dotloop/callback"]
    assert query["state"][0].startswith("dotloop_mcp_")


@pytest.mark.asyncio
async def test_hosted_oauth_dotloop_callback_resumes_mcp_authorization() -> None:
    def token_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["grant_type"] == "authorization_code"
        assert request.url.params["code"] == "dotloop-code"
        return httpx.Response(
            200,
            json={
                "access_token": "dotloop-access",
                "refresh_token": "dotloop-refresh",
                "expires_in": 3600,
            },
        )

    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(public_consent=False),
        dotloop_credential_provider=_dotloop_provider(
            http_client=httpx.Client(transport=httpx.MockTransport(token_handler))
        ),
    )
    redirect_uri = "http://127.0.0.1:7777/callback"
    async with _client(application) as client:
        register_response = await client.post(
            "/oauth/register",
            json={"redirect_uris": [redirect_uri], "scope": "dotloop:read"},
        )
        client_id = register_response.json()["client_id"]
        verifier = "test-verifier"
        authorize_response = await client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": _pkce_challenge(verifier),
                "code_challenge_method": "S256",
                "scope": "dotloop:read",
                "state": "mcp-state",
            },
            follow_redirects=False,
        )
        dotloop_state = parse_qs(urlsplit(authorize_response.headers["location"]).query)["state"][0]
        assert dotloop_state.startswith("dotloop_mcp_")

        callback_response = await client.get(
            "/oauth/dotloop/callback",
            params={"code": "dotloop-code", "state": dotloop_state},
            follow_redirects=False,
        )
        callback_query = parse_qs(urlsplit(callback_response.headers["location"]).query)
        token_response = await client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code": callback_query["code"][0],
                "code_verifier": verifier,
            },
        )

    assert callback_response.status_code == 302
    assert callback_query["state"] == ["mcp-state"]
    assert token_response.status_code == 200
    assert token_response.json()["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_hosted_oauth_valid_dotloop_token_skips_dotloop_redirect() -> None:
    application = DotloopHostedOAuthApplication(
        auth_settings=_auth_settings(),
        hosted_settings=_hosted_settings(public_consent=False),
        dotloop_credential_provider=_dotloop_provider(
            token=DotloopApiToken(
                access_token="dotloop-access",
                refresh_token="dotloop-refresh",
                expires_at=1_000,
            )
        ),
    )
    redirect_uri = "http://127.0.0.1:7777/callback"
    async with _client(application) as client:
        register_response = await client.post(
            "/oauth/register",
            json={"redirect_uris": [redirect_uri], "scope": "dotloop:read"},
        )
        client_id = register_response.json()["client_id"]
        response = await client.get(
            "/oauth/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": "challenge",
                "scope": "dotloop:read",
                "state": "mcp-state",
            },
            follow_redirects=False,
        )

    parsed_redirect = urlsplit(response.headers["location"])
    query = parse_qs(parsed_redirect.query)
    assert response.status_code == 302
    assert parsed_redirect.netloc == "127.0.0.1:7777"
    assert query["code"][0]
    assert query["state"] == ["mcp-state"]
