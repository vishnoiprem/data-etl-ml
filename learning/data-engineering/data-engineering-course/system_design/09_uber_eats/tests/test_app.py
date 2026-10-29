"""HTTP tests for the Uber Eats Flask app.

Run with:
    cd system_design
    python -m unittest 09_uber_eats.tests.test_app -v
"""

from __future__ import annotations

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import (  # noqa: E402
    ACCEPTED,
    CANCELLED,
    DELIVERED,
    PICKED_UP,
    PLACED,
    UberEatsService,
)


def _create_restaurant_with_item(client, name="R1"):
    rv = client.post(
        "/api/restaurants",
        data=json.dumps(
            {"name": name, "address": "1 Main St", "lat": 0.0, "lng": 0.0}
        ),
        content_type="application/json",
    )
    assert rv.status_code == 201, rv.get_data(as_text=True)
    r = rv.get_json()
    rv = client.post(
        f"/api/restaurants/{r['restaurant_id']}/menu",
        data=json.dumps({"name": "Pizza", "price_cents": 1200}),
        content_type="application/json",
    )
    assert rv.status_code == 201, rv.get_data(as_text=True)
    return r, rv.get_json()


def _create_driver(client, name="D1", lat=0.001, lng=0.001):
    rv = client.post(
        "/api/drivers",
        data=json.dumps({"name": name, "lat": lat, "lng": lng}),
        content_type="application/json",
    )
    assert rv.status_code == 201
    return rv.get_json()


class UberEatsAppTest(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()
        self.app = create_app(service=self.svc)
        self.client = self.app.test_client()

    # ---- restaurants & menus ----

    def test_create_and_get_restaurant(self):
        r, _ = _create_restaurant_with_item(self.client, "R1")
        rv = self.client.get(f"/api/restaurants/{r['restaurant_id']}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["name"], "R1")
        # Menu is on the restaurant record.
        self.assertGreater(len(rv.get_json()["menu"]), 0)

    def test_list_restaurants(self):
        _create_restaurant_with_item(self.client, "A")
        _create_restaurant_with_item(self.client, "B")
        rv = self.client.get("/api/restaurants")
        self.assertEqual(rv.status_code, 200)
        names = [r["name"] for r in rv.get_json()["restaurants"]]
        self.assertIn("A", names)
        self.assertIn("B", names)

    def test_invalid_latlng_returns_400(self):
        rv = self.client.post(
            "/api/restaurants",
            data=json.dumps(
                {"name": "x", "address": "a", "lat": 200.0, "lng": 0.0}
            ),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 400)

    # ---- drivers ----

    def test_create_and_list_drivers(self):
        _create_driver(self.client, "D1")
        _create_driver(self.client, "D2")
        rv = self.client.get("/api/drivers")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.get_json()["drivers"]), 2)

    # ---- orders: placement ----

    def test_place_order_returns_placed(self):
        r, item = _create_restaurant_with_item(self.client)
        driver = _create_driver(self.client)
        rv = self.client.post(
            "/api/orders",
            data=json.dumps(
                {
                    "eater_id": 1,
                    "restaurant_id": r["restaurant_id"],
                    "items": [{"menu_item_id": item["item_id"], "qty": 2}],
                    "address": "home",
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 201)
        o = rv.get_json()
        self.assertEqual(o["status"], PLACED)
        self.assertEqual(o["subtotal_cents"], 2400)
        self.assertEqual(o["suggested_driver_id"], driver["driver_id"])

    def test_place_order_unknown_restaurant_400(self):
        rv = self.client.post(
            "/api/orders",
            data=json.dumps(
                {
                    "eater_id": 1,
                    "restaurant_id": 999_999,
                    "items": [{"menu_item_id": 1, "qty": 1}],
                    "address": "x",
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 400)

    # ---- state transitions ----

    def test_full_lifecycle(self):
        r, item = _create_restaurant_with_item(self.client)
        driver = _create_driver(self.client)
        # Place.
        o = self.client.post(
            "/api/orders",
            data=json.dumps(
                {
                    "eater_id": 1,
                    "restaurant_id": r["restaurant_id"],
                    "items": [{"menu_item_id": item["item_id"], "qty": 1}],
                    "address": "x",
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ),
            content_type="application/json",
        ).get_json()
        # Accept.
        rv = self.client.post(
            f"/api/orders/{o['order_id']}/accept",
            data=json.dumps({"driver_id": driver["driver_id"]}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], ACCEPTED)
        # Picked up.
        rv = self.client.post(
            f"/api/orders/{o['order_id']}/status",
            data=json.dumps({"status": PICKED_UP, "by": str(driver["driver_id"])}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], PICKED_UP)
        # Delivered.
        rv = self.client.post(
            f"/api/orders/{o['order_id']}/status",
            data=json.dumps({"status": DELIVERED, "by": str(driver["driver_id"])}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], DELIVERED)

    def test_invalid_transition_returns_409(self):
        r, item = _create_restaurant_with_item(self.client)
        driver = _create_driver(self.client)
        o = self.client.post(
            "/api/orders",
            data=json.dumps(
                {
                    "eater_id": 1,
                    "restaurant_id": r["restaurant_id"],
                    "items": [{"menu_item_id": item["item_id"], "qty": 1}],
                    "address": "x",
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ),
            content_type="application/json",
        ).get_json()
        # PICKED_UP before ACCEPTED.
        rv = self.client.post(
            f"/api/orders/{o['order_id']}/status",
            data=json.dumps({"status": PICKED_UP, "by": "x"}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 409)

    def test_cancel_from_placed(self):
        r, item = _create_restaurant_with_item(self.client)
        o = self.client.post(
            "/api/orders",
            data=json.dumps(
                {
                    "eater_id": 1,
                    "restaurant_id": r["restaurant_id"],
                    "items": [{"menu_item_id": item["item_id"], "qty": 1}],
                    "address": "x",
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ),
            content_type="application/json",
        ).get_json()
        rv = self.client.post(
            f"/api/orders/{o['order_id']}/status",
            data=json.dumps({"status": CANCELLED, "by": "1"}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], CANCELLED)

    def test_list_orders_by_state(self):
        r, item = _create_restaurant_with_item(self.client)
        for i in range(3):
            self.client.post(
                "/api/orders",
                data=json.dumps(
                    {
                        "eater_id": i + 1,
                        "restaurant_id": r["restaurant_id"],
                        "items": [{"menu_item_id": item["item_id"], "qty": 1}],
                        "address": "x",
                        "lat": 0.0,
                        "lng": 0.0,
                    }
                ),
                content_type="application/json",
            )
        rv = self.client.get(f"/api/orders?state={PLACED}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.get_json()["orders"]), 3)
        rv = self.client.get(f"/api/orders?state={DELIVERED}")
        self.assertEqual(rv.get_json()["orders"], [])

    # ---- health & metrics ----

    def test_health(self):
        rv = self.client.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()["ok"])

    def test_metrics_text(self):
        rv = self.client.get("/metrics")
        self.assertEqual(rv.status_code, 200)
        body = rv.get_data(as_text=True)
        self.assertIn("orders_total", body)
        self.assertIn("transition_latency_ms", body)

    def test_index(self):
        rv = self.client.get("/")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["service"], "uber_eats")


if __name__ == "__main__":
    unittest.main()
