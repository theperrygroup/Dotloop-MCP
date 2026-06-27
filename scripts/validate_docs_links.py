"""Lightweight docs validation for local Markdown references."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    """Validate that required planning and runtime docs exist."""
    required_paths = [
        Path("README.md"),
        Path("docs/planning/dotloop-mcp-buildout/README.md"),
        Path("docs/planning/dotloop-mcp-buildout/execution/dotloop-mcp-buildout-plan.md"),
        Path("docs/research/dotloop-mcp-buildout_results/dotloop-library-surface.md"),
        Path("docs/api/dotloop-api-coverage-matrix.md"),
        Path("docs/api/dotloop-library-method-coverage.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing required doc: {path}")
        return 1
    print("Docs validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
