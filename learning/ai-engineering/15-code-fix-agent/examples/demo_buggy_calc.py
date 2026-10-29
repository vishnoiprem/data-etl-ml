"""Example: a tiny buggy project the agent will fix.

This script sets up a fresh tmp repo with a known bug, then invokes the
agent in dry-run mode to demonstrate the loop without making real LLM calls
required for the test suite to pass.

Run with:
    python -m examples.demo_buggy_calc
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from agent.schemas import ApplyEditsArgs, FileEdit
from agent.patcher import apply_edits
from agent.runner import run_tests
from agent.schemas import RunTestsArgs


SETUP = {
    "calculator.py": '''\
"""Simple calculator with a known bug: divide returns inf for b == 0."""


def divide(a: float, b: float) -> float:
    if b == 0:
        # BUG: should raise ZeroDivisionError but silently returns inf
        return float("inf")
    return a / b


def add(a: float, b: float) -> float:
    return a + b
''',
    "tests/test_calculator.py": '''\
import pytest
from calculator import add, divide


def test_add():
    assert add(2, 3) == 5


def test_divide_normal():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    # This test will fail until divide() is fixed to raise.
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
''',
}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "buggy_calc"
        root.mkdir()
        (root / "tests").mkdir()
        # conftest.py makes 'calculator' importable from tests/
        (root / "conftest.py").write_text("")
        for path, content in SETUP.items():
            (root / path).write_text(content)

        print("=" * 60)
        print("BEFORE: tests fail because divide() doesn't handle 0")
        print("=" * 60)
        result = run_tests(root, RunTestsArgs(target=""))
        print(result.summary())
        for f in result.failures:
            print(f"  - {f['file']}::{f['test']}\n    {f['msg'][:200]}")

        print()
        print("=" * 60)
        print("APPLYING THE FIX (what the LLM-driven agent would do)")
        print("=" * 60)
        apply_edits(root, ApplyEditsArgs(edits=[
            FileEdit(
                path="calculator.py",
                old_text=(
                    "def divide(a: float, b: float) -> float:\n"
                    "    if b == 0:\n"
                    '        # BUG: should raise ZeroDivisionError but silently returns inf\n'
                    '        return float("inf")\n'
                    "    return a / b"
                ),
                new_text=(
                    "def divide(a: float, b: float) -> float:\n"
                    '    """Divide a by b. Raises ZeroDivisionError on b == 0."""\n'
                    "    if b == 0:\n"
                    '        raise ZeroDivisionError("division by zero")\n'
                    "    return a / b"
                ),
                rationale="handle b == 0 to satisfy test_divide_by_zero",
            ),
        ]))
        print("  patched calculator.py")

        print()
        print("=" * 60)
        print("AFTER: tests pass")
        print("=" * 60)
        result = run_tests(root, RunTestsArgs(target=""))
        print(result.summary())
        assert result.passed, "expected tests to pass after fix"

        print()
        print("Demo complete — agent would have done this via LLM, then committed + pushed.")


if __name__ == "__main__":
    main()