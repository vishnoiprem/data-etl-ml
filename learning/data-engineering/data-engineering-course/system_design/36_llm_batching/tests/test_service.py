"""Unit tests for the LLM batching service."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import BatchingService  # noqa: E402


class BatchingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        # Small batch / short window for fast tests.
        self.svc = BatchingService(batch_size=4, window_ms=20.0)

    def tearDown(self) -> None:
        self.svc.shutdown()

    # ---- validation ----------------------------------------------------

    def test_rejects_bad_batch_size(self):
        with self.assertRaises(ValueError):
            BatchingService(batch_size=0, window_ms=10.0)
        with self.assertRaises(ValueError):
            BatchingService(batch_size=4, window_ms=0)

    def test_submit_validation(self):
        with self.assertRaises(ValueError):
            self.svc.submit("")
        with self.assertRaises(ValueError):
            self.svc.submit(123)  # type: ignore[arg-type]

    # ---- batch-size trigger -------------------------------------------

    def test_fills_on_batch_size(self):
        ids = [self.svc.submit(f"q-{i}") for i in range(4)]
        # Wait for the batch to flush.
        for qid in ids:
            q = self.svc.get(qid, timeout=1.0)
            self.assertIsNotNone(q.response)
        s = self.svc.stats()
        self.assertEqual(s["batches"], 1)
        self.assertEqual(s["queries_in_batches"], 4)
        # Each query carries its slot in the mock response.
        for i, qid in enumerate(ids):
            self.assertIn(f"batch-slot {i}", self.svc.get(qid).response)

    # ---- window-time trigger ------------------------------------------

    def test_fills_on_window(self):
        ids = [self.svc.submit("only one")]
        q = self.svc.get(ids[0], timeout=1.0)
        self.assertIsNotNone(q.response)
        s = self.svc.stats()
        self.assertEqual(s["batches"], 1)
        self.assertEqual(s["queries_in_batches"], 1)

    # ---- multiple windows ---------------------------------------------

    def test_two_windows(self):
        ids_a = [self.svc.submit(f"a-{i}") for i in range(4)]
        for qid in ids_a:
            self.svc.get(qid, timeout=1.0)
        ids_b = [self.svc.submit(f"b-{i}") for i in range(2)]
        # Window timer for ids_b is 20ms — give it room.
        for qid in ids_b:
            self.svc.get(qid, timeout=1.0)
        s = self.svc.stats()
        self.assertGreaterEqual(s["batches"], 2)
        self.assertEqual(s["queries_in_batches"], 6)
        # First batch should be size 4; second batch at least 2.
        self.assertEqual(s["max_batch_size"], 4)

    # ---- throughput improvement ---------------------------------------

    def test_throughput_improvement(self):
        """N queries should compress into ~N/batch_size batches."""
        N = 8
        ids = [self.svc.submit(f"q-{i}") for i in range(N)]
        for qid in ids:
            self.svc.get(qid, timeout=1.0)
        s = self.svc.stats()
        # batch_size=4, N=8 → 2 batches → throughput_x ≈ 4.
        self.assertEqual(s["batches"], 2)
        self.assertEqual(s["throughput_x"], 4.0)
        self.assertEqual(s["avg_batch_size"], 4.0)

    # ---- manual flush ------------------------------------------------

    def test_flush_now(self):
        self.svc.submit("a")
        self.svc.submit("b")
        n = self.svc.flush_now()
        self.assertEqual(n, 2)
        s = self.svc.stats()
        self.assertEqual(s["batches"], 1)
        self.assertEqual(s["queries_in_batches"], 2)

    # ---- timeout on get ----------------------------------------------

    def test_get_timeout_returns_pending(self):
        qid = self.svc.submit("slow")
        # Don't flush — get() should time out returning the partial query.
        q = self.svc.get(qid, timeout=0.05)
        self.assertIsNotNone(q)
        self.assertIsNone(q.response)
        # Cleanup.
        self.svc.flush_now()

    def test_get_unknown_returns_none(self):
        self.assertIsNone(self.svc.get(999, timeout=0.01))

    def test_avg_wait_ms(self):
        ids = [self.svc.submit("hi") for _ in range(2)]
        for qid in ids:
            self.svc.get(qid, timeout=1.0)
        s = self.svc.stats()
        self.assertGreater(s["avg_wait_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
