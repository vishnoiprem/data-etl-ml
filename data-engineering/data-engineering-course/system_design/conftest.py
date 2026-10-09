"""Pytest configuration: makes `common` and per-module `code` importable.

Pytest adds the project root to sys.path automatically, so we just need
to ensure the system_design directory is discoverable.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Clear persisted KeyValueStore state from previous test runs so each
# session starts clean.  Each module's service uses a hardcoded
# ``var/<name>.json`` path, so without this the tests inherit stale
# data.
_VAR_DIR = os.path.join(HERE, "var")
if os.path.isdir(_VAR_DIR):
    shutil.rmtree(_VAR_DIR, ignore_errors=True)
