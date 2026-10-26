"""HTTP-level tests for the JobScheduler (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.ids import Snowflake  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from code.app import JOB_REGISTRY, create_app  # noqa: E402
from code.service import FunctionJobRunner, JobScheduler  # noqa: E402


class FakeClock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class JobSchedulerAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_sched_app",
            persist_path=os.path.join(self.tmpdir, "sched.json"),
        )
        self.clock = FakeClock()
        self.svc = JobScheduler(
            store=self.store,
            idgen=Snowflake(machine_id=11),
            runner=FunctionJobRunner(JOB_REGISTRY),
            time_fn=self.clock,
            start_worker=False,
        )
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_create_cron_job(self):
        r = self.client.post("/api/jobs", json={
            "name": "ping",
            "kind": "cron",
            "interval_seconds": 60,
            "payload": {"fn": "ping"},
        })
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["kind"], "cron")
        self.assertEqual(body["status"], "active")

    def test_create_rejects_bad_kind(self):
        r = self.client.post("/api/jobs", json={"name": "x", "kind": "wat"})
        self.assertEqual(r.status_code, 400)

    def test_list_and_get(self):
        r = self.client.post("/api/jobs", json={
            "name": "j1", "kind": "cron", "interval_seconds": 30,
            "payload": {"fn": "noop"},
        })
        jid = r.get_json()["job_id"]
        r2 = self.client.get("/api/jobs")
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(len(r2.get_json()["jobs"]), 1)
        r3 = self.client.get(f"/api/jobs/{jid}")
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.get_json()["name"], "j1")

    def test_get_missing(self):
        r = self.client.get("/api/jobs/9999999")
        self.assertEqual(r.status_code, 404)

    def test_manual_trigger_via_http(self):
        r = self.client.post("/api/jobs", json={
            "name": "m", "kind": "cron", "interval_seconds": 999.0,
            "payload": {"fn": "noop"},
        })
        jid = r.get_json()["job_id"]
        r2 = self.client.post(f"/api/jobs/{jid}/run", json={})
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["trigger"], "manual")

    def test_list_runs(self):
        r = self.client.post("/api/jobs", json={
            "name": "t", "kind": "cron", "interval_seconds": 999.0,
            "payload": {"fn": "noop"},
        })
        jid = r.get_json()["job_id"]
        self.client.post(f"/api/jobs/{jid}/run", json={})
        r2 = self.client.get(f"/api/runs?job_id={jid}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(len(r2.get_json()["runs"]), 1)

    def test_dag_create_and_trigger(self):
        r = self.client.post("/api/jobs", json={
            "name": "etl",
            "kind": "dag",
            "children": [
                {"name": "a", "kind": "once", "run_at": self.clock(),
                 "payload": {"fn": "noop"}},
                {"name": "b", "kind": "once", "run_at": self.clock(),
                 "payload": {"fn": "noop", "depends_on": ["a"]}},
            ],
        })
        self.assertEqual(r.status_code, 201)
        jid = r.get_json()["job_id"]
        r2 = self.client.post(f"/api/jobs/{jid}/run", json={})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["status"], "success")

    def test_metrics(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("jobs_created_total", r.get_data(as_text=True))

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["service"], "job_scheduler")


if __name__ == "__main__":
    unittest.main()
