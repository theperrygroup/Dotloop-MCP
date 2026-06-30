"""Unit tests for Dotloop app OAuth token handling."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from dotloop_mcp.app_oauth import (
    DotloopApiToken,
    DotloopAppCredentialProvider,
    DotloopAppOAuthClient,
    DotloopAppOAuthRequiredError,
    InMemoryDotloopApiTokenStore,
    SecretsManagerDotloopApiTokenStore,
)
from dotloop_mcp.config import DotloopAppOAuthSettings


def _settings() -> DotloopAppOAuthSettings:
    return DotloopAppOAuthSettings(
        enabled=True,
        client_id="client-id",
        client_secret="client-secret",
        authorize_url="https://auth.dotloop.com/oauth/authorize",
        token_url="https://auth.dotloop.com/oauth/token",
        redirect_url="https://dotloop.example.com/oauth/dotloop/callback",
        token_secret_arn="arn:aws:secretsmanager:token",
        token_refresh_leeway_seconds=60,
        token_request_timeout_seconds=5,
    )


class FakeSecretsManagerClient:
    def __init__(self, secret_string: str = "") -> None:
        self.secret_string = secret_string
        self.saved_secret_strings: list[str] = []

    def get_secret_value(self, **kwargs: str) -> dict[str, str]:
        assert kwargs["SecretId"] == "secret-id"
        return {"SecretString": self.secret_string}

    def put_secret_value(self, **kwargs: str) -> dict[str, str]:
        assert kwargs["SecretId"] == "secret-id"
        self.secret_string = kwargs["SecretString"]
        self.saved_secret_strings.append(kwargs["SecretString"])
        return {"VersionId": "1"}


def test_api_token_parses_and_serializes_secret_string() -> None:
    token = DotloopApiToken.from_secret_string(
        json.dumps(
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_at": 200,
                "updated_at": 100,
            }
        )
    )

    assert token is not None
    assert token.is_fresh(now=100, leeway_seconds=60)
    assert not token.is_fresh(now=160, leeway_seconds=60)
    assert json.loads(token.to_secret_string())["access_token"] == "access"


def test_api_token_rejects_invalid_secret_string() -> None:
    with pytest.raises(DotloopAppOAuthRequiredError, match="Reconnect"):
        DotloopApiToken.from_secret_string("not-json")


def test_secrets_manager_store_loads_and_saves_token() -> None:
    client = FakeSecretsManagerClient(
        json.dumps(
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_at": 200,
            }
        )
    )
    store = SecretsManagerDotloopApiTokenStore(secret_id="secret-id", client=client)

    token = store.load()
    assert token is not None
    store.save(token)

    assert client.saved_secret_strings
    assert "access" in client.saved_secret_strings[-1]


def test_oauth_client_builds_authorization_url() -> None:
    client = DotloopAppOAuthClient(settings=_settings())

    authorize_url = client.authorization_url(state="state-value")

    assert authorize_url.startswith("https://auth.dotloop.com/oauth/authorize?")
    assert "client_id=client-id" in authorize_url
    assert "redirect_uri=https%3A%2F%2Fdotloop.example.com%2Foauth%2Fdotloop%2Fcallback" in (
        authorize_url
    )
    assert "state=state-value" in authorize_url


def test_oauth_client_exchanges_authorization_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["grant_type"] == "authorization_code"
        assert request.url.params["code"] == "auth-code"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = DotloopAppOAuthClient(
        settings=_settings(),
        http_client=http_client,
        time_provider=lambda: 100,
    )

    token = client.exchange_authorization_code(code="auth-code")

    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
    assert token.expires_at == 3700


def test_oauth_client_refreshes_token() -> None:
    captured_body: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.append(request.content)
        return httpx.Response(
            200,
            json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 10},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = DotloopAppOAuthClient(
        settings=_settings(),
        http_client=http_client,
        time_provider=lambda: 100,
    )

    token = client.refresh_token(refresh_token="old-refresh")

    assert token.access_token == "new-access"
    assert b"grant_type=refresh_token" in captured_body[0]
    assert b"refresh_token=old-refresh" in captured_body[0]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"access_token": "", "refresh_token": "refresh", "expires_in": 10},
        {"access_token": "access", "refresh_token": "", "expires_in": 10},
        {"access_token": "access", "refresh_token": "refresh", "expires_in": "bad"},
    ],
)
def test_oauth_client_rejects_invalid_token_payload(payload: dict[str, Any]) -> None:
    http_client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    )
    client = DotloopAppOAuthClient(settings=_settings(), http_client=http_client)

    with pytest.raises(DotloopAppOAuthRequiredError, match="Reconnect"):
        client.refresh_token(refresh_token="refresh")


def test_credential_provider_uses_fresh_token_without_refresh() -> None:
    store = InMemoryDotloopApiTokenStore(
        DotloopApiToken(access_token="access", refresh_token="refresh", expires_at=1_000)
    )
    provider = DotloopAppCredentialProvider(
        settings=_settings(),
        store=store,
        time_provider=lambda: 100,
    )

    assert provider.get_access_token() == "access"


def test_credential_provider_refreshes_expiring_token() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 500},
        )

    store = InMemoryDotloopApiTokenStore(
        DotloopApiToken(access_token="old-access", refresh_token="old-refresh", expires_at=120)
    )
    oauth_client = DotloopAppOAuthClient(
        settings=_settings(),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        time_provider=lambda: 100,
    )
    provider = DotloopAppCredentialProvider(
        settings=_settings(),
        store=store,
        oauth_client=oauth_client,
        time_provider=lambda: 100,
    )

    assert provider.get_access_token() == "new-access"
    assert store.token is not None
    assert store.token.refresh_token == "new-refresh"


def test_credential_provider_requires_oauth_when_token_missing() -> None:
    provider = DotloopAppCredentialProvider(
        settings=_settings(),
        store=InMemoryDotloopApiTokenStore(),
    )

    with pytest.raises(DotloopAppOAuthRequiredError, match="Reconnect"):
        provider.get_access_token()
