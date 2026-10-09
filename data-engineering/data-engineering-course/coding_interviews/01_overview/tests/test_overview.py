"""Tests for the Module 01 overview code problems.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make ``code/`` importable as a flat namespace (per the data_modeling track pattern).
HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from t03_move_zeros import solve_move_zeros  # type: ignore  # noqa: E402
from t04_remove_duplicates import solve_remove_duplicates  # type: ignore  # noqa: E402
from t05_subarray_sum import solve_subarray_sum  # type: ignore  # noqa: E402


class MoveZerosTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_move_zeros([0, 1, 0, 3, 12]), [1, 3, 12, 0, 0])

    def test_no_zeros(self):
        self.assertEqual(solve_move_zeros([1, 2, 3]), [1, 2, 3])

    def test_all_zeros(self):
        self.assertEqual(solve_move_zeros([0, 0, 0]), [0, 0, 0])

    def test_empty(self):
        self.assertEqual(solve_move_zeros([]), [])

    def test_negatives_and_zeros(self):
        self.assertEqual(solve_move_zeros([-1, 0, 2, 0, 3]), [-1, 2, 3, 0, 0])


class RemoveDuplicatesTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_remove_duplicates("programming"), "progamin")

    def test_no_dupes(self):
        self.assertEqual(solve_remove_duplicates("abc"), "abc")

    def test_all_same(self):
        self.assertEqual(solve_remove_duplicates("aaaa"), "a")

    def test_empty(self):
        self.assertEqual(solve_remove_duplicates(""), "")

    def test_case_sensitive(self):
        self.assertEqual(solve_remove_duplicates("AaBbAa"), "AaBb")


class SubarraySumTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]), 6)

    def test_all_negative(self):
        self.assertEqual(solve_subarray_sum([-3, -1, -2]), -1)

    def test_single(self):
        self.assertEqual(solve_subarray_sum([5]), 5)

    def test_all_positive(self):
        self.assertEqual(solve_subarray_sum([1, 2, 3, 4]), 10)

    def test_empty(self):
        self.assertEqual(solve_subarray_sum([]), 0)


if __name__ == "__main__":
    unittest.main()
