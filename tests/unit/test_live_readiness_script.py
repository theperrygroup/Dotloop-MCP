"""Tests for the non-secret live-readiness preflight."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from scripts import check_live_readiness


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


def test_live_readiness_reports_blocked_without_secret_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DOTLOOP_RUN_LIVE_TESTS", raising=False)
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("DOTLOOP_API_KEY", raising=False)

    assert check_live_readiness.main([]) == 0

    output = capsys.readouterr().out
    assert "blocked" in output
    assert "missing" in output


def test_live_readiness_reads_env_file_without_printing_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("DOTLOOP_RUN_LIVE_TESTS", raising=False)
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "DOTLOOP_RUN_LIVE_TESTS=1",
                "DOTLOOP_ACCESS_TOKEN=secret-token-value",
            ]
        ),
        encoding="utf-8",
    )

    assert check_live_readiness.main(["--env-file", str(env_file)]) == 0

    output = capsys.readouterr().out
    assert "Live Dotloop read readiness: ready" in output
    assert "Dotloop token environment: present" in output
    assert "secret-token-value" not in output


def test_live_readiness_can_require_account_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DOTLOOP_RUN_LIVE_TESTS", raising=False)
    monkeypatch.delenv("DOTLOOP_ACCESS_TOKEN", raising=False)

    assert check_live_readiness.main(["--require-ready"]) == 1


def test_live_readiness_reports_ready_without_printing_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DOTLOOP_RUN_LIVE_TESTS", "1")
    monkeypatch.setenv("DOTLOOP_ACCESS_TOKEN", "secret-token-value")

    assert check_live_readiness.main([]) == 0

    output = capsys.readouterr().out
    assert "ready" in output
    assert "secret-token-value" not in output
