"""Tests for Module 11 — Linked Lists."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from _ll_helpers import from_list, to_list, ListNode  # type: ignore  # noqa: E402
from p80_reverse_list import solve_reverse_list  # type: ignore  # noqa: E402
from p81_merge_two_sorted import solve_merge_two_sorted  # type: ignore  # noqa: E402
from p82_cycle import solve_has_cycle  # type: ignore  # noqa: E402
from p83_remove_nth import solve_remove_nth  # type: ignore  # noqa: E402
from p84_add_two_numbers import solve_add_two_numbers  # type: ignore  # noqa: E402
from p85_merge_k_sorted import solve_merge_k_sorted  # type: ignore  # noqa: E402


class ReverseListTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(to_list(solve_reverse_list(from_list([1, 2, 3, 4]))),
                         [4, 3, 2, 1])

    def test_empty(self):
        self.assertIsNone(solve_reverse_list(None))

    def test_single(self):
        self.assertEqual(to_list(solve_reverse_list(from_list([1]))), [1])


class MergeTwoSortedTests(unittest.TestCase):
    def test_basic(self):
        a, b = from_list([1, 2, 4]), from_list([1, 3, 4])
        self.assertEqual(to_list(solve_merge_two_sorted(a, b)),
                         [1, 1, 2, 3, 4, 4])

    def test_one_empty(self):
        self.assertEqual(to_list(solve_merge_two_sorted(from_list([1, 2]), None)),
                         [1, 2])


class CycleTests(unittest.TestCase):
    def test_with_cycle(self):
        a = ListNode(3); b = ListNode(2); c = ListNode(0); d = ListNode(-4)
        a.next, b.next, c.next, d.next = b, c, d, b
        self.assertTrue(solve_has_cycle(a))

    def test_no_cycle(self):
        self.assertFalse(solve_has_cycle(from_list([1, 2, 3])))

    def test_empty(self):
        self.assertFalse(solve_has_cycle(None))


class RemoveNthTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(to_list(solve_remove_nth(from_list([1, 2, 3, 4, 5]), 2)),
                         [1, 2, 3, 5])

    def test_remove_head(self):
        self.assertEqual(to_list(solve_remove_nth(from_list([1, 2]), 2)), [2])

    def test_remove_last(self):
        self.assertEqual(to_list(solve_remove_nth(from_list([1, 2, 3]), 1)),
                         [1, 2])


class AddTwoNumbersTests(unittest.TestCase):
    def test_basic(self):
        a, b = from_list([2, 4, 3]), from_list([5, 6, 4])
        self.assertEqual(to_list(solve_add_two_numbers(a, b)), [7, 0, 8])

    def test_carry(self):
        a, b = from_list([9, 9, 9]), from_list([1])
        self.assertEqual(to_list(solve_add_two_numbers(a, b)), [0, 0, 0, 1])

    def test_one_empty(self):
        self.assertEqual(to_list(solve_add_two_numbers(from_list([1, 2]), None)),
                         [1, 2])


class MergeKSortedTests(unittest.TestCase):
    def test_basic(self):
        lists = [from_list([1, 4, 5]), from_list([1, 3, 4]), from_list([2, 6])]
        self.assertEqual(to_list(solve_merge_k_sorted(lists)),
                         [1, 1, 2, 3, 4, 4, 5, 6])

    def test_empty(self):
        self.assertIsNone(solve_merge_k_sorted([]))

    def test_with_nones(self):
        self.assertEqual(
            to_list(solve_merge_k_sorted([None, from_list([1, 2])])), [1, 2]
        )


if __name__ == "__main__":
    unittest.main()
