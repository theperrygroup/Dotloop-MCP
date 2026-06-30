"""Built-in OAuth authorization-server routes for hosted Dotloop MCP."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

from dotloop_mcp.auth import DotloopMcpJwtVerifier
from dotloop_mcp.config import DotloopConfigurationError, DotloopHostedOAuthSettings
from dotloop_mcp.config import DotloopMcpAuthSettings

_SUPPORTED_CODE_CHALLENGE_METHODS = {"plain", "S256"}
_DEFAULT_SUBJECT = "dotloop-hosted-user"


@dataclass(frozen=True)
class _ClientRegistration:
    redirect_uris: tuple[str, ...]
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class _AuthorizationCode:
    client_id: str
    redirect_uri: str
    scopes: tuple[str, ...]
    code_challenge: str
    code_challenge_method: str
    expires_at: int


@dataclass(frozen=True)
class _RefreshToken:
    client_id: str
    scopes: tuple[str, ...]
    subject: str
    expires_at: int


class _StaticJwkClient:
    def __init__(self, public_key: rsa.RSAPublicKey) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str | bytes) -> _StaticSigningKey:
        return _StaticSigningKey(self._public_key)


@dataclass(frozen=True)
class _StaticSigningKey:
    key: rsa.RSAPublicKey


class DotloopHostedOAuthApplication:
    """Starlette route provider for a minimal hosted MCP OAuth issuer."""

    def __init__(
        self,
        *,
        auth_settings: DotloopMcpAuthSettings,
        hosted_settings: DotloopHostedOAuthSettings,
        private_key: rsa.RSAPrivateKey | None = None,
        time_provider: Any | None = None,
    ) -> None:
        """Initialize hosted OAuth routes and token verifier material."""
        if not auth_settings.enabled:
            raise DotloopConfigurationError("Hosted OAuth requires MCP auth to be enabled.")
        if not hosted_settings.enabled:
            raise DotloopConfigurationError("Hosted OAuth settings must be enabled.")

        self._auth_settings = auth_settings
        self._hosted_settings = hosted_settings
        self._private_key = private_key or rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._kid = "dotloop-hosted-current"
        self._time_provider = time_provider or (lambda: int(time.time()))
        self._clients: dict[str, _ClientRegistration] = {}
        self._authorization_codes: dict[str, _AuthorizationCode] = {}
        self._refresh_tokens: dict[str, _RefreshToken] = {}

    @property
    def issuer(self) -> str:
        """Return the configured issuer URL without a trailing slash."""
        return self._required("DOTLOOP_MCP_AUTH_ISSUER_URL", self._auth_settings.issuer_url)

    @property
    def resource_server_url(self) -> str:
        """Return the configured MCP resource URL."""
        return self._required(
            "DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL",
            self._auth_settings.resource_server_url,
        )

    def token_verifier(self) -> DotloopMcpJwtVerifier:
        """Return a verifier that validates tokens issued by this app instance."""
        return DotloopMcpJwtVerifier(
            self._auth_settings,
            jwk_client=_StaticJwkClient(self._private_key.public_key()),
        )

    def routes(self) -> tuple[Route, ...]:
        """Return public hosted OAuth routes to mount on the MCP HTTP app."""
        return (
            Route("/.well-known/oauth-authorization-server", self.authorization_server_metadata),
            Route("/.well-known/openid-configuration", self.authorization_server_metadata),
            Route("/.well-known/jwks.json", self.jwks),
            Route("/oauth/register", self.register_client, methods=["POST"]),
            Route("/oauth/authorize", self.authorize, methods=["GET", "POST"]),
            Route("/oauth/token", self.token, methods=["POST"]),
        )

    async def authorization_server_metadata(self, _: Request) -> JSONResponse:
        """Return OAuth authorization-server discovery metadata."""
        return JSONResponse(
            {
                "issuer": self.issuer,
                "authorization_endpoint": self.endpoint_url("/oauth/authorize"),
                "token_endpoint": self.endpoint_url("/oauth/token"),
                "registration_endpoint": self.endpoint_url("/oauth/register"),
                "jwks_uri": self.endpoint_url("/.well-known/jwks.json"),
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": sorted(_SUPPORTED_CODE_CHALLENGE_METHODS),
                "token_endpoint_auth_methods_supported": ["none"],
                "scopes_supported": list(self._auth_settings.required_scopes),
            },
            headers={"Cache-Control": "public, max-age=3600"},
        )

    async def jwks(self, _: Request) -> JSONResponse:
        """Return the current public signing key as JWKS."""
        public_jwk = json.loads(RSAAlgorithm.to_jwk(self._private_key.public_key()))
        public_jwk.update({"kid": self._kid, "use": "sig", "alg": "RS256"})
        return JSONResponse(
            {"keys": [public_jwk]},
            headers={"Cache-Control": "public, max-age=300, must-revalidate"},
        )

    async def register_client(self, request: Request) -> JSONResponse:
        """Register a public OAuth client through dynamic client registration."""
        payload = await _json_body(request)
        redirect_uris = payload.get("redirect_uris")
        if not isinstance(redirect_uris, list) or not redirect_uris:
            return _oauth_error("invalid_client_metadata", "redirect_uris is required.", 400)
        typed_redirect_uris = tuple(uri for uri in redirect_uris if isinstance(uri, str))
        if len(typed_redirect_uris) != len(redirect_uris) or not all(
            _is_redirect_uri(uri) for uri in typed_redirect_uris
        ):
            return _oauth_error("invalid_client_metadata", "redirect_uris must be valid URIs.", 400)

        requested_scopes = _requested_scopes(payload.get("scope"), self._auth_settings.required_scopes)
        if not self._scopes_supported(requested_scopes):
            return _oauth_error("invalid_scope", "Requested scope is not supported.", 400)

        client_id = secrets.token_urlsafe(24)
        self._clients[client_id] = _ClientRegistration(
            redirect_uris=typed_redirect_uris,
            scopes=requested_scopes,
        )
        return JSONResponse(
            {
                "client_id": client_id,
                "client_id_issued_at": self._now(),
                "redirect_uris": list(typed_redirect_uris),
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": " ".join(requested_scopes),
            },
            status_code=201,
        )

    async def authorize(self, request: Request) -> Response:
        """Validate an authorization request and redirect with a short-lived code."""
        if not self._hosted_settings.public_consent_enabled:
            return HTMLResponse(
                _html_page(
                    "Dotloop MCP authorization is not enabled for this deployment.",
                    "Set DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=1 only for staging "
                    "or after a real login/consent boundary is available.",
                ),
                status_code=403,
            )

        params = await _request_params(request)
        validation_error = self._validate_authorize_params(params)
        if validation_error is not None:
            return validation_error

        client_id = params["client_id"]
        redirect_uri = params["redirect_uri"]
        scopes = _requested_scopes(params.get("scope"), self._clients[client_id].scopes)
        code = secrets.token_urlsafe(32)
        self._authorization_codes[code] = _AuthorizationCode(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=params["code_challenge"],
            code_challenge_method=params.get("code_challenge_method") or "plain",
            expires_at=self._now() + self._hosted_settings.authorization_code_seconds,
        )

        redirect_params = {"code": code}
        if params.get("state"):
            redirect_params["state"] = params["state"]
        return RedirectResponse(_append_query_params(redirect_uri, redirect_params), status_code=302)

    async def token(self, request: Request) -> JSONResponse:
        """Exchange an authorization code or refresh token for a Bearer access token."""
        params = await _request_params(request)
        grant_type = params.get("grant_type")
        if grant_type == "authorization_code":
            return self._authorization_code_token(params)
        if grant_type == "refresh_token":
            return self._refresh_token_token(params)
        return _oauth_error("unsupported_grant_type", "Unsupported grant_type.", 400)

    def endpoint_url(self, path: str) -> str:
        """Build a URL below the configured issuer origin."""
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.issuer}{normalized_path}"

    def _authorization_code_token(self, params: dict[str, str]) -> JSONResponse:
        code = params.get("code")
        client_id = params.get("client_id")
        redirect_uri = params.get("redirect_uri")
        code_verifier = params.get("code_verifier")
        if not code or not client_id or not redirect_uri or not code_verifier:
            return _oauth_error("invalid_request", "Missing authorization_code parameters.", 400)

        authorization_code = self._authorization_codes.pop(code, None)
        if authorization_code is None or authorization_code.expires_at < self._now():
            return _oauth_error("invalid_grant", "Authorization code is invalid or expired.", 400)
        if authorization_code.client_id != client_id or authorization_code.redirect_uri != redirect_uri:
            return _oauth_error("invalid_grant", "Authorization code binding is invalid.", 400)
        if not _verify_pkce(
            verifier=code_verifier,
            challenge=authorization_code.code_challenge,
            method=authorization_code.code_challenge_method,
        ):
            return _oauth_error("invalid_grant", "PKCE verification failed.", 400)

        refresh_token = secrets.token_urlsafe(48)
        self._refresh_tokens[refresh_token] = _RefreshToken(
            client_id=client_id,
            scopes=authorization_code.scopes,
            subject=_DEFAULT_SUBJECT,
            expires_at=self._now() + self._hosted_settings.refresh_token_seconds,
        )
        return self._token_response(
            client_id=client_id,
            scopes=authorization_code.scopes,
            subject=_DEFAULT_SUBJECT,
            refresh_token=refresh_token,
        )

    def _refresh_token_token(self, params: dict[str, str]) -> JSONResponse:
        refresh_token = params.get("refresh_token")
        client_id = params.get("client_id")
        if not refresh_token or not client_id:
            return _oauth_error("invalid_request", "Missing refresh_token parameters.", 400)

        stored_refresh_token = self._refresh_tokens.get(refresh_token)
        if stored_refresh_token is None or stored_refresh_token.expires_at < self._now():
            return _oauth_error("invalid_grant", "Refresh token is invalid or expired.", 400)
        if stored_refresh_token.client_id != client_id:
            return _oauth_error("invalid_grant", "Refresh token binding is invalid.", 400)

        return self._token_response(
            client_id=client_id,
            scopes=stored_refresh_token.scopes,
            subject=stored_refresh_token.subject,
            refresh_token=refresh_token,
        )

    def _token_response(
        self,
        *,
        client_id: str,
        scopes: tuple[str, ...],
        subject: str,
        refresh_token: str,
    ) -> JSONResponse:
        now = self._now()
        expires_in = self._hosted_settings.access_token_seconds
        claims = {
            "iss": self.issuer,
            "aud": self._auth_settings.audience or self.resource_server_url,
            "resource": self.resource_server_url,
            "sub": subject,
            "client_id": client_id,
            "scope": " ".join(scopes),
            "iat": now,
            "nbf": now,
            "exp": now + expires_in,
        }
        access_token = jwt.encode(
            claims,
            self._private_key,
            algorithm="RS256",
            headers={"kid": self._kid},
        )
        return JSONResponse(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": expires_in,
                "scope": " ".join(scopes),
                "refresh_token": refresh_token,
            },
            headers={"Cache-Control": "no-store"},
        )

    def _validate_authorize_params(self, params: dict[str, str]) -> Response | None:
        if params.get("response_type") != "code":
            return _oauth_error("unsupported_response_type", "Only response_type=code is supported.", 400)
        client_id = params.get("client_id")
        if not client_id or client_id not in self._clients:
            return _oauth_error("invalid_request", "Unknown client_id.", 400)
        redirect_uri = params.get("redirect_uri")
        if not redirect_uri or redirect_uri not in self._clients[client_id].redirect_uris:
            return _oauth_error("invalid_request", "redirect_uri is not registered.", 400)
        code_challenge = params.get("code_challenge")
        if not code_challenge:
            return _oauth_error("invalid_request", "code_challenge is required.", 400)
        code_challenge_method = params.get("code_challenge_method") or "plain"
        if code_challenge_method not in _SUPPORTED_CODE_CHALLENGE_METHODS:
            return _oauth_error("invalid_request", "Unsupported code_challenge_method.", 400)
        requested_scopes = _requested_scopes(params.get("scope"), self._clients[client_id].scopes)
        if not self._scopes_supported(requested_scopes):
            return _oauth_error("invalid_scope", "Requested scope is not supported.", 400)
        return None

    def _scopes_supported(self, requested_scopes: tuple[str, ...]) -> bool:
        supported_scopes = set(self._auth_settings.required_scopes)
        return not supported_scopes or set(requested_scopes).issubset(supported_scopes)

    def _required(self, name: str, value: str | None) -> str:
        if value:
            return value.rstrip("/")
        raise DotloopConfigurationError(f"{name} is required when hosted OAuth is enabled.")

    def _now(self) -> int:
        return int(self._time_provider())


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


async def _request_params(request: Request) -> dict[str, str]:
    if request.method == "GET":
        return {key: value for key, value in request.query_params.items()}

    body = (await request.body()).decode("utf-8")
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            return {str(key): str(value) for key, value in payload.items() if value is not None}
        return {}

    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items() if values}


def _requested_scopes(value: Any, default: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, str):
        scopes = tuple(scope for scope in value.split() if scope)
        return scopes or default
    return default


def _is_redirect_uri(value: str) -> bool:
    parsed = urlsplit(value)
    return bool(parsed.scheme and (parsed.netloc or parsed.scheme not in {"http", "https"}))


def _append_query_params(url: str, params: dict[str, str]) -> str:
    parsed = urlsplit(url)
    query = urlencode({**dict(parse_qs(parsed.query, keep_blank_values=True)), **params}, doseq=True)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def _verify_pkce(*, verifier: str, challenge: str, method: str) -> bool:
    if method == "plain":
        return secrets.compare_digest(verifier, challenge)
    if method == "S256":
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return secrets.compare_digest(encoded, challenge)
    return False


def _oauth_error(error: str, description: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {"error": error, "error_description": description},
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _html_page(title: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{title}</title></head><body>"
        f"<h1>{title}</h1><p>{body}</p>"
        "</body></html>"
    )
