"""Tests for local validation helper scripts."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts import validate_docs_links, validate_method_coverage


def test_docs_validation_allows_absent_ignored_docs_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("# Dotloop MCP\n")
    monkeypatch.chdir(tmp_path)

    assert validate_docs_links.main() == 0


def test_docs_validation_checks_local_docs_tree_when_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("# Dotloop MCP\n")
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)

    assert validate_docs_links.main() == 1


def test_method_coverage_validation_passes() -> None:
    assert validate_method_coverage.main() == 0
