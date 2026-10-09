"""Tests for Module 10 — Stacks & Queues."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p72_valid_parentheses import solve_valid_parentheses  # type: ignore  # noqa: E402
from p73_min_stack import solve_min_stack  # type: ignore  # noqa: E402
from p74_eval_rpn import solve_eval_rpn  # type: ignore  # noqa: E402
from p75_daily_temperatures import solve_daily_temperatures  # type: ignore  # noqa: E402
from p76_largest_rectangle import solve_largest_rectangle  # type: ignore  # noqa: E402
from p77_queue_using_stacks import solve_queue_ops  # type: ignore  # noqa: E402
from p78_sliding_window_max import solve_sliding_window_max  # type: ignore  # noqa: E402
from p79_basic_calculator import solve_basic_calculator  # type: ignore  # noqa: E402


class ValidParensTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(solve_valid_parentheses("()[]{}"))

    def test_invalid(self):
        self.assertFalse(solve_valid_parentheses("([)]"))

    def test_empty(self):
        self.assertTrue(solve_valid_parentheses(""))


class MinStackTests(unittest.TestCase):
    def test_basic(self):
        ops = [
            ("MinStack",),
            ("push", -2),
            ("push", 0),
            ("push", -3),
            ("getMin",),
            ("pop",),
            ("top",),
            ("getMin",),
        ]
        self.assertEqual(solve_min_stack(ops), [-3, 0, -2])

    def test_single(self):
        ops = [("MinStack",), ("push", 5), ("top",), ("getMin",)]
        self.assertEqual(solve_min_stack(ops), [5, 5])


class EvalRPNTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_eval_rpn(["2", "1", "+", "3", "*"]), 9)

    def test_subtraction(self):
        self.assertEqual(solve_eval_rpn(["4", "13", "5", "/", "+"]), 6)

    def test_division(self):
        # Truncation toward zero (Python's default int division differs for negatives,
        # but for positive inputs it's identical).
        self.assertEqual(solve_eval_rpn(["10", "6", "/"]), 1)


class DailyTempsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]),
            [1, 1, 4, 2, 1, 1, 0, 0],
        )

    def test_descending(self):
        self.assertEqual(solve_daily_temperatures([5, 4, 3, 2, 1]), [0, 0, 0, 0, 0])


class LargestRectangleTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_largest_rectangle([2, 1, 5, 6, 2, 3]), 10)

    def test_empty(self):
        self.assertEqual(solve_largest_rectangle([]), 0)

    def test_single(self):
        self.assertEqual(solve_largest_rectangle([5]), 5)


class QueueFromStacksTests(unittest.TestCase):
    def test_basic(self):
        ops = [
            ("Queue",),
            ("push", 1),
            ("push", 2),
            ("peek",),
            ("pop",),
            ("empty",),
        ]
        self.assertEqual(solve_queue_ops(ops), [1, 1, False])

    def test_fifo(self):
        ops = [
            ("Queue",),
            ("push", 1),
            ("push", 2),
            ("push", 3),
            ("pop",),
            ("pop",),
            ("pop",),
        ]
        self.assertEqual(solve_queue_ops(ops), [1, 2, 3])


class SlidingWindowMaxTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3),
            [3, 3, 5, 5, 6, 7],
        )

    def test_k_one(self):
        self.assertEqual(solve_sliding_window_max([1, 2, 3], 1), [1, 2, 3])

    def test_empty(self):
        self.assertEqual(solve_sliding_window_max([], 3), [])


class BasicCalculatorTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(solve_basic_calculator("1 + 1"), 2)

    def test_parens(self):
        self.assertEqual(solve_basic_calculator("(1+(4+5+2)-3)+(6+8)"), 23)

    def test_unary_minus_via_zero(self):
        self.assertEqual(solve_basic_calculator("(5-(1+(4)))"), 0)


if __name__ == "__main__":
    unittest.main()
