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


if __name__ == "__main__":
    unittest.main()
