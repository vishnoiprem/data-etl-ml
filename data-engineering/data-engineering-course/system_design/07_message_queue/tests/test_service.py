"""Unit tests for MessageQueueService.

Run with:
    cd system_design
    python -m unittest 07_message_queue.tests.test_service -v
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    MessageQueueService,
    MAX_PARTITIONS,
    DEFAULT_PARTITIONS,
)


class TestTopics(unittest.TestCase):
    def setUp(self):
        self.svc = MessageQueueService()

    def test_create_and_list(self):
        t = self.svc.create_topic("events", partitions=3)
        self.assertEqual(t.name, "events")
        self.assertEqual(t.partitions, 3)
        topics = self.svc.list_topics()
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0].name, "events")

    def test_duplicate_topic_rejected(self):
        self.svc.create_topic("events")
        with self.assertRaises(ValueError):
            self.svc.create_topic("events")

    def test_too_many_partitions_rejected(self):
        with self.assertRaises(ValueError):
            self.svc.create_topic("big", partitions=MAX_PARTITIONS + 1)

    def test_delete_topic(self):
        self.svc.create_topic("temp")
        # Write a record so the partition log exists.
        self.svc.produce("temp", key="k", value="v")
        self.assertTrue(self.svc.delete_topic("temp"))
        self.assertIsNone(self.svc.get_topic("temp"))
        self.assertEqual(self.svc.topic_log_size("temp", 0), 0)


class TestProduce(unittest.TestCase):
    def setUp(self):
        self.svc = MessageQueueService()
        self.svc.create_topic("events", partitions=3)

    def test_produce_assigns_offset_zero_for_first_record(self):
        r = self.svc.produce("events", key="k1", value="hello")
        self.assertEqual(r.offset, 0)
        self.assertEqual(r.partition, hash("k1") % 3)
        self.assertGreater(r.message_id, 0)

    def test_same_key_lands_on_same_partition(self):
        # Design §3 / §5 — per-key ordering requires sticky hashing.
        partitions = set()
        for i in range(10):
            r = self.svc.produce("events", key="sticky", value=f"v{i}")
            partitions.add(r.partition)
        self.assertEqual(len(partitions), 1)

    def test_round_robin_for_keyless_produce(self):
        # No key -> spread across all partitions.
        partitions = set()
        for i in range(DEFAULT_PARTITIONS * 2):
            r = self.svc.produce("events", value=f"v{i}")
            partitions.add(r.partition)
        self.assertEqual(partitions, set(range(DEFAULT_PARTITIONS)))

    def test_offsets_increase_per_partition(self):
        r1 = self.svc.produce("events", key="k", value="a")
        r2 = self.svc.produce("events", key="k", value="b")
        self.assertEqual(r1.partition, r2.partition)
        self.assertEqual(r2.offset, r1.offset + 1)

    def test_value_must_be_stringifiable(self):
        # Non-string values are coerced — the broker treats payload
        # as opaque bytes (here: str).
        r = self.svc.produce("events", value=42)
        self.assertEqual(r.value, "42")

    def test_produce_to_unknown_topic_raises(self):
        with self.assertRaises(ValueError):
            self.svc.produce("nope", value="x")


class TestConsumerGroups(unittest.TestCase):
    def setUp(self):
        self.svc = MessageQueueService()
        self.svc.create_topic("events", partitions=2)
        for i in range(5):
            self.svc.produce("events", key=f"k{i}", value=f"v{i}")

    def test_create_and_list_groups(self):
        g = self.svc.create_group("workers")
        self.assertEqual(g.name, "workers")
        self.assertEqual(self.svc.list_groups()[0].name, "workers")

    def test_duplicate_group_rejected(self):
        self.svc.create_group("workers")
        with self.assertRaises(ValueError):
            self.svc.create_group("workers")

    def test_consume_returns_records_earliest(self):
        self.svc.create_group("g1", reset="earliest")
        batch = self.svc.consume("events", group="g1", max_records=100)
        # 5 records across 2 partitions — round-robin fetch from the
        # most-behind partition returns at least one, but the cap is
        # the partition's log size. Repeat to drain.
        seen = []
        for _ in range(10):
            seen.extend(self.svc.consume("events", group="g1", max_records=100))
            if len(seen) >= 5:
                break
        self.assertEqual(len(seen), 5)
        # All 5 records have a unique offset (across partitions combined).
        offsets = [(r.partition, r.offset) for r in seen]
        self.assertEqual(len(set(offsets)), 5)

    def test_consume_does_not_repeat_after_commit(self):
        self.svc.create_group("g1", reset="earliest")
        # Drain.
        for _ in range(10):
            self.svc.consume("events", group="g1", max_records=100)
        # Second pass should return nothing — all committed.
        again = self.svc.consume("events", group="g1", max_records=100)
        self.assertEqual(again, [])

    def test_consume_without_commit_replays(self):
        self.svc.create_group("g1", reset="earliest")
        self.svc.consume("events", group="g1", max_records=100, commit=False)
        # The committed offset never moved, so a second call returns
        # the same records again (the design's at-least-once contract).
        again = self.svc.consume("events", group="g1", max_records=100)
        self.assertGreater(len(again), 0)

    def test_commit_explicit(self):
        self.svc.create_group("g1", reset="earliest")
        self.svc.commit("g1", "events", 0, 0)
        self.svc.commit("g1", "events", 1, 0)
        self.assertEqual(self.svc.group_offsets("g1")["events:0"], 0)
        self.assertEqual(self.svc.group_offsets("g1")["events:1"], 0)

    def test_separate_groups_have_independent_offsets(self):
        self.svc.create_group("g1", reset="earliest")
        self.svc.create_group("g2", reset="earliest")
        self.svc.consume("events", group="g1", max_records=100)
        # g2 still has all records available.
        again = self.svc.consume("events", group="g2", max_records=100)
        self.assertGreater(len(again), 0)

    def test_consume_latest_skips_history(self):
        self.svc.create_group("late", reset="latest")
        # New produce after the group is created.
        self.svc.produce("events", key="new", value="now")
        batch = self.svc.consume("events", group="late", max_records=100)
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0].value, "now")

    def test_manual_reset_on_consume(self):
        # Group has no committed offset and reset=earliest, so
        # calling consume with reset=latest on the first fetch
        # skips history.
        self.svc.create_group("g1", reset="earliest")
        # Add a new record AFTER the group is created; consuming
        # with reset=latest returns just it.
        r = self.svc.produce("events", key="newk", value="brand-new")
        batch = self.svc.consume(
            "events", group="g1", max_records=100, reset="latest"
        )
        values = [x.value for x in batch]
        self.assertIn("brand-new", values)


class TestScaleChecks(unittest.TestCase):
    def test_stats(self):
        svc = MessageQueueService()
        svc.create_topic("t", partitions=2)
        for i in range(4):
            svc.produce("t", key=f"k{i}", value=str(i))
        svc.create_group("g")
        s = svc.stats()
        self.assertEqual(s["topics"], 1)
        self.assertEqual(s["groups"], 1)
        self.assertEqual(s["total_records"], 4)


if __name__ == "__main__":
    unittest.main()
