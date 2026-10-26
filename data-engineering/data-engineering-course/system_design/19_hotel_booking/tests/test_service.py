"""Tests for the Hotel Booking service.

Headline test: two concurrent bookings of overlapping date ranges
on the same room — only one wins.
"""

from __future__ import annotations

import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    HotelBookingService,
    InvalidDateRange,
    NotAuthorized,
    RoomNotFound,
    RoomUnavailable,
)


class HotelBookingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = HotelBookingService()
        self.hotel = self.svc.create_hotel("Inn", "Berkeley")
        self.room = self.svc.create_room(self.hotel["hotel_id"], "101", 2, 15_000)
        self.rid = self.room["room_id"]

    # ---- basic API ----------------------------------------------------

    def test_create_hotel_and_room(self):
        self.assertEqual(self.hotel["name"], "Inn")
        self.assertEqual(self.room["room_number"], "101")
        self.assertEqual(self.svc.list_hotels()[0]["hotel_id"], self.hotel["hotel_id"])

    def test_book_basic(self):
        b = self.svc.book(
            self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-12"
        )
        self.assertEqual(b["status"], "active")
        self.assertEqual(b["check_in"], "2026-10-10")
        self.assertEqual(b["check_out"], "2026-10-12")

    def test_book_overlap_rejected(self):
        self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-15")
        with self.assertRaises(RoomUnavailable) as ctx:
            self.svc.book(self.rid, user_id=2, check_in="2026-10-12", check_out="2026-10-14")
        self.assertIn(ctx.exception.conflicts[0], [b for b in [1]])

    def test_half_open_range_does_not_overlap(self):
        # Booking ends on 10-15; another starts 10-15 — should NOT conflict.
        self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-15")
        b2 = self.svc.book(self.rid, user_id=2, check_in="2026-10-15", check_out="2026-10-18")
        self.assertEqual(b2["status"], "active")

    def test_availability_with_conflicts(self):
        b = self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-12")
        res = self.svc.availability(self.rid, "2026-10-09", "2026-10-20")
        self.assertFalse(res["available"])
        self.assertIn(b["booking_id"], res["conflicts"])

    def test_availability_disjoint(self):
        b = self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-12")
        res = self.svc.availability(self.rid, "2026-11-01", "2026-11-05")
        self.assertTrue(res["available"])
        self.assertNotIn(b["booking_id"], res["conflicts"])

    def test_cancel_frees_dates(self):
        b = self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-12")
        self.svc.cancel(b["booking_id"], user_id=1)
        # Now we can book again.
        b2 = self.svc.book(self.rid, user_id=2, check_in="2026-10-10", check_out="2026-10-12")
        self.assertEqual(b2["status"], "active")

    def test_cancel_by_wrong_user_rejected(self):
        b = self.svc.book(self.rid, user_id=1, check_in="2026-10-10", check_out="2026-10-12")
        with self.assertRaises(NotAuthorized):
            self.svc.cancel(b["booking_id"], user_id=99)

    def test_invalid_date_range_rejected(self):
        with self.assertRaises(InvalidDateRange):
            self.svc.book(self.rid, user_id=1, check_in="2026-10-12", check_out="2026-10-10")
        with self.assertRaises(InvalidDateRange):
            self.svc.book(self.rid, user_id=1, check_in="bad", check_out="2026-10-10")

    def test_unknown_room_raises(self):
        with self.assertRaises(RoomNotFound):
            self.svc.book(999999, user_id=1, check_in="2026-10-10", check_out="2026-10-12")

    # ---- concurrency: the headline test -------------------------------

    def test_concurrent_overlapping_bookings_only_one_wins(self):
        # All threads try to book the same overlapping range on the same room.
        n = 20
        successes: list[dict] = []
        conflicts: list[Exception] = []
        successes_lock = threading.Lock()
        start = threading.Event()

        def attempt(uid: int) -> None:
            start.wait()
            try:
                b = self.svc.book(
                    self.rid,
                    user_id=uid,
                    check_in="2026-10-10",
                    check_out="2026-10-15",
                )
                with successes_lock:
                    successes.append(b)
            except Exception as e:
                with successes_lock:
                    conflicts.append(e)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(successes), 1, f"expected 1 success, got {len(successes)}")
        self.assertEqual(len(conflicts), n - 1)
        for c in conflicts:
            self.assertIsInstance(c, RoomUnavailable)
        self.assertEqual(self.svc.book_wins, 1)
        self.assertEqual(self.svc.book_conflicts, n - 1)

    def test_concurrent_disjoint_bookings_all_succeed(self):
        # Sanity: 5 users, 5 non-overlapping ranges, all succeed.
        ranges = [
            ("2026-10-01", "2026-10-03"),
            ("2026-10-04", "2026-10-06"),
            ("2026-10-07", "2026-10-09"),
            ("2026-10-10", "2026-10-12"),
            ("2026-10-13", "2026-10-15"),
        ]
        successes: list[dict] = []
        conflicts: list[Exception] = []
        successes_lock = threading.Lock()
        start = threading.Event()

        def attempt(uid: int, ci: str, co: str) -> None:
            start.wait()
            try:
                b = self.svc.book(self.rid, user_id=uid, check_in=ci, check_out=co)
                with successes_lock:
                    successes.append(b)
            except Exception as e:
                with successes_lock:
                    conflicts.append(e)

        threads = [
            threading.Thread(target=attempt, args=(i, ranges[i][0], ranges[i][1]))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(successes), 5)
        self.assertEqual(len(conflicts), 0)

    def test_concurrent_partially_overlapping_mixed(self):
        # Some threads try [10-10, 10-12), some try [10-11, 10-13).
        # Half-open semantics: [10-10, 10-12) and [10-12, 10-14) DO NOT overlap.
        # We use [10-10, 10-12) and [10-11, 10-13) which DO overlap.
        n = 10
        successes: list[dict] = []
        conflicts: list[Exception] = []
        successes_lock = threading.Lock()
        start = threading.Event()

        def attempt_a(uid: int) -> None:
            start.wait()
            try:
                b = self.svc.book(
                    self.rid, user_id=uid, check_in="2026-10-10", check_out="2026-10-12"
                )
                with successes_lock:
                    successes.append(b)
            except Exception as e:
                with successes_lock:
                    conflicts.append(e)

        def attempt_b(uid: int) -> None:
            start.wait()
            try:
                b = self.svc.book(
                    self.rid, user_id=uid + 100, check_in="2026-10-11", check_out="2026-10-13"
                )
                with successes_lock:
                    successes.append(b)
            except Exception as e:
                with successes_lock:
                    conflicts.append(e)

        threads = []
        for i in range(n):
            threads.append(threading.Thread(target=attempt_a, args=(i,)))
            threads.append(threading.Thread(target=attempt_b, args=(i,)))
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        # Exactly one of (a_i, b_i) can win for each i, and there is only one
        # possible winner for the whole set since all ranges overlap each other.
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(conflicts), 2 * n - 1)


if __name__ == "__main__":
    unittest.main()
