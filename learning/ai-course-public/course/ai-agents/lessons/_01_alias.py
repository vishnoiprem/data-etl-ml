"""
================================================================
_01_alias  --  Python-importable alias for lessons/01-roi-formula.py
================================================================

Python can't `import "01-roi-formula"` because filenames starting
with digits aren't valid module names.  This file re-exports the
public API so the notebook can do:

    from lessons._01_alias import demo, monthly_roi

Run:    not meant to be run directly
Keys:   none
"""

from lessons import _01_loader  # noqa: F401  -- ensures the loader path exists


# Re-export from the loader so callers can import from _01_alias directly
from lessons._01_loader import (  # type: ignore  # noqa: F401
    LESSON_NUMBER,
    WEEKS_PER_MONTH,
    USE_CASE_CRITERIA,
    REQUIRED_INPUTS,
    RANGES,
    UseCaseScore,
    USE_CASES,
    monthly_value,
    monthly_roi,
    score_use_case,
    demo,
)
