"""Tests for the non-secret live-readiness preflight."""

from __future__ import annotations

import pytest
from scripts import check_live_readiness


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
