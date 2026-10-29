"""
conftest.py — make `src/` importable for pytest.

We do this in conftest (vs. an installed package) so the project
remains a flat layout that anyone can clone-and-run without poetry.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
