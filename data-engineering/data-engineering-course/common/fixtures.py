"""Path helpers to the shared ``sample_data/`` directory.

Tracks import this so they don't all have to know the relative
location of the sample CSVs.
"""

from __future__ import annotations

from pathlib import Path

# common/ is one level below the course root, and sample_data/ sits
# at the course root. So the parent of ``common`` is the course root.
_HERE = Path(__file__).resolve().parent
COURSE_ROOT = _HERE.parent
SAMPLE_DATA_DIR: Path = COURSE_ROOT / "sample_data"


def fixture_path(name: str) -> Path:
    """Return the absolute path to a file under ``sample_data/``."""
    if not name:
        raise ValueError("fixture_path requires a non-empty file name")
    return SAMPLE_DATA_DIR / name


def list_fixtures(suffix: Optional[str] = None) -> list[str]:
    """Return the names of all files in ``SAMPLE_DATA_DIR``.

    Pass ``suffix=".csv"`` (etc.) to filter.
    """
    if not SAMPLE_DATA_DIR.exists():
        return []
    out = []
    for p in sorted(SAMPLE_DATA_DIR.iterdir()):
        if not p.is_file():
            continue
        if suffix and not p.name.endswith(suffix):
            continue
        out.append(p.name)
    return out
