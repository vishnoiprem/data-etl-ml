"""Pytest config for apex-rag-omni.

`asyncio_mode = "auto"` lets us use `async def` test functions and
async fixtures without having to decorate every one with
`@pytest.mark.asyncio`. Required for tests/test_api.py.
"""
import sys
from pathlib import Path

# Make the project importable when pytest is invoked from any cwd.
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402


def pytest_collection_modifyitems(config, items):
    """Auto-mark async tests so pytest-asyncio picks them up."""
    for item in items:
        if "asyncio" in item.keywords:
            continue
        # If the test function is a coroutine, mark it.
        if getattr(item, "obj", None) is not None and hasattr(item.obj, "__code__"):
            if item.obj.__code__.co_flags & 0x100:  # CO_COROUTINE
                item.add_marker(pytest.mark.asyncio)
