#!/usr/bin/env python3
"""Validate built distribution artifacts in an isolated virtual environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"


def _latest_artifact(directory: Path, pattern: str) -> Path:
    """Return the newest matching artifact in a directory."""
    artifacts = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime)
    if not artifacts:
        raise FileNotFoundError(f"No build artifact matched {pattern!r} in {directory}.")
    return artifacts[-1]


def _python_command(bin_dir: Path, command: str) -> Path:
    """Return a platform-specific executable path from a virtual environment."""
    suffix = ".exe" if os.name == "nt" else ""
    return bin_dir / f"{command}{suffix}"


def _run(command: Sequence[str], *, cwd: Path | None = None) -> None:
    """Run a command and raise if it fails."""
    subprocess.run(
        command,
        check=True,
        cwd=str(cwd) if cwd is not None else None,
    )


def main() -> None:
    """Validate that built artifacts can be installed and exercised."""
    if not DIST_DIR.exists():
        raise SystemExit("dist/ does not exist. Run `uv build --clear` first.")
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise SystemExit("uv is required for build artifact validation.")

    sdist_path = _latest_artifact(DIST_DIR, "*.tar.gz")
    wheel_path = _latest_artifact(DIST_DIR, "*.whl")

    with tempfile.TemporaryDirectory(prefix="dotloop-mcp-build-") as temp_dir:
        venv_dir = Path(temp_dir) / "venv"
        _run([uv_path, "venv", str(venv_dir)])
        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        python_path = _python_command(bin_dir, "python")
        cli_path = _python_command(bin_dir, "dotloop-mcp")
        hosted_cli_path = _python_command(bin_dir, "dotloop-mcp-hosted")

        _run([uv_path, "pip", "install", "--python", str(python_path), str(wheel_path)])
        _run([str(cli_path), "--help"])
        _run([str(hosted_cli_path), "--help"])
        _run(
            [
                str(python_path),
                "-c",
                (
                    "import dotloop_mcp; "
                    "assert dotloop_mcp.__version__; "
                    "print(dotloop_mcp.__version__)"
                ),
            ]
        )

    print(
        "Validated build artifacts:",
        sdist_path.name,
        wheel_path.name,
    )


if __name__ == "__main__":
    main()
