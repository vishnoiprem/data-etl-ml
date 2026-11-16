"""Make `src/copyforge_ai` importable from any working directory."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
