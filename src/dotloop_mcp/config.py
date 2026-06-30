"""Configuration for the Dotloop MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit, urlunsplit


class DotloopConfigurationError(RuntimeError):
    """Raised when local Dotloop MCP configuration is invalid."""


def load_dotloop_env_file(env_file: str | Path | None = None) -> None:
    """Load DOTLOOP_* values from a local env file without printing secrets.

    Existing process environment values win. By default, this reads `.env` from
    the current working directory. `DOTLOOP_ENV_FILE` can point at a different
    file.
    """
    configured_path = env_file or os.getenv("DOTLOOP_ENV_FILE")
    path = Path(configured_path) if configured_path else Path.cwd() / ".env"
    if not path.exists():
        if configured_path:
            raise DotloopConfigurationError("DOTLOOP_ENV_FILE points to a missing file.")
        return
    if not path.is_file():
        raise DotloopConfigurationError("Dotloop env file path must be a file.")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise DotloopConfigurationError(
                f"Dotloop env file line {line_number} must use NAME=VALUE syntax."
            )
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if not name.startswith("DOTLOOP_"):
            continue
        if name in os.environ:
            continue
        value = raw_value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ[name] = value


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise DotloopConfigurationError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise DotloopConfigurationError(f"{name} must be greater than zero.")
    return value


def _read_non_negative_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise DotloopConfigurationError(f"{name} must be an integer.") from exc
    if value < 0:
        raise DotloopConfigurationError(f"{name} must be zero or greater.")
    return value


def _read_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    raise DotloopConfigurationError(f"{name} must be a boolean value.")


def _read_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    values = tuple(value.strip() for value in raw_value.split(",") if value.strip())
    return values


def _normalize_public_http_url(name: str, raw_value: str) -> str:
    value = raw_value.strip()
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise DotloopConfigurationError(f"{name} must be an absolute HTTP(S) URL.")
    if parsed.username or parsed.password:
        raise DotloopConfigurationError(f"{name} must not include user info.")
    if parsed.query or parsed.fragment:
        raise DotloopConfigurationError(f"{name} must not include query strings or fragments.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise DotloopConfigurationError(f"{name} has an invalid port.") from exc

    host = parsed.hostname.lower()
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme.lower() != "https" and host not in local_hosts:
        raise DotloopConfigurationError(f"{name} must use HTTPS unless it is localhost.")

    netloc_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    netloc = f"{netloc_host}:{port}" if port is not None else netloc_host
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))


def _read_required_auth_url(name: str) -> str:
    raw_value = os.getenv(name)
    if not raw_value:
        raise DotloopConfigurationError(f"{name} is required when MCP auth is enabled.")
    return _normalize_public_http_url(name, raw_value)


@dataclass(frozen=True)
class DotloopSettings:
    """Settings used to construct the local Dotloop API client."""

    access_token: str
    base_url: str = "https://api-gateway.dotloop.com/public/v2"
    timeout: int = 30

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> DotloopSettings:
        """Load settings from local environment variables.

        Args:
            env_file: Optional env file path. Defaults to `.env` in the current
                working directory, or `DOTLOOP_ENV_FILE` when set.

        Returns:
            Dotloop client settings.

        Raises:
            DotloopConfigurationError: If required settings are missing.
        """
        load_dotloop_env_file(env_file)
        access_token = os.getenv("DOTLOOP_ACCESS_TOKEN") or os.getenv("DOTLOOP_API_KEY")
        if not access_token:
            raise DotloopConfigurationError(
                "A Dotloop access token is required. Set DOTLOOP_ACCESS_TOKEN."
            )
        return cls(
            access_token=access_token,
            base_url=os.getenv("DOTLOOP_BASE_URL", cls.base_url),
            timeout=_read_int("DOTLOOP_TIMEOUT_SECONDS", cls.timeout),
        )


@dataclass(frozen=True)
class DotloopMcpAuthSettings:
    """Settings for authenticating inbound HTTP MCP callers."""

    enabled: bool = False
    issuer_url: str | None = None
    resource_server_url: str | None = None
    jwks_url: str | None = None
    required_scopes: tuple[str, ...] = ("dotloop:read",)
    audience: str | None = None
    allowed_algorithms: tuple[str, ...] = ("RS256",)
    token_leeway_seconds: int = 30
    jwks_cache_seconds: int = 300

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> DotloopMcpAuthSettings:
        """Load inbound MCP auth settings from local environment variables."""
        load_dotloop_env_file(env_file)
        enabled = _read_bool("DOTLOOP_MCP_AUTH_ENABLED", False)
        if not enabled:
            return cls()

        return cls(
            enabled=True,
            issuer_url=_read_required_auth_url("DOTLOOP_MCP_AUTH_ISSUER_URL"),
            resource_server_url=_read_required_auth_url("DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL"),
            jwks_url=_read_required_auth_url("DOTLOOP_MCP_AUTH_JWKS_URL"),
            required_scopes=_read_csv("DOTLOOP_MCP_AUTH_REQUIRED_SCOPES", ("dotloop:read",)),
            audience=os.getenv("DOTLOOP_MCP_AUTH_AUDIENCE") or None,
            allowed_algorithms=_read_csv("DOTLOOP_MCP_AUTH_ALLOWED_ALGORITHMS", ("RS256",)),
            token_leeway_seconds=_read_non_negative_int(
                "DOTLOOP_MCP_AUTH_TOKEN_LEEWAY_SECONDS",
                cls.token_leeway_seconds,
            ),
            jwks_cache_seconds=_read_int(
                "DOTLOOP_MCP_AUTH_JWKS_CACHE_SECONDS",
                cls.jwks_cache_seconds,
            ),
        )

    def require_enabled_value(self, name: str, value: str | None) -> str:
        """Return a required auth value after narrowing optional config types."""
        if value:
            return value
        raise DotloopConfigurationError(f"{name} is required when MCP auth is enabled.")


@dataclass(frozen=True)
class DotloopServerSettings:
    """Settings used to start the MCP server."""

    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    streamable_http_path: str = "/mcp"
    log_level: str = "INFO"
    mcp_auth: DotloopMcpAuthSettings = field(default_factory=DotloopMcpAuthSettings)

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> DotloopServerSettings:
        """Load server settings from local environment variables.

        Args:
            env_file: Optional env file path. Defaults to `.env` in the current
                working directory, or `DOTLOOP_ENV_FILE` when set.

        Returns:
            Server bootstrap settings.

        Raises:
            DotloopConfigurationError: If the transport is invalid.
        """
        load_dotloop_env_file(env_file)
        raw_transport = os.getenv("DOTLOOP_TRANSPORT", cls.transport)
        if raw_transport not in {"stdio", "streamable-http"}:
            raise DotloopConfigurationError(
                "DOTLOOP_TRANSPORT must be either 'stdio' or 'streamable-http'."
            )
        transport = cast(Literal["stdio", "streamable-http"], raw_transport)
        return cls(
            transport=transport,
            host=os.getenv("DOTLOOP_HOST", cls.host),
            port=_read_int("DOTLOOP_PORT", cls.port),
            streamable_http_path=os.getenv(
                "DOTLOOP_STREAMABLE_HTTP_PATH",
                cls.streamable_http_path,
            ),
            log_level=os.getenv("DOTLOOP_LOG_LEVEL", cls.log_level).upper(),
            mcp_auth=DotloopMcpAuthSettings.from_env(env_file),
        )
