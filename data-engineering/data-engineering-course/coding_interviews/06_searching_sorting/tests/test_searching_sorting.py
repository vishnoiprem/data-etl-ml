"""Tests for Module 06 — Searching & Sorting."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p37_binary_search import solve_binary_search  # type: ignore  # noqa: E402
from p38_search_insert import solve_search_insert  # type: ignore  # noqa: E402
from p39_first_and_last import solve_first_and_last  # type: ignore  # noqa: E402
from p40_search_2d_matrix import solve_search_2d  # type: ignore  # noqa: E402
from p41_find_peak import solve_find_peak  # type: ignore  # noqa: E402
from p42_merge_sorted import solve_merge_sorted  # type: ignore  # noqa: E402
from p43_sort_colors import solve_sort_colors  # type: ignore  # noqa: E402
from p44_top_k_frequent import solve_top_k_frequent  # type: ignore  # noqa: E402


class BinarySearchTests(unittest.TestCase):
    def test_found(self):
        self.assertEqual(solve_binary_search([-1, 0, 3, 5, 9, 12], 9), 4)

    def test_not_found(self):
        self.assertEqual(solve_binary_search([-1, 0, 3, 5, 9, 12], 2), -1)

    def test_empty(self):
        self.assertEqual(solve_binary_search([], 1), -1)


class SearchInsertTests(unittest.TestCase):
    def test_present(self):
        self.assertEqual(solve_search_insert([1, 3, 5, 6], 5), 2)

    def test_insert_at_end(self):
        self.assertEqual(solve_search_insert([1, 3, 5, 6], 7), 4)

    def test_insert_at_start(self):
        self.assertEqual(solve_search_insert([1, 3, 5, 6], 0), 0)


class FirstAndLastTests(unittest.TestCase):
    def test_found(self):
        self.assertEqual(solve_first_and_last([5, 7, 7, 8, 8, 10], 8), [3, 4])

    def test_not_found(self):
        self.assertEqual(solve_first_and_last([5, 7, 7, 8, 8, 10], 6), [-1, -1])

    def test_single(self):
        self.assertEqual(solve_first_and_last([1], 1), [0, 0])


class Search2DTests(unittest.TestCase):
    def test_found(self):
        m = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
        self.assertTrue(solve_search_2d(m, 3))

    def test_not_found(self):
        m = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
        self.assertFalse(solve_search_2d(m, 13))

    def test_empty(self):
        self.assertFalse(solve_search_2d([], 1))


class FindPeakTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_find_peak([1, 2, 3, 1]), 2)

    def test_descending(self):
        self.assertEqual(solve_find_peak([4, 3, 2, 1]), 0)

    def test_ascending(self):
        self.assertEqual(solve_find_peak([1, 2, 3, 4]), 3)


class MergeSortedTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_merge_sorted([1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3),
                         [1, 2, 2, 3, 5, 6])

    def test_no_overlap(self):
        self.assertEqual(solve_merge_sorted([1, 2, 3, 0, 0, 0], 3, [4, 5, 6], 3),
                         [1, 2, 3, 4, 5, 6])

    def test_empty_nums2(self):
        self.assertEqual(solve_merge_sorted([1, 2, 3], 3, [], 0), [1, 2, 3])


class SortColorsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_sort_colors([2, 0, 2, 1, 1, 0]), [0, 0, 1, 1, 2, 2])

    def test_already_sorted(self):
        self.assertEqual(solve_sort_colors([0, 1, 2]), [0, 1, 2])

    def test_all_same(self):
        self.assertEqual(solve_sort_colors([1, 1, 1]), [1, 1, 1])


class TopKFrequentTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(sorted(solve_top_k_frequent([1, 1, 1, 2, 2, 3], 2)), [1, 2])

    def test_single(self):
        self.assertEqual(solve_top_k_frequent([1], 1), [1])

    def test_all_unique(self):
        self.assertEqual(sorted(solve_top_k_frequent([1, 2, 3, 4], 2)), [1, 2])


if __name__ == "__main__":
    unittest.main()
