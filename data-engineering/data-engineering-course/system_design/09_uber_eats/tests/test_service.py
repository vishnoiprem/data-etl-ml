"""Unit tests for UberEatsService.

Run with:
    cd system_design
    python -m unittest 09_uber_eats.tests.test_service -v
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    ACCEPTED,
    CANCELLED,
    DELIVERED,
    InvalidTransitionError,
    PICKED_UP,
    PLACED,
    UberEatsService,
)


class TestRestaurants(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()

    def test_create_and_get(self):
        r = self.svc.create_restaurant("R1", "addr", 37.0, -122.0)
        self.assertTrue(r.restaurant_id)
        loaded = self.svc.get_restaurant(r.restaurant_id)
        self.assertEqual(loaded.name, "R1")

    def test_invalid_lat_lng(self):
        with self.assertRaises(ValueError):
            self.svc.create_restaurant("x", "addr", 200.0, 0.0)
        with self.assertRaises(ValueError):
            self.svc.create_restaurant("x", "addr", 0.0, 200.0)

    def test_add_menu_item(self):
        r = self.svc.create_restaurant("R1", "addr", 37.0, -122.0)
        i = self.svc.add_menu_item(r.restaurant_id, "Pizza", 1200)
        self.assertEqual(i.price_cents, 1200)
        r2 = self.svc.get_restaurant(r.restaurant_id)
        self.assertIn(str(i.item_id), r2.menu)

    def test_add_menu_to_unknown_restaurant(self):
        with self.assertRaises(ValueError):
            self.svc.add_menu_item(999_999, "x", 100)

    def test_invalid_price(self):
        r = self.svc.create_restaurant("R1", "addr", 37.0, -122.0)
        with self.assertRaises(ValueError):
            self.svc.add_menu_item(r.restaurant_id, "x", 0)
        with self.assertRaises(ValueError):
            self.svc.add_menu_item(r.restaurant_id, "x", -1)


class TestDrivers(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()

    def test_create_and_get(self):
        d = self.svc.create_driver("D1", 37.0, -122.0)
        self.assertTrue(d.driver_id)
        self.assertTrue(d.available)

    def test_set_availability(self):
        d = self.svc.create_driver("D1", 37.0, -122.0)
        self.svc.set_driver_available(d.driver_id, False)
        d2 = self.svc.get_driver(d.driver_id)
        self.assertFalse(d2.available)


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()
        # Restaurant at origin.
        self.r = self.svc.create_restaurant("R", "addr", 0.0, 0.0)
        # Two drivers — one near, one far.
        self.d_near = self.svc.create_driver("near", 0.001, 0.001)
        self.d_far = self.svc.create_driver("far", 10.0, 10.0)
        # A driver who's not available.
        self.d_busy = self.svc.create_driver(
            "busy", 0.0, 0.0, available=False
        )

    def test_nearest_driver_picks_closest(self):
        best = self.svc.nearest_driver((0.0, 0.0))
        self.assertIsNotNone(best)
        self.assertEqual(best.driver_id, self.d_near.driver_id)

    def test_nearest_driver_skips_unavailable(self):
        # Mark the near driver unavailable; the only remaining
        # available is the far one.
        self.svc.set_driver_available(self.d_near.driver_id, False)
        best = self.svc.nearest_driver((0.0, 0.0))
        self.assertEqual(best.driver_id, self.d_far.driver_id)

    def test_nearest_driver_no_one_available(self):
        # Mark all available drivers off.
        self.svc.set_driver_available(self.d_near.driver_id, False)
        self.svc.set_driver_available(self.d_far.driver_id, False)
        self.assertIsNone(self.svc.nearest_driver((0.0, 0.0)))


class TestOrderPlacement(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()
        self.r = self.svc.create_restaurant("R", "addr", 0.0, 0.0)
        self.pizza = self.svc.add_menu_item(self.r.restaurant_id, "Pizza", 1200)
        self.salad = self.svc.add_menu_item(self.r.restaurant_id, "Salad", 800)
        self.driver = self.svc.create_driver("D", 0.001, 0.001)

    def test_place_order_prices_items(self):
        o = self.svc.place_order(
            eater_id=1,
            restaurant_id=self.r.restaurant_id,
            items=[
                {"menu_item_id": self.pizza.item_id, "qty": 2},
                {"menu_item_id": self.salad.item_id, "qty": 1},
            ],
            address="home",
            lat=0.0,
            lng=0.0,
        )
        # 2*1200 + 1*800 = 3200
        self.assertEqual(o.subtotal_cents, 3200)
        self.assertEqual(len(o.items), 2)
        self.assertEqual(o.status, PLACED)
        self.assertEqual(o.suggested_driver_id, self.driver.driver_id)

    def test_place_order_unknown_restaurant_raises(self):
        with self.assertRaises(ValueError):
            self.svc.place_order(
                eater_id=1,
                restaurant_id=999_999,
                items=[{"menu_item_id": 1, "qty": 1}],
                address="x",
                lat=0.0,
                lng=0.0,
            )

    def test_place_order_unknown_menu_item_raises(self):
        with self.assertRaises(ValueError):
            self.svc.place_order(
                eater_id=1,
                restaurant_id=self.r.restaurant_id,
                items=[{"menu_item_id": 999_999, "qty": 1}],
                address="x",
                lat=0.0,
                lng=0.0,
            )

    def test_place_order_empty_items_rejected(self):
        with self.assertRaises(ValueError):
            self.svc.place_order(
                eater_id=1,
                restaurant_id=self.r.restaurant_id,
                items=[],
                address="x",
                lat=0.0,
                lng=0.0,
            )

    def test_price_snapshot_is_independent_of_menu_edits(self):
        # Order placed, then we "raise" the price of the menu item.
        o = self.svc.place_order(
            eater_id=1,
            restaurant_id=self.r.restaurant_id,
            items=[{"menu_item_id": self.pizza.item_id, "qty": 1}],
            address="x",
            lat=0.0,
            lng=0.0,
        )
        # Replace the menu item in place.
        r = self.svc.get_restaurant(self.r.restaurant_id)
        r.menu[str(self.pizza.item_id)]["price_cents"] = 9999
        self.svc.store.set(self.svc._k_rest(r.restaurant_id), r.to_dict())
        # Order subtotal is unchanged.
        o2 = self.svc.get_order(o.order_id)
        self.assertEqual(o2.subtotal_cents, 1200)
        self.assertEqual(o2.items[0]["price_cents"], 1200)


class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.svc = UberEatsService()
        self.r = self.svc.create_restaurant("R", "addr", 0.0, 0.0)
        self.pizza = self.svc.add_menu_item(self.r.restaurant_id, "P", 1000)
        self.driver = self.svc.create_driver("D", 0.001, 0.001)
        self.order = self.svc.place_order(
            eater_id=1,
            restaurant_id=self.r.restaurant_id,
            items=[{"menu_item_id": self.pizza.item_id, "qty": 1}],
            address="x",
            lat=0.0,
            lng=0.0,
        )

    def test_full_happy_path(self):
        o = self.svc.accept_order(self.order.order_id, self.driver.driver_id)
        self.assertEqual(o.status, ACCEPTED)
        self.assertEqual(o.driver_id, self.driver.driver_id)

        o = self.svc.transition(o.order_id, PICKED_UP, by=str(self.driver.driver_id))
        self.assertEqual(o.status, PICKED_UP)

        o = self.svc.transition(o.order_id, DELIVERED, by=str(self.driver.driver_id))
        self.assertEqual(o.status, DELIVERED)

        # History records every transition.
        history_statuses = [h["status"] for h in o.history]
        self.assertEqual(
            history_statuses, [PLACED, ACCEPTED, PICKED_UP, DELIVERED]
        )

    def test_cancel_from_placed(self):
        o = self.svc.transition(self.order.order_id, CANCELLED, by="1")
        self.assertEqual(o.status, CANCELLED)

    def test_cancel_from_accepted(self):
        self.svc.accept_order(self.order.order_id, self.driver.driver_id)
        o = self.svc.transition(self.order.order_id, CANCELLED, by="ops")
        self.assertEqual(o.status, CANCELLED)

    def test_pickup_before_accept_rejected(self):
        with self.assertRaises(InvalidTransitionError):
            self.svc.transition(self.order.order_id, PICKED_UP, by="x")

    def test_deliver_before_pickup_rejected(self):
        self.svc.accept_order(self.order.order_id, self.driver.driver_id)
        with self.assertRaises(InvalidTransitionError):
            self.svc.transition(self.order.order_id, DELIVERED, by="x")

    def test_double_accept_rejected(self):
        self.svc.accept_order(self.order.order_id, self.driver.driver_id)
        with self.assertRaises(InvalidTransitionError):
            self.svc.accept_order(self.order.order_id, self.driver.driver_id)

    def test_terminal_states_are_terminal(self):
        # DELIVERED is terminal.
        self.svc.accept_order(self.order.order_id, self.driver.driver_id)
        self.svc.transition(self.order.order_id, PICKED_UP, by="x")
        self.svc.transition(self.order.order_id, DELIVERED, by="x")
        for s in [PLACED, ACCEPTED, PICKED_UP, CANCELLED, DELIVERED]:
            with self.assertRaises(InvalidTransitionError):
                self.svc.transition(self.order.order_id, s, by="x")

    def test_accept_with_unavailable_driver_rejected(self):
        self.svc.set_driver_available(self.driver.driver_id, False)
        with self.assertRaises(ValueError):
            self.svc.accept_order(self.order.order_id, self.driver.driver_id)

    def test_accept_wrong_driver_rejected(self):
        # Create a second driver, who is not the suggested one.
        other = self.svc.create_driver("Other", 0.001, 0.001)
        with self.assertRaises(ValueError):
            self.svc.accept_order(self.order.order_id, other.driver_id)


class TestStats(unittest.TestCase):
    def test_stats_counts_by_state(self):
        svc = UberEatsService()
        r = svc.create_restaurant("R", "addr", 0.0, 0.0)
        i = svc.add_menu_item(r.restaurant_id, "P", 100)
        d = svc.create_driver("D", 0.001, 0.001)
        o = svc.place_order(
            eater_id=1, restaurant_id=r.restaurant_id,
            items=[{"menu_item_id": i.item_id, "qty": 1}],
            address="x", lat=0.0, lng=0.0,
        )
        s = svc.stats()
        self.assertEqual(s["restaurants"], 1)
        self.assertEqual(s["drivers"], 1)
        self.assertEqual(s["orders"], 1)
        self.assertEqual(s["orders_by_state"][PLACED], 1)


if __name__ == "__main__":
    unittest.main()
