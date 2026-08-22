"""Put the project root on sys.path so `pytest` works from any directory.

Without this, `from app import app` only resolves when pytest happens to be
invoked from the project root.
"""

import sys
from pathlib import Path

ROOT = str(Path(__file__).parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
