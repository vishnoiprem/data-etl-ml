"""HTTP-level tests for the Parking Garage service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import ParkingGarageService  # noqa: E402


class ParkingGarageAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ParkingGarageService(floors=2, spots_per_floor=5)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("checkin_total", r.get_data(as_text=True))

    def test_checkin_closest_spot(self):
        r = self.client.post("/api/checkin", json={"vehicle_id": 1})
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["floor"], 1)
        self.assertEqual(body["spot_id"], "F1-S001")

    def test_checkout_e2e(self):
        r = self.client.post("/api/checkin", json={"vehicle_id": 1})
        ticket_id = r.get_json()["ticket_id"]
        r = self.client.post("/api/checkout", json={"ticket_id": ticket_id})
        self.assertEqual(r.status_code, 200)
        self.assertIn("fee_cents", r.get_json())

    def test_availability_endpoint(self):
        r = self.client.get("/api/availability")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["total_free"], 10)
        self.assertEqual(body["total_capacity"], 10)

    def test_garage_full_returns_503(self):
        for i in range(1, 11):  # 2 floors * 5 spots
            r = self.client.post("/api/checkin", json={"vehicle_id": i})
            self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/checkin", json={"vehicle_id": 99})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json()["error"], "garage_full")

    def test_unknown_ticket_returns_404(self):
        r = self.client.post("/api/checkout", json={"ticket_id": 99999999})
        self.assertEqual(r.status_code, 404)

    def test_get_ticket_endpoint(self):
        r = self.client.post("/api/checkin", json={"vehicle_id": 1})
        ticket_id = r.get_json()["ticket_id"]
        r = self.client.get(f"/api/tickets/{ticket_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["vehicle_id"], 1)


if __name__ == "__main__":
    unittest.main()
