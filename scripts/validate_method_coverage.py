"""Validate method-level Dotloop coverage docs against the installed package."""

from __future__ import annotations

import inspect
from pathlib import Path

from dotloop import DotloopClient
from dotloop.auth import AuthClient

_DOC_PATH = Path("docs/api/dotloop-library-method-coverage.md")
_GENERIC_HTTP_METHODS = {"get", "post", "patch", "delete"}
_CLIENT_DOMAINS = (
    "account",
    "profile",
    "loop",
    "loop_detail",
    "loop_it",
    "contact",
    "folder",
    "document",
    "participant",
    "task",
    "activity",
    "template",
    "webhook",
)


def _public_domain_methods(domain_client: object) -> list[str]:
    """Return named public domain methods, excluding generic HTTP helpers."""
    methods: list[str] = []
    for method_name, member in inspect.getmembers(domain_client, predicate=callable):
        if method_name.startswith("_") or method_name in _GENERIC_HTTP_METHODS:
            continue
        methods.append(method_name)
    return sorted(methods)


def _expected_method_tokens() -> list[str]:
    """Build expected method tokens from the installed `dotloop` package."""
    client = DotloopClient(api_key="coverage-validation")
    expected: list[str] = []

    for domain_name in _CLIENT_DOMAINS:
        domain_client = getattr(client, domain_name)
        for method_name in _public_domain_methods(domain_client):
            if domain_name == "loop_it":
                expected.append(f"`loop_it.{method_name}`")
            else:
                expected.append(f"`{method_name}`")

    auth = AuthClient(
        api_key="coverage-validation",
        client_id="coverage-validation",
        client_secret="coverage-validation",
        redirect_uri="http://localhost",
    )
    expected.extend(f"`{method_name}`" for method_name in _public_domain_methods(auth))
    return sorted(set(expected))


def main() -> int:
    """Validate that every expected method token appears in the coverage doc."""
    if not _DOC_PATH.exists():
        print(f"Missing method coverage doc: {_DOC_PATH}")
        return 1

    doc_text = _DOC_PATH.read_text()
    missing = [method_token for method_token in _expected_method_tokens() if method_token not in doc_text]
    if missing:
        print("Method coverage doc is missing package methods:")
        for method_token in missing:
            print(f"- {method_token}")
        return 1

    print("Method coverage validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
