"""Tests for the Parking Garage service.

Headline test: many concurrent check-ins all get distinct spots, and
the per-floor free count is accurate afterwards.
"""

from __future__ import annotations

import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    GarageFull,
    ParkingGarageService,
    TicketAlreadyClosed,
    TicketNotFound,
)


class ParkingGarageServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = ParkingGarageService(floors=3, spots_per_floor=10)

    # ---- basic API ----------------------------------------------------

    def test_checkin_returns_closest_spot(self):
        s = self.svc.checkin(vehicle_id=1)
        # Closest to entry = floor 1, lowest number.
        self.assertEqual(s["floor"], 1)
        self.assertEqual(s["spot_id"], "F1-S001")
        self.assertEqual(s["type"], "standard")

    def test_checkin_increments_free_decrement(self):
        before = self.svc.availability()["per_floor"][1]
        self.svc.checkin(vehicle_id=1)
        after = self.svc.availability()["per_floor"][1]
        self.assertEqual(after, before - 1)

    def test_checkout_releases_spot(self):
        s = self.svc.checkin(vehicle_id=1)
        before = self.svc.availability()["per_floor"][1]
        out = self.svc.checkout(s["ticket_id"])
        after = self.svc.availability()["per_floor"][1]
        self.assertEqual(after, before + 1)
        self.assertGreaterEqual(out["fee_cents"], 0)
        self.assertGreaterEqual(out["duration_seconds"], 0)
        # Spot is free again
        all_spots = {sp["spot_id"]: sp for sp in self.svc.list_spots()}
        self.assertEqual(all_spots[s["spot_id"]]["status"], "free")

    def test_checkout_unknown_ticket_raises(self):
        with self.assertRaises(TicketNotFound):
            self.svc.checkout(99999999)

    def test_double_checkout_raises(self):
        s = self.svc.checkin(vehicle_id=1)
        self.svc.checkout(s["ticket_id"])
        with self.assertRaises(TicketAlreadyClosed):
            self.svc.checkout(s["ticket_id"])

    def test_preferred_type_honored(self):
        # Floor 1 spots: 1-4 standard, 5-7 compact, 8-10 ev.
        s = self.svc.checkin(vehicle_id=1, preferred_type="ev")
        # First free EV on floor 1 is S008.
        self.assertEqual(s["spot_id"], "F1-S008")
        self.assertEqual(s["type"], "ev")

    def test_garage_full_raises(self):
        small = ParkingGarageService(floors=1, spots_per_floor=3)
        small.checkin(vehicle_id=1)
        small.checkin(vehicle_id=2)
        small.checkin(vehicle_id=3)
        with self.assertRaises(GarageFull):
            small.checkin(vehicle_id=4)

    def test_availability_reflects_state(self):
        a = self.svc.availability()
        self.assertEqual(a["total_free"], 30)
        self.assertEqual(a["total_capacity"], 30)
        self.svc.checkin(vehicle_id=1)
        b = self.svc.availability()
        self.assertEqual(b["total_free"], 29)

    def test_checkout_to_empty_then_refill(self):
        s = self.svc.checkin(vehicle_id=1)
        self.svc.checkout(s["ticket_id"])
        s2 = self.svc.checkin(vehicle_id=2)
        # Same spot — closest to entry.
        self.assertEqual(s2["spot_id"], s["spot_id"])

    # ---- concurrency: the headline test -------------------------------

    def test_concurrent_checkin_all_distinct_spots(self):
        n = 20
        sessions: list[dict] = []
        failures: list[Exception] = []
        sessions_lock = threading.Lock()
        start = threading.Event()

        def attempt(uid: int) -> None:
            start.wait()
            try:
                s = self.svc.checkin(vehicle_id=uid)
                with sessions_lock:
                    sessions.append(s)
            except Exception as e:
                with sessions_lock:
                    failures.append(e)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(failures), 0, f"unexpected failures: {failures}")
        self.assertEqual(len(sessions), n)
        # All distinct spots
        spot_ids = [s["spot_id"] for s in sessions]
        self.assertEqual(len(set(spot_ids)), n, "duplicate spot assignment!")
        # Spots are all valid
        valid = {sp["spot_id"] for sp in self.svc.list_spots()}
        for sid in spot_ids:
            self.assertIn(sid, valid)
        # All on floor 1 (closest to entry, and we have capacity)
        floors = {s["floor"] for s in sessions}
        self.assertEqual(floors, {1})
        # Per-floor free count matches.
        self.assertEqual(self.svc.availability()["per_floor"][1], 30 - n)
        self.assertEqual(self.svc.checkin_total, n)

    def test_concurrent_checkin_overflow_to_upper_floors(self):
        # Use a small garage to force overflow.
        small = ParkingGarageService(floors=2, spots_per_floor=2)
        n = 6  # 2 + 2 + 2 retries
        sessions: list[dict] = []
        failures: list[Exception] = []
        sessions_lock = threading.Lock()
        start = threading.Event()

        def attempt(uid: int) -> None:
            start.wait()
            try:
                s = small.checkin(vehicle_id=uid)
                with sessions_lock:
                    sessions.append(s)
            except Exception as e:
                with sessions_lock:
                    failures.append(e)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(sessions), 4)
        self.assertEqual(len(failures), 2)
        for f in failures:
            self.assertIsInstance(f, GarageFull)
        spot_ids = [s["spot_id"] for s in sessions]
        self.assertEqual(len(set(spot_ids)), 4)

    def test_concurrent_checkin_and_checkout_consistency(self):
        # Mix: 4 checkins, then immediate checkouts, then 4 more.
        n = 4
        sessions: list[dict] = []
        sessions_lock = threading.Lock()
        start = threading.Event()

        def do_checkin(uid: int) -> None:
            start.wait()
            s = self.svc.checkin(vehicle_id=uid)
            with sessions_lock:
                sessions.append(s)

        threads = [threading.Thread(target=do_checkin, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(sessions), n)

        for s in sessions:
            self.svc.checkout(s["ticket_id"])

        # Now do another batch.
        sessions2: list[dict] = []
        sessions2_lock = threading.Lock()
        start2 = threading.Event()

        def do_checkin2(uid: int) -> None:
            start2.wait()
            s = self.svc.checkin(vehicle_id=uid)
            with sessions2_lock:
                sessions2.append(s)

        threads2 = [threading.Thread(target=do_checkin2, args=(i,)) for i in range(n)]
        for t in threads2:
            t.start()
        start2.set()
        for t in threads2:
            t.join(timeout=5)
        self.assertEqual(len(sessions2), n)
        # All distinct
        ids1 = {s["spot_id"] for s in sessions}
        ids2 = {s["spot_id"] for s in sessions2}
        self.assertEqual(len(ids1), n)
        self.assertEqual(len(ids2), n)


if __name__ == "__main__":
    unittest.main()
