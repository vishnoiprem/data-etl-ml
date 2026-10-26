"""HTTP-level tests for the ExportService (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.ids import Snowflake  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from code.app import create_app  # noqa: E402
from code.service import (  # noqa: E402
    ActivityCollection,
    BlobStore,
    ExportService,
    OrdersCollection,
    PreferencesCollection,
    UserProfileCollection,
)


class FakeClock:
    def __init__(self, t: float = 2_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class ExportAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_export_app",
            persist_path=os.path.join(self.tmpdir, "exp.json"),
        )
        self.blobs = BlobStore(root=os.path.join(self.tmpdir, "blobs"))
        self.clock = FakeClock()
        self.profiles = {"u-1": {"name": "Alice"}, "u-2": {"name": "Bob"}}
        self.orders = {"u-1": [{"order_id": "o1", "amount": 9.99}]}
        self.activity = {"u-1": [{"event": "login"}]}
        self.prefs = {"u-1": {"newsletter": True}}
        self.svc = ExportService(
            store=self.store,
            blob_store=self.blobs,
            idgen=Snowflake(machine_id=12),
            collections=[
                UserProfileCollection(profiles=self.profiles),
                OrdersCollection(orders=self.orders),
                ActivityCollection(activity=self.activity),
                PreferencesCollection(prefs=self.prefs),
            ],
            ttl_seconds=120.0,
            time_fn=self.clock,
            start_worker=False,
        )
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    def _drain(self, max_ticks: int = 50) -> None:
        for _ in range(max_ticks):
            if not self.svc.run_once():
                return

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_create_export(self):
        r = self.client.post("/api/exports", json={"user_id": "u-1"})
        self.assertEqual(r.status_code, 202)
        body = r.get_json()
        self.assertIn("export_id", body)
        self.assertEqual(body["user_id"], "u-1")
        self.assertEqual(body["status"], "queued")

    def test_create_rejects_missing_user_id(self):
        r = self.client.post("/api/exports", json={})
        self.assertEqual(r.status_code, 400)

    def test_get_export_after_processing(self):
        r = self.client.post("/api/exports", json={"user_id": "u-1"})
        eid = r.get_json()["export_id"]
        self._drain()
        r2 = self.client.get(f"/api/exports/{eid}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["status"], "ready")

    def test_get_export_missing(self):
        r = self.client.get("/api/exports/99999")
        self.assertEqual(r.status_code, 404)

    def test_download_returns_compiled_data(self):
        r = self.client.post("/api/exports", json={"user_id": "u-1"})
        eid = r.get_json()["export_id"]
        self._drain()
        r2 = self.client.get(f"/api/exports/{eid}/download")
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertIn("data", body)
        self.assertEqual(body["data"]["profile"][0]["name"], "Alice")

    def test_download_not_ready_409(self):
        r = self.client.post("/api/exports", json={"user_id": "u-1"})
        eid = r.get_json()["export_id"]
        # Don't drain — status is still queued.
        r2 = self.client.get(f"/api/exports/{eid}/download")
        self.assertIn(r2.status_code, (409, 410))

    def test_download_after_expiry(self):
        r = self.client.post("/api/exports", json={"user_id": "u-1"})
        eid = r.get_json()["export_id"]
        self._drain()
        # Advance past TTL.
        self.clock.advance(180.0)
        r2 = self.client.get(f"/api/exports/{eid}/download")
        self.assertEqual(r2.status_code, 410)

    def test_list_by_user(self):
        self.client.post("/api/exports", json={"user_id": "u-1"})
        self.client.post("/api/exports", json={"user_id": "u-2"})
        r = self.client.get("/api/exports?user_id=u-1")
        self.assertEqual(r.status_code, 200)
        exps = r.get_json()["exports"]
        self.assertEqual(len(exps), 1)
        self.assertEqual(exps[0]["user_id"], "u-1")

    def test_metrics(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("exports_created_total", text)
        self.assertIn("queue_size", text)

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["service"], "user_data_export")


if __name__ == "__main__":
    unittest.main()
