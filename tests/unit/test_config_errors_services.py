"""Unit tests for config, error mapping, and the Dotloop service adapter."""

from __future__ import annotations

import base64
import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
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
from pydantic import ValidationError as PydanticValidationError
from tests.conftest import FakeDotloopClient

from dotloop_mcp.config import (
    DotloopConfigurationError,
    DotloopServerSettings,
    DotloopSettings,
)
from dotloop_mcp.errors import DotloopMCPError, map_dotloop_exception
from dotloop_mcp.logging import configure_logging, redact_text
from dotloop_mcp.mcp_tools import ListLoopsToolInput
from dotloop_mcp.models.common import DownloadDocumentRequest, to_json_object, to_json_value
from dotloop_mcp.services import DotloopService


@pytest.fixture(autouse=True)
def _isolate_dotloop_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    original_dotloop_env = {
        name: value for name, value in os.environ.items() if name.startswith("DOTLOOP_")
    }
    monkeypatch.chdir(tmp_path)
    for name in tuple(os.environ):
        if name.startswith("DOTLOOP_"):
            del os.environ[name]
    yield
    for name in tuple(os.environ):
        if name.startswith("DOTLOOP_"):
            del os.environ[name]
    os.environ.update(original_dotloop_env)


def test_dotloop_settings_loads_primary_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOTLOOP_ACCESS_TOKEN", "token-value")
    monkeypatch.setenv("DOTLOOP_BASE_URL", "https://example.test/v2")
    monkeypatch.setenv("DOTLOOP_TIMEOUT_SECONDS", "12")

    settings = DotloopSettings.from_env()

    assert settings.access_token == "token-value"
    assert settings.base_url == "https://example.test/v2"
    assert settings.timeout == 12


def test_dotloop_settings_loads_local_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("DOTLOOP_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "DOTLOOP_ACCESS_TOKEN=env-file-token",
                "DOTLOOP_BASE_URL=https://env-file.test/public/v2",
                "DOTLOOP_TIMEOUT_SECONDS=18",
                "UNRELATED_SECRET=not-loaded",
            ]
        ),
        encoding="utf-8",
    )

    settings = DotloopSettings.from_env()

    assert settings.access_token == "env-file-token"
    assert settings.base_url == "https://env-file.test/public/v2"
    assert settings.timeout == 18
    assert "UNRELATED_SECRET" not in os.environ


def test_dotloop_settings_keeps_exported_values_over_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DOTLOOP_ACCESS_TOKEN", "exported-token")
    (tmp_path / ".env").write_text("DOTLOOP_ACCESS_TOKEN=env-file-token\n", encoding="utf-8")

    settings = DotloopSettings.from_env()

    assert settings.access_token == "exported-token"


def test_dotloop_settings_loads_legacy_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("DOTLOOP_API_KEY", "legacy-token")

    settings = DotloopSettings.from_env()

    assert settings.access_token == "legacy-token"
    assert settings.timeout == 30


def test_dotloop_settings_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("DOTLOOP_API_KEY", raising=False)

    with pytest.raises(DotloopConfigurationError, match="access token"):
        DotloopSettings.from_env()


@pytest.mark.parametrize("timeout", ["bad", "0"])
def test_dotloop_settings_validates_integer_env(
    monkeypatch: pytest.MonkeyPatch,
    timeout: str,
) -> None:
    monkeypatch.setenv("DOTLOOP_ACCESS_TOKEN", "token-value")
    monkeypatch.setenv("DOTLOOP_TIMEOUT_SECONDS", timeout)

    with pytest.raises(DotloopConfigurationError):
        DotloopSettings.from_env()


def test_server_settings_loads_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOTLOOP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("DOTLOOP_HOST", "0.0.0.0")
    monkeypatch.setenv("DOTLOOP_PORT", "8123")
    monkeypatch.setenv("DOTLOOP_STREAMABLE_HTTP_PATH", "/custom")
    monkeypatch.setenv("DOTLOOP_LOG_LEVEL", "debug")

    settings = DotloopServerSettings.from_env()

    assert settings.transport == "streamable-http"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8123
    assert settings.streamable_http_path == "/custom"
    assert settings.log_level == "DEBUG"


def test_server_settings_validates_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOTLOOP_TRANSPORT", "bad")

    with pytest.raises(DotloopConfigurationError, match="DOTLOOP_TRANSPORT"):
        DotloopServerSettings.from_env()


