"""Unit tests for built-in hosted OAuth issuer routes."""

from __future__ import annotations

import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from starlette.applications import Starlette

from dotloop_mcp.config import DotloopHostedOAuthSettings, DotloopMcpAuthSettings
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
