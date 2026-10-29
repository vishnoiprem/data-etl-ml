"""
conftest.py — pytest configuration for the Datastream course.

Makes the `project/` directory importable from every test, so the tests
can `import cdc` without installing the project as a package.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
