"""Tests for the M07 practice solutions.

The tests assert the *invariants* a senior solution
should have:

  * Each fact table has the expected grain (one row
    per the documented event).
  * SCD 2 dims have at least one versioned row.
  * Conformed dims (date, etc.) are shared across
    facts.
  * Aggregations on the fact produce the documented
    values.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

import sys
import unittest
from pathlib import Path

# Make `common` and the local `code/` importable.
HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(COURSE_ROOT))
sys.path.insert(0, str(HERE.parent / "code"))

from common import QueryRunner  # type: ignore

from solutions import build_hospital, build_hotel, build_library  # type: ignore


# ---- library ------------------------------------------------------------


class TestLibrary(unittest.TestCase):
    def test_build_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            tables = build_library(q)
        for expected in [
            "dim_book", "dim_patron", "dim_branch", "dim_date",
            "fact_loans",
        ]:
            self.assertIn(expected, tables)

    def test_fact_loans_grain(self):
        with QueryRunner(":memory:") as q:
            build_library(q)
            rows = q.query_all("SELECT * FROM fact_loans")
        # Three loans seeded.
        self.assertEqual(len(rows), 3)

    def test_patron_scd2_versions(self):
        with QueryRunner(":memory:") as q:
            build_library(q)
            rows = q.query_all(
                "SELECT * FROM dim_patron WHERE patron_id = 101"
            )
        # Alice has two SCD2 versions.
        self.assertEqual(len(rows), 2)
        current = [r for r in rows if r["is_current"] == 1]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["patron_type"], "adult")

    def test_overdue_count_matches_seed(self):
        with QueryRunner(":memory:") as q:
            build_library(q)
            res = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_loans "
                "WHERE days_overdue > 0"
            )
        # Loan 1 was 15 days overdue; loans 2 and 3 not.
        self.assertEqual(res["n"], 1)


# ---- hospital -----------------------------------------------------------


class TestHospital(unittest.TestCase):
    def test_build_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            tables = build_hospital(q)
        for expected in [
            "dim_patient", "dim_ward", "dim_surgeon",
            "dim_procedure_code", "dim_date",
            "fact_admissions", "fact_procedures",
        ]:
            self.assertIn(expected, tables)

    def test_fact_admissions_grain(self):
        with QueryRunner(":memory:") as q:
            build_hospital(q)
            rows = q.query_all("SELECT * FROM fact_admissions")
        # Two admissions seeded.
        self.assertEqual(len(rows), 2)
        # LOS populated for both.
        for r in rows:
            self.assertIsNotNone(r["los_days"])
            self.assertGreater(r["los_days"], 0)

    def test_fact_procedures_grain(self):
        with QueryRunner(":memory:") as q:
            build_hospital(q)
            rows = q.query_all("SELECT * FROM fact_procedures")
        # Two procedures.
        self.assertEqual(len(rows), 2)
        # One has a complication.
        with_comp = [r for r in rows if r["complication_flag"] == 1]
        self.assertEqual(len(with_comp), 1)

    def test_patient_scd2_versions(self):
        with QueryRunner(":memory:") as q:
            build_hospital(q)
            rows = q.query_all(
                "SELECT * FROM dim_patient WHERE patient_id = 1001"
            )
        # Patient 1001 has two SCD2 versions: private then
        # medicare.
        self.assertEqual(len(rows), 2)
        current = [r for r in rows if r["is_current"] == 1]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["insurance_type"], "medicare")

    def test_procedure_links_to_admission(self):
        with QueryRunner(":memory:") as q:
            build_hospital(q)
            # Each procedure must reference a valid admission.
            n = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_procedures p "
                "JOIN fact_admissions a "
                "  ON p.admission_key = a.admission_key"
            )["n"]
        self.assertEqual(n, 2)


# ---- hotel --------------------------------------------------------------


class TestHotel(unittest.TestCase):
    def test_build_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            tables = build_hotel(q)
        for expected in [
            "dim_guest", "dim_hotel", "dim_room_type",
            "dim_channel", "dim_date",
            "fact_reservations", "fact_room_nights",
        ]:
            self.assertIn(expected, tables)

    def test_reservations_grain(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            rows = q.query_all("SELECT * FROM fact_reservations")
        # Three reservations.
        self.assertEqual(len(rows), 3)
        # Two have cancel_date_key NULL, one set.
        cancelled = [r for r in rows if r["cancel_date_key"] is not None]
        self.assertEqual(len(cancelled), 1)
        # Each is 5 nights.
        for r in rows:
            self.assertEqual(r["num_nights"], 5)

    def test_room_nights_total_matches_reservations(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            occupied = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_room_nights "
                "WHERE occupied_flag = 1"
            )["n"]
        # 5 (res 1) + 5 (res 3) = 10 occupied nights.
        self.assertEqual(occupied, 10)

    def test_occupancy_rate(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            res = q.query_one(
                "SELECT "
                "  100.0 * SUM(occupied_flag) / COUNT(*) AS pct "
                "FROM fact_room_nights"
            )
        # 10 occupied / 15 total = 66.67%.
        self.assertAlmostEqual(res["pct"], 66.67, places=1)

    def test_cancellation_count(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            res = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_reservations "
                "WHERE cancel_date_key IS NOT NULL"
            )
        self.assertEqual(res["n"], 1)

    def test_revenue_per_reservation(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            rows = q.query_all(
                "SELECT reservation_key, total_room_revenue "
                "FROM fact_reservations ORDER BY reservation_key"
            )
        # Res 1: 5 * 1000 = 5000.  Res 2: 5 * 200 = 1000.
        # Res 3: 5 * 500 = 2500.
        self.assertAlmostEqual(rows[0]["total_room_revenue"], 5000.0)
        self.assertAlmostEqual(rows[1]["total_room_revenue"], 1000.0)
        self.assertAlmostEqual(rows[2]["total_room_revenue"], 2500.0)

    def test_guest_scd2_versions(self):
        with QueryRunner(":memory:") as q:
            build_hotel(q)
            rows = q.query_all(
                "SELECT * FROM dim_guest WHERE guest_id = 501"
            )
        # Alice has two SCD2 versions.
        self.assertEqual(len(rows), 2)
        current = [r for r in rows if r["is_current"] == 1]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["loyalty_tier"], "gold")


if __name__ == "__main__":
    unittest.main()
