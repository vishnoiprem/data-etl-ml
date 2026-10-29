"""Unit tests for the extraction module.

Run with::

    python3 scripts/run_all_tests.py data_pipeline_design
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]  # .../data_engineering_course
sys.path.insert(0, str(COURSE_ROOT.parent))  # for `common`


def _load(name: str, file_name: str):
    """Load a module by file path (the directory name starts with a digit)."""
    path = HERE.parent / "code" / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # so @dataclass can find __module__
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


cdc = _load("data_pipeline_design_extraction_cdc", "cdc.py")
api_poller = _load("data_pipeline_design_extraction_api_poller", "api_poller.py")
jdbc_extractor = _load(
    "data_pipeline_design_extraction_jdbc", "jdbc_extractor.py"
)
schema_registry = _load(
    "data_pipeline_design_extraction_schema_registry", "schema_registry.py"
)

CDCPipeline = cdc.CDCPipeline
CDCEvent = cdc.CDCEvent
ApiPoller = api_poller.ApiPoller
MockPaginatedAPI = api_poller.MockPaginatedAPI
JDBCExtractor = jdbc_extractor.JDBCExtractor
KeysetExtractor = jdbc_extractor.KeysetExtractor
SchemaRegistry = schema_registry.SchemaRegistry
IncompatibleSchemaError = schema_registry.IncompatibleSchemaError


def _make_memory_sink():
    return _MemorySink()


class _MemorySink:
    """A tiny sink that just appends rows to a list."""
    def __init__(self) -> None:
        self.rows = []

    def write(self, rows):
        self.rows.extend(rows)


# =========================================================================
# CDC tests
# =========================================================================


class CDCPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sink = _MemorySink()
        self.pipeline = CDCPipeline(sink=self.sink, table="users", pk="id")

    def test_first_run_emits_inserts(self):
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Carol"},
        ]
        events = self.pipeline.run_once(rows)
        # First run: every row is a "create" event.
        self.assertEqual(len(events), 3)
        self.assertEqual([e.op for e in events], ["c", "c", "c"])
        # Sink has 3 events written.
        self.assertEqual(len(self.sink.rows), 3)

    def test_second_run_unchanged_emits_nothing(self):
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        self.pipeline.run_once(rows)
        events = self.pipeline.run_once(rows)
        self.assertEqual(events, [])

    def test_insert_then_update_then_insert(self):
        # First run: 5 inserts
        first = [{"id": i, "name": f"u{i}"} for i in range(1, 6)]
        self.pipeline.run_once(first)
        # Second run: update id=1, insert id=6
        second = first + []
        second[0] = {"id": 1, "name": "Alice2"}
        second = second + [{"id": 6, "name": "u6"}]
        events = self.pipeline.run_once(second)
        # Expect 1 update + 1 insert.
        ops = sorted([e.op for e in events])
        self.assertEqual(ops, ["c", "u"])

    def test_delete_emits_delete_event(self):
        self.pipeline.run_once(
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        )
        # Remove id=1
        events = self.pipeline.run_once([{"id": 2, "name": "Bob"}])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].op, "d")
        self.assertEqual(events[0].before, {"id": 1, "name": "Alice"})

    def test_event_shape(self):
        e = CDCEvent(op="c", table="t", key={"id": 1}, after={"id": 1, "v": 2})
        d = e.to_dict()
        self.assertEqual(d["op"], "c")
        self.assertEqual(d["after"], {"id": 1, "v": 2})
        self.assertIn("ts_ms", d)


# =========================================================================
# API poller tests
# =========================================================================


class ApiPollerTests(unittest.TestCase):
    def test_three_pages_of_five(self):
        rows = [{"id": i, "name": f"row-{i}"} for i in range(15)]
        with MockPaginatedAPI(rows, page_size=5) as base:
            poller = ApiPoller(
                base_url=base,
                page_size=5,
                page_param="page_size",
            )
            out = list(poller.poll_all())
            self.assertEqual(len(out), 15)
            self.assertEqual(out[0]["id"], 0)
            self.assertEqual(out[-1]["id"], 14)

    def test_single_page_no_next_cursor(self):
        rows = [{"id": i} for i in range(3)]
        with MockPaginatedAPI(rows, page_size=5) as base:
            poller = ApiPoller(base_url=base, page_size=5)
            out = list(poller.poll_all())
            self.assertEqual(len(out), 3)

    def test_empty_response(self):
        with MockPaginatedAPI([], page_size=5) as base:
            poller = ApiPoller(base_url=base, page_size=5)
            out = list(poller.poll_all())
            self.assertEqual(out, [])

    def test_429_triggers_backoff(self):
        """429 response should be retried with backoff."""
        # Inject a fetch that returns 429 once then 200.
        calls = {"n": 0}

        def fake_fetch(url):
            calls["n"] += 1
            if calls["n"] == 1:
                return 429, {"Retry-After": "0"}, ""
            return 200, {}, json.dumps({"data": [{"id": 1}], "next_cursor": None})

        poller = ApiPoller(
            base_url="http://x/y",
            page_size=5,
            fetch=fake_fetch,
            sleep=lambda _s: None,
        )
        out = list(poller.poll_all())
        self.assertEqual(out, [{"id": 1}])
        self.assertEqual(calls["n"], 2)

    def test_5xx_retries(self):
        calls = {"n": 0}

        def fake_fetch(url):
            calls["n"] += 1
            if calls["n"] < 3:
                return 503, {}, ""
            return 200, {}, json.dumps({"data": [{"id": 1}], "next_cursor": None})

        poller = ApiPoller(
            base_url="http://x/y",
            page_size=5,
            fetch=fake_fetch,
            sleep=lambda _s: None,
        )
        out = list(poller.poll_all())
        self.assertEqual(out, [{"id": 1}])

    def test_4xx_raises(self):
        def fake_fetch(url):
            return 404, {}, "not found"

        poller = ApiPoller(
            base_url="http://x/y",
            page_size=5,
            fetch=fake_fetch,
            sleep=lambda _s: None,
        )
        with self.assertRaises(RuntimeError):
            list(poller.poll_all())


# =========================================================================
# JDBC extractor tests
# =========================================================================


class JDBCExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner

        self.q = QueryRunner(":memory:")
        self.q.execute(
            "CREATE TABLE users ("
            " id INTEGER PRIMARY KEY,"
            " name TEXT,"
            " updated_at TEXT"
            ")"
        )
        # Seed 5 users.
        for i in range(1, 6):
            self.q.execute(
                "INSERT INTO users(id, name, updated_at) VALUES (?, ?, ?)",
                (i, f"u{i}", f"2024-01-{i:02d}T00:00:00"),
            )

    def test_first_extract_returns_all(self):
        ext = JDBCExtractor(
            runner=self.q, table="users", watermark_store={}
        )
        result = ext.extract()
        self.assertEqual(len(result.rows), 5)
        self.assertEqual(result.new_watermark, "2024-01-05T00:00:00")

    def test_second_extract_returns_none(self):
        ext = JDBCExtractor(
            runner=self.q, table="users", watermark_store={"users": "2024-01-05T00:00:00"}
        )
        result = ext.extract()
        self.assertEqual(result.rows, [])

    def test_extract_after_new_insert(self):
        store: dict = {"users": "2024-01-05T00:00:00"}
        ext = JDBCExtractor(
            runner=self.q, table="users", watermark_store=store
        )
        self.q.execute(
            "INSERT INTO users(id, name, updated_at) VALUES (?, ?, ?)",
            (6, "u6", "2024-01-06T00:00:00"),
        )
        result = ext.extract()
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["id"], 6)
        ext.commit(result.new_watermark)
        self.assertEqual(store["users"], "2024-01-06T00:00:00")

    def test_page_size_truncation(self):
        ext = JDBCExtractor(
            runner=self.q,
            table="users",
            watermark_store={},
            page_size=2,
        )
        result = ext.extract()
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(result.truncated)


class KeysetExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner

        self.q = QueryRunner(":memory:")
        self.q.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, v TEXT)")
        for i in range(1, 6):
            self.q.execute("INSERT INTO events(id, v) VALUES (?, ?)", (i, f"e{i}"))

    def test_first_extract(self):
        ext = KeysetExtractor(runner=self.q, table="events")
        result = ext.extract()
        self.assertEqual(len(result.rows), 5)
        self.assertEqual(result.new_watermark, 5)

    def test_extract_after_insert(self):
        store: dict = {"events": 5}
        ext = KeysetExtractor(runner=self.q, table="events", watermark_store=store)
        self.q.execute("INSERT INTO events(id, v) VALUES (?, ?)", (6, "e6"))
        result = ext.extract()
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["id"], 6)
        ext.commit(result.new_watermark)
        self.assertEqual(store["events"], 6)


# =========================================================================
# Schema registry tests
# =========================================================================


class SchemaRegistryTests(unittest.TestCase):
    def test_register_first_schema(self):
        reg = SchemaRegistry()
        v = reg.register("users", {"id": "int", "name": "str"})
        self.assertEqual(v.version, 1)
        self.assertEqual(len(reg.versions("users")), 1)

    def test_add_column_is_compatible(self):
        reg = SchemaRegistry()
        reg.register("users", {"id": "int", "name": "str"})
        v = reg.register("users", {"id": "int", "name": "str", "email": "str"})
        self.assertEqual(v.version, 2)

    def test_remove_column_is_incompatible(self):
        reg = SchemaRegistry()
        reg.register("users", {"id": "int", "name": "str"})
        with self.assertRaises(IncompatibleSchemaError):
            reg.register("users", {"id": "int"})

    def test_widening_type_is_compatible(self):
        reg = SchemaRegistry()
        reg.register("t", {"x": "int"})
        v = reg.register("t", {"x": "float"})
        self.assertEqual(v.version, 2)

    def test_narrowing_type_is_incompatible(self):
        reg = SchemaRegistry()
        reg.register("t", {"x": "str"})
        with self.assertRaises(IncompatibleSchemaError):
            reg.register("t", {"x": "int"})

    def test_rename_looks_like_remove_add(self):
        reg = SchemaRegistry()
        reg.register("t", {"name": "str"})
        with self.assertRaises(IncompatibleSchemaError):
            reg.register("t", {"full_name": "str"})

    def test_check_contract_happy(self):
        reg = SchemaRegistry()
        reg.register("users", {"id": "int", "name": "str"})
        errors = reg.check_contract("users", {"id": 1, "name": "Alice"})
        self.assertEqual(errors, [])

    def test_check_contract_missing_column(self):
        reg = SchemaRegistry()
        reg.register("users", {"id": "int", "name": "str"})
        errors = reg.check_contract("users", {"id": 1})
        self.assertEqual(len(errors), 1)
        self.assertIn("name", errors[0])

    def test_check_contract_type_mismatch(self):
        reg = SchemaRegistry()
        reg.register("t", {"x": "int"})
        errors = reg.check_contract("t", {"x": "not-an-int-as-string"})
        # "not-an-int..." is a string; "int" expected → not widenable.
        self.assertEqual(len(errors), 1)
        self.assertIn("x", errors[0])

    def test_check_contract_no_schema(self):
        reg = SchemaRegistry()
        errors = reg.check_contract("users", {"id": 1})
        self.assertEqual(len(errors), 1)
        self.assertIn("no schema", errors[0])


if __name__ == "__main__":
    unittest.main()
