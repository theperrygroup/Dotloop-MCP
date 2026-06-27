"""Safe Dotloop error mapping for MCP tools."""

from __future__ import annotations

from dotloop.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DotloopError,
    NotFoundError,
    RateLimitError,
    RedirectError,
    ServerError,
    ValidationError,
)

from dotloop_mcp.logging import redact_text


class DotloopMCPError(RuntimeError):
    """MCP-safe Dotloop error."""


def map_dotloop_exception(exc: Exception) -> DotloopMCPError:
    """Map library exceptions to stable MCP-safe errors.

    Args:
        exc: Exception raised by the Dotloop package or local service code.

    Returns:
        MCP-safe runtime error.
    """
    if isinstance(exc, AuthenticationError):
        return DotloopMCPError("Dotloop authentication failed.")
    if isinstance(exc, AuthorizationError):
        return DotloopMCPError("Dotloop authorization failed for this operation.")
    if isinstance(exc, NotFoundError):
        return DotloopMCPError("Dotloop resource was not found.")
    if isinstance(exc, RateLimitError):
        return DotloopMCPError("Dotloop rate limit was exceeded.")
    if isinstance(exc, RedirectError):
        return DotloopMCPError("Dotloop resource has moved or was merged.")
    if isinstance(exc, ValidationError):
        return DotloopMCPError("Dotloop rejected the request parameters.")
    if isinstance(exc, ServerError):
        return DotloopMCPError("Dotloop returned a server error.")
    if isinstance(exc, DotloopError):
        return DotloopMCPError(redact_text(exc.message))
    return DotloopMCPError(redact_text(str(exc)))
