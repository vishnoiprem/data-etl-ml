"""Service-level tests for the APM service."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import APMService  # noqa: E402


class APMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = APMService()

    def test_ingest_span_assigns_snowflake_id(self) -> None:
        span = self.svc.ingest_span(
            trace_id="t1", service="api", name="GET /",
        )
        self.assertGreater(span["span_id"], 0)
        self.assertEqual(span["status"], "ok")

    def test_ingest_span_validates_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.ingest_span(trace_id="", service="api", name="x")
        with self.assertRaises(ValueError):
            self.svc.ingest_span(trace_id="t", service="", name="x")

    def test_get_trace_links_parents(self) -> None:
        self.svc.ingest_span(trace_id="t2", service="a", name="root",
                             span_id=10, parent_span_id=0)
        self.svc.ingest_span(trace_id="t2", service="b", name="child",
                             span_id=11, parent_span_id=10)
        self.svc.ingest_span(trace_id="t2", service="c", name="grand",
                             span_id=12, parent_span_id=11)
        trace = self.svc.get_trace("t2")
        self.assertEqual(len(trace["spans"]), 3)
        self.assertEqual(len(trace["roots"]), 1)
        root = trace["roots"][0]
        self.assertEqual(root["span_id"], 10)
        self.assertEqual(len(root["children"]), 1)
        self.assertEqual(len(root["children"][0]["children"]), 1)

    def test_error_rate_and_latency(self) -> None:
        now = int(time.time() * 1000)
        for i, status in enumerate(["ok", "ok", "error", "ok", "error"]):
            self.svc.ingest_span(
                trace_id=f"t{i}", service="checkout", name="charge",
                duration_ms=10 * (i + 1),
                start_ms=now,
                status=status,
            )
        stats = self.svc.service_error_rate("checkout", window_s=600,
                                            with_latency=True)
        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["errors"], 2)
        self.assertAlmostEqual(stats["error_rate"], 0.4)
        self.assertGreater(stats["p95_ms"], 0)

    def test_list_services(self) -> None:
        self.svc.ingest_span(trace_id="a", service="a", name="x")
        self.svc.ingest_span(trace_id="b", service="a", name="x")
        self.svc.ingest_span(trace_id="c", service="b", name="x")
        svcs = self.svc.list_services()
        names = [s["name"] for s in svcs]
        self.assertIn("a", names)
        self.assertIn("b", names)

    def test_trace_index_caps(self) -> None:
        # cap is 10_000; we don't blast that many in a unit test, but we can
        # check that the index contains the trace ids we ingested.
        self.svc.ingest_span(trace_id="tt1", service="s", name="x")
        self.svc.ingest_span(trace_id="tt2", service="s", name="x")
        idx = self.svc.list_traces()
        self.assertIn("tt1", idx)
        self.assertIn("tt2", idx)

    def test_unknown_trace(self) -> None:
        trace = self.svc.get_trace("nonexistent")
        self.assertEqual(trace["spans"], [])
        self.assertEqual(trace["roots"], [])


if __name__ == "__main__":
    unittest.main()
