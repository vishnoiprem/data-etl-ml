#!/usr/bin/env python3
"""Run the full test suite with sane defaults.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Equivalent to: `pytest -q` but always runs from the project root.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [sys.executable, "-m", "pytest", "-q", str(PROJECT / "tests")]
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=PROJECT)


if __name__ == "__main__":
    sys.exit(main())
