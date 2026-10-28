"""A miniature test framework, so we can see what pytest does.

In a real project you would use pytest directly. This module exists so the
notebook can demonstrate the *shape* of a parametrised test - and so the
exercise has a home for the helper functions.
"""
from __future__ import annotations


class AssertionFailed(Exception):
    """Raised when a test assertion fails."""


def check(condition, message=""):
    """Assert a condition.

    Args:
        condition: The boolean condition.
        message: An optional failure message.

    Raises:
        AssertionFailed: When the condition is false.
    """
    if not condition:
        raise AssertionFailed(message or "assertion failed")


def check_equal(actual, expected, message=""):
    """Assert equality.

    Args:
        actual: The value under test.
        expected: The expected value.
        message: An optional failure message.

    Raises:
        AssertionFailed: When the values differ.
    """
    if actual != expected:
        raise AssertionFailed(
            message or f"expected {expected!r}, got {actual!r}"
        )


def run_cases(name, fn, cases):
    """Run a test function over a list of argument tuples.

    Args:
        name: The test's name.
        fn: The function under test.
        cases: A list of positional-argument tuples.

    Returns:
        The number of cases that passed.
    """
    passed = 0
    for case in cases:
        try:
            fn(*case)
            passed += 1
            print(f"    PASS  {name}{case}")
        except (AssertionFailed, AssertionError) as exc:
            print(f"    FAIL  {name}{case}: {exc}")
    return passed
