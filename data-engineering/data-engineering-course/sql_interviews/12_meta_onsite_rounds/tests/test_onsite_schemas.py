"""Tests for the 5 Meta DE data-modeling schemas.

Loads sql_interviews/12_meta_onsite_rounds/code/meta_onsite_schemas.sql
into a fresh in-memory SQLite, then asserts the canonical answer
query for each of the 5 most-asked questions.

Pairs with sql_interviews/12_meta_onsite_rounds/design/04_concrete_solutions.md.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQL_DIR = HERE.parent / "code"
COURSE_ROOT = HERE.parent.parent.parent

sys.path.insert(0, str(COURSE_ROOT))

from common import QueryRunner  # type: ignore  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _fresh_runner() -> QueryRunner:
    q = QueryRunner(":memory:")
    raw = _read(SQL_DIR / "meta_onsite_schemas.sql")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    cleaned = "\n".join(lines)
    for stmt in cleaned.split(";"):
        s = stmt.strip()
        if s:
            q.execute(s)
    return q


class TestQ1ReelsStarSchema(unittest.TestCase):
    """The SCD Type 2 dim is the killer dim. Re-run historical metrics
    by joining fct to the version that was live at the time.
    """

    def test_current_algorithm_version(self):
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT algorithm_name FROM dim_algorithm_version
            WHERE  is_current = 1
        """)
        self.assertEqual(out[0]['algorithm_name'], 'reels_v3')

    def test_reel_view_count(self):
        qr = _fresh_runner()
        out = qr.query_all("SELECT COUNT(*) AS n FROM fct_reel_view")
        self.assertEqual(out[0]['n'], 6)

    def test_bridge_table(self):
        qr = _fresh_runner()
        out = qr.query_all("SELECT COUNT(*) AS n FROM reel_hashtag_bridge")
        self.assertEqual(out[0]['n'], 5)


class TestQ2CrossPlatformIdentity(unittest.TestCase):
    def test_user_1_resolves_to_2_platforms(self):
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT platform FROM user_identity_bridge
            WHERE  unified_user_id = 1
            ORDER BY platform
        """)
        self.assertEqual([r['platform'] for r in out], ['IG', 'WA'])


class TestQ3AdsAuctionTimeTravel(unittest.TestCase):
    def test_3_auctions_won_2_lost(self):
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT won_flag, COUNT(*) AS n
            FROM   fct_auction_event
            GROUP BY won_flag
            ORDER BY won_flag
        """)
        flags = {r['won_flag']: r['n'] for r in out}
        self.assertEqual(flags[0], 2)  # lost
        self.assertEqual(flags[1], 3)  # won

    def test_impression_revenue_sum(self):
        qr = _fresh_runner()
        out = qr.query_all("SELECT SUM(revenue_cents) AS s FROM fct_impression")
        self.assertEqual(out[0]['s'], 730)


class TestQ4RideShareFunnel(unittest.TestCase):
    def test_completed_trip_count(self):
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT COUNT(*) AS n FROM fct_trip
            WHERE  status = 'completed'
        """)
        self.assertEqual(out[0]['n'], 2)

    def test_event_count_per_trip(self):
        """Trip 1: 3 events (request, pickup, dropoff). Trip 2: 3. Trip 3: 1."""
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT trip_id, COUNT(*) AS n
            FROM   fct_trip_event
            GROUP BY trip_id
            ORDER BY trip_id
        """)
        self.assertEqual([r['n'] for r in out], [3, 3, 1])


class TestQ5MetricInvestigation(unittest.TestCase):
    def test_drop_is_localized_to_segment_1(self):
        """The like_rate for segment 1 dropped on Feb 14 (0.42 -> 0.30).
        Segment 2 is stable around 0.40. So the drop is localized to
        the (US, mobile) segment, not all users.
        """
        qr = _fresh_runner()
        out = qr.query_all("""
            SELECT time_bucket, segment_id, value
            FROM   fct_metric_value
            WHERE  metric_id = 1
            ORDER BY segment_id, time_bucket
        """)
        seg1 = [r['value'] for r in out if r['segment_id'] == 1]
        seg2 = [r['value'] for r in out if r['segment_id'] == 2]
        # seg1: 0.42, 0.41, 0.30, 0.28  -> drops
        self.assertGreater(seg1[0], seg1[2])
        # seg2: 0.40, 0.41, 0.40, 0.41  -> stable
        self.assertAlmostEqual(seg2[0], seg2[2], places=2)


if __name__ == "__main__":
    unittest.main()
