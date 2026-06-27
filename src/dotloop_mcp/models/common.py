"""Shared MCP model helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class StrictRequestModel(BaseModel):
    """Base class for strict MCP request models."""

    model_config = ConfigDict(extra="forbid")


class ProfileIdRequest(StrictRequestModel):
    """Request model containing a Dotloop profile ID."""

    profile_id: int = Field(gt=0)


class ProfileLoopRequest(ProfileIdRequest):
    """Request model containing a profile and loop ID."""

    loop_id: int = Field(gt=0)


class FolderRequest(ProfileLoopRequest):
    """Request model containing a folder ID."""

    folder_id: int = Field(gt=0)


class DocumentRequest(ProfileLoopRequest):
    """Request model containing a document ID."""

    document_id: int = Field(gt=0)
    folder_id: int | None = Field(default=None, gt=0)


class DownloadDocumentRequest(DocumentRequest):
    """Request model for a size-limited document download."""

    max_bytes: int = Field(default=5_000_000, gt=0, le=50_000_000)


class ParticipantRequest(ProfileLoopRequest):
    """Request model containing a participant ID."""

    participant_id: int = Field(gt=0)


class TaskListRequest(ProfileLoopRequest):
    """Request model containing a task list ID."""

    tasklist_id: int = Field(gt=0)


class TaskRequest(TaskListRequest):
    """Request model containing a task ID."""

    task_id: int = Field(gt=0)


class TemplateRequest(ProfileIdRequest):
    """Request model containing a loop template ID."""

    template_id: int = Field(gt=0)


def to_json_value(value: object) -> JsonValue:
    """Convert common Python values to JSON-safe values.

    Args:
        value: The raw value to convert.

    Returns:
        A JSON-safe representation of the value.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, bytes):
        return {"contentLength": len(value)}
    if isinstance(value, dict):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [to_json_value(item) for item in value]
    return str(value)


def to_json_object(value: object) -> JsonObject:
    """Convert a value to a JSON object.

    Args:
        value: The raw value to convert.

    Returns:
        A JSON object. Non-dictionary values are wrapped under `data`.
    """
    converted = to_json_value(value)
    if isinstance(converted, dict):
        return converted
    return {"data": converted}
