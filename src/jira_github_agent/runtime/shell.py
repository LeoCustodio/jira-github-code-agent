from __future__ import annotations
from pathlib import Path
import subprocess
from typing import Optional

def run(cmd: list[str], cwd: Optional[Path] = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

def run_capture(command: str, cwd: Path) -> dict:
    p = subprocess.run(command, cwd=str(cwd), shell=True, capture_output=True, text=True)
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout[-20000:],
        "stderr": p.stderr[-20000:],
    }
