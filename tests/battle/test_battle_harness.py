"""Battle fixture, scenario, and scoring tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from scripts.battle_report import load_call_log, score_call_log
from scripts.validate_battle_scenarios import (
    MINIMUM_CATEGORY_COUNTS,
    load_scenario_corpus,
    scenario_count_by_category,
    validate_scenario_corpus,
)

from dotloop_mcp.config import DotloopServerSettings
from dotloop_mcp.mcp_server import create_server


def test_battle_scenario_corpus_meets_required_matrix() -> None:
    corpus = load_scenario_corpus()
    errors = validate_scenario_corpus(corpus)
    counts = scenario_count_by_category(corpus)

    assert errors == []
    assert sum(counts.values()) >= 150
    for category, minimum in MINIMUM_CATEGORY_COUNTS.items():
        assert counts[category] >= minimum


@pytest.mark.asyncio
async def test_battle_fixture_mode_records_public_tool_calls(tmp_path: Path) -> None:
    record_path = tmp_path / "mcp_calls.jsonl"
    server = create_server(
        server_settings=DotloopServerSettings(
            battle_fixture_mode=True,
            battle_record_path=str(record_path),
        )
    )

    result = await server.call_tool("dotloop_get_account", {})

    calls = load_call_log(record_path)
    assert result
    assert calls[0]["tool_name"] == "dotloop_get_account"
    assert calls[0]["arguments"] == {}
    assert calls[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_battle_fixture_corpus_calls_score_cleanly(tmp_path: Path) -> None:
    corpus = load_scenario_corpus()
    record_path = tmp_path / "corpus" / "mcp_calls.jsonl"
    server = create_server(
        server_settings=DotloopServerSettings(
            battle_fixture_mode=True,
            battle_record_path=str(record_path),
        )
    )

    for scenario in _scenarios(corpus):
        for expected_call in scenario["expected_tool_calls"]:
            await server.call_tool(expected_call["name"], expected_call["arguments"])

    calls = load_call_log(record_path)
    score = score_call_log(corpus, calls)

    assert score["passed"] is True
    assert score["expected_calls"] == score["actual_calls"]
    assert score["matched_calls"] == score["expected_calls"]
    assert score["write_like_calls"] == []
    assert score["leaked_terms"] == []


def test_battle_fixture_env_mode_does_not_require_dotloop_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in tuple(os.environ):
        if name.startswith("DOTLOOP_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DOTLOOP_BATTLE_FIXTURE_MODE", "1")
    monkeypatch.setenv("DOTLOOP_BATTLE_RECORD_PATH", str(tmp_path / "mcp_calls.jsonl"))

    server = create_server()

    assert server is not None


def _scenarios(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = corpus.get("scenarios")
    assert isinstance(scenarios, list)
    typed_scenarios: list[dict[str, Any]] = []
    for scenario in scenarios:
        assert isinstance(scenario, dict)
        expected_calls = scenario.get("expected_tool_calls")
        assert isinstance(expected_calls, list)
        typed_scenarios.append(scenario)
    return typed_scenarios
