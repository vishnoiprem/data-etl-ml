"""Tests for Module 15 — Mock Interviews."""

from __future__ import annotations

import sys
import unittest
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from m113_meta_screen import solve_fizzbuzz, solve_valid_parens_wildcard  # type: ignore  # noqa: E402
from m114_google_phone import solve_longest_two_distinct  # type: ignore  # noqa: E402
from m115_meta_onsite import RateLimiter  # type: ignore  # noqa: E402
from m116_google_onsite import WeightedRandom  # type: ignore  # noqa: E402
from m117_senior_mixed import LFUCache  # type: ignore  # noqa: E402
from m118_faang_final import ThreadSafeKV  # type: ignore  # noqa: E402
from m119_meta_screen_v2 import (  # type: ignore  # noqa: E402
    top_5_pages_by_upward_trend,
    second_highest_per_department,
    tumbling_window_counts,
)


class FizzBuzzTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_fizzbuzz(15)[-3:], ["13", "14", "FizzBuzz"])

    def test_three(self):
        self.assertEqual(solve_fizzbuzz(3), ["1", "2", "Fizz"])

    def test_zero(self):
        self.assertEqual(solve_fizzbuzz(0), [])


class ValidParensWildcardTests(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(solve_valid_parens_wildcard("()"))
        self.assertTrue(solve_valid_parens_wildcard("(*)"))
        self.assertTrue(solve_valid_parens_wildcard("(*))"))

    def test_invalid(self):
        self.assertFalse(solve_valid_parens_wildcard(")("))
        self.assertFalse(solve_valid_parens_wildcard("(()"))

    def test_empty(self):
        self.assertTrue(solve_valid_parens_wildcard(""))


class LongestTwoDistinctTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_longest_two_distinct("eceba"), 3)

    def test_repeating(self):
        self.assertEqual(solve_longest_two_distinct("ccaabbb"), 5)

    def test_empty(self):
        self.assertEqual(solve_longest_two_distinct(""), 0)


class RateLimiterTests(unittest.TestCase):
    def test_within_limit(self):
        rl = RateLimiter(limit=3, window_seconds=10)
        self.assertTrue(rl.hit("u1", 1))
        self.assertTrue(rl.hit("u1", 2))
        self.assertTrue(rl.hit("u1", 3))
        self.assertFalse(rl.hit("u1", 4))   # 4th in window

    def test_window_slide(self):
        rl = RateLimiter(limit=2, window_seconds=5)
        self.assertTrue(rl.hit("u1", 1))
        self.assertTrue(rl.hit("u1", 2))
        self.assertFalse(rl.hit("u1", 3))
        self.assertTrue(rl.hit("u1", 6))   # 1, 2 are out of window

    def test_per_user(self):
        rl = RateLimiter(limit=1, window_seconds=10)
        self.assertTrue(rl.hit("a", 1))
        self.assertTrue(rl.hit("b", 1))


class WeightedRandomTests(unittest.TestCase):
    def test_invalid_weights(self):
        with self.assertRaises(ValueError):
            WeightedRandom([-1, 2])
        with self.assertRaises(ValueError):
            WeightedRandom([0, 0])

    def test_distribution(self):
        picker = WeightedRandom([1, 9])
        counts = [0, 0]
        for _ in range(5000):
            counts[picker.pick()] += 1
        # The 9-weight bucket should be ~9x the 1-weight bucket.
        ratio = counts[1] / max(counts[0], 1)
        self.assertGreater(ratio, 5)
        self.assertLess(ratio, 15)


class LFUCacheTests(unittest.TestCase):
    def test_basic(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)
        cache.put(3, 3)  # evicts key 2
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)

    def test_lru_tiebreak(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        # Tie on freq; key 1 is older, so it should be evicted.
        cache.put(3, 3)
        self.assertEqual(cache.get(1), -1)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LFUCache(0)


class ThreadSafeKVTests(unittest.TestCase):
    def test_set_get(self):
        store = ThreadSafeKV()
        store.set("a", 1, ttl_seconds=10)
        self.assertEqual(store.get("a"), 1)

    def test_ttl_expiry(self):
        store = ThreadSafeKV()
        store.set("a", 1, ttl_seconds=0.05)
        self.assertEqual(store.get("a"), 1)
        time.sleep(0.1)
        self.assertIsNone(store.get("a"))

    def test_delete(self):
        store = ThreadSafeKV()
        store.set("a", 1, ttl_seconds=10)
        store.delete("a")
        self.assertIsNone(store.get("a"))


class M119MetaScreenV2Tests(unittest.TestCase):
    """The 2026 Meta Python screen is pandas/dict, not DSA.
    m119 ships 3 of the 5 problems; the other 2 live in
    sql_interviews/11_meta_screen/code/meta_screen_python.py.
    """

    def test_upward_trend_returns_pages_with_positive_slope(self):
        import pandas as pd
        df = pd.DataFrame({
            "page_id": [1]*7 + [2]*7 + [3]*7,
            "day": list(range(7)) * 3,
            "impressions": [10, 20, 30, 40, 50, 60, 70,    # up
                            70, 60, 50, 40, 30, 20, 10,    # down
                            10, 10, 10, 10, 10, 10, 10],   # flat
        })
        out = top_5_pages_by_upward_trend(df)
        # Only page 1 has a positive slope.
        self.assertEqual(out, [1])

    def test_upward_trend_excludes_pages_with_fewer_than_5_days(self):
        import pandas as pd
        df = pd.DataFrame({
            "page_id": [1]*6 + [2]*3,        # page 2 only has 3 days
            "day": [0, 1, 2, 3, 4, 5, 0, 1, 2],
            "impressions": [10, 20, 30, 40, 50, 60,  # page 1, up
                            10, 20, 30],            # page 2, up but ignored
        })
        out = top_5_pages_by_upward_trend(df)
        # page 2 excluded (< 5 days) -> only page 1
        self.assertEqual(out, [1])

    def test_second_highest_distinct_salary(self):
        rows = [("a", "eng", 100), ("b", "eng", 90), ("c", "eng", 80),
                ("d", "sales", 200), ("e", "sales", 100), ("f", "sales", 50)]
        out = second_highest_per_department(rows)
        # eng: 100, 90, 80 -> second-highest distinct = 90
        # sales: 200, 100, 50 -> second-highest distinct = 100
        self.assertEqual(out, {"eng": 90, "sales": 100})

    def test_second_highest_returns_None_when_only_one_distinct(self):
        rows = [("a", "eng", 100), ("b", "eng", 100), ("c", "eng", 100)]
        out = second_highest_per_department(rows)
        self.assertEqual(out, {"eng": None})

    def test_tumbling_window_buckets(self):
        # 15-min windows (900s): 0 and 300 -> bucket 0; 1200 and 1700 -> bucket 900
        events = [(0, 1), (300, 1), (1200, 1), (1700, 1)]
        out = tumbling_window_counts(events, window_seconds=900)
        self.assertEqual(out, [(0, 2), (900, 2)])


if __name__ == "__main__":
    unittest.main()
