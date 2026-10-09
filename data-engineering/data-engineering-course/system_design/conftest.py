"""Pytest configuration: makes `common` and per-module `code` importable.

Pytest adds the project root to sys.path automatically, so we just need
to ensure the system_design directory is discoverable.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
