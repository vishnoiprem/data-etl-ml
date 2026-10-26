"""Tests for Module 05 — Hash Tables."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p31_valid_anagram import solve_valid_anagram  # type: ignore  # noqa: E402
from p32_group_anagrams import solve_group_anagrams  # type: ignore  # noqa: E402
from p33_longest_substring import solve_longest_substring  # type: ignore  # noqa: E402
from p34_subarray_sum_k import solve_subarray_sum_k  # type: ignore  # noqa: E402
from p35_lru_cache import solve_lru_cache  # type: ignore  # noqa: E402
from p36_min_window_substring import solve_min_window_substring  # type: ignore  # noqa: E402


class ValidAnagramTests(unittest.TestCase):
    def test_anagram(self):
        self.assertTrue(solve_valid_anagram("anagram", "nagaram"))

    def test_not_anagram(self):
        self.assertFalse(solve_valid_anagram("rat", "car"))

    def test_empty(self):
        self.assertTrue(solve_valid_anagram("", ""))


class GroupAnagramsTests(unittest.TestCase):
    def test_basic(self):
        out = solve_group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
        out_sorted = sorted([sorted(g) for g in out])
        self.assertEqual(out_sorted, [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]])

    def test_empty(self):
        self.assertEqual(solve_group_anagrams([]), [])

    def test_singletons(self):
        out = solve_group_anagrams(["a", "b", "c"])
        self.assertEqual(len(out), 3)


class LongestSubstringTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_longest_substring("abcabcbb"), 3)

    def test_all_unique(self):
        self.assertEqual(solve_longest_substring("abcdef"), 6)

    def test_all_same(self):
        self.assertEqual(solve_longest_substring("aaaa"), 1)

    def test_empty(self):
        self.assertEqual(solve_longest_substring(""), 0)


class SubarraySumKTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_subarray_sum_k([1, 1, 1], 2), 2)

    def test_negatives(self):
        self.assertEqual(solve_subarray_sum_k([1, -1, 1, -1, 1], 0), 6)

    def test_no_match(self):
        self.assertEqual(solve_subarray_sum_k([1, 2, 3], 10), 0)

    def test_empty(self):
        self.assertEqual(solve_subarray_sum_k([], 0), 0)


class LRUCacheTests(unittest.TestCase):
    def test_basic(self):
        ops = [
            ("LRUCache", 2),
            ("put", 1, 1),
            ("put", 2, 2),
            ("get", 1),
            ("put", 3, 3),
            ("get", 2),
        ]
        self.assertEqual(solve_lru_cache(ops), [1, -1])

    def test_update_keeps_recent(self):
        ops = [
            ("LRUCache", 2),
            ("put", 1, 1),
            ("put", 2, 2),
            ("get", 1),    # marks 1 as recent
            ("put", 3, 3),  # evicts 2
            ("get", 2),     # -1
            ("get", 3),     # 3
        ]
        self.assertEqual(solve_lru_cache(ops), [1, -1, 3])

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            solve_lru_cache([("LRUCache", 0)])  # constructor raises


class MinWindowSubstringTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_min_window_substring("ADOBECODEBANC", "ABC"), "BANC")

    def test_no_match(self):
        self.assertEqual(solve_min_window_substring("a", "b"), "")

    def test_exact(self):
        self.assertEqual(solve_min_window_substring("a", "a"), "a")

    def test_empty_t(self):
        self.assertEqual(solve_min_window_substring("abc", ""), "")


if __name__ == "__main__":
    unittest.main()
