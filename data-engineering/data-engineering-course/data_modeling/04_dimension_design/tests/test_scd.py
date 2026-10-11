"""Tests for the SCD implementations.

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

from common import Column, QueryRunner, Table  # type: ignore

from scd import (  # type: ignore
    FOREVER,
    is_degenerate_dim,
    is_junk_dim_cardinality,
    mark_conformed,
    role_playing_dim_note,
    scd1_update,
    scd2_insert,
    scd3_add_column,
)


def _build_dim_users(q: QueryRunner) -> None:
    """Build a small dim_users table for SCD tests."""
    t = Table("dim_users", [
        Column("id", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
        Column("plan", "TEXT"),
        Column("country", "TEXT"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False),
        Column("is_current", "INTEGER", nullable=False),
    ])
    q.execute(t.to_ddl())


class TestSCD1(unittest.TestCase):
    def test_overwrites_in_place(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            q.execute(
                "INSERT INTO dim_users VALUES "
                "(1, 100, 'Alice', 'free', 'US', "
                "'2024-01-01', '9999-12-31', 1)"
            )
            rows = scd1_update(
                q, "dim_users", "customer_id", 100,
                {"name": "Alice Smith"},
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Alice Smith")

    def test_keeps_history_but_no_extra_rows(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            q.execute(
                "INSERT INTO dim_users VALUES "
                "(1, 100, 'Alice', 'free', 'US', "
                "'2024-01-01', '9999-12-31', 1)"
            )
            scd1_update(q, "dim_users", "customer_id", 100,
                        {"name": "Alice S."})
            scd1_update(q, "dim_users", "customer_id", 100,
                        {"country": "UK"})
            # Still 1 row — SCD1 overwrites.
            count = q.query_one("SELECT COUNT(*) AS n FROM dim_users")["n"]
        self.assertEqual(count, 1)

    def test_empty_update_raises(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            with self.assertRaises(ValueError):
                scd1_update(q, "dim_users", "customer_id", 100, {})


class TestSCD2(unittest.TestCase):
    def test_first_insert_creates_current_row(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            rows = scd2_insert(
                q, "dim_users", "customer_id", 100,
                {"customer_id": 100, "name": "Alice", "plan": "free",
                 "country": "US"},
                effective_date="2024-01-01",
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["is_current"], 1)
        self.assertEqual(rows[0]["expiry_date"], FOREVER)

    def test_second_insert_expires_first(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            scd2_insert(
                q, "dim_users", "customer_id", 100,
                {"customer_id": 100, "name": "Alice", "plan": "free",
                 "country": "US"},
                effective_date="2024-01-01",
            )
            scd2_insert(
                q, "dim_users", "customer_id", 100,
                {"customer_id": 100, "name": "Alice", "plan": "pro",
                 "country": "US"},
                effective_date="2024-06-01",
            )
            rows = q.query_all(
                "SELECT * FROM dim_users WHERE customer_id = 100 "
                "ORDER BY effective_date"
            )
        self.assertEqual(len(rows), 2)
        # Old row expired, new row current.
        self.assertEqual(rows[0]["is_current"], 0)
        self.assertEqual(rows[0]["expiry_date"], "2024-05-31")
        self.assertEqual(rows[1]["is_current"], 1)
        self.assertEqual(rows[1]["plan"], "pro")

    def test_three_versions_keep_all_history(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            for date_, plan in [
                ("2024-01-01", "free"),
                ("2024-06-01", "pro"),
                ("2024-12-01", "enterprise"),
            ]:
                scd2_insert(
                    q, "dim_users", "customer_id", 100,
                    {"customer_id": 100, "name": "Alice",
                     "plan": plan, "country": "US"},
                    effective_date=date_,
                )
            rows = q.query_all(
                "SELECT plan, is_current FROM dim_users "
                "WHERE customer_id = 100 ORDER BY effective_date"
            )
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            [r["plan"] for r in rows], ["free", "pro", "enterprise"]
        )
        self.assertEqual(
            [r["is_current"] for r in rows], [0, 0, 1]
        )

    def test_new_fields_must_include_natural_key(self):
        with QueryRunner(":memory:") as q:
            _build_dim_users(q)
            with self.assertRaises(ValueError):
                scd2_insert(
                    q, "dim_users", "customer_id", 100,
                    {"name": "Alice"},  # missing customer_id
                )


class TestSCD3(unittest.TestCase):
    def test_tracks_previous_value(self):
        with QueryRunner(":memory:") as q:
            t = Table("dim_users", [
                Column("customer_id", "INTEGER", primary_key=True),
                Column("plan", "TEXT"),
            ])
            q.execute(t.to_ddl())
            q.execute("INSERT INTO dim_users VALUES (1, 'free')")
            rows = scd3_add_column(
                q, "dim_users", "customer_id", 1,
                "previous_plan", "pro",
            )
        self.assertEqual(rows[0]["plan"], "pro")
        self.assertEqual(rows[0]["previous_plan"], "free")

    def test_only_one_level_of_history(self):
        with QueryRunner(":memory:") as q:
            t = Table("dim_users", [
                Column("customer_id", "INTEGER", primary_key=True),
                Column("plan", "TEXT"),
            ])
            q.execute(t.to_ddl())
            q.execute("INSERT INTO dim_users VALUES (1, 'free')")
            scd3_add_column(q, "dim_users", "customer_id", 1,
                            "previous_plan", "pro")
            # Third change overwrites the previous, not chained.
            scd3_add_column(q, "dim_users", "customer_id", 1,
                            "previous_plan", "enterprise")
            row = q.query_one(
                "SELECT * FROM dim_users WHERE customer_id = 1"
            )
        self.assertEqual(row["plan"], "enterprise")
        self.assertEqual(row["previous_plan"], "pro")

    def test_missing_row_raises(self):
        with QueryRunner(":memory:") as q:
            t = Table("dim_users", [
                Column("customer_id", "INTEGER", primary_key=True),
                Column("plan", "TEXT"),
            ])
            q.execute(t.to_ddl())
            with self.assertRaises(ValueError):
                scd3_add_column(q, "dim_users", "customer_id", 999,
                                "previous_plan", "pro")


class TestDimensionHeuristics(unittest.TestCase):
    def test_junk_dim_under_50(self):
        self.assertTrue(is_junk_dim_cardinality(5))
        self.assertTrue(is_junk_dim_cardinality(50))
        self.assertFalse(is_junk_dim_cardinality(51))
        self.assertFalse(is_junk_dim_cardinality(0))

    def test_degenerate_dim_single_column(self):
        self.assertTrue(is_degenerate_dim(1, 1000))
        self.assertFalse(is_degenerate_dim(2, 1000))
        self.assertFalse(is_degenerate_dim(1, 1))

    def test_conformed_dim_label(self):
        out = mark_conformed(["dim_date", "dim_user"])
        self.assertIn("Conformed", out)
        self.assertIn("dim_date", out)

    def test_role_playing_dim_note(self):
        out = role_playing_dim_note("ship_date", "dim_date")
        self.assertIn("ship_date", out)
        self.assertIn("dim_date", out)


if __name__ == "__main__":
    unittest.main()
