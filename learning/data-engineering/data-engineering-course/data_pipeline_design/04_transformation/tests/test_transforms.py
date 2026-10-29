"""Unit tests for the transformation module.

Run with::

    python3 scripts/run_all_tests.py data_pipeline_design
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]
sys.path.insert(0, str(COURSE_ROOT.parent))


def _load(name: str, file_name: str):
    path = HERE.parent / "code" / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


sql_transforms = _load("data_pipeline_design_transforms_sql", "sql_transforms.py")
py_transforms = _load("data_pipeline_design_transforms_py", "py_transforms.py")
data_quality = _load("data_pipeline_design_transforms_dq", "data_quality.py")


# =========================================================================
# SQL transforms tests
# =========================================================================


class SQLTransformsTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner
        self.q = QueryRunner(":memory:")

    def test_stg_orders_loads_all_rows(self):
        n = sql_transforms.build_all(self.q)
        self.assertEqual(n["stg_orders"], 7)
        self.assertEqual(n["stg_users"], 4)

    def test_int_orders_with_user_has_left_join(self):
        sql_transforms.build_all(self.q)
        # All 7 orders should join to a user (no orphan user_ids in the seed).
        n = self.q.query_one("SELECT COUNT(*) AS n FROM int_orders_with_user")["n"]
        self.assertEqual(n, 7)

    def test_fct_orders_daily_aggregates(self):
        sql_transforms.build_all(self.q)
        rows = self.q.query_all(
            "SELECT order_day, country, order_count, revenue "
            "FROM fct_orders_daily ORDER BY order_day, country"
        )
        # 2024-01-15 US (Alice, paid $50) and 2024-01-20 US (Alice, shipped $30) and
        # 2024-01-21 UK (Bob, delivered $75) and 2024-01-22 UK (Bob, paid $18) and
        # 2024-01-23 US (Alice, refunded $12 — excluded because status not in paid/shipped/delivered)
        # Pending 2024-01-23 is excluded (status pending not in list)
        # Cancelled 2024-01-22 is excluded.
        # So we have rows for 2024-01-15 US, 2024-01-20 US, 2024-01-21 UK, 2024-01-22 UK.
        days = [r["order_day"] for r in rows]
        self.assertEqual(len(rows), 4)
        self.assertEqual(days[0], "2024-01-15")
        self.assertEqual(days[-1], "2024-01-22")

    def test_fct_orders_daily_excludes_cancelled(self):
        sql_transforms.build_all(self.q)
        cancelled = self.q.query_one(
            "SELECT COUNT(*) AS n FROM fct_orders_daily "
            "WHERE order_day = '2024-01-22' AND country = 'DE'"
        )["n"]
        self.assertEqual(cancelled, 0)  # Carol's order is excluded

    def test_fct_orders_daily_revenue_sum(self):
        sql_transforms.build_all(self.q)
        total = self.q.query_one(
            "SELECT COALESCE(SUM(revenue), 0) AS s FROM fct_orders_daily"
        )["s"]
        # 50 + 30 + 75 + 18 = 173
        self.assertAlmostEqual(total, 173.0, places=2)

    def test_dim_users_scd2_has_current_flag(self):
        sql_transforms.build_all(self.q)
        rows = self.q.query_all(
            "SELECT user_id, is_current FROM dim_users_scd2 ORDER BY user_id"
        )
        # All four users have exactly one current row.
        current = [r for r in rows if r["is_current"] == 1]
        self.assertEqual(len(current), 4)
        # All rows have is_current as 0 or 1.
        for r in rows:
            self.assertIn(r["is_current"], (0, 1))

    def test_dim_users_scd2_valid_to_open_for_current(self):
        sql_transforms.build_all(self.q)
        rows = self.q.query_all(
            "SELECT valid_to FROM dim_users_scd2 WHERE is_current = 1"
        )
        for r in rows:
            self.assertEqual(r["valid_to"], "9999-12-31")

    def test_build_all_is_idempotent(self):
        sql_transforms.build_all(self.q)
        first = self.q.query_one("SELECT COUNT(*) AS n FROM stg_orders")["n"]
        sql_transforms.build_all(self.q)
        second = self.q.query_one("SELECT COUNT(*) AS n FROM stg_orders")["n"]
        self.assertEqual(first, second)


# =========================================================================
# Python transform tests
# =========================================================================


class PyTransformsTests(unittest.TestCase):
    def test_coerce_types_int(self):
        rows = [{"a": "1"}, {"a": "2"}, {"a": "x"}]
        out = py_transforms.coerce_types(rows, {"a": "int"})
        self.assertEqual(out[0]["a"], 1)
        self.assertEqual(out[1]["a"], 2)
        # Bad value is left as-is.
        self.assertEqual(out[2]["a"], "x")

    def test_coerce_types_json(self):
        rows = [{"a": '{"x": 1}'}]
        out = py_transforms.coerce_types(rows, {"a": "json"})
        self.assertEqual(out[0]["a"], {"x": 1})

    def test_coerce_types_bool(self):
        rows = [{"a": "true"}, {"a": "0"}, {"a": "yes"}]
        out = py_transforms.coerce_types(rows, {"a": "bool"})
        self.assertTrue(out[0]["a"])
        self.assertFalse(out[1]["a"])
        self.assertTrue(out[2]["a"])

    def test_normalize_keys(self):
        rows = [{"UserId": 1, "UserName": "Alice"}]
        out = py_transforms.normalize_keys(rows, case="lower")
        self.assertEqual(out[0], {"userid": 1, "username": "Alice"})

    def test_dedupe_by_key_last(self):
        rows = [
            {"id": 1, "v": "a"},
            {"id": 2, "v": "b"},
            {"id": 1, "v": "c"},
        ]
        out = py_transforms.dedupe_by_key(rows, ["id"], strategy="last")
        self.assertEqual(len(out), 2)
        # id=1 should be the latest ("c").
        for r in out:
            if r["id"] == 1:
                self.assertEqual(r["v"], "c")

    def test_dedupe_by_key_first(self):
        rows = [
            {"id": 1, "v": "a"},
            {"id": 1, "v": "c"},
        ]
        out = py_transforms.dedupe_by_key(rows, ["id"], strategy="first")
        self.assertEqual(out[0]["v"], "a")

    def test_enrich_left_join(self):
        rows = [{"user_id": 1, "name": "Alice"}, {"user_id": 2, "name": "Bob"}]
        lookup = {1: {"country": "US", "tier": "pro"}}
        out = py_transforms.enrich(rows, lookup, on="user_id", how="left")
        self.assertEqual(out[0]["country"], "US")
        self.assertEqual(out[0]["tier"], "pro")
        # No match: columns are null.
        self.assertIsNone(out[1]["country"])

    def test_enrich_inner_skips_unmatched(self):
        rows = [{"user_id": 1}, {"user_id": 99}]
        lookup = {1: {"country": "US"}}
        out = py_transforms.enrich(rows, lookup, on="user_id", how="inner")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["country"], "US")

    def test_group_aggregate_sum_and_count(self):
        rows = [
            {"country": "US", "total": 10},
            {"country": "US", "total": 20},
            {"country": "UK", "total": 5},
        ]
        out = py_transforms.group_aggregate(
            rows,
            by=["country"],
            aggs={
                "n": ("total", len),
                "sum_total": ("total", sum),
            },
        )
        by_country = {r["country"]: r for r in out}
        self.assertEqual(by_country["US"]["n"], 2)
        self.assertEqual(by_country["US"]["sum_total"], 30)
        self.assertEqual(by_country["UK"]["n"], 1)


# =========================================================================
# Data quality tests
# =========================================================================


class DataQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner
        self.q = QueryRunner(":memory:")
        self.q.execute(
            "CREATE TABLE t ("
            " id INTEGER,"
            " email TEXT,"
            " status TEXT,"
            " score REAL"
            ")"
        )
        self.q.executemany(
            "INSERT INTO t VALUES (?, ?, ?, ?)",
            [
                (1, "a@x.com", "paid", 1.0),
                (2, "b@x.com", "shipped", 2.0),
                (3, "c@x.com", "delivered", 3.0),
            ],
        )

    def test_not_null_passes(self):
        self.assertTrue(data_quality.expect_column_values_to_not_be_null(self.q, "t", "id"))

    def test_not_null_fails_with_null(self):
        self.q.execute("INSERT INTO t VALUES (NULL, 'd@x.com', 'paid', 4.0)")
        self.assertFalse(data_quality.expect_column_values_to_not_be_null(self.q, "t", "id"))

    def test_unique_passes(self):
        self.assertTrue(data_quality.expect_column_values_to_be_unique(self.q, "t", "id"))

    def test_unique_fails_with_duplicate(self):
        self.q.execute("INSERT INTO t VALUES (1, 'dup@x.com', 'paid', 1.0)")
        self.assertFalse(data_quality.expect_column_values_to_be_unique(self.q, "t", "id"))

    def test_length_between_passes(self):
        self.assertTrue(
            data_quality.expect_column_value_lengths_to_be_between(
                self.q, "t", "email", min_length=3, max_length=20
            )
        )

    def test_length_between_fails(self):
        self.q.execute("INSERT INTO t VALUES (4, 'x', 'paid', 1.0)")
        self.assertFalse(
            data_quality.expect_column_value_lengths_to_be_between(
                self.q, "t", "email", min_length=3, max_length=20
            )
        )

    def test_in_set_passes(self):
        self.assertTrue(
            data_quality.expect_column_values_to_be_in_set(
                self.q, "t", "status", ["paid", "shipped", "delivered"]
            )
        )

    def test_in_set_fails(self):
        self.assertFalse(
            data_quality.expect_column_values_to_be_in_set(
                self.q, "t", "status", ["paid", "shipped"]
            )
        )

    def test_row_count_between_passes(self):
        self.assertTrue(
            data_quality.expect_row_count_to_be_between(self.q, "t", 1, 100)
        )

    def test_row_count_between_fails_low(self):
        self.assertFalse(
            data_quality.expect_row_count_to_be_between(self.q, "t", 10, 100)
        )

    def test_row_count_between_fails_high(self):
        self.assertFalse(
            data_quality.expect_row_count_to_be_between(self.q, "t", 1, 2)
        )

    def test_mean_between_passes(self):
        self.assertTrue(
            data_quality.expect_column_mean_to_be_between(self.q, "t", "score", 0, 5)
        )

    def test_mean_between_fails(self):
        self.assertFalse(
            data_quality.expect_column_mean_to_be_between(self.q, "t", "score", 10, 20)
        )

    def test_run_suite(self):
        results = data_quality.run_suite(
            self.q,
            [
                {"fn": "expect_column_values_to_not_be_null", "args": ["t", "id"]},
                {"fn": "expect_column_values_to_be_unique", "args": ["t", "id"]},
                {"fn": "expect_row_count_to_be_between", "args": ["t", 1, 100]},
            ],
        )
        self.assertEqual(len(results), 3)
        for k, v in results.items():
            self.assertTrue(v, f"expectation {k} should pass")

    def test_run_suite_with_failure(self):
        self.q.execute("INSERT INTO t VALUES (NULL, 'd@x.com', 'paid', 4.0)")
        results = data_quality.run_suite(
            self.q,
            [{"fn": "expect_column_values_to_not_be_null", "args": ["t", "id"]}],
        )
        self.assertFalse(results["expect_column_values_to_not_be_null"])


if __name__ == "__main__":
    unittest.main()
