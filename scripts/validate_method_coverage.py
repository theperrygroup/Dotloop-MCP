"""Validate method-level Dotloop coverage against the installed package."""

from __future__ import annotations

from dotloop_mcp.coverage import METHOD_COVERAGE_MARKDOWN, unclassified_method_keys


def main() -> int:
    """Validate that every installed package method has an explicit classification."""
    missing = unclassified_method_keys()
    if missing:
        print("Method coverage has unclassified package methods:")
        for method_key in missing:
            print(f"- {method_key}")
        return 1

    if "Dotloop Library Method Coverage" not in METHOD_COVERAGE_MARKDOWN:
        print("Method coverage resource did not render expected title.")
        return 1

    print("Method coverage validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
