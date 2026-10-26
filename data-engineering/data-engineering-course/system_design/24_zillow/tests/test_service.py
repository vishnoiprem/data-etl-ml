"""Service-level tests for the Zillow service."""

from __future__ import annotations

import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import ZillowService, haversine_km  # noqa: E402


class ZillowServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ZillowService()

    def test_haversine_zero_for_same_point(self) -> None:
        self.assertAlmostEqual(haversine_km(40.0, -70.0, 40.0, -70.0), 0.0)

    def test_haversine_known_value(self) -> None:
        # NYC -> London is ~5570 km
        d = haversine_km(40.7128, -74.0060, 51.5074, -0.1278)
        self.assertAlmostEqual(d, 5570, delta=50)

    def test_create_validates(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.create_listing(lat=100, lng=0, price=1)
        with self.assertRaises(ValueError):
            self.svc.create_listing(lat=0, lng=0, price=-1)

    def test_create_and_get(self) -> None:
        rec = self.svc.create_listing(
            lat=40.0, lng=-70.0, price=500_000, beds=3, baths=2, sqft=1500,
            address="1 Main St",
        )
        self.assertTrue(rec["id"])
        self.assertEqual(rec["price"], 500_000)
        fetched = self.svc.get_listing(rec["id"])
        self.assertEqual(fetched["address"], "1 Main St")

    def test_search_radius(self) -> None:
        # Two listings: one near, one far.
        near = self.svc.create_listing(lat=40.0, lng=-70.0, price=100_000)
        far = self.svc.create_listing(lat=41.0, lng=-71.0, price=100_000)
        res = self.svc.search(40.0, -70.0, radius_km=20)
        ids = {r["id"] for r in res["results"]}
        self.assertIn(near["id"], ids)
        self.assertNotIn(far["id"], ids)

    def test_search_filters(self) -> None:
        cheap = self.svc.create_listing(lat=40.0, lng=-70.0, price=100_000, beds=2)
        pricey = self.svc.create_listing(lat=40.0, lng=-70.0, price=900_000, beds=4)
        res = self.svc.search(40.0, -70.0, radius_km=5, max_price=200_000)
        ids = {r["id"] for r in res["results"]}
        self.assertIn(cheap["id"], ids)
        self.assertNotIn(pricey["id"], ids)

        res = self.svc.search(40.0, -70.0, radius_km=5, min_beds=3)
        ids = {r["id"] for r in res["results"]}
        self.assertIn(pricey["id"], ids)
        self.assertNotIn(cheap["id"], ids)

    def test_search_sort_by_distance(self) -> None:
        a = self.svc.create_listing(lat=40.0, lng=-70.0, price=1)
        b = self.svc.create_listing(lat=40.001, lng=-70.0, price=1)
        c = self.svc.create_listing(lat=40.002, lng=-70.0, price=1)
        res = self.svc.search(40.0, -70.0, radius_km=5)
        ids = [r["id"] for r in res["results"]]
        # a is closest, c is farthest among the three
        self.assertEqual(ids[0], a["id"])
        self.assertEqual(ids[-1], c["id"])

    def test_search_validates_coords(self) -> None:
        with self.assertRaises(ValueError):
            self.svc.search(lat=200, lng=0, radius_km=1)


if __name__ == "__main__":
    unittest.main()
