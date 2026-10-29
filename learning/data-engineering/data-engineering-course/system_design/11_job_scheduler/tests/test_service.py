"""Unit tests for the JobScheduler service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.ids import Snowflake  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from code.service import (  # noqa: E402
    DAGCycleError,
    FunctionJobRunner,
    InvalidJobError,
    JobNotFoundError,
    JobScheduler,
    topo_sort_children,
)


class FakeClock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class JobSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_sched",
            persist_path=os.path.join(self.tmpdir, "sched.json"),
        )
        self.clock = FakeClock()
        self.registry = {
            "noop": lambda payload: {"ok": True, "echo": payload},
            "fail": lambda payload: (_ for _ in ()).throw(RuntimeError("boom")),
        }
        self.svc = JobScheduler(
            store=self.store,
            idgen=Snowflake(machine_id=11),
            runner=FunctionJobRunner(self.registry),
            time_fn=self.clock,
            start_worker=False,
        )

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    # ---- validation -----------------------------------------------------

    def test_validate_rejects_unknown_kind(self):
        with self.assertRaises(InvalidJobError):
            self.svc.create_job({"name": "x", "kind": "wat"})

    def test_validate_rejects_once_without_run_at(self):
        with self.assertRaises(InvalidJobError):
            self.svc.create_job({"name": "x", "kind": "once"})

    def test_validate_rejects_cron_with_bad_interval(self):
        with self.assertRaises(InvalidJobError):
            self.svc.create_job({"name": "x", "kind": "cron", "interval_seconds": -1})

    def test_dag_cycle_rejected(self):
        with self.assertRaises(DAGCycleError):
            self.svc.create_job({
                "name": "etl",
                "kind": "dag",
                "children": [
                    {"name": "a", "kind": "once", "run_at": 1,
                     "payload": {"depends_on": ["b"]}},
                    {"name": "b", "kind": "once", "run_at": 1,
                     "payload": {"depends_on": ["a"]}},
                ],
            })

    def test_topo_sort(self):
        # Build fake children (no scheduler call).
        from code.service import Job
        a = Job(job_id=1, name="a", kind="once", payload={"depends_on": []})
        b = Job(job_id=2, name="b", kind="once", payload={"depends_on": ["a"]})
        c = Job(job_id=3, name="c", kind="once", payload={"depends_on": ["b"]})
        self.assertEqual(topo_sort_children([c, a, b]), [1, 2, 3])

    # ---- once / cron ---------------------------------------------------

    def test_once_runs_due(self):
        self.clock.t = 100.0
        job = self.svc.create_job({
            "name": "hello", "kind": "once", "run_at": 100.0,
            "payload": {"fn": "noop"},
        })
        self.svc.run_once()
        runs = self.svc.list_runs(job_id=job["job_id"])
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "success")

    def test_once_does_not_run_in_future(self):
        self.clock.t = 50.0
        self.svc.create_job({
            "name": "future", "kind": "once", "run_at": 100.0,
            "payload": {"fn": "noop"},
        })
        self.assertFalse(self.svc.run_once())
        self.assertEqual(len(self.svc.list_runs()), 0)

    def test_cron_runs_and_reschedules(self):
        self.clock.t = 100.0
        self.svc.create_job({
            "name": "tick", "kind": "cron", "interval_seconds": 10.0,
            "payload": {"fn": "noop"},
        })
        self.svc.run_once()  # at t=100
        self.clock.advance(10.0)  # t=110
        self.svc.run_once()
        self.clock.advance(10.0)  # t=120
        self.svc.run_once()
        runs = self.svc.list_runs()
        self.assertEqual(len(runs), 3)

    def test_failed_run_records_error(self):
        self.clock.t = 100.0
        job = self.svc.create_job({
            "name": "boom", "kind": "once", "run_at": 100.0,
            "payload": {"fn": "fail"},
        })
        self.svc.run_once()
        run = self.svc.list_runs(job_id=job["job_id"])[0]
        self.assertEqual(run["status"], "failed")
        self.assertIn("boom", run["error"])

    # ---- manual trigger -----------------------------------------------

    def test_manual_trigger_creates_run(self):
        self.clock.t = 100.0
        job = self.svc.create_job({
            "name": "m", "kind": "cron", "interval_seconds": 999.0,
            "payload": {"fn": "noop"},
        })
        run = self.svc.trigger_now(job["job_id"])
        self.assertEqual(run["trigger"], "manual")
        self.assertEqual(run["status"], "success")

    def test_manual_trigger_missing_raises(self):
        with self.assertRaises(JobNotFoundError):
            self.svc.trigger_now(999_999_999)

    # ---- DAG ----------------------------------------------------------

    def test_dag_runs_children_in_order(self):
        self.clock.t = 100.0
        job = self.svc.create_job({
            "name": "etl",
            "kind": "dag",
            "children": [
                {"name": "extract", "kind": "once", "run_at": 100.0,
                 "payload": {"fn": "noop"}},
                {"name": "transform", "kind": "once", "run_at": 100.0,
                 "payload": {"fn": "noop", "depends_on": ["extract"]}},
                {"name": "load", "kind": "once", "run_at": 100.0,
                 "payload": {"fn": "noop", "depends_on": ["transform"]}},
            ],
        })
        run = self.svc.trigger_now(job["job_id"])
        self.assertEqual(run["status"], "success")
        # 3 child runs were created.
        self.assertEqual(len(self.svc.list_runs()), 3)

    def test_dag_skips_when_dep_failed(self):
        self.clock.t = 100.0
        job = self.svc.create_job({
            "name": "etl2",
            "kind": "dag",
            "children": [
                {"name": "a", "kind": "once", "run_at": 100.0,
                 "payload": {"fn": "fail"}},
                {"name": "b", "kind": "once", "run_at": 100.0,
                 "payload": {"fn": "noop", "depends_on": ["a"]}},
            ],
        })
        run = self.svc.trigger_now(job["job_id"])
        self.assertEqual(run["status"], "failed")
        # b should be marked failed because a failed.
        runs = self.svc.list_runs()
        names_to_status = {}
        for j in self.svc.list_jobs():
            for r in self.svc.list_runs(job_id=j["job_id"]):
                if r["job_id"] in (r2["job_id"] for r2 in [r]):
                    pass
        # Simpler: find the run for child b by job name.
        child_jobs = [j for j in self.svc.list_jobs() if j["name"] == "b"]
        self.assertEqual(len(child_jobs), 1)
        b_runs = self.svc.list_runs(job_id=child_jobs[0]["job_id"])
        self.assertEqual(b_runs[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
