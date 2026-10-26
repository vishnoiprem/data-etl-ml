"""Shared pytest fixtures + import guards.

The CI contract for this project (matching `.../03-distrained-slm/slm/train.py`):
if peft / trl / transformers aren't importable, every GPU-marked test is skipped
rather than failing. That keeps `make test` green on a laptop and on CI.

`PYTHONPATH` note: `make test` runs from the project root, so `agent` is
importable. If you run `pytest tests/` directly from elsewhere, set
`PYTHONPATH=.` first.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Optional-dependency probes, mirroring agent.train.HAVE_PEFT ---
try:
    import peft  # noqa: F401  type: ignore
    import transformers  # noqa: F401  type: ignore
    import trl  # noqa: F401  type: ignore

    HAVE_PEFT = True
except ImportError:
    HAVE_PEFT = False

try:
    import datasets  # noqa: F401  type: ignore

    HAVE_DATASETS = True
except ImportError:
    HAVE_DATASETS = False

try:
    import numpy  # noqa: F401  type: ignore
    import scipy  # noqa: F401  type: ignore

    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


requires_peft = pytest.mark.skipif(
    not HAVE_PEFT, reason="peft/trl/transformers not installed (CI mode)"
)
requires_datasets = pytest.mark.skipif(
    not HAVE_DATASETS, reason="datasets not installed"
)
requires_scipy = pytest.mark.skipif(
    not HAVE_SCIPY, reason="scipy not installed (drift fallback is numpy-only)"
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def settings():
    """Fresh settings bundle, cache cleared so env changes in a test are visible."""
    from agent.config import load_settings

    load_settings.cache_clear()
    s = load_settings()
    yield s
    load_settings.cache_clear()


@pytest.fixture
def tmp_prompts() -> tuple[str, ...]:
    from agent.dataset import HELD_OUT_PROMPTS

    return HELD_OUT_PROMPTS