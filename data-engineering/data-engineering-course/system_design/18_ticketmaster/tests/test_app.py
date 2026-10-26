"""HTTP-level tests for the Ticketmaster service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import TicketmasterService  # noqa: E402


class TicketmasterAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = TicketmasterService(hold_ttl_seconds=60.0)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.svc.stop()

    def _create_event(self, rows=2, cols=2, name="Show"):
        r = self.client.post(
            "/api/events", json={"name": name, "rows": rows, "cols": cols}
        )
        self.assertEqual(r.status_code, 201)
        return r.get_json()["event_id"]

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("hold_total", r.get_data(as_text=True))

    def test_create_event_and_list_seats(self):
        eid = self._create_event(rows=2, cols=3)
        r = self.client.get(f"/api/events/{eid}/seats")
        self.assertEqual(r.status_code, 200)
        seats = r.get_json()["seats"]
        self.assertEqual(len(seats), 6)

    def test_hold_purchase_e2e(self):
        eid = self._create_event()
        r = self.client.post(
            f"/api/events/{eid}/seats/A-1/hold", json={"user_id": 7}
        )
        self.assertEqual(r.status_code, 201)
        hold_token = r.get_json()["hold_token"]
        r = self.client.post(
            f"/api/events/{eid}/seats/A-1/purchase",
            json={"user_id": 7, "hold_token": hold_token},
        )
        self.assertEqual(r.status_code, 201)
        self.assertIn("ticket_id", r.get_json())

    def test_hold_conflict_returns_409(self):
        eid = self._create_event()
        r1 = self.client.post(
            f"/api/events/{eid}/seats/A-1/hold", json={"user_id": 1}
        )
        self.assertEqual(r1.status_code, 201)
        r2 = self.client.post(
            f"/api/events/{eid}/seats/A-1/hold", json={"user_id": 2}
        )
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(r2.get_json()["error"], "seat_unavailable")

    def test_release_e2e(self):
        eid = self._create_event()
        r = self.client.post(
            f"/api/events/{eid}/seats/A-1/hold", json={"user_id": 9}
        )
        hold_token = r.get_json()["hold_token"]
        r = self.client.post(
            f"/api/events/{eid}/seats/A-1/release",
            json={"user_id": 9, "hold_token": hold_token},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["released"])
        # Now holdable again.
        r = self.client.post(
            f"/api/events/{eid}/seats/A-1/hold", json={"user_id": 10}
        )
        self.assertEqual(r.status_code, 201)

    def test_unknown_event_returns_404(self):
        r = self.client.get("/api/events/99999999")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
