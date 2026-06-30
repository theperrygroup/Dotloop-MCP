"""Inbound MCP URL authentication helpers."""

from __future__ import annotations

from typing import Any, Protocol

import anyio
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from dotloop_mcp.config import DotloopMcpAuthSettings
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings


class _SigningKey(Protocol):
    @property
    def key(self) -> Any:
        """Return the public key used to verify a JWT."""


class _JwkClient(Protocol):
    def get_signing_key_from_jwt(self, token: str | bytes) -> _SigningKey:
        """Return the signing key for a JWT."""


def build_mcp_auth_settings(settings: DotloopMcpAuthSettings) -> AuthSettings:
    """Build FastMCP auth settings from Dotloop MCP auth configuration."""
    issuer_url = settings.require_enabled_value(
        "DOTLOOP_MCP_AUTH_ISSUER_URL",
        settings.issuer_url,
    )
    resource_server_url = settings.require_enabled_value(
        "DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL",
        settings.resource_server_url,
    )
    return AuthSettings.model_validate(
        {
            "issuer_url": issuer_url,
            "resource_server_url": resource_server_url,
            "required_scopes": list(settings.required_scopes) or None,
        }
    )


class DotloopMcpJwtVerifier(TokenVerifier):
    """Validate inbound MCP Bearer JWTs against a configured JWKS endpoint."""

    def __init__(
        self,
        settings: DotloopMcpAuthSettings,
        *,
        jwk_client: _JwkClient | None = None,
    ) -> None:
        """Initialize the verifier with auth settings and an optional JWKS client."""
        self._settings = settings
        jwks_url = settings.require_enabled_value("DOTLOOP_MCP_AUTH_JWKS_URL", settings.jwks_url)
        self._jwk_client = jwk_client or PyJWKClient(
            jwks_url,
            cache_jwk_set=True,
            lifespan=settings.jwks_cache_seconds,
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify an inbound Bearer token for the MCP resource server."""
        return await anyio.to_thread.run_sync(self._verify_token_sync, token)

    def _verify_token_sync(self, token: str) -> AccessToken | None:
        try:
            header = jwt.get_unverified_header(token)
            algorithm = header.get("alg")
            if not isinstance(algorithm, str) or algorithm not in self._settings.allowed_algorithms:
                return None

            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self._settings.allowed_algorithms),
                issuer=self._settings.issuer_url,
                options={"verify_aud": False},
                leeway=self._settings.token_leeway_seconds,
            )
        except PyJWTError:
            return None

        if not isinstance(claims, dict):
            return None
        typed_claims = claims
        if not self._is_intended_resource(typed_claims):
            return None

        scopes = parse_scope_claims(typed_claims)
        if not set(self._settings.required_scopes).issubset(scopes):
            return None

        expires_at = typed_claims.get("exp")
        subject = typed_claims.get("sub")
        client_id = (
            typed_claims.get("client_id")
            or typed_claims.get("azp")
            or typed_claims.get("sub")
            or "unknown"
        )

        return AccessToken(
            token="[validated]",
            client_id=str(client_id),
            scopes=sorted(scopes),
            expires_at=int(expires_at) if isinstance(expires_at, int) else None,
            resource=self._settings.resource_server_url,
            subject=str(subject) if isinstance(subject, str) else None,
            claims=typed_claims,
        )

    def _is_intended_resource(self, claims: dict[str, Any]) -> bool:
        allowed_targets = {self._settings.resource_server_url}
        if self._settings.audience:
            allowed_targets.add(self._settings.audience)

        claim_targets = _string_values(claims.get("aud")) | _string_values(claims.get("resource"))
        return bool(claim_targets & {target for target in allowed_targets if target})


def parse_scope_claims(claims: dict[str, Any]) -> set[str]:
    """Parse OAuth scopes from common JWT `scope` or `scp` claims."""
    scope_values = _scope_values(claims.get("scope")) | _scope_values(claims.get("scp"))
    return {scope for scope in scope_values if scope}


def _scope_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {scope.strip() for scope in value.split() if scope.strip()}
    return _string_values(value)


def _string_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list | tuple | set):
        return {item for item in value if isinstance(item, str)}
    return set()
