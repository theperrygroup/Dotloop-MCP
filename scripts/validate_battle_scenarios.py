"""Validate the Dotloop MCP AI battle-test scenario corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

DEFAULT_SCENARIO_FILE = Path("tests/battle/scenarios/dotloop_ai_battle_scenarios.json")

MINIMUM_CATEGORY_COUNTS = {
    "identity_navigation": 35,
    "loop_document": 35,
    "people_workflow": 25,
    "templates": 20,
    "multi_turn": 20,
    "negative_safety": 15,
}

WRITE_TOOL_VERBS = {
    "add",
    "archive",
    "create",
    "delete",
    "remove",
    "revoke",
    "send",
    "update",
    "upload",
}


def load_scenario_corpus(path: str | Path = DEFAULT_SCENARIO_FILE) -> dict[str, Any]:
    """Load the battle-test scenario corpus."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Scenario corpus must be a JSON object.")
    return payload


def scenario_count_by_category(corpus: dict[str, Any]) -> Counter[str]:
    """Return scenario counts grouped by category."""
    scenarios = _scenarios(corpus)
    return Counter(str(scenario.get("category")) for scenario in scenarios)


def validate_scenario_corpus(corpus: dict[str, Any]) -> list[str]:
    """Return validation errors for the scenario corpus."""
    errors: list[str] = []
    scenarios = _scenarios(corpus)
    if corpus.get("version") != 1:
        errors.append("Scenario corpus version must be 1.")
    if len(scenarios) < sum(MINIMUM_CATEGORY_COUNTS.values()):
        errors.append("Scenario corpus must contain at least 150 scenarios.")

    seen_ids: set[str] = set()
    for index, scenario in enumerate(scenarios, 1):
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"Scenario {index} is missing a string id.")
        elif scenario_id in seen_ids:
            errors.append(f"Scenario id is duplicated: {scenario_id}.")
        else:
            seen_ids.add(scenario_id)

        category = scenario.get("category")
        if category not in MINIMUM_CATEGORY_COUNTS:
            errors.append(f"Scenario {scenario_id or index} has an unknown category.")

        turns = scenario.get("turns")
        if not isinstance(turns, list) or not turns:
            errors.append(f"Scenario {scenario_id or index} must include turns.")

        expected_calls = scenario.get("expected_tool_calls")
        if not isinstance(expected_calls, list):
            errors.append(f"Scenario {scenario_id or index} must include expected_tool_calls.")
            continue
        if category == "negative_safety" and expected_calls:
            errors.append(f"Negative scenario {scenario_id or index} must not expect tool calls.")
        for call in expected_calls:
            errors.extend(_validate_expected_call(call, scenario_id or str(index)))

    category_counts = scenario_count_by_category(corpus)
    for category, minimum in MINIMUM_CATEGORY_COUNTS.items():
        if category_counts[category] < minimum:
            errors.append(
                f"Category {category} has {category_counts[category]} scenarios; "
                f"expected at least {minimum}."
            )
    return errors


def _scenarios(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list):
        return []
    return [scenario for scenario in scenarios if isinstance(scenario, dict)]


def _validate_expected_call(call: Any, scenario_id: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(call, dict):
        return [f"Scenario {scenario_id} has a non-object expected tool call."]
    name = call.get("name")
    if not isinstance(name, str) or not name.startswith("dotloop_"):
        errors.append(f"Scenario {scenario_id} expected call must use a dotloop_* tool.")
    elif any(f"_{verb}_" in name for verb in WRITE_TOOL_VERBS):
        errors.append(f"Scenario {scenario_id} expected write-like tool {name}.")
    arguments = call.get("arguments")
    if not isinstance(arguments, dict):
        errors.append(f"Scenario {scenario_id} expected call {name} must include arguments.")
    return errors


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Validate Dotloop MCP battle scenarios.")
    parser.add_argument("scenario_file", nargs="?", default=str(DEFAULT_SCENARIO_FILE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the battle scenario corpus from the command line."""
    args = build_parser().parse_args(argv)
    corpus = load_scenario_corpus(args.scenario_file)
    errors = validate_scenario_corpus(corpus)
    if errors:
        for error in errors:
            print(error)
        return 1
    counts = scenario_count_by_category(corpus)
    total = sum(counts.values())
    print(f"Battle scenario validation passed: {total} scenarios.")
    for category in sorted(MINIMUM_CATEGORY_COUNTS):
        print(f"{category}: {counts[category]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