def test_error_mapping_uses_safe_messages() -> None:
    assert str(map_dotloop_exception(AuthenticationError("raw secret"))) == (
        "Dotloop authentication failed."
    )
    assert str(map_dotloop_exception(RateLimitError("too many"))) == (
        "Dotloop rate limit was exceeded."
    )
    assert str(map_dotloop_exception(ValidationError("bad"))) == (
        "Dotloop rejected the request parameters."
    )
    assert str(map_dotloop_exception(AuthorizationError("denied"))) == (
        "Dotloop authorization failed for this operation."
    )
    assert str(map_dotloop_exception(NotFoundError("missing"))) == (
        "Dotloop resource was not found."
    )
    assert str(map_dotloop_exception(RedirectError("merged"))) == (
        "Dotloop resource has moved or was merged."
    )
    assert str(map_dotloop_exception(ServerError("down"))) == ("Dotloop returned a server error.")
    assert str(map_dotloop_exception(DotloopError("DOTLOOP_ACCESS_TOKEN=abc"))) == (
        "DOTLOOP_ACCESS_TOKEN=[REDACTED]"
    )
    assert str(map_dotloop_exception(RuntimeError("Authorization: Bearer token"))) == (
        "Authorization: Bearer [REDACTED]"
    )


def test_logging_helpers_redact_tokens() -> None:
    assert redact_text("DOTLOOP_API_KEY=abc123") == "DOTLOOP_API_KEY=[REDACTED]"
    assert redact_text("Authorization: Basic abc123") == "Authorization: Basic [REDACTED]"
    assert redact_text("access_token=abc123&scope=read") == "access_token=[REDACTED]&scope=read"
    assert redact_text('"client_secret":"abc123"') == '"client_secret":"[REDACTED]"'

    logger = configure_logging("debug")

    assert logger.level == logging.DEBUG


def test_request_model_validation() -> None:
    with pytest.raises(PydanticValidationError):
        DownloadDocumentRequest.model_validate(
            {"profile_id": 1, "loop_id": 2, "document_id": 3, "max_bytes": 0}
        )

    request = ListLoopsToolInput.model_validate({"profile_id": 1, "batch_size": 25})
    assert request.batch_size == 25
    assert request.batch_number == 1


def test_json_helpers_shape_common_values() -> None:
    assert to_json_value(b"abc") == {"contentLength": 3}
    assert to_json_value({"items": ("a", "b")}) == {"items": ["a", "b"]}
    assert to_json_object("value") == {"data": "value"}


@pytest.mark.asyncio
async def test_service_calls_fake_client_and_shapes_download() -> None:
    service = DotloopService(FakeDotloopClient())

    account = await service.get_account()
    download = await service.download_document(1, 2, 3, max_bytes=100)

    assert account["data"] == {"id": 1, "firstName": "Ada"}
    assert download["sizeBytes"] == len(b"pdf:1:2:3:None")
    assert download["contentBase64"] == base64.b64encode(b"pdf:1:2:3:None").decode("ascii")


@pytest.mark.asyncio
async def test_service_rejects_oversized_download() -> None:
    service = DotloopService(FakeDotloopClient())

    with pytest.raises(DotloopMCPError, match="exceeding"):
        await service.download_document(1, 2, 3, max_bytes=1)


@pytest.mark.asyncio
async def test_service_maps_json_call_errors() -> None:
    class BrokenAccount:
        def get_account(self) -> dict[str, object]:
            raise RuntimeError("Authorization: Bearer token")

    client = FakeDotloopClient()
    cast(Any, client).account = BrokenAccount()
    service = DotloopService(client)

    with pytest.raises(DotloopMCPError, match="REDACTED"):
        await service.get_account()


@pytest.mark.asyncio
async def test_service_rejects_non_byte_download() -> None:
    class BrokenDocument:
        def download_document(
            self,
            profile_id: int,
            loop_id: int,
            document_id: int,
            folder_id: int | None = None,
        ) -> str:
            return f"{profile_id}:{loop_id}:{document_id}:{folder_id}"

    client = FakeDotloopClient()
    cast(Any, client).document = BrokenDocument()
    service = DotloopService(client)

    with pytest.raises(DotloopMCPError, match="did not return bytes"):
        await service.download_document(1, 2, 3)
