"""Tests for the four fact-table types.

Author: Prem Vishnoi <pvishnoi@avilx.com>
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

from fact_tables import (  # type: ignore
    build_accumulating_snapshot_fact,
    build_factless_fact,
    build_periodic_snapshot_fact,
    build_transactional_fact,
)


class TestTransactional(unittest.TestCase):
    def test_creates_schema(self):
        with QueryRunner(":memory:") as q:
            tables = build_transactional_fact(q)
        for n in ("dim_customer", "dim_product", "dim_date",
                  "fact_sales_transactional"):
            self.assertIn(n, tables)

    def test_fact_has_three_rows(self):
        with QueryRunner(":memory:") as q:
            build_transactional_fact(q)
            n = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_sales_transactional"
            )["n"]
        self.assertEqual(n, 3)

    def test_measures_are_additive(self):
        with QueryRunner(":memory:") as q:
            build_transactional_fact(q)
            row = q.query_one(
                "SELECT SUM(net_amount) AS total "
                "FROM fact_sales_transactional"
            )
        # 100 + 70 + 150 = 320
        self.assertAlmostEqual(row["total"], 320.0, places=2)


class TestPeriodicSnapshot(unittest.TestCase):
    def test_creates_schema(self):
        with QueryRunner(":memory:") as q:
            tables = build_periodic_snapshot_fact(q)
        for n in ("dim_customer", "dim_plan", "dim_date",
                  "fact_subscription_monthly_snapshot"):
            self.assertIn(n, tables)

    def test_one_row_per_customer_per_period(self):
        with QueryRunner(":memory:") as q:
            build_periodic_snapshot_fact(q)
            # 3 customers × 3 months = 9, but Bob and Carol
            # don't exist in Jan (they sign up later).
            # In our fixture, every customer has at least one
            # row, so 7 rows.
            n = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_subscription_monthly_snapshot"
            )["n"]
        self.assertEqual(n, 7)

    def test_churned_flag_marks_zero_mrr(self):
        with QueryRunner(":memory:") as q:
            build_periodic_snapshot_fact(q)
            row = q.query_one(
                "SELECT mrr FROM fact_subscription_monthly_snapshot "
                "WHERE is_churned = 1"
            )
        self.assertEqual(row["mrr"], 0.0)


class TestAccumulatingSnapshot(unittest.TestCase):
    def test_creates_schema(self):
        with QueryRunner(":memory:") as q:
            tables = build_accumulating_snapshot_fact(q)
        for n in ("dim_customer", "dim_date",
                  "fact_order_accumulating_snapshot"):
            self.assertIn(n, tables)

    def test_each_row_has_a_lifecycle(self):
        with QueryRunner(":memory:") as q:
            build_accumulating_snapshot_fact(q)
            # Order 3 is in transit (no delivery yet).
            row = q.query_one(
                "SELECT delivery_date_key, days_to_deliver "
                "FROM fact_order_accumulating_snapshot WHERE order_id = 1003"
            )
        self.assertIsNone(row["delivery_date_key"])
        self.assertIsNone(row["days_to_deliver"])

    def test_lag_measures_correct(self):
        with QueryRunner(":memory:") as q:
            build_accumulating_snapshot_fact(q)
            row = q.query_one(
                "SELECT days_to_pay, days_to_ship, days_to_deliver "
                "FROM fact_order_accumulating_snapshot WHERE order_id = 1001"
            )
        # Order 1001: pay=Jan2 (1d from order), ship=Jan3
        # (1d from pay), deliver=Jan5 (2d from ship).
        # Our convention: each lag is days from the previous
        # milestone, not from the original order.
        self.assertEqual(row["days_to_pay"], 1)
        self.assertEqual(row["days_to_ship"], 1)
        self.assertEqual(row["days_to_deliver"], 2)


class TestFactlessFact(unittest.TestCase):
    def test_creates_schema(self):
        with QueryRunner(":memory:") as q:
            tables = build_factless_fact(q)
        for n in ("dim_user", "dim_event", "dim_date",
                  "fact_attendance_factless"):
            self.assertIn(n, tables)

    def test_fact_has_no_numeric_columns(self):
        with QueryRunner(":memory:") as q:
            build_factless_fact(q)
            cols = q.query_all(
                "PRAGMA table_info(fact_attendance_factless)"
            )
            numeric_types = ("INTEGER", "REAL", "NUMERIC")
            for col in cols:
                # Only the PK and FKs — no measures.
                if col["name"] in (
                    "attendance_key", "user_key", "event_key", "date_key"
                ):
                    continue
                self.assertNotIn(
                    col["type"].upper(), numeric_types,
                    f"{col['name']} has a numeric type, "
                    f"which a factless fact should not have",
                )

    def test_attendance_count_matches_joins(self):
        with QueryRunner(":memory:") as q:
            build_factless_fact(q)
            row = q.query_one(
                "SELECT COUNT(*) AS n FROM fact_attendance_factless"
            )
        self.assertEqual(row["n"], 5)


if __name__ == "__main__":
    unittest.main()
