"""Tests for the Module 04 — Arrays problems.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p19_two_sum import solve_two_sum  # type: ignore  # noqa: E402
from p20_best_time import solve_best_time  # type: ignore  # noqa: E402
from p21_contains_duplicate import solve_contains_duplicate  # type: ignore  # noqa: E402
from p22_product_except_self import solve_product_except_self  # type: ignore  # noqa: E402
from p23_max_subarray import solve_max_subarray  # type: ignore  # noqa: E402
from p24_max_product import solve_max_product  # type: ignore  # noqa: E402
from p25_min_rotated import solve_min_rotated  # type: ignore  # noqa: E402
from p26_search_rotated import solve_search_rotated  # type: ignore  # noqa: E402
from p27_three_sum import solve_three_sum  # type: ignore  # noqa: E402
from p28_container_water import solve_container_water  # type: ignore  # noqa: E402
from p29_trapping_rain import solve_trapping_rain  # type: ignore  # noqa: E402
from p30_first_missing_positive import solve_first_missing_positive  # type: ignore  # noqa: E402


class TwoSumTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_two_sum([2, 7, 11, 15], 9), (0, 1))

    def test_negative_numbers(self):
        self.assertEqual(solve_two_sum([-3, 4, 3, 90], 0), (0, 2))

    def test_no_solution(self):
        self.assertEqual(solve_two_sum([1, 2, 3], 7), (-1, -1))

    def test_duplicates(self):
        self.assertEqual(solve_two_sum([3, 3], 6), (0, 1))


class BestTimeTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_best_time([7, 1, 5, 3, 6, 4]), 5)

    def test_descending(self):
        self.assertEqual(solve_best_time([7, 6, 4, 3, 1]), 0)

    def test_empty(self):
        self.assertEqual(solve_best_time([]), 0)

    def test_single(self):
        self.assertEqual(solve_best_time([5]), 0)


class ContainsDuplicateTests(unittest.TestCase):
    def test_dup(self):
        self.assertTrue(solve_contains_duplicate([1, 2, 3, 1]))

    def test_no_dup(self):
        self.assertFalse(solve_contains_duplicate([1, 2, 3, 4]))

    def test_empty(self):
        self.assertFalse(solve_contains_duplicate([]))


class ProductExceptSelfTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_product_except_self([1, 2, 3, 4]), [24, 12, 8, 6])

    def test_with_zero(self):
        self.assertEqual(solve_product_except_self([0, 1, 2, 3]), [6, 0, 0, 0])

    def test_two_elements(self):
        self.assertEqual(solve_product_except_self([4, 5]), [5, 4])


class MaxSubarrayTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]), 6)

    def test_all_negative(self):
        self.assertEqual(solve_max_subarray([-3, -1, -2]), -1)

    def test_single(self):
        self.assertEqual(solve_max_subarray([5]), 5)


class MaxProductTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_max_product([2, 3, -2, 4]), 6)

    def test_negatives(self):
        self.assertEqual(solve_max_product([-2, 0, -1]), 0)

    def test_two_negatives(self):
        self.assertEqual(solve_max_product([-2, 3, -4]), 24)


class MinRotatedTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_min_rotated([3, 4, 5, 1, 2]), 1)

    def test_not_rotated(self):
        self.assertEqual(solve_min_rotated([1, 2, 3, 4, 5]), 1)

    def test_single(self):
        self.assertEqual(solve_min_rotated([7]), 7)


class SearchRotatedTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_search_rotated([4, 5, 6, 7, 0, 1, 2], 0), 4)

    def test_not_found(self):
        self.assertEqual(solve_search_rotated([4, 5, 6, 7, 0, 1, 2], 3), -1)

    def test_not_rotated(self):
        self.assertEqual(solve_search_rotated([1, 2, 3, 4, 5], 4), 3)


class ThreeSumTests(unittest.TestCase):
    def test_basic(self):
        out = solve_three_sum([-1, 0, 1, 2, -1, -4])
        self.assertEqual(sorted(out), [[-1, -1, 2], [-1, 0, 1]])

    def test_no_solution(self):
        self.assertEqual(solve_three_sum([0, 1, 1]), [])

    def test_all_zeros(self):
        self.assertEqual(solve_three_sum([0, 0, 0]), [[0, 0, 0]])

    def test_empty(self):
        self.assertEqual(solve_three_sum([]), [])


class ContainerWaterTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_container_water([1, 8, 6, 2, 5, 4, 8, 3, 7]), 49)

    def test_two(self):
        self.assertEqual(solve_container_water([1, 1]), 1)

    def test_descending(self):
        self.assertEqual(solve_container_water([4, 3, 2, 1]), 4)


class TrappingRainTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_trapping_rain([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]), 6)

    def test_empty(self):
        self.assertEqual(solve_trapping_rain([]), 0)

    def test_flat(self):
        self.assertEqual(solve_trapping_rain([1, 1, 1]), 0)


class FirstMissingPositiveTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_first_missing_positive([1, 2, 0]), 3)

    def test_all_present(self):
        self.assertEqual(solve_first_missing_positive([1, 2, 3]), 4)

    def test_negatives(self):
        self.assertEqual(solve_first_missing_positive([7, 8, 9, 11, 12]), 1)

    def test_empty(self):
        self.assertEqual(solve_first_missing_positive([]), 1)


if __name__ == "__main__":
    unittest.main()
