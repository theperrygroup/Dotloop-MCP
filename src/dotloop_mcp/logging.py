"""Logging helpers with conservative token redaction."""

from __future__ import annotations

import logging
import re

_TOKEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(DOTLOOP_(?:ACCESS_TOKEN|API_KEY)=)[^\s]+"), r"\1[REDACTED]"),
    (
        re.compile(
            r"(Authorization:\s*(?:Bearer|Basic)\s+)[A-Za-z0-9._~+/=-]+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r'("(?:access|refresh)[_-]?token"\s*:\s*")[^"]+(")', re.IGNORECASE),
        r"\1[REDACTED]\2",
    ),
    (
        re.compile(
            r'("(?:api[_-]?key|client[_-]?secret)"\s*:\s*")[^"]+(")',
            re.IGNORECASE,
        ),
        r"\1[REDACTED]\2",
    ),
    (
        re.compile(r"((?:access|refresh)[_-]?token\s*[=:]\s*)[^\s&]+", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"((?:api[_-]?key|client[_-]?secret)\s*[=:]\s*)[^\s&]+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
)


def redact_text(value: str) -> str:
    """Redact token-like values from text.

    Args:
        value: Raw text.

    Returns:
        Redacted text.
    """
    redacted = value
    for pattern, replacement in _TOKEN_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure package logging.

    Args:
        level: Logging level name.

    Returns:
        Configured package logger.
    """
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    logger = logging.getLogger("dotloop_mcp")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
