"""Unit tests for the loading module.

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


bulk_loader = _load("data_pipeline_design_loading_bulk", "bulk_loader.py")
streaming_loader = _load("data_pipeline_design_loading_stream", "streaming_loader.py")
upsert = _load("data_pipeline_design_loading_upsert", "upsert.py")
partitioning = _load("data_pipeline_design_loading_partitioning", "partitioning.py")
idempotency = _load("data_pipeline_design_loading_idempotency", "idempotency.py")


# =========================================================================
# Bulk loader tests
# =========================================================================


class BulkLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner
        self.q = QueryRunner(":memory:")

    def test_basic_load(self):
        result = bulk_loader.bulk_load(
            self.q, "users",
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
        )
        self.assertEqual(result["row_count"], 2)
        rows = self.q.query_all("SELECT id, name FROM users ORDER BY id")
        self.assertEqual(rows, [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])

    def test_load_replaces_existing(self):
        bulk_loader.bulk_load(
            self.q, "users", [{"id": 1, "name": "Alice"}]
        )
        # Second load replaces the entire table.
        bulk_loader.bulk_load(
            self.q, "users", [{"id": 2, "name": "Bob"}]
        )
        rows = self.q.query_all("SELECT id FROM users")
        self.assertEqual(rows, [{"id": 2}])

    def test_load_records_in_load_log(self):
        bulk_loader.bulk_load(
            self.q, "users", [{"id": 1, "name": "Alice"}]
        )
        history = bulk_loader.get_load_history(self.q, target="users")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["row_count"], 1)
        self.assertIsNotNone(history[0]["finished_at"])

    def test_empty_load(self):
        result = bulk_loader.bulk_load(self.q, "users", [])
        self.assertEqual(result["row_count"], 0)
        # Table is not created on an empty load.
        rows = self.q.query_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        self.assertEqual(rows, [])


# =========================================================================
# Streaming loader tests
# =========================================================================


class StreamingLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.broker = streaming_loader.InMemoryBroker()
        self.broker.create_topic("events", partitions=2)
        self.loaded_batches: list = []
        self.loaded_events: list = []

        def load_fn(events):
            self.loaded_batches.append(list(events))
            self.loaded_events.extend(events)

        self.loader = streaming_loader.StreamingLoader(
            self.broker,
            group="loader",
            topic="events",
            load_fn=load_fn,
            batch_size=3,
            linger_ms=10,
        )

    def test_publish_and_poll(self):
        self.broker.publish("events", {"id": 1}, key="a")
        self.broker.publish("events", {"id": 2}, key="b")
        n = self.loader.poll_once()
        # batch_size=3, only 2 events, not enough to flush
        self.assertEqual(n, 0)

    def test_batch_flush(self):
        for i in range(3):
            self.broker.publish("events", {"id": i}, key=f"k{i}")
        n = self.loader.poll_once()
        self.assertEqual(n, 3)
        self.assertEqual(self.loader.events_loaded, 3)
        self.assertEqual(self.loader.batches_loaded, 1)

    def test_offset_committed_after_load(self):
        for i in range(3):
            self.broker.publish("events", {"id": i}, key=f"k{i}")
        self.loader.poll_once()
        # A new consumer in the same group should see no events.
        loader2 = streaming_loader.StreamingLoader(
            self.broker, "loader", "events", lambda e: None, batch_size=100
        )
        n = loader2.poll_once()
        self.assertEqual(n, 0)

    def test_offset_not_committed_on_failure(self):
        def bad_load(events):
            raise RuntimeError("load failed")

        loader = streaming_loader.StreamingLoader(
            self.broker, "g2", "events", bad_load, batch_size=2, linger_ms=10
        )
        self.broker.publish("events", {"id": 1}, key="x")
        self.broker.publish("events", {"id": 2}, key="y")
        # poll_once with batch_size=2 should reach the threshold
        # and raise because the load function fails.
        with self.assertRaises(RuntimeError):
            loader.poll_once()
        # A retry with a fresh loader should re-deliver the same events.
        loader3 = streaming_loader.StreamingLoader(
            self.broker, "g2", "events", lambda e: None, batch_size=10
        )
        loader3.poll_once()
        n2 = loader3.flush()
        self.assertEqual(n2, 2)


# =========================================================================
# Upsert tests
# =========================================================================


class UpsertTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner
        self.q = QueryRunner(":memory:")
        self.q.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, status TEXT)"
        )
        # Insert 10 rows.
        rows = [{"id": i, "name": f"u{i}", "status": "active"} for i in range(1, 11)]
        for r in rows:
            self.q.execute(
                "INSERT INTO users VALUES (?, ?, ?)", (r["id"], r["name"], r["status"])
            )

    def test_spec_10_5_change(self):
        """Spec: insert 10, upsert 5 changes, assert 10 rows + 5 changed."""
        changes = [
            {"id": 1, "name": "u1", "status": "inactive"},
            {"id": 2, "name": "u2", "status": "inactive"},
            {"id": 3, "name": "u3", "status": "inactive"},
            {"id": 4, "name": "u4", "status": "inactive"},
            {"id": 5, "name": "u5", "status": "inactive"},
        ]
        result = upsert.merge_into(
            self.q, "users", changes, on_keys=["id"], update_cols=["status"]
        )
        self.assertEqual(result["updated"], 5)
        self.assertEqual(result["inserted"], 0)
        # Still 10 rows.
        n = self.q.query_one("SELECT COUNT(*) AS n FROM users")["n"]
        self.assertEqual(n, 10)
        # The 5 changed rows have status='inactive'.
        inactive = self.q.query_one(
            "SELECT COUNT(*) AS n FROM users WHERE status = 'inactive'"
        )["n"]
        self.assertEqual(inactive, 5)

    def test_insert_and_update(self):
        rows = [
            {"id": 1, "name": "u1", "status": "vip"},     # update
            {"id": 11, "name": "u11", "status": "active"},  # insert
        ]
        result = upsert.merge_into(
            self.q, "users", rows, on_keys=["id"], update_cols=["status", "name"]
        )
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["inserted"], 1)
        n = self.q.query_one("SELECT COUNT(*) AS n FROM users")["n"]
        self.assertEqual(n, 11)

    def test_missing_key_skipped(self):
        rows = [
            {"id": None, "name": "bad", "status": "x"},  # missing key
            {"id": 1, "name": "u1", "status": "x"},
        ]
        result = upsert.merge_into(
            self.q, "users", rows, on_keys=["id"], update_cols=["status"]
        )
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["updated"], 1)


# =========================================================================
# Partitioning tests
# =========================================================================


class PartitioningTests(unittest.TestCase):
    def setUp(self) -> None:
        from common import QueryRunner
        self.q = QueryRunner(":memory:")

    def test_date_partitioner(self):
        p = partitioning.DatePartitioner("order_date")
        self.assertEqual(
            p.partition_name({"order_date": "2024-01-15T10:00:00Z"}),
            "2024-01-15",
        )

    def test_key_partitioner(self):
        p = partitioning.KeyPartitioner("user_id")
        self.assertEqual(p.partition_name({"user_id": 42}), "42")

    def test_hash_partitioner_is_stable(self):
        p = partitioning.HashPartitioner("user_id", n_buckets=16)
        a = p.partition_name({"user_id": 42})
        b = p.partition_name({"user_id": 42})
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("bucket_"))

    def test_hash_partitioner_spread(self):
        p = partitioning.HashPartitioner("user_id", n_buckets=4)
        seen = set()
        for i in range(100):
            seen.add(p.partition_name({"user_id": i}))
        # All four buckets should appear with 100 different keys.
        self.assertEqual(len(seen), 4)

    def test_partitioned_load(self):
        rows = [
            {"id": 1, "order_date": "2024-01-15"},
            {"id": 2, "order_date": "2024-01-15"},
            {"id": 3, "order_date": "2024-01-16"},
        ]
        result = partitioning.partitioned_load(
            self.q, "orders", rows, partitioning.DatePartitioner("order_date")
        )
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(set(result["partitions"].keys()), {"2024-01-15", "2024-01-16"})
        # 2 rows in the 2024-01-15 partition, 1 in the other.
        # Dashes are replaced with underscores in the table name.
        self.assertEqual(
            self.q.query_one(
                "SELECT COUNT(*) AS n FROM orders__part_2024_01_15"
            )["n"],
            2,
        )


# =========================================================================
# Idempotency tests
# =========================================================================


class IdempotencyTests(unittest.TestCase):
    def test_cache_dedup(self):
        cache = idempotency.IdempotencyCache(max_size=10)
        self.assertTrue(cache.add("a"))
        self.assertFalse(cache.add("a"))
        self.assertTrue(cache.add("b"))
        self.assertEqual(len(cache), 2)

    def test_cache_eviction(self):
        cache = idempotency.IdempotencyCache(max_size=2)
        cache.add("a")
        cache.add("b")
        cache.add("c")  # evicts "a"
        self.assertNotIn("a", cache)
        self.assertIn("b", cache)
        self.assertIn("c", cache)

    def test_dedup_by_key(self):
        rows = [
            {"id": 1, "v": "a"},
            {"id": 2, "v": "b"},
            {"id": 1, "v": "c"},  # duplicate
        ]
        unique, dropped = idempotency.dedup_by_key(rows, key_fn=lambda r: r["id"])
        self.assertEqual(dropped, 1)
        self.assertEqual(len(unique), 2)

    def test_idempotent_load_first_call(self):
        registry = idempotency.LoadRegistry()
        calls = []

        def load_fn(rows):
            calls.append(rows)
            return len(rows)

        ran, result = idempotency.idempotent_load(
            load_fn, registry, load_id="L1", rows=[1, 2, 3]
        )
        self.assertTrue(ran)
        self.assertEqual(result, 3)
        self.assertEqual(calls, [[1, 2, 3]])

    def test_idempotent_load_second_call_noop(self):
        registry = idempotency.LoadRegistry()
        calls = []

        def load_fn(rows):
            calls.append(rows)
            return len(rows)

        idempotency.idempotent_load(load_fn, registry, "L1", [1, 2, 3])
        ran, result = idempotency.idempotent_load(
            load_fn, registry, "L1", [1, 2, 3]
        )
        self.assertFalse(ran)
        self.assertEqual(len(calls), 1)

    def test_idempotent_load_different_ids(self):
        registry = idempotency.LoadRegistry()
        calls = []

        def load_fn(rows):
            calls.append(rows)
            return len(rows)

        idempotency.idempotent_load(load_fn, registry, "L1", [1])
        idempotency.idempotent_load(load_fn, registry, "L2", [2])
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
