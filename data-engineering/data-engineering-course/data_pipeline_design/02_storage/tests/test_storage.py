"""Unit tests for the storage abstractions.

Run with::

    python3 -m unittest data_pipeline_design.02_storage.tests.test_storage -v

Or via the top-level runner::

    python3 scripts/run_all_tests.py data_pipeline_design
"""

from __future__ import annotations

import csv
import importlib.util
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]  # .../data_engineering_course
CODE_FILE = HERE.parent / "code" / "storage_abstractions.py"

# Make ``common`` importable from the course root.
sys.path.insert(0, str(COURSE_ROOT.parent))

# Load the storage module by file path because the directory name
# starts with a digit, which is illegal in Python's dotted import
# syntax. The course-level test runner uses the same trick.
_spec = importlib.util.spec_from_file_location(
    "data_pipeline_design_storage", CODE_FILE
)
storage = importlib.util.module_from_spec(_spec)
sys.modules["data_pipeline_design_storage"] = storage  # for @dataclass
_spec.loader.exec_module(storage)  # type: ignore[union-attr]

CsvSource = storage.CsvSource
SqliteSink = storage.SqliteSink
MemorySink = storage.MemorySink
BatchSink = storage.BatchSink
BatchingStreamSink = storage.BatchingStreamSink
InMemorySource = storage.InMemorySource
Source = storage.Source
Sink = storage.Sink
StreamSink = storage.StreamSink


def _write_csv(path: str, header: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ---- abstract base classes --------------------------------------------


class AbstractBehaviorTests(unittest.TestCase):
    """Sanity-check the abstract classes can't be instantiated naively."""

    def test_source_is_abstract(self):
        with self.assertRaises(TypeError):
            Source()  # type: ignore[abstract]

    def test_sink_is_abstract(self):
        with self.assertRaises(TypeError):
            Sink()  # type: ignore[abstract]

    def test_stream_sink_is_abstract(self):
        with self.assertRaises(TypeError):
            StreamSink()  # type: ignore[abstract]


# ---- CsvSource --------------------------------------------------------


class CsvSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "users.csv")
        _write_csv(
            self.path,
            ["id", "name", "country"],
            [
                [1, "Alice", "US"],
                [2, "Bob", "UK"],
                [3, "Carol", "DE"],
            ],
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_read_yields_dicts(self):
        rows = list(CsvSource(self.path).read())
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {"id": "1", "name": "Alice", "country": "US"})

    def test_to_list_materializes(self):
        rows = CsvSource(self.path).to_list()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[-1]["name"], "Carol")

    def test_empty_file_yields_nothing(self):
        empty_path = os.path.join(self.tmp, "empty.csv")
        _write_csv(empty_path, ["a", "b"], [])
        self.assertEqual(list(CsvSource(empty_path).read()), [])


# ---- MemorySink -------------------------------------------------------


class MemorySinkTests(unittest.TestCase):
    def test_write_appends(self):
        sink = MemorySink()
        sink.write([{"id": 1}, {"id": 2}])
        sink.write([{"id": 3}])
        self.assertEqual(sink.rows, [{"id": 1}, {"id": 2}, {"id": 3}])

    def test_len_reports_count(self):
        sink = MemorySink()
        sink.write([{"id": i} for i in range(5)])
        self.assertEqual(len(sink), 5)

    def test_empty_write_is_noop(self):
        sink = MemorySink()
        sink.write([])
        self.assertEqual(sink.rows, [])


# ---- InMemorySource ---------------------------------------------------


class InMemorySourceTests(unittest.TestCase):
    def test_read_yields_dicts(self):
        src = InMemorySource([{"id": 1}, {"id": 2}])
        rows = list(src.read())
        self.assertEqual(rows, [{"id": 1}, {"id": 2}])

    def test_copies_input(self):
        # Mutating the returned dict must not affect the source.
        original = [{"id": 1}]
        src = InMemorySource(original)
        list(src.read())[0]["id"] = 99
        self.assertEqual(src._rows[0]["id"], 1)


# ---- SqliteSink -------------------------------------------------------


class SqliteSinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self) -> None:
        self.conn.close()

    def test_write_creates_table_and_inserts(self):
        sink = SqliteSink(self.conn, "users")
        sink.write([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        cur = self.conn.execute("SELECT id, name FROM users ORDER BY id")
        self.assertEqual(
            list(cur.fetchall()),
            [(1, "Alice"), (2, "Bob")],
        )

    def test_type_inference_numeric(self):
        sink = SqliteSink(self.conn, "metrics")
        sink.write([{"value": 1.5, "n": 7}])
        cur = self.conn.execute(
            "SELECT typeof(value), typeof(n) FROM metrics"
        )
        types = cur.fetchone()
        self.assertEqual(types, ("real", "integer"))

    def test_empty_write_is_noop(self):
        sink = SqliteSink(self.conn, "t")
        sink.write([])
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='t'"
        )
        self.assertIsNone(cur.fetchone())


# ---- BatchSink --------------------------------------------------------


class BatchSinkTests(unittest.TestCase):
    def test_batches_until_threshold(self):
        inner = MemorySink()
        sink = BatchSink(inner, batch_size=3)
        sink.write([{"i": 1}, {"i": 2}])  # buffer = 2
        self.assertEqual(len(inner), 0)
        sink.write([{"i": 3}])  # buffer reaches 3, flushes
        self.assertEqual(len(inner), 3)
        self.assertEqual(inner.rows, [{"i": 1}, {"i": 2}, {"i": 3}])

    def test_close_flushes_remainder(self):
        inner = MemorySink()
        sink = BatchSink(inner, batch_size=10)
        sink.write([{"i": 1}, {"i": 2}])
        sink.close()
        self.assertEqual(len(inner), 2)

    def test_multiple_batches(self):
        inner = MemorySink()
        sink = BatchSink(inner, batch_size=2)
        for i in range(7):
            sink.write([{"i": i}])
        sink.close()
        self.assertEqual(len(inner), 7)
        # 7 rows, batch_size=2 → 3 full flushes (rows 0-1, 2-3, 4-5) + 1 partial (row 6)
        self.assertEqual(sink.flush_count, 4)

    def test_rejects_zero_batch_size(self):
        with self.assertRaises(ValueError):
            BatchSink(MemorySink(), batch_size=0)


# ---- BatchingStreamSink ----------------------------------------------


class BatchingStreamSinkTests(unittest.TestCase):
    def test_writes_one_at_a_time(self):
        sink = BatchingStreamSink(batch_size=2)
        sink.write_one({"i": 1})
        sink.write_one({"i": 2})  # triggers flush
        self.assertEqual(len(sink.flushed), 1)
        self.assertEqual(sink.flushed[0], [{"i": 1}, {"i": 2}])
        sink.write_one({"i": 3})
        self.assertEqual(len(sink.flushed), 1)
        sink.flush()
        self.assertEqual(len(sink.flushed), 2)
        self.assertEqual(sink.flushed[1], [{"i": 3}])


# ---- integration: source -> sink via common.Pipeline -----------------


class PipelineIntegrationTests(unittest.TestCase):
    def test_csv_to_sqlite_via_pipeline(self):
        from common import Pipeline

        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "in.csv")
            _write_csv(
                path, ["id", "name"], [[1, "a"], [2, "b"], [3, "c"]]
            )
            conn = sqlite3.connect(":memory:")
            try:
                source = CsvSource(path)
                sink = SqliteSink(conn, "out")

                # Coerce id to int in the transform layer — the
                # whole point of a transform is to clean up the
                # stringly-typed CSV.
                def coerce_id(rows):
                    for r in rows:
                        yield {"id": int(r["id"]), "name": r["name"]}

                p = Pipeline(
                    "copy",
                    lambda: list(source.read()),
                    lambda rows: list(coerce_id(rows)),
                    sink.write,
                    retries=1,
                )
                p.run()
                rows = conn.execute(
                    "SELECT id, name FROM out ORDER BY id"
                ).fetchall()
                self.assertEqual(rows, [(1, "a"), (2, "b"), (3, "c")])
            finally:
                conn.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
