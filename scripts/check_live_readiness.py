"""Report non-secret readiness for optional live Dotloop read checks."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dotloop_mcp.config import load_dotloop_env_file


@dataclass(frozen=True)
class LiveReadiness:
    """Non-secret live-readiness status."""

    run_flag_enabled: bool
    token_present: bool
    profile_id_present: bool
    loop_id_present: bool

    @property
    def account_ready(self) -> bool:
        """Whether the account live smoke can run."""
        return self.run_flag_enabled and self.token_present

    @property
    def loop_ready(self) -> bool:
        """Whether loop-specific live smokes can run."""
        return self.account_ready and self.profile_id_present and self.loop_id_present


def get_live_readiness(env_file: str | Path | None = None) -> LiveReadiness:
    """Read live-readiness state without exposing secret values."""
    load_dotloop_env_file(env_file)
    return LiveReadiness(
        run_flag_enabled=os.getenv("DOTLOOP_RUN_LIVE_TESTS") == "1",
        token_present=bool(os.getenv("DOTLOOP_ACCESS_TOKEN") or os.getenv("DOTLOOP_API_KEY")),
        profile_id_present=bool(os.getenv("DOTLOOP_LIVE_PROFILE_ID")),
        loop_id_present=bool(os.getenv("DOTLOOP_LIVE_LOOP_ID")),
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Check optional live Dotloop read readiness.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero when account-level live reads are not ready.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional DOTLOOP_* env file path. Defaults to .env or DOTLOOP_ENV_FILE.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Print live-readiness status without printing credentials."""
    args = build_parser().parse_args(argv)
    readiness = get_live_readiness(args.env_file)
    status = "ready" if readiness.account_ready else "blocked"

    print(f"Live Dotloop read readiness: {status}")
    print(f"DOTLOOP_RUN_LIVE_TESTS=1: {'present' if readiness.run_flag_enabled else 'missing'}")
    print(f"Dotloop token environment: {'present' if readiness.token_present else 'missing'}")
    print(
        "Optional profile/loop identifiers: "
        f"{'present' if readiness.loop_ready else 'missing or incomplete'}"
    )
    print("Account/profile read smokes require the run flag and a token.")
    print("Loop-specific read smokes also require profile and loop identifiers.")

    if args.require_ready and not readiness.account_ready:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
