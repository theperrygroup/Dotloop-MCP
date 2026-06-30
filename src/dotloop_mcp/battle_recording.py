"""Safe MCP tool-call recording for AI battle tests."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from dotloop_mcp.models.common import JsonObject, JsonValue

_SECRET_MARKERS = (
    "access_token",
    "api_key",
    "authorization",
    "bearer",
    "client_secret",
    "refresh_token",
    "token",
)


@dataclass(frozen=True)
class ToolCallRecord:
    """One safe MCP tool-call record."""

    sequence: int
    timestamp: float
    tool_name: str
    arguments: dict[str, JsonValue]
    status: str
    result_summary: dict[str, JsonValue] | None = None
    error: str | None = None


class ToolCallRecorder:
    """Append-only JSONL recorder for battle-test MCP calls."""

    def __init__(self, path: str | Path) -> None:
        """Initialize a recorder.

        Args:
            path: JSONL destination path.
        """
        self._path = Path(path)
        self._sequence = 0
        self._lock = Lock()

    @classmethod
    def from_path(cls, path: str | Path | None) -> ToolCallRecorder | None:
        """Return a recorder when a path is configured."""
        if path is None or str(path).strip() == "":
            return None
        return cls(path)

    @property
    def path(self) -> Path:
        """Return the JSONL output path."""
        return self._path

    def record_success(
        self,
        tool_name: str,
        arguments: dict[str, object],
        result: JsonObject,
    ) -> None:
        """Record a successful tool call."""
        self._record(
            tool_name=tool_name,
            arguments=arguments,
            status="ok",
            result_summary=_summarize_result(result),
            error=None,
        )

    def record_error(self, tool_name: str, arguments: dict[str, object], error: Exception) -> None:
        """Record a failed tool call without exposing raw exception internals."""
        self._record(
            tool_name=tool_name,
            arguments=arguments,
            status="error",
            result_summary=None,
            error=str(error),
        )

    def _record(
        self,
        *,
        tool_name: str,
        arguments: dict[str, object],
        status: str,
        result_summary: dict[str, JsonValue] | None,
        error: str | None,
    ) -> None:
        with self._lock:
            self._sequence += 1
            record = ToolCallRecord(
                sequence=self._sequence,
                timestamp=time.time(),
                tool_name=tool_name,
                arguments=_redact_mapping(arguments),
                status=status,
                result_summary=result_summary,
                error=_redact_text(error) if error is not None else None,
            )
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as output_file:
                output_file.write(json.dumps(record.__dict__, sort_keys=True) + "\n")


def _redact_mapping(values: dict[str, object]) -> dict[str, JsonValue]:
    return {str(key): _redact_value(str(key), value) for key, value in values.items()}


def _redact_value(key: str, value: object) -> JsonValue:
    lowered_key = key.lower()
    if any(marker in lowered_key for marker in _SECRET_MARKERS):
        return "[REDACTED]"
    if value is None or isinstance(value, str | int | float | bool):
        if isinstance(value, str):
            return _redact_text(value)
        return value
    if isinstance(value, dict):
        return {
            str(item_key): _redact_value(str(item_key), item) for item_key, item in value.items()
        }
    if isinstance(value, list | tuple | set):
        return [_redact_value(key, item) for item in value]
    return _redact_text(str(value))


def _redact_text(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        return "[REDACTED]"
    return value


def _summarize_result(result: JsonObject) -> dict[str, JsonValue]:
    result_keys: list[JsonValue] = [str(key) for key in sorted(result)]
    summary: dict[str, JsonValue] = {
        "type": "object",
        "keys": result_keys,
    }
    data = result.get("data")
    if isinstance(data, list):
        summary["dataCount"] = len(data)
    elif isinstance(data, dict):
        data_keys: list[JsonValue] = [str(key) for key in sorted(data)]
        summary["dataKeys"] = data_keys
    for key in ("contentType", "documentId", "sizeBytes"):
        value = result.get(key)
        if value is not None and isinstance(value, str | int | float | bool):
            summary[key] = value
    return summary
