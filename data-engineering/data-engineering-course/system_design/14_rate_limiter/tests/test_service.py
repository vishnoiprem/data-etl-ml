"""Unit tests for the rate limiter core service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    TokenBucket,
    FixedWindow,
    SlidingWindow,
    RateLimiter,
)


class TokenBucketTests(unittest.TestCase):
    def test_allows_burst_up_to_limit(self):
        state = TokenBucket.init()
        for _ in range(5):
            d = TokenBucket.check(state, now=0.0, limit=5, window=60.0)
            self.assertTrue(d.allowed)
        # Next should be denied.
        d = TokenBucket.check(state, now=0.0, limit=5, window=60.0)
        self.assertFalse(d.allowed)

    def test_refills_over_time(self):
        state = TokenBucket.init()
        # Drain
        for _ in range(10):
            TokenBucket.check(state, now=0.0, limit=10, window=60.0)
        # Move time forward 6s — refill = 10 * 6 / 60 = 1 token
        d = TokenBucket.check(state, now=6.0, limit=10, window=60.0)
        self.assertTrue(d.allowed)

    def test_cost_greater_than_one(self):
        state = TokenBucket.init()
        d = TokenBucket.check(state, now=0.0, limit=10, window=60.0, cost=5)
        self.assertTrue(d.allowed)
        self.assertEqual(d.remaining, 5)


class FixedWindowTests(unittest.TestCase):
    def test_window_reset(self):
        state = FixedWindow.init()
        # 3 calls in window 0..60
        for _ in range(3):
            d = FixedWindow.check(state, now=0.0, limit=3, window=60.0)
            self.assertTrue(d.allowed)
        d = FixedWindow.check(state, now=10.0, limit=3, window=60.0)
        self.assertFalse(d.allowed)
        # After window: reset
        d = FixedWindow.check(state, now=70.0, limit=3, window=60.0)
        self.assertTrue(d.allowed)


class SlidingWindowTests(unittest.TestCase):
    def test_drops_old_timestamps(self):
        state = SlidingWindow.init()
        SlidingWindow.check(state, now=0.0, limit=3, window=60.0)
        SlidingWindow.check(state, now=10.0, limit=3, window=60.0)
        SlidingWindow.check(state, now=20.0, limit=3, window=60.0)
        # 4th at t=30 inside window
        d = SlidingWindow.check(state, now=30.0, limit=3, window=60.0)
        self.assertFalse(d.allowed)
        # After window passes, slot freed
        d = SlidingWindow.check(state, now=70.0, limit=3, window=60.0)
        self.assertTrue(d.allowed)


class RateLimiterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rl = RateLimiter(capacity=1_000)

    def test_validates_parameters(self):
        with self.assertRaises(ValueError):
            self.rl.check(key="", limit=10, window_seconds=60)
        with self.assertRaises(ValueError):
            self.rl.check(key="u", limit=0, window_seconds=60)
        with self.assertRaises(ValueError):
            self.rl.check(key="u", limit=10, window_seconds=0)
        with self.assertRaises(ValueError):
            self.rl.check(key="u", limit=10, window_seconds=60, cost=0)
        with self.assertRaises(ValueError):
            self.rl.check(key="u", limit=10, window_seconds=60, strategy="bogus")

    def test_token_bucket_basic(self):
        d = self.rl.check("u1", limit=3, window_seconds=60, strategy="token_bucket")
        self.assertTrue(d.allowed)
        self.assertEqual(d.strategy, "token_bucket")

    def test_fixed_window_basic(self):
        d = self.rl.check("u1", limit=3, window_seconds=60, strategy="fixed_window")
        self.assertTrue(d.allowed)
        self.assertEqual(d.strategy, "fixed_window")

    def test_sliding_window_basic(self):
        d = self.rl.check("u1", limit=3, window_seconds=60, strategy="sliding_window")
        self.assertTrue(d.allowed)
        self.assertEqual(d.strategy, "sliding_window")

    def test_isolation_between_keys(self):
        for _ in range(3):
            self.rl.check("u1", limit=3, window_seconds=60, strategy="token_bucket")
        d1 = self.rl.check("u1", limit=3, window_seconds=60, strategy="token_bucket")
        self.assertFalse(d1.allowed)
        d2 = self.rl.check("u2", limit=3, window_seconds=60, strategy="token_bucket")
        self.assertTrue(d2.allowed)

    def test_reset_specific_key(self):
        for _ in range(3):
            self.rl.check("u1", limit=3, window_seconds=60, strategy="token_bucket")
        self.rl.reset(key="u1", strategy="token_bucket")
        d = self.rl.check("u1", limit=3, window_seconds=60, strategy="token_bucket")
        self.assertTrue(d.allowed)

    def test_reset_all(self):
        self.rl.check("u1", limit=3, window_seconds=60)
        self.rl.check("u2", limit=3, window_seconds=60)
        n = self.rl.reset()
        self.assertGreaterEqual(n, 2)

    def test_inspect(self):
        self.rl.check("k", limit=10, window_seconds=60, strategy="token_bucket")
        info = self.rl.inspect("k", strategy="token_bucket")
        self.assertEqual(info["strategy"], "token_bucket")
        self.assertIn("state", info)

    def test_stats_tracks_allow_deny(self):
        self.rl.check("k", limit=1, window_seconds=60)
        self.rl.check("k", limit=1, window_seconds=60)
        s = self.rl.stats()
        self.assertGreaterEqual(s["allow"], 1)
        self.assertGreaterEqual(s["deny"], 1)


if __name__ == "__main__":
    unittest.main()
