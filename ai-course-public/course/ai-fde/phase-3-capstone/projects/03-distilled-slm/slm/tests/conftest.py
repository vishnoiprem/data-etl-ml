"""conftest.py — make the slm/ dir + Phase 3's eval module importable for pytest."""
import sys
from pathlib import Path

# slm/ dir (so dataset, train, serve, eval can be imported as siblings)
SLM = Path(__file__).parent.parent
if str(SLM) not in sys.path:
    sys.path.insert(0, str(SLM))

# Phase 3's eval module (we reuse run_eval)
_PHASE3_EVAL = SLM.parent.parent.parent / "phase-2-applications" / "service"
if str(_PHASE3_EVAL) not in sys.path:
    sys.path.insert(0, str(_PHASE3_EVAL))