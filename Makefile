.DEFAULT_GOAL := help

.PHONY: help sync docs-check format-check lint typecheck test coverage cli-help live-readiness-check live-read-check live-identity-check battle-smoke battle-test battle-report validate build build-smoke release-validate

help:
	@printf "%s\n" \
		"make sync             Install locked project dependencies with uv" \
		"make docs-check       Validate docs references" \
		"make format-check     Check Ruff formatting" \
		"make lint             Run Ruff lint checks" \
		"make typecheck        Run mypy" \
		"make test             Run pytest" \
		"make coverage         Run branch coverage" \
		"make cli-help         Check the CLI entrypoint" \
		"make live-readiness-check Report non-secret live read readiness" \
		"make live-read-check  Run optional live read smoke checks" \
		"make live-identity-check Alias for live-read-check" \
		"make battle-smoke     Validate battle fixture, scenario corpus, and scorer" \
		"make battle-test      Run automated battle harness tests" \
		"make battle-report    Score a battle call log with DOTLOOP_BATTLE_CALL_LOG" \
		"make validate         Run the local validation stack" \
		"make build            Build sdist and wheel artifacts" \
		"make build-smoke      Build artifacts and validate wheel install/CLI" \
		"make release-validate Run validation plus build smoke checks"

sync:
	uv sync --frozen

docs-check:
	uv run python scripts/validate_docs_links.py
	uv run python scripts/validate_method_coverage.py

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest

coverage:
	uv run coverage run --branch -m pytest
	uv run coverage report

cli-help:
	uv run python -m dotloop_mcp.cli --help

live-readiness-check:
	uv run python scripts/check_live_readiness.py

live-read-check:
	DOTLOOP_RUN_LIVE_TESTS=1 uv run python scripts/check_live_readiness.py --require-ready
	DOTLOOP_RUN_LIVE_TESTS=1 uv run pytest tests/live -m live

live-identity-check: live-read-check

battle-smoke:
	rm -rf tmp/ai-battle/smoke
	uv run python scripts/validate_battle_scenarios.py
	DOTLOOP_BATTLE_FIXTURE_MODE=1 DOTLOOP_BATTLE_RECORD_PATH=tmp/ai-battle/smoke/local/mcp_calls.jsonl uv run python scripts/run_battle_smoke.py
	uv run python scripts/battle_report.py --call-log tmp/ai-battle/smoke/local/mcp_calls.jsonl --client local-smoke --allow-partial

battle-test:
	uv run pytest tests/battle -q

battle-report:
	uv run python scripts/battle_report.py --call-log "$${DOTLOOP_BATTLE_CALL_LOG:-tmp/ai-battle/latest/mcp_calls.jsonl}" --client "$${DOTLOOP_BATTLE_CLIENT:-manual}"

validate:
	$(MAKE) sync
	$(MAKE) docs-check
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	$(MAKE) coverage
	$(MAKE) cli-help

build:
	uv build --clear

build-smoke: build
	uv run python scripts/validate_build_artifacts.py

release-validate:
	$(MAKE) validate
	$(MAKE) build-smoke
