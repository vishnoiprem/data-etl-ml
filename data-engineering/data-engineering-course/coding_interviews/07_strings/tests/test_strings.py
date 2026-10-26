"""Tests for Module 07 — Strings."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p45_reverse_string import solve_reverse_string  # type: ignore  # noqa: E402
from p46_valid_palindrome import solve_valid_palindrome  # type: ignore  # noqa: E402
from p47_longest_common_prefix import solve_longest_common_prefix  # type: ignore  # noqa: E402
from p48_longest_palindromic import solve_longest_palindromic  # type: ignore  # noqa: E402
from p49_atoi import solve_atoi  # type: ignore  # noqa: E402
from p50_at_most_k_distinct import solve_at_most_k_distinct  # type: ignore  # noqa: E402
from p51_min_remove_parens import solve_min_remove_parens  # type: ignore  # noqa: E402
from p52_char_replacement import solve_char_replacement  # type: ignore  # noqa: E402
from p53_edit_distance import solve_edit_distance  # type: ignore  # noqa: E402


class ReverseStringTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_reverse_string(list("hello")), ['o', 'l', 'l', 'e', 'h'])

    def test_empty(self):
        self.assertEqual(solve_reverse_string([]), [])

    def test_single(self):
        self.assertEqual(solve_reverse_string(list("a")), ['a'])


class ValidPalindromeTests(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(solve_valid_palindrome("A man, a plan, a canal: Panama"))

    def test_not_palindrome(self):
        self.assertFalse(solve_valid_palindrome("race a car"))

    def test_empty(self):
        self.assertTrue(solve_valid_palindrome(""))


class LongestCommonPrefixTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_longest_common_prefix(["flower", "flow", "flight"]), "fl")

    def test_no_common(self):
        self.assertEqual(solve_longest_common_prefix(["dog", "racecar", "car"]), "")

    def test_single(self):
        self.assertEqual(solve_longest_common_prefix(["solo"]), "solo")

    def test_empty(self):
        self.assertEqual(solve_longest_common_prefix([]), "")


class LongestPalindromicTests(unittest.TestCase):
    def test_basic(self):
        self.assertIn(solve_longest_palindromic("babad"), ("bab", "aba"))

    def test_even(self):
        self.assertEqual(solve_longest_palindromic("cbbd"), "bb")

    def test_single(self):
        self.assertEqual(solve_longest_palindromic("a"), "a")


class AtoiTests(unittest.TestCase):
    def test_negative(self):
        self.assertEqual(solve_atoi("   -42"), -42)

    def test_positive(self):
        self.assertEqual(solve_atoi("4193 with words"), 4193)

    def test_overflow_positive(self):
        self.assertEqual(solve_atoi("99999999999999"), 2**31 - 1)

    def test_overflow_negative(self):
        self.assertEqual(solve_atoi("-99999999999999"), -(2**31))


class AtMostKDistinctTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_at_most_k_distinct("eceba", 2), 3)

    def test_k_zero(self):
        self.assertEqual(solve_at_most_k_distinct("abc", 0), 0)

    def test_all_unique(self):
        self.assertEqual(solve_at_most_k_distinct("abc", 3), 3)


class MinRemoveParensTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_min_remove_parens("a)b(c)d"), "ab(c)d")

    def test_balanced(self):
        self.assertEqual(solve_min_remove_parens("(a(b)c)"), "(a(b)c)")

    def test_unmatched_open(self):
        self.assertEqual(solve_min_remove_parens("((("), "")


class CharReplacementTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_char_replacement("ABAB", 2), 4)

    def test_k_zero(self):
        self.assertEqual(solve_char_replacement("AABABBA", 0), 2)

    def test_all_same(self):
        self.assertEqual(solve_char_replacement("AAAA", 0), 4)


class EditDistanceTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_edit_distance("horse", "ros"), 3)

    def test_identical(self):
        self.assertEqual(solve_edit_distance("abc", "abc"), 0)

    def test_empty(self):
        self.assertEqual(solve_edit_distance("", "abc"), 3)

    def test_substitution(self):
        self.assertEqual(solve_edit_distance("abc", "abd"), 1)


if __name__ == "__main__":
    unittest.main()
