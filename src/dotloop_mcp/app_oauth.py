"""Dotloop app OAuth and hosted API-token storage."""

from __future__ import annotations

import base64
import importlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, Self
from urllib.parse import urlencode

import httpx
from dotloop import DotloopClient

from dotloop_mcp.config import DotloopAppOAuthSettings, DotloopConfigurationError
from dotloop_mcp.errors import DotloopMCPError


class DotloopAppOAuthError(DotloopMCPError):
    """MCP-safe Dotloop app OAuth error."""


class DotloopAppOAuthRequiredError(DotloopAppOAuthError):
    """Raised when the hosted MCP must be reconnected through Dotloop OAuth."""


_RECONNECT_MESSAGE = "Dotloop app authorization is required. Reconnect the MCP connector."


@dataclass(frozen=True)
class DotloopApiToken:
    """Refreshable Dotloop API token state stored outside process memory."""

    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = "Bearer"
    updated_at: int | None = None

    @classmethod
    def from_secret_string(cls, value: str) -> Self | None:
        """Parse token state from a Secrets Manager string."""
        normalized_value = str(value or "").strip()
        if not normalized_value:
            return None
        try:
            payload = json.loads(normalized_value)
        except json.JSONDecodeError as exc:
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
        if not isinstance(payload, dict):
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        return cls.from_mapping(payload)

    @classmethod
    def from_oauth_response(cls, payload: dict[str, Any], *, now: int) -> Self:
        """Build token state from a Dotloop OAuth token response."""
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        expires_in_raw = payload.get("expires_in") or 0
        try:
            expires_in = int(expires_in_raw)
        except (TypeError, ValueError) as exc:
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
        token_type = payload.get("token_type")
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + max(expires_in, 0),
            token_type=token_type if isinstance(token_type, str) and token_type else "Bearer",
            updated_at=now,
        )

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> Self:
        """Build token state from a decoded secret payload."""
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        expires_at_raw = payload.get("expires_at")
        token_type = payload.get("token_type")
        updated_at_raw = payload.get("updated_at")
        if not isinstance(access_token, str) or not access_token.strip():
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        if not isinstance(expires_at_raw, str | int | float):
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        try:
            expires_at = int(expires_at_raw)
        except (TypeError, ValueError) as exc:
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
        updated_at: int | None
        if updated_at_raw is None:
            updated_at = None
        else:
            if not isinstance(updated_at_raw, str | int | float):
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
            try:
                updated_at = int(updated_at_raw)
            except (TypeError, ValueError) as exc:
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            token_type=token_type if isinstance(token_type, str) and token_type else "Bearer",
            updated_at=updated_at,
        )

    def is_fresh(self, *, now: int, leeway_seconds: int) -> bool:
        """Return whether this access token is usable after the refresh leeway."""
        return self.expires_at > now + leeway_seconds

    def to_secret_string(self) -> str:
        """Serialize token state for Secrets Manager."""
        return json.dumps(
            {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.expires_at,
                "token_type": self.token_type,
                "updated_at": self.updated_at,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


class DotloopApiTokenStore(Protocol):
    """Storage boundary for refreshable Dotloop API token state."""

    def load(self) -> DotloopApiToken | None:
        """Load token state when present."""
        ...

    def save(self, token: DotloopApiToken) -> None:
        """Persist token state."""
        ...


class SecretsManagerDotloopApiTokenStore:
    """Secrets Manager backed single-tenant Dotloop API token store."""

    def __init__(self, *, secret_id: str, client: Any | None = None) -> None:
        """Initialize a Secrets Manager token store."""
        self._secret_id = secret_id
        self._client = client

    @property
    def client(self) -> Any:
        """Return the lazily constructed Secrets Manager client."""
        if self._client is None:
            boto3 = importlib.import_module("boto3")
            self._client = boto3.client("secretsmanager")
        return self._client

    def load(self) -> DotloopApiToken | None:
        """Load token state from Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=self._secret_id)
        except Exception as exc:  # noqa: BLE001 - normalize provider errors safely
            raise DotloopAppOAuthError("Dotloop app token store is unavailable.") from exc
        secret_string = response.get("SecretString")
        if not isinstance(secret_string, str) or not secret_string.strip():
            return None
        return DotloopApiToken.from_secret_string(secret_string)

    def save(self, token: DotloopApiToken) -> None:
        """Write token state to Secrets Manager."""
        try:
            self.client.put_secret_value(
                SecretId=self._secret_id,
                SecretString=token.to_secret_string(),
            )
        except Exception as exc:  # noqa: BLE001 - normalize provider errors safely
            raise DotloopAppOAuthError("Dotloop app token store is unavailable.") from exc


class InMemoryDotloopApiTokenStore:
    """In-memory token store for tests and local smoke paths."""

    def __init__(self, token: DotloopApiToken | None = None) -> None:
        """Initialize the in-memory store."""
        self.token = token

    def load(self) -> DotloopApiToken | None:
        """Return the current token state."""
        return self.token

    def save(self, token: DotloopApiToken) -> None:
        """Persist token state in memory."""
        self.token = token


class DotloopAppOAuthClient:
    """Client for Dotloop's OAuth authorization-code and refresh flows."""

    def __init__(
        self,
        *,
        settings: DotloopAppOAuthSettings,
        http_client: httpx.Client | None = None,
        time_provider: Callable[[], int] | None = None,
    ) -> None:
        """Initialize the Dotloop OAuth client."""
        self._settings = settings
        self._http_client = http_client
        self._time_provider = time_provider or (lambda: int(time.time()))

    def authorization_url(self, *, state: str) -> str:
        """Build a Dotloop authorize URL for one hosted MCP connection flow."""
        query_string = urlencode(
            {
                "response_type": "code",
                "client_id": self._required("DOTLOOP_API_CLIENT_ID", self._settings.client_id),
                "redirect_uri": self._required(
                    "DOTLOOP_APP_OAUTH_REDIRECT_URL",
                    self._settings.redirect_url,
                ),
                "state": state,
            }
        )
        return f"{self._settings.authorize_url}?{query_string}"

    def exchange_authorization_code(self, *, code: str) -> DotloopApiToken:
        """Exchange a Dotloop authorization code for refreshable token state."""
        return self._post_token(
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._required(
                    "DOTLOOP_APP_OAUTH_REDIRECT_URL",
                    self._settings.redirect_url,
                ),
            },
        )

    def refresh_token(self, *, refresh_token: str) -> DotloopApiToken:
        """Refresh Dotloop API token state."""
        return self._post_token(
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

    def _post_token(
        self,
        *,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> DotloopApiToken:
        client = self._http_client or httpx.Client(
            timeout=self._settings.token_request_timeout_seconds
        )
        close_client = self._http_client is None
        try:
            try:
                response = client.post(
                    self._settings.token_url,
                    headers={
                        "Authorization": f"Basic {self._encoded_client_credentials()}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    params=params,
                    data=data,
                )
            except httpx.HTTPError as exc:
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
            if response.status_code >= 400:
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE) from exc
            if not isinstance(payload, dict):
                raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
            return DotloopApiToken.from_oauth_response(payload, now=self._now())
        finally:
            if close_client:
                client.close()

    def _encoded_client_credentials(self) -> str:
        raw_credentials = (
            f"{self._required('DOTLOOP_API_CLIENT_ID', self._settings.client_id)}:"
            f"{self._required('DOTLOOP_API_SECRET', self._settings.client_secret)}"
        )
        return base64.b64encode(raw_credentials.encode("ISO-8859-1")).decode("ascii")

    def _required(self, name: str, value: str | None) -> str:
        if value:
            return value
        raise DotloopConfigurationError(f"{name} is required when Dotloop app OAuth is enabled.")

    def _now(self) -> int:
        return int(self._time_provider())


class DotloopAppCredentialProvider:
    """Provide current Dotloop API access tokens through app OAuth."""

    def __init__(
        self,
        *,
        settings: DotloopAppOAuthSettings,
        store: DotloopApiTokenStore,
        oauth_client: DotloopAppOAuthClient | None = None,
        time_provider: Callable[[], int] | None = None,
    ) -> None:
        """Initialize the credential provider."""
        self._settings = settings
        self._store = store
        self._oauth_client = oauth_client or DotloopAppOAuthClient(settings=settings)
        self._time_provider = time_provider or (lambda: int(time.time()))

    def authorization_url(self, *, state: str) -> str:
        """Build a Dotloop authorize URL for one hosted connection flow."""
        return self._oauth_client.authorization_url(state=state)

    def get_access_token(self) -> str:
        """Return a current Dotloop API access token, refreshing when needed."""
        token = self._store.load()
        if token is None:
            raise DotloopAppOAuthRequiredError(_RECONNECT_MESSAGE)
        if token.is_fresh(
            now=self._now(),
            leeway_seconds=self._settings.token_refresh_leeway_seconds,
        ):
            return token.access_token
        refreshed_token = self._oauth_client.refresh_token(refresh_token=token.refresh_token)
        self._store.save(refreshed_token)
        return refreshed_token.access_token

    def has_access_token(self) -> bool:
        """Return whether a usable access token can be loaded or refreshed."""
        try:
            self.get_access_token()
        except DotloopAppOAuthRequiredError:
            return False
        return True

    def exchange_authorization_code(self, *, code: str) -> DotloopApiToken:
        """Exchange a Dotloop OAuth code and persist the resulting token state."""
        token = self._oauth_client.exchange_authorization_code(code=code)
        self._store.save(token)
        return token

    def build_client_factory(self) -> Callable[[], DotloopClient]:
        """Return a DotloopClient factory that injects fresh app OAuth tokens."""
        return DotloopAppOAuthClientFactory(
            credential_provider=self,
            base_url=self._settings.base_url,
            timeout=self._settings.timeout,
        )

    def _now(self) -> int:
        return int(self._time_provider())


@dataclass(frozen=True)
class DotloopAppOAuthClientFactory:
    """Factory for Dotloop clients backed by the app OAuth credential provider."""

    credential_provider: DotloopAppCredentialProvider
    base_url: str
    timeout: int

    def __call__(self) -> DotloopClient:
        """Return a Dotloop client using a current app OAuth access token."""
        return DotloopClient(
            api_key=self.credential_provider.get_access_token(),
            base_url=self.base_url,
            timeout=self.timeout,
        )


def build_dotloop_app_credential_provider(
    settings: DotloopAppOAuthSettings,
) -> DotloopAppCredentialProvider:
    """Build the default hosted Dotloop app OAuth credential provider."""
    if not settings.enabled or not settings.token_secret_arn:
        raise DotloopConfigurationError("Dotloop app OAuth settings are not enabled.")
    return DotloopAppCredentialProvider(
        settings=settings,
        store=SecretsManagerDotloopApiTokenStore(secret_id=settings.token_secret_arn),
    )
