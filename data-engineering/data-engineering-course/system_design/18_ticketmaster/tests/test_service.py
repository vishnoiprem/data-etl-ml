"""Tests for the Ticketmaster service.

Includes the core concurrency test: many threads racing for the same
seat — exactly one wins, every other gets SeatUnavailable.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    HoldExpired,
    HoldTokenMismatch,
    SeatNotFound,
    SeatUnavailable,
    TicketmasterService,
)


class TicketmasterServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = TicketmasterService(hold_ttl_seconds=60.0)

    def tearDown(self) -> None:
        self.svc.stop()

    # ---- basic API ----------------------------------------------------

    def test_create_event_seats(self):
        ev = self.svc.create_event("Concert", rows=3, cols=4)
        seats = self.svc.list_seats(ev["event_id"])
        self.assertEqual(len(seats), 12)
        for s in seats:
            self.assertEqual(s["status"], "available")

    def test_hold_purchase_flow(self):
        ev = self.svc.create_event("Show", rows=2, cols=2)["event_id"]
        h = self.svc.hold(ev, "A-1", user_id=1)
        self.assertGreater(h["hold_token"], 0)
        seat = self.svc.get_seat(ev, "A-1")
        self.assertEqual(seat["status"], "held")
        self.assertEqual(seat["held_by"], 1)
        ticket = self.svc.purchase(ev, "A-1", user_id=1, hold_token=h["hold_token"])
        self.assertGreater(ticket["ticket_id"], 0)
        seat = self.svc.get_seat(ev, "A-1")
        self.assertEqual(seat["status"], "sold")

    def test_hold_then_release(self):
        ev = self.svc.create_event("Show", rows=1, cols=1)["event_id"]
        h = self.svc.hold(ev, "A-1", user_id=1)
        self.svc.release(ev, "A-1", user_id=1, hold_token=h["hold_token"])
        seat = self.svc.get_seat(ev, "A-1")
        self.assertEqual(seat["status"], "available")

    def test_purchase_with_wrong_token(self):
        ev = self.svc.create_event("Show", rows=1, cols=1)["event_id"]
        h = self.svc.hold(ev, "A-1", user_id=1)
        with self.assertRaises(HoldTokenMismatch):
            self.svc.purchase(ev, "A-1", user_id=1, hold_token=h["hold_token"] + 1)

    def test_hold_then_purchase_again_after_release(self):
        ev = self.svc.create_event("Show", rows=1, cols=1)["event_id"]
        h1 = self.svc.hold(ev, "A-1", user_id=1)
        self.svc.release(ev, "A-1", user_id=1, hold_token=h1["hold_token"])
        h2 = self.svc.hold(ev, "A-1", user_id=2)
        self.assertNotEqual(h1["hold_token"], h2["hold_token"])

    def test_unknown_event_raises(self):
        with self.assertRaises(SeatNotFound):
            self.svc.hold(999999, "A-1", user_id=1)

    def test_hold_taken_seat_conflicts(self):
        ev = self.svc.create_event("Show", rows=1, cols=1)["event_id"]
        self.svc.hold(ev, "A-1", user_id=1)
        with self.assertRaises(SeatUnavailable):
            self.svc.hold(ev, "A-1", user_id=2)

    def test_purchase_after_expiry(self):
        # Use a 1-second TTL so we can wait it out.
        svc = TicketmasterService(hold_ttl_seconds=0.2, sweeper_interval=10.0)
        try:
            ev = svc.create_event("Show", rows=1, cols=1)["event_id"]
            h = svc.hold(ev, "A-1", user_id=1)
            time.sleep(0.3)
            with self.assertRaises(HoldExpired):
                svc.purchase(ev, "A-1", user_id=1, hold_token=h["hold_token"])
        finally:
            svc.stop()

    # ---- concurrency: the headline test -------------------------------

    def test_concurrent_holds_only_one_wins(self):
        ev = self.svc.create_event("Race", rows=1, cols=1)["event_id"]
        n = 20
        winners: list[int] = []
        losers: list[Exception] = []
        winners_lock = threading.Lock()
        start = threading.Event()

        def attempt(uid: int) -> None:
            start.wait()
            try:
                res = self.svc.hold(ev, "A-1", user_id=uid)
                with winners_lock:
                    winners.append(res["user_id"])
            except SeatUnavailable as e:
                with winners_lock:
                    losers.append(e)
            except Exception as e:  # pragma: no cover
                with winners_lock:
                    losers.append(e)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        start.set()  # release all simultaneously
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(winners), 1, f"expected 1 winner, got {len(winners)}")
        self.assertEqual(len(losers), n - 1)
        seat = self.svc.get_seat(ev, "A-1")
        self.assertEqual(seat["status"], "held")
        self.assertEqual(seat["held_by"], winners[0])
        self.assertEqual(self.svc.hold_wins, 1)
        self.assertEqual(self.svc.hold_conflicts, n - 1)

    def test_concurrent_purchase_only_one_succeeds(self):
        """A more subtle race: many threads all hold+attempt purchase.

        Only one of them should be able to *hold* the seat in the first
        place, so the others never even reach purchase.
        """
        ev = self.svc.create_event("Race", rows=1, cols=1)["event_id"]
        successes: list[dict] = []
        conflicts: list[Exception] = []
        successes_lock = threading.Lock()
        start = threading.Event()

        def worker(uid: int) -> None:
            start.wait()
            try:
                h = self.svc.hold(ev, "A-1", user_id=uid)
                ticket = self.svc.purchase(
                    ev, "A-1", user_id=uid, hold_token=h["hold_token"]
                )
                with successes_lock:
                    successes.append(ticket)
            except Exception as e:
                with successes_lock:
                    conflicts.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        start.set()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(conflicts), 14)
        seat = self.svc.get_seat(ev, "A-1")
        self.assertEqual(seat["status"], "sold")


if __name__ == "__main__":
    unittest.main()
