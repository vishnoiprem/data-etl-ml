"""
================================================================
_01_loader  --  imports the lesson file with a digit-prefix name.
================================================================

Uses importlib to load `01-roi-formula.py` (which can't be imported
by its raw name because it starts with a digit) and re-exports its
public symbols.  This indirection is only for the notebook path;
the lesson's own `if __name__ == "__main__": demo()` still works
when you run `python3 lessons/01-roi-formula.py` directly.
"""

import importlib.util
import sys
from pathlib import Path

_LESSON_PATH = Path(__file__).parent / "01-roi-formula.py"
_spec = importlib.util.spec_from_file_location("lessons._01_roiformula", _LESSON_PATH)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["lessons._01_roiformula"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

# Re-export everything
LESSON_NUMBER = _mod.LESSON_NUMBER
WEEKS_PER_MONTH = _mod.WEEKS_PER_MONTH
USE_CASE_CRITERIA = _mod.USE_CASE_CRITERIA
REQUIRED_INPUTS = _mod.REQUIRED_INPUTS
RANGES = _mod.RANGES
UseCaseScore = _mod.UseCaseScore
USE_CASES = _mod.USE_CASES
monthly_value = _mod.monthly_value
monthly_roi = _mod.monthly_roi
score_use_case = _mod.score_use_case
demo = _mod.demo
