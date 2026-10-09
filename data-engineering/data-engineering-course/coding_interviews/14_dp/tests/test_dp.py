"""Tests for Module 14 — Dynamic Programming."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p103_climbing_stairs import solve_climbing_stairs  # type: ignore  # noqa: E402
from p104_coin_change import solve_coin_change  # type: ignore  # noqa: E402
from p105_lis import solve_lis  # type: ignore  # noqa: E402
from p106_word_break import solve_word_break  # type: ignore  # noqa: E402
from p107_house_robber import solve_house_robber  # type: ignore  # noqa: E402
from p108_decode_ways import solve_decode_ways  # type: ignore  # noqa: E402
from p109_unique_paths import solve_unique_paths  # type: ignore  # noqa: E402
from p110_lcs import solve_lcs  # type: ignore  # noqa: E402
from p111_edit_distance import solve_edit_distance_dp  # type: ignore  # noqa: E402
from p112_burst_balloons import solve_burst_balloons  # type: ignore  # noqa: E402


class ClimbingStairsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_climbing_stairs(3), 3)

    def test_one(self):
        self.assertEqual(solve_climbing_stairs(1), 1)

    def test_zero(self):
        self.assertEqual(solve_climbing_stairs(0), 1)


class CoinChangeTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_coin_change([1, 5, 11, 25], 30), 2)

    def test_impossible(self):
        self.assertEqual(solve_coin_change([2], 3), -1)

    def test_zero_amount(self):
        self.assertEqual(solve_coin_change([1, 2, 5], 0), 0)


class LISTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_lis([10, 9, 2, 5, 3, 7, 101, 18]), 4)

    def test_descending(self):
        self.assertEqual(solve_lis([5, 4, 3, 2, 1]), 1)

    def test_empty(self):
        self.assertEqual(solve_lis([]), 0)


class WordBreakTests(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(solve_word_break("leetcode", ["leet", "code"]))

    def test_no_break(self):
        self.assertFalse(solve_word_break("catsandog", ["cat", "sand", "dog"]))


class HouseRobberTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_house_robber([1, 2, 3, 1]), 4)

    def test_two(self):
        self.assertEqual(solve_house_robber([2, 7, 9, 3, 1]), 12)

    def test_empty(self):
        self.assertEqual(solve_house_robber([]), 0)


class DecodeWaysTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_decode_ways("226"), 3)

    def test_zero(self):
        self.assertEqual(solve_decode_ways("0"), 0)

    def test_ten(self):
        self.assertEqual(solve_decode_ways("10"), 1)


class UniquePathsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_unique_paths(3, 7), 28)

    def test_one_by_one(self):
        self.assertEqual(solve_unique_paths(1, 1), 1)

    def test_three_three(self):
        self.assertEqual(solve_unique_paths(3, 3), 6)


class LCSTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_lcs("abcde", "ace"), 3)

    def test_no_common(self):
        self.assertEqual(solve_lcs("abc", "def"), 0)

    def test_identical(self):
        self.assertEqual(solve_lcs("abc", "abc"), 3)


class EditDistanceTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_edit_distance_dp("horse", "ros"), 3)

    def test_identical(self):
        self.assertEqual(solve_edit_distance_dp("abc", "abc"), 0)


class BurstBalloonsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_burst_balloons([3, 1, 5, 8]), 167)

    def test_empty(self):
        self.assertEqual(solve_burst_balloons([]), 0)

    def test_single(self):
        self.assertEqual(solve_burst_balloons([5]), 5)


if __name__ == "__main__":
    unittest.main()
