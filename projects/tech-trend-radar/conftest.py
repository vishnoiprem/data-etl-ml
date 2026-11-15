"""Make `src/tech_trend_radar` importable from any cwd.

The package lives under `src/`, so the project root has to be on `sys.path`
before pytest collects anything. The `Makefile` sets `PYTHONPATH` as well; this
file is what makes `pytest` work when it is invoked directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
