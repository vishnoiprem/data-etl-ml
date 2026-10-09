"""conftest.py — make the slm/ dir + Phase 3's eval module importable for pytest."""
import sys
from pathlib import Path

# slm/ dir (so dataset, train, serve, eval can be imported as siblings)
SLM = Path(__file__).parent.parent
# IMPORTANT: insert slm/ LAST so `import eval` finds slm/eval.py,
# not Phase 3's service/eval.py. Phase 3's eval is loaded explicitly
# in slm/eval.py via importlib to avoid this collision.
_PHASE3_EVAL = SLM.parent.parent.parent / "phase-3-deployment" / "service"
if str(_PHASE3_EVAL) not in sys.path:
    sys.path.insert(0, str(_PHASE3_EVAL))
if str(SLM) not in sys.path:
    sys.path.insert(0, str(SLM))