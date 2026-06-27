"""Configuration for the Dotloop MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, cast


class DotloopConfigurationError(RuntimeError):
    """Raised when local Dotloop MCP configuration is invalid."""


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


@dataclass(frozen=True)
class DotloopSettings:
    """Settings used to construct the local Dotloop API client."""

    access_token: str
    base_url: str = "https://api-gateway.dotloop.com/public/v2"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> DotloopSettings:
        """Load settings from local environment variables.

        Returns:
            Dotloop client settings.

        Raises:
            DotloopConfigurationError: If required settings are missing.
        """
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
class DotloopServerSettings:
    """Settings used to start the MCP server."""

    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    streamable_http_path: str = "/mcp"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> DotloopServerSettings:
        """Load server settings from local environment variables.

        Returns:
            Server bootstrap settings.

        Raises:
            DotloopConfigurationError: If the transport is invalid.
        """
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
        )
