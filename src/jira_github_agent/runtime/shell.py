# jira_github_agent/runtime/shell.py
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Union


def run(
    cmd: List[str],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
) -> None:
    """
    Run a command and raise a helpful error if it fails.
    Accepts env for non-interactive git operations.
    """
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if cp.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {cp.returncode}): {cmd}\n"
            f"cwd: {cwd}\n\n"
            f"stdout:\n{cp.stdout}\n\n"
            f"stderr:\n{cp.stderr}\n"
        )


def run_capture(
    command: str,
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Run a shell command (string) and capture output.
    """
    cp = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "ok": cp.returncode == 0,
        "returncode": cp.returncode,
        "stdout": cp.stdout,
        "stderr": cp.stderr,
    }