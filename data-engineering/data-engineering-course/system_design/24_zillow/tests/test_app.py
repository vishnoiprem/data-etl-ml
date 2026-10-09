"""HTTP-level tests for the Zillow service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import ZillowService  # noqa: E402


class ZillowAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ZillowService()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_create_and_get(self) -> None:
        r = self.client.post("/api/listings", json={
            "lat": 40.0, "lng": -70.0, "price": 700_000,
            "beds": 3, "baths": 2, "sqft": 1800, "address": "42 Test Ave",
        })
        self.assertEqual(r.status_code, 201)
        listing_id = r.get_json()["id"]
        r = self.client.get(f"/api/listings/{listing_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["address"], "42 Test Ave")

    def test_create_validates(self) -> None:
        r = self.client.post("/api/listings", json={"price": -1})
        self.assertEqual(r.status_code, 400)

    def test_get_missing(self) -> None:
        r = self.client.get("/api/listings/9999")
        self.assertEqual(r.status_code, 404)

    def test_search(self) -> None:
        self.client.post("/api/listings", json={
            "lat": 40.0, "lng": -70.0, "price": 100_000, "beds": 2,
        })
        self.client.post("/api/listings", json={
            "lat": 40.01, "lng": -70.0, "price": 800_000, "beds": 4,
        })
        r = self.client.get(
            "/api/search?lat=40.0&lng=-70.0&radius_km=5&max_price=200000"
        )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["beds"], 2)

    def test_search_with_filters(self) -> None:
        self.client.post("/api/listings", json={
            "lat": 40.0, "lng": -70.0, "price": 500_000, "beds": 3,
        })
        r = self.client.get(
            "/api/search?lat=40.0&lng=-70.0&radius_km=2&min_beds=2"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["results"]), 1)

    def test_health_and_metrics(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"create_listing_total", r.data)


if __name__ == "__main__":
    unittest.main()
