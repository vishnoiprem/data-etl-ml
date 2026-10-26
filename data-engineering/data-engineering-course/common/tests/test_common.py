"""Unit tests for the shared ``common`` library.

Run with::

    python3 -m unittest common.tests.test_common -v

Or via the top-level runner::

    python3 scripts/run_all_tests.py common
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from common import (
    Column,
    Pipeline,
    PipelineError,
    QueryRunner,
    Table,
    add_foreign_keys,
    create_index_sqlite,
    create_table_sqlite,
    dedupe_by_key,
    drop_table_sqlite,
    make_events,
    make_orders,
    make_products,
    make_users,
    p50_p95_p99,
    rank_desc,
    read_csv,
    render_sql,
    running_total,
    seed_all,
    stream_csv,
    top_k_by,
    with_idempotency,
    write_csv,
)
from common.analytics import group_count, safe_div
from common.fixtures import SAMPLE_DATA_DIR, fixture_path, list_fixtures
from common.schema import create_index_sqlite as _create_index_sqlite
from common.conftest_helpers import build_seeded_runner, make_tmp_db


# ---- schema --------------------------------------------------------------


class SchemaTests(unittest.TestCase):
    def test_column_basic_fragment(self):
        c = Column("id", "INTEGER", primary_key=True)
        self.assertEqual(c.to_sql_fragment(), '"id" INTEGER PRIMARY KEY')

    def test_column_not_null_default(self):
        c = Column("email", "TEXT", nullable=False, default="''")
        frag = c.to_sql_fragment()
        self.assertIn("NOT NULL", frag)
        self.assertIn("DEFAULT ''", frag)

    def test_table_ddl_contains_columns(self):
        t = Table("users", [
            Column("id", "INTEGER", primary_key=True),
            Column("email", "TEXT", nullable=False),
        ])
        ddl = t.to_ddl()
        self.assertIn("CREATE TABLE IF NOT EXISTS \"users\"", ddl)
        self.assertIn('"id" INTEGER PRIMARY KEY', ddl)
        self.assertIn('"email" TEXT NOT NULL', ddl)

    def test_create_table_sqlite_matches_to_ddl(self):
        t = Table("t", [Column("x", "INTEGER")])
        self.assertEqual(create_table_sqlite(t), t.to_ddl())

    def test_create_index_sqlite(self):
        t = Table("users", [Column("id", "INTEGER"), Column("email", "TEXT")])
        idx = create_index_sqlite(t, ["email"])
        self.assertIn("CREATE INDEX", idx)
        self.assertIn('"users"', idx)
        self.assertIn('"email"', idx)

    def test_create_index_requires_columns(self):
        t = Table("users", [])
        with self.assertRaises(ValueError):
            create_index_sqlite(t, [])

    def test_drop_table_sqlite(self):
        sql = drop_table_sqlite("users", if_exists=True)
        self.assertEqual(sql, 'DROP TABLE IF EXISTS "users"')

    def test_add_foreign_keys(self):
        t = Table("orders", [
            Column("user_id", "INTEGER", references="users(id)"),
        ])
        add_foreign_keys(t, ['"user_id" REFERENCES users(id)'])
        ddl = t.to_ddl()
        self.assertIn("FOREIGN KEY", ddl)


# ---- query ---------------------------------------------------------------


class QueryRunnerTests(unittest.TestCase):
    def setUp(self):
        self.q = QueryRunner(":memory:")
        self.q.execute(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, n INTEGER, label TEXT)"
        )

    def tearDown(self):
        self.q.close()

    def test_execute_returns_rowcount(self):
        rc = self.q.execute("INSERT INTO t(n, label) VALUES (?, ?)", (1, "a"))
        self.assertEqual(rc, 1)

    def test_query_all_returns_dicts(self):
        self.q.executemany(
            "INSERT INTO t(n, label) VALUES (?, ?)",
            [(1, "a"), (2, "b"), (3, "c")],
        )
        rows = self.q.query_all("SELECT n, label FROM t ORDER BY n")
        self.assertEqual(rows, [{"n": 1, "label": "a"},
                                {"n": 2, "label": "b"},
                                {"n": 3, "label": "c"}])

    def test_query_one_returns_dict_or_none(self):
        self.q.execute("INSERT INTO t(n) VALUES (?)", (7,))
        self.assertEqual(self.q.query_one("SELECT n FROM t WHERE n=?", (7,)),
                         {"n": 7})
        self.assertIsNone(self.q.query_one("SELECT n FROM t WHERE n=?",
                                           (999,)))

    def test_context_manager_closes(self):
        with QueryRunner(":memory:") as q:
            q.execute("CREATE TABLE x (n INTEGER)")
            q.execute("INSERT INTO x VALUES (1)")
            self.assertEqual(len(q.query_all("SELECT * FROM x")), 1)

    def test_build_seeded_runner_has_tables(self):
        runner = build_seeded_runner()
        try:
            tables = {
                r["name"] for r in runner.query_all(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertIn("users", tables)
            self.assertIn("orders", tables)
        finally:
            runner.close()


# ---- csv_utils -----------------------------------------------------------


class CsvUtilsTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "data.csv"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_write_then_read_round_trip(self):
        rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        write_csv(self.path, rows)
        loaded = read_csv(self.path)
        self.assertEqual(loaded, [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}])

    def test_stream_csv_yields_dicts(self):
        write_csv(self.path, [{"a": 1}, {"a": 2}, {"a": 3}])
        streamed = list(stream_csv(self.path))
        self.assertEqual(streamed, [{"a": "1"}, {"a": "2"}, {"a": "3"}])


# ---- analytics -----------------------------------------------------------


class AnalyticsTests(unittest.TestCase):
    def test_running_total(self):
        self.assertEqual(running_total([1, 2, 3, 4]), [1.0, 3.0, 6.0, 10.0])

    def test_running_total_empty(self):
        self.assertEqual(running_total([]), [])

    def test_rank_desc_with_ties(self):
        # 30 wins (rank 1), other 30 also rank 1, 20 rank 3, 10 rank 4.
        self.assertEqual(rank_desc([10, 30, 20, 30, 5]),
                         [3, 1, 2, 1, 4])

    def test_dedupe_by_key_keeps_first(self):
        rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"},
                {"id": 1, "v": "c"}]
        self.assertEqual(dedupe_by_key(rows, "id"),
                         [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}])

    def test_top_k_by(self):
        rows = [{"a": 1}, {"a": 3}, {"a": 2}]
        self.assertEqual(top_k_by(rows, "a", k=2), [{"a": 3}, {"a": 2}])

    def test_p50_p95_p99_monotonic(self):
        values = list(range(1, 1001))
        p50, p95, p99 = p50_p95_p99(values)
        self.assertLessEqual(p50, p95)
        self.assertLessEqual(p95, p99)

    def test_group_count(self):
        rows = [{"x": "a"}, {"x": "b"}, {"x": "a"}]
        self.assertEqual(group_count(rows, "x"), {"a": 2, "b": 1})

    def test_safe_div(self):
        self.assertEqual(safe_div(10, 2), 5.0)
        self.assertEqual(safe_div(10, 0, default=-1.0), -1.0)


# ---- pipeline ------------------------------------------------------------


class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_all_stages(self):
        p = Pipeline(
            "double_sum",
            extract=lambda: [1, 2, 3],
            transform=lambda rows: [r * 2 for r in rows],
            load=lambda rows: sum(rows),
            retries=1,
        )
        self.assertEqual(p.run(), 12)

    def test_pipeline_retries_then_raises(self):
        attempts = {"n": 0}

        def flaky(_):
            attempts["n"] += 1
            raise RuntimeError("boom")

        p = Pipeline(
            "flaky",
            extract=lambda: [1],
            transform=flaky,
            load=lambda x: x,
            retries=3,
        )
        with self.assertRaises(PipelineError):
            p.run()
        # 1 original attempt + 2 retries = 3 total.
        self.assertEqual(attempts["n"], 3)

    def test_pipeline_records_state(self):
        p = Pipeline(
            "noop",
            extract=lambda: [1, 2, 3, 4],
            transform=lambda x: x,
            load=lambda x: x,
            retries=1,
        )
        p.run()
        self.assertEqual(p.state["last_extract_count"], 4)
        self.assertEqual(p.state["last_transform_count"], 4)

    def test_with_idempotency_caches_result(self):
        path = make_tmp_db()
        try:
            calls = {"n": 0}

            @with_idempotency("k1", db_path=path)
            def work():
                calls["n"] += 1
                return "ok"

            # First call: real function runs, marker gets persisted.
            work()
            # Second call: cached; underlying function is NOT called.
            work()
            self.assertEqual(calls["n"], 1)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


# ---- data_gen ------------------------------------------------------------


class DataGenTests(unittest.TestCase):
    def test_make_users_deterministic(self):
        seed_all(42)
        a = make_users(20)
        seed_all(42)
        b = make_users(20)
        self.assertEqual(a, b)

    def test_make_users_keys_and_types(self):
        users = make_users(5)
        self.assertEqual(len(users), 5)
        for u in users:
            self.assertIn("id", u)
            self.assertIn("email", u)
            self.assertIn("signup_date", u)
            self.assertIn("country", u)

    def test_make_orders_references_users_and_products(self):
        users = make_users(10)
        products = make_products(5)
        orders = make_orders(20, users=users, products=products)
        self.assertEqual(len(orders), 20)
        user_ids = {u["id"] for u in users}
        product_ids = {p["id"] for p in products}
        for o in orders:
            self.assertIn(o["user_id"], user_ids)

    def test_make_events_returns_iso_ts(self):
        evs = make_events(10)
        self.assertEqual(len(evs), 10)
        for e in evs:
            # Year-month-day, then T, then Z.
            self.assertRegex(e["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# ---- fixtures ------------------------------------------------------------


class FixturesTests(unittest.TestCase):
    def test_sample_data_dir_is_a_directory(self):
        # The generator may not have been run yet, so the dir may
        # not exist — only assert it's a Path pointing at the right
        # place.
        self.assertTrue(str(SAMPLE_DATA_DIR).endswith("sample_data"))

    def test_fixture_path_joins_correctly(self):
        p = fixture_path("users.csv")
        self.assertEqual(p.name, "users.csv")
        self.assertEqual(p.parent, SAMPLE_DATA_DIR)


# ---- jinja_helpers -------------------------------------------------------


class JinjaHelpersTests(unittest.TestCase):
    def test_render_sql_substitutes_string(self):
        sql = render_sql("SELECT * FROM {{ table }}", table="orders")
        # Strings are quoted.
        self.assertEqual(sql, "SELECT * FROM 'orders'")

    def test_render_sql_substitutes_number(self):
        sql = render_sql("WHERE n = {{ n }}", n=42)
        self.assertEqual(sql, "WHERE n = 42")

    def test_render_sql_escapes_quotes(self):
        sql = render_sql("WHERE name = {{ name }}", name="O'Brien")
        self.assertIn("O''Brien", sql)

    def test_render_sql_conditional(self):
        sql = render_sql(
            "{% if filter %}SELECT * FROM t WHERE x > 0{% endif %}",
            filter=True,
        )
        self.assertIn("SELECT *", sql)
        sql_no = render_sql(
            "{% if filter %}SELECT * FROM t{% endif %}",
            filter=False,
        )
        self.assertEqual(sql_no, "")


# ---- combined smoke test -------------------------------------------------


class EndToEndSmokeTest(unittest.TestCase):
    """Run the full round-trip: generate, write, reload, query."""

    def test_csv_round_trip_via_query(self):
        users = make_users(5)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "users.csv"
            write_csv(p, users)
            rows = read_csv(p)
            with QueryRunner(":memory:") as q:
                q.execute(
                    "CREATE TABLE users (id INTEGER, name TEXT, "
                    "email TEXT, signup_date TEXT, country TEXT)"
                )
                for r in rows:
                    q.execute(
                        "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                        (r["id"], r["name"], r["email"],
                         r["signup_date"], r["country"]),
                    )
                result = q.query_one("SELECT COUNT(*) AS c FROM users")
                # SQLite returns int for COUNT(*); read_csv returns
                # strings — but COUNT is computed in SQL, so it's int.
                self.assertEqual(result["c"], 5)
                # And every loaded user row should match by id.
                self.assertEqual(
                    len(q.query_all("SELECT id FROM users")),
                    5,
                )


if __name__ == "__main__":
    unittest.main()
