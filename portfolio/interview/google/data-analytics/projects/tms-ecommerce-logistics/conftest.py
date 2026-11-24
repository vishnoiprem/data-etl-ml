"""Root conftest.

Its only job is to make ``src/`` importable so the test suite and the demo
script can run straight from a checkout without an editable install.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
