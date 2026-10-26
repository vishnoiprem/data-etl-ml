"""conftest.py — make the sibling `service/` dir importable for pytest."""
import sys
from pathlib import Path

SVC = Path(__file__).parent.parent
if str(SVC) not in sys.path:
    sys.path.insert(0, str(SVC))