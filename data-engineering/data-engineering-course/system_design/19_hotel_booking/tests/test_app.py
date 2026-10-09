"""HTTP-level tests for the Hotel Booking service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import HotelBookingService  # noqa: E402


class HotelBookingAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = HotelBookingService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()
        # Seed: one hotel, one room.
        r = self.client.post(
            "/api/hotels", json={"name": "Inn", "city": "Berkeley"}
        )
        self.hotel_id = r.get_json()["hotel_id"]
        r = self.client.post(
            f"/api/hotels/{self.hotel_id}/rooms",
            json={"room_number": "101", "capacity": 2, "price_cents": 15000},
        )
        self.room_id = r.get_json()["room_id"]

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("book_total", r.get_data(as_text=True))

    def test_book_e2e(self):
        r = self.client.post(
            f"/api/rooms/{self.room_id}/book",
            json={
                "user_id": 1,
                "check_in": "2026-10-10",
                "check_out": "2026-10-12",
            },
        )
        self.assertEqual(r.status_code, 201)
        booking_id = r.get_json()["booking_id"]
        r = self.client.get(f"/api/bookings/{booking_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "active")

    def test_overlapping_book_returns_409(self):
        r = self.client.post(
            f"/api/rooms/{self.room_id}/book",
            json={"user_id": 1, "check_in": "2026-10-10", "check_out": "2026-10-12"},
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.post(
            f"/api/rooms/{self.room_id}/book",
            json={"user_id": 2, "check_in": "2026-10-11", "check_out": "2026-10-13"},
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["error"], "room_unavailable")
        self.assertGreater(len(r.get_json()["conflicts"]), 0)

    def test_availability_endpoint(self):
        r = self.client.get(
            f"/api/rooms/{self.room_id}/availability?from=2026-11-01&to=2026-11-05"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["available"])

    def test_invalid_date_range_returns_400(self):
        r = self.client.post(
            f"/api/rooms/{self.room_id}/book",
            json={
                "user_id": 1,
                "check_in": "2026-10-12",
                "check_out": "2026-10-10",
            },
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()["error"], "invalid_date_range")

    def test_cancel_e2e(self):
        r = self.client.post(
            f"/api/rooms/{self.room_id}/book",
            json={"user_id": 1, "check_in": "2026-10-10", "check_out": "2026-10-12"},
        )
        booking_id = r.get_json()["booking_id"]
        r = self.client.post(
            f"/api/bookings/{booking_id}/cancel", json={"user_id": 1}
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["cancelled"])

    def test_unknown_room_returns_404(self):
        r = self.client.post(
            "/api/rooms/9999999/book",
            json={"user_id": 1, "check_in": "2026-10-10", "check_out": "2026-10-12"},
        )
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
