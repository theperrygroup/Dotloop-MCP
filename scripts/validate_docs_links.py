"""Lightweight docs validation for local Markdown references."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    """Validate tracked docs and optional local planning docs."""
    tracked_paths = [
        Path("README.md"),
    ]
    optional_local_paths = [
        Path("docs/planning/dotloop-mcp-buildout/README.md"),
        Path("docs/planning/dotloop-mcp-buildout/execution/dotloop-mcp-buildout-plan.md"),
        Path("docs/research/dotloop-mcp-buildout_results/dotloop-library-surface.md"),
        Path("docs/api/dotloop-api-coverage-matrix.md"),
        Path("docs/api/dotloop-library-method-coverage.md"),
    ]
    missing = [str(path) for path in tracked_paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing required doc: {path}")
        return 1

    if Path("docs").exists():
        missing_optional = [str(path) for path in optional_local_paths if not path.exists()]
        if missing_optional:
            for path in missing_optional:
                print(f"Missing local planning doc: {path}")
            return 1
    else:
        print("Optional ignored docs tree is absent; skipped local planning doc checks.")

    print("Docs validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
