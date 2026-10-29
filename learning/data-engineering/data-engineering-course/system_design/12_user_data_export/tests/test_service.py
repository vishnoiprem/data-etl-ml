"""Unit tests for the ExportService."""

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
    ActivityCollection,
    BlobStore,
    ExportError,
    ExportNotFoundError,
    ExportService,
    InvalidUserError,
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


class ExportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_export",
            persist_path=os.path.join(self.tmpdir, "exp.json"),
        )
        self.blobs = BlobStore(root=os.path.join(self.tmpdir, "blobs"))
        self.clock = FakeClock()
        self.profiles = {"u-1": {"name": "Alice"}}
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
            ttl_seconds=60.0,
            time_fn=self.clock,
            start_worker=False,
        )

    def tearDown(self) -> None:
        self.svc.stop_worker(timeout=0.5)

    def _drain(self, max_ticks: int = 50) -> None:
        for _ in range(max_ticks):
            if not self.svc.run_once():
                return

    # ---- create ---------------------------------------------------------

    def test_create_export_persists(self):
        e = self.svc.create_export("u-1")
        self.assertEqual(e.user_id, "u-1")
        self.assertEqual(e.status, "queued")
        self.assertIsNotNone(self.svc.get_export(e.export_id))

    def test_create_rejects_empty_user_id(self):
        with self.assertRaises(InvalidUserError):
            self.svc.create_export("")

    def test_create_rejects_non_string(self):
        with self.assertRaises(InvalidUserError):
            self.svc.create_export(None)  # type: ignore[arg-type]

    # ---- happy path ----------------------------------------------------

    def test_export_becomes_ready(self):
        e = self.svc.create_export("u-1")
        self._drain()
        data = self.svc.get_export(e.export_id)
        self.assertEqual(data["status"], "ready")
        self.assertGreater(data["size_bytes"], 0)
        self.assertIsNotNone(data["expires_at"])

    def test_download_returns_blob(self):
        e = self.svc.create_export("u-1")
        self._drain()
        blob = self.svc.download(e.export_id)
        self.assertIn("meta", blob)
        self.assertIn("data", blob)
        self.assertEqual(blob["data"]["profile"][0]["name"], "Alice")
        self.assertEqual(len(blob["data"]["orders"]), 1)

    def test_download_not_ready_raises(self):
        e = self.svc.create_export("u-1")
        with self.assertRaises(ExportError):
            self.svc.download(e.export_id)

    def test_download_missing_raises(self):
        with self.assertRaises(ExportNotFoundError):
            self.svc.download(99_999)

    # ---- per-user listing ---------------------------------------------

    def test_list_exports_filtered_by_user(self):
        a = self.svc.create_export("u-1")
        self.svc.create_export("u-2")
        u1 = self.svc.list_exports(user_id="u-1")
        ids = [e["export_id"] for e in u1]
        self.assertIn(a.export_id, ids)
        self.assertEqual(len(u1), 1)

    # ---- expiry --------------------------------------------------------

    def test_export_expires(self):
        e = self.svc.create_export("u-1")
        self._drain()
        # Advance past expiry.
        self.clock.advance(120.0)
        # Tick once to perform the expiry sweep.
        self.svc.run_once()
        data = self.svc.get_export(e.export_id)
        self.assertEqual(data["status"], "expired")
        # Download should 410 (ExportNotFoundError).
        with self.assertRaises(ExportNotFoundError):
            self.svc.download(e.export_id)

    def test_lazy_expiry_on_download(self):
        e = self.svc.create_export("u-1")
        self._drain()
        self.clock.advance(120.0)
        with self.assertRaises(ExportNotFoundError):
            self.svc.download(e.export_id)
        self.assertEqual(self.svc.get_export(e.export_id)["status"], "expired")

    # ---- failure --------------------------------------------------------

    def test_collection_failure_marks_failed(self):
        class Bad(Collection := ActivityCollection):  # noqa: F841
            pass

        # Simpler: replace one collection with a raising one.
        class Raising:
            name = "explode"
            def collect(self, user_id): raise RuntimeError("kaboom")
        self.svc.collections = [Raising()]
        e = self.svc.create_export("u-1")
        self._drain()
        data = self.svc.get_export(e.export_id)
        self.assertEqual(data["status"], "failed")
        self.assertIn("kaboom", data["error"])

    def test_oversize_blob_marked_failed(self):
        big_payload = {"x": "a" * (1024 * 1024)}  # 1 MB string
        self.svc.max_blob_bytes = 1024  # 1 KB
        # Make a profile that explodes size.
        self.svc.collections = [
            UserProfileCollection(
                profiles={"u-1": big_payload}
            )
        ]
        e = self.svc.create_export("u-1")
        self._drain()
        self.assertEqual(self.svc.get_export(e.export_id)["status"], "failed")

    # ---- recovery -------------------------------------------------------

    def test_in_flight_runs_recover_to_queued(self):
        e = self.svc.create_export("u-1")
        # Manually mark it running.
        data = self.svc.get_export(e.export_id)
        data["status"] = "running"
        self.store.set(f"export:{e.export_id}", data)
        # New service should re-queue it.
        svc2 = ExportService(
            store=self.store,
            blob_store=self.blobs,
            idgen=Snowflake(machine_id=13),
            collections=self.svc.collections,
            ttl_seconds=60.0,
            start_worker=False,
        )
        try:
            self.assertEqual(
                svc2.get_export(e.export_id)["status"], "queued"
            )
        finally:
            svc2.stop_worker(timeout=0.2)


if __name__ == "__main__":
    unittest.main()
