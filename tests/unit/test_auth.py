"""Unit tests for inbound MCP URL authentication."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from dotloop_mcp.auth import DotloopMcpJwtVerifier, build_mcp_auth_settings, parse_scope_claims
from dotloop_mcp.config import DotloopMcpAuthSettings


@dataclass(frozen=True)
class _SigningKey:
    key: Any


class _FakeJwkClient:
    def __init__(self, key: Any) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, token: str | bytes) -> _SigningKey:
        return _SigningKey(self._key)


@pytest.fixture
def private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def auth_settings() -> DotloopMcpAuthSettings:
    return DotloopMcpAuthSettings(
        enabled=True,
        issuer_url="https://auth.example.com",
        resource_server_url="https://dotloop-mcp.example.com/mcp",
        jwks_url="https://auth.example.com/.well-known/jwks.json",
        required_scopes=("dotloop:read",),
        allowed_algorithms=("RS256",),
        token_leeway_seconds=0,
        jwks_cache_seconds=300,
    )


def _claims(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": "https://auth.example.com",
        "aud": "https://dotloop-mcp.example.com/mcp",
        "sub": "user-123",
        "client_id": "client-123",
        "scope": "dotloop:read profile:read",
        "exp": now + 300,
        "nbf": now - 10,
    }
    claims.update(overrides)
    return claims


def _encode_token(private_key: rsa.RSAPrivateKey, claims: dict[str, Any]) -> str:
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-key"})


def _verifier(
    settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> DotloopMcpJwtVerifier:
    return DotloopMcpJwtVerifier(
        settings,
        jwk_client=_FakeJwkClient(private_key.public_key()),
    )


def test_build_mcp_auth_settings_uses_resource_metadata(
    auth_settings: DotloopMcpAuthSettings,
) -> None:
    settings = build_mcp_auth_settings(auth_settings)

    assert str(settings.issuer_url).rstrip("/") == "https://auth.example.com"
    assert str(settings.resource_server_url).rstrip("/") == "https://dotloop-mcp.example.com/mcp"
    assert settings.required_scopes == ["dotloop:read"]


@pytest.mark.asyncio
async def test_jwt_verifier_accepts_valid_token(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> None:
    token = _encode_token(private_key, _claims())

    access_token = await _verifier(auth_settings, private_key).verify_token(token)

    assert access_token is not None
    assert access_token.token == "[validated]"
    assert access_token.client_id == "client-123"
    assert access_token.subject == "user-123"
    assert access_token.resource == "https://dotloop-mcp.example.com/mcp"
    assert "dotloop:read" in access_token.scopes


@pytest.mark.asyncio
async def test_jwt_verifier_accepts_resource_claim_without_audience(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> None:
    token = _encode_token(
        private_key,
        _claims(aud=None, resource="https://dotloop-mcp.example.com/mcp", scp=["dotloop:read"]),
    )

    access_token = await _verifier(auth_settings, private_key).verify_token(token)

    assert access_token is not None


@pytest.mark.asyncio
async def test_jwt_verifier_accepts_configured_audience(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> None:
    settings = DotloopMcpAuthSettings(
        **{
            **auth_settings.__dict__,
            "audience": "dotloop-mcp-api",
        }
    )
    token = _encode_token(private_key, _claims(aud="dotloop-mcp-api"))

    access_token = await _verifier(settings, private_key).verify_token(token)

    assert access_token is not None


@pytest.mark.asyncio
async def test_jwt_verifier_rejects_bad_signature(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _encode_token(other_key, _claims())

    assert await _verifier(auth_settings, private_key).verify_token(token) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims",
    [
        _claims(iss="https://other.example.com"),
        _claims(aud="https://other.example.com/mcp", resource=None),
        _claims(exp=int(time.time()) - 60),
        _claims(scope="profile:read"),
    ],
)
async def test_jwt_verifier_rejects_invalid_claims(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
    claims: dict[str, Any],
) -> None:
    token = _encode_token(private_key, claims)

    assert await _verifier(auth_settings, private_key).verify_token(token) is None


@pytest.mark.asyncio
async def test_jwt_verifier_rejects_disallowed_algorithm(
    auth_settings: DotloopMcpAuthSettings,
    private_key: rsa.RSAPrivateKey,
) -> None:
    settings = DotloopMcpAuthSettings(
        **{
            **auth_settings.__dict__,
            "allowed_algorithms": ("ES256",),
        }
    )
    token = _encode_token(private_key, _claims())

    assert await _verifier(settings, private_key).verify_token(token) is None


def test_parse_scope_claims_supports_scope_and_scp() -> None:
    assert parse_scope_claims({"scope": "one two", "scp": ["three", "four"]}) == {
        "one",
        "two",
        "three",
        "four",
    }
