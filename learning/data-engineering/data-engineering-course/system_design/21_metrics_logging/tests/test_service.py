"""Service-level tests for the Metrics + Logging service."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import MetricsLoggingService  # noqa: E402


class MetricsLoggingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = MetricsLoggingService()

    def test_ingest_single_metric(self) -> None:
        res = self.svc.ingest_metric("http_requests", 1.0, {"path": "/"})
        self.assertTrue(res["ok"])
        series = self.svc.list_series("http_requests")
        self.assertEqual(len(series), 1)

    def test_label_normalization_merges_series(self) -> None:
        self.svc.ingest_metric("http_requests", 1.0, {"a": "1", "b": "2"})
        self.svc.ingest_metric("http_requests", 1.0, {"b": "2", "a": "1"})
        series = self.svc.list_series("http_requests")
        self.assertEqual(len(series), 1)

    def test_range_query_aggregates_buckets(self) -> None:
        now = int(time.time() * 1000)
        # 3 samples in the same minute bucket
        for offset in (0, 1, 2):
            self.svc.ingest_metric(
                "rps", float(offset), {"svc": "api"}, ts=(now + offset) / 1000.0,
            )
        res = self.svc.query("rps", ts_from=(now - 5000) / 1000.0,
                             ts_to=(now + 10000) / 1000.0, step=60, agg="avg")
        self.assertEqual(len(res["points"]), 1)
        self.assertAlmostEqual(res["points"][0]["v"], 1.0)

    def test_aggregation_modes(self) -> None:
        now = int(time.time() * 1000)
        for v in (1, 2, 3, 4):
            self.svc.ingest_metric("m", float(v), {}, ts=(now + v) / 1000.0)
        f = (now - 5000) / 1000.0
        t = (now + 10000) / 1000.0
        self.assertAlmostEqual(self.svc.query("m", f, t, agg="sum")["points"][0]["v"], 10)
        self.assertAlmostEqual(self.svc.query("m", f, t, agg="max")["points"][0]["v"], 4)
        self.assertAlmostEqual(self.svc.query("m", f, t, agg="min")["points"][0]["v"], 1)
        self.assertAlmostEqual(self.svc.query("m", f, t, agg="count")["points"][0]["v"], 4)

    def test_invalid_agg_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.query("m", 0, 1, agg="bogus")

    def test_log_ingest_and_search(self) -> None:
        self.svc.ingest_log("hello world", level="info", labels={"app": "x"})
        self.svc.ingest_log("another message", level="warn", labels={"app": "y"})
        self.svc.ingest_log("error happened", level="error", labels={"app": "x"})
        results = self.svc.search_logs("hello")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["msg"], "hello world")

        results = self.svc.search_logs("x", limit=10)
        # "x" appears in app=x labels of two records.
        self.assertGreaterEqual(len(results), 2)

    def test_log_search_case_insensitive(self) -> None:
        self.svc.ingest_log("Error Something", level="error")
        self.assertEqual(len(self.svc.search_logs("ERROR")), 1)

    def test_stats(self) -> None:
        self.svc.ingest_metric("m1", 1.0, {"k": "v"})
        self.svc.ingest_log("hi")
        s = self.svc.stats()
        self.assertEqual(s["series"], 1)
        self.assertEqual(s["logs"], 1)


if __name__ == "__main__":
    unittest.main()
