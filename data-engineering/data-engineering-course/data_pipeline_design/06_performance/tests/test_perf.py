"""Unit tests for the performance / fault-tolerance module.

Run with::

    python3 scripts/run_all_tests.py data_pipeline_design
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]
sys.path.insert(0, str(COURSE_ROOT.parent))


def _load(name: str, file_name: str):
    path = HERE.parent / "code" / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


orchestrator = _load("data_pipeline_design_perf_orch", "orchestrator.py")
retry = _load("data_pipeline_design_perf_retry", "retry.py")
monitoring = _load("data_pipeline_design_perf_mon", "monitoring.py")

Dag = orchestrator.Dag
TaskState = orchestrator.TaskState


# =========================================================================
# Orchestrator tests
# =========================================================================


class DagTests(unittest.TestCase):
    def test_linear_dag(self):
        dag = Dag("linear")
        dag.add_task("a", lambda: "A")
        dag.add_task("b", lambda: "B", depends_on=["a"])
        dag.add_task("c", lambda: "C", depends_on=["b"])
        results = dag.run()
        self.assertEqual(results, {"a": "A", "b": "B", "c": "C"})
        self.assertEqual(dag.execution_order, ["a", "b", "c"])

    def test_diamond_dag(self):
        """A → B, A → C, (B, C) → D"""
        dag = Dag("diamond")
        order: list = []

        def make(name):
            def fn():
                order.append(name)
                return name
            return fn

        dag.add_task("a", make("a"))
        dag.add_task("b", make("b"), depends_on=["a"])
        dag.add_task("c", make("c"), depends_on=["a"])
        dag.add_task("d", make("d"), depends_on=["b", "c"])
        results = dag.run()
        self.assertEqual(set(results.keys()), {"a", "b", "c", "d"})
        # 'a' runs first; 'd' runs last.
        self.assertEqual(order[0], "a")
        self.assertEqual(order[-1], "d")
        # 'b' and 'c' both run after 'a' and before 'd'.
        self.assertLess(order.index("a"), order.index("b"))
        self.assertLess(order.index("a"), order.index("c"))
        self.assertLess(order.index("b"), order.index("d"))
        self.assertLess(order.index("c"), order.index("d"))

    def test_cycle_detected(self):
        dag = Dag("cycle")
        # We can't easily create a cycle via add_task because
        # add_task rejects unknown deps. Instead, monkey-patch
        # _deps to inject the cycle.
        dag.add_task("a", lambda: None)
        dag.add_task("b", lambda: None, depends_on=["a"])
        dag._deps["a"].append("b")
        with self.assertRaises(ValueError):
            dag.run()

    def test_unknown_dependency_rejected(self):
        dag = Dag("test")
        with self.assertRaises(ValueError):
            dag.add_task("a", lambda: None, depends_on=["nope"])

    def test_duplicate_task_rejected(self):
        dag = Dag("test")
        dag.add_task("a", lambda: None)
        with self.assertRaises(ValueError):
            dag.add_task("a", lambda: None)

    def test_failing_task_propagates(self):
        dag = Dag("test")

        def boom():
            raise RuntimeError("boom")

        dag.add_task("a", boom)
        with self.assertRaises(RuntimeError):
            dag.run()
        self.assertEqual(dag.state["a"], TaskState.FAILED)

    def test_downstream_skipped_when_dep_fails(self):
        dag = Dag("test")
        dag.add_task("a", lambda: None)
        dag.add_task("b", lambda: 1 / 0, depends_on=["a"])
        dag.add_task("c", lambda: "C", depends_on=["b"])
        with self.assertRaises(ZeroDivisionError):
            dag.run()
        # 'c' was skipped because 'b' failed.
        self.assertEqual(dag.state["c"], TaskState.SKIPPED)


# =========================================================================
# Retry tests
# =========================================================================


class RetryTests(unittest.TestCase):
    def test_succeeds_first_try(self):
        calls = []

        @retry.retry(max_attempts=3, backoff=0.0, jitter=False, sleep=lambda _: None)
        def fn():
            calls.append(1)
            return "ok"

        self.assertEqual(fn(), "ok")
        self.assertEqual(calls, [1])

    def test_succeeds_after_two_failures(self):
        calls = []

        @retry.retry(max_attempts=3, backoff=0.0, jitter=False, sleep=lambda _: None)
        def fn():
            calls.append(1)
            if len(calls) < 3:
                raise RuntimeError("flaky")
            return "ok"

        self.assertEqual(fn(), "ok")
        self.assertEqual(len(calls), 3)

    def test_fails_after_max_attempts(self):
        calls = []

        @retry.retry(max_attempts=3, backoff=0.0, jitter=False, sleep=lambda _: None)
        def fn():
            calls.append(1)
            raise RuntimeError("always fails")

        with self.assertRaises(RuntimeError):
            fn()
        self.assertEqual(len(calls), 3)

    def test_retry_on_filters_exceptions(self):
        calls = []

        @retry.retry(
            max_attempts=3, backoff=0.0, jitter=False,
            retry_on=(ValueError,), sleep=lambda _: None,
        )
        def fn():
            calls.append(1)
            raise TypeError("not retried")

        with self.assertRaises(TypeError):
            fn()
        self.assertEqual(len(calls), 1)  # No retry on TypeError

    def test_jitter_keeps_wait_in_range(self):
        # Verify the wait time is computed, not just skipped.
        waits: list = []

        @retry.retry(max_attempts=2, backoff=1.0, jitter=True, sleep=waits.append)
        def fn():
            raise RuntimeError("x")

        with self.assertRaises(RuntimeError):
            fn()
        # One wait between attempt 1 and attempt 2.
        self.assertEqual(len(waits), 1)
        # With jitter, wait is in [0.5, 1.5) of backoff=1.0.
        self.assertGreaterEqual(waits[0], 0.5)
        self.assertLess(waits[0], 1.5)

    def test_max_attempts_validation(self):
        with self.assertRaises(ValueError):
            retry.retry(max_attempts=0)

    def test_backoff_validation(self):
        with self.assertRaises(ValueError):
            retry.retry(max_attempts=2, backoff=-1.0)


# =========================================================================
# Monitoring tests
# =========================================================================


class SLATrackerTests(unittest.TestCase):
    def test_empty_tracker(self):
        t = monitoring.SLATracker()
        self.assertEqual(t.success_rate("missing"), 0.0)
        self.assertEqual(t.p95_duration("missing"), 0.0)
        self.assertEqual(t.n_samples("missing"), 0)

    def test_record_and_query(self):
        t = monitoring.SLATracker()
        t.record_job("p", duration_ms=100, success=True)
        t.record_job("p", duration_ms=200, success=True)
        t.record_job("p", duration_ms=300, success=False)
        self.assertEqual(t.n_samples("p"), 3)
        self.assertAlmostEqual(t.success_rate("p"), 2 / 3, places=4)
        self.assertEqual(t.p50_duration("p"), 200)
        # 95th percentile of [100, 200, 300] = 300 (nearest-rank).
        self.assertEqual(t.p95_duration("p"), 300)

    def test_p95_with_100_samples(self):
        """Spec test: feed 100 fake job runs, assert p95."""
        t = monitoring.SLATracker()
        for i in range(100):
            t.record_job("p", duration_ms=i * 10, success=(i % 10 != 0))
        # 100 samples, success rate 90/100.
        self.assertAlmostEqual(t.success_rate("p"), 0.9, places=2)
        # p95 of [0, 10, 20, ..., 990]: nearest-rank idx = round(0.95 * 99) = 94
        # → durations[94] = 940.
        self.assertEqual(t.p95_duration("p"), 940)
        self.assertEqual(t.n_samples("p"), 100)

    def test_window_eviction(self):
        t = monitoring.SLATracker(window_minutes=60)
        # Manually inject an old sample by patching ts.
        t.record_job("p", duration_ms=100, success=True)
        # Backdate the sample.
        only_sample = t._samples["p"][0]
        only_sample.ts = only_sample.ts - 7200  # 2 hours ago
        # The sample is now outside the 60-minute window.
        self.assertEqual(t.n_samples("p"), 0)
        self.assertEqual(t.success_rate("p"), 0.0)

    def test_validation(self):
        t = monitoring.SLATracker()
        with self.assertRaises(ValueError):
            t.record_job("p", duration_ms=-1, success=True)

    def test_separate_jobs_tracked_independently(self):
        t = monitoring.SLATracker()
        t.record_job("a", duration_ms=100, success=True)
        t.record_job("b", duration_ms=200, success=False)
        self.assertEqual(t.success_rate("a"), 1.0)
        self.assertEqual(t.success_rate("b"), 0.0)
        self.assertEqual(t.p95_duration("a"), 100)
        self.assertEqual(t.p95_duration("b"), 200)


if __name__ == "__main__":
    unittest.main()
