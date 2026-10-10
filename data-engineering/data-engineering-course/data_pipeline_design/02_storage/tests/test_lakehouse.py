"""Tests for the lakehouse reference implementation (Lesson 08)."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "code")))

from lakehouse import BronzeLayer, GoldLayer, Lakehouse, Record, SilverLayer  # type: ignore  # noqa: E402


class TestBronzeLayer(unittest.TestCase):
    def test_ingest_appends(self):
        b = BronzeLayer()
        b.ingest(Record({"id": 1}))
        b.ingest(Record({"id": 2}))
        self.assertEqual(len(b), 2)


class TestSilverLayer(unittest.TestCase):
    def test_dedup_keeps_latest(self):
        s = SilverLayer(key_fields=["id"])
        s.conform(Record({"id": 1, "v": "first"}, ingested_at=100))
        s.conform(Record({"id": 1, "v": "second"}, ingested_at=200))
        self.assertEqual(len(s), 1)
        self.assertEqual(s.storage["1"].data["v"], "second")

    def test_distinct_keys_stay_distinct(self):
        s = SilverLayer(key_fields=["id"])
        s.conform(Record({"id": 1, "v": "a"}))
        s.conform(Record({"id": 2, "v": "b"}))
        self.assertEqual(len(s), 2)


class TestGoldLayer(unittest.TestCase):
    def test_sum_aggregation(self):
        g = GoldLayer()
        rows = [
            Record({"customer_id": 1, "amount": 10}),
            Record({"customer_id": 1, "amount": 20}),
            Record({"customer_id": 2, "amount": 5}),
        ]
        g.aggregate(rows, group_by=["customer_id"], measure="amount", agg="sum")
        self.assertEqual(len(g), 2)
        out = {r["customer_id"]: r["amount"] for r in g.storage}
        self.assertEqual(out, {1: 30, 2: 5})

    def test_count_aggregation(self):
        g = GoldLayer()
        rows = [
            Record({"customer_id": 1, "amount": 10}),
            Record({"customer_id": 1, "amount": 20}),
            Record({"customer_id": 2, "amount": 5}),
        ]
        g.aggregate(rows, group_by=["customer_id"], measure="amount", agg="count")
        out = {r["customer_id"]: r["amount"] for r in g.storage}
        self.assertEqual(out, {1: 2, 2: 1})

    def test_avg_aggregation(self):
        g = GoldLayer()
        rows = [
            Record({"customer_id": 1, "amount": 10}),
            Record({"customer_id": 1, "amount": 20}),
        ]
        g.aggregate(rows, group_by=["customer_id"], measure="amount", agg="avg")
        out = {r["customer_id"]: r["amount"] for r in g.storage}
        self.assertEqual(out, {1: 15.0})


class TestLakehouseEndToEnd(unittest.TestCase):
    def test_three_layer_flow(self):
        lh = Lakehouse(key_fields=["order_id"])
        lh.ingest({"order_id": 1, "customer_id": 100, "amount": 50.0})
        lh.ingest({"order_id": 2, "customer_id": 100, "amount": 75.0})
        lh.ingest({"order_id": 1, "customer_id": 100, "amount": 60.0})  # late
        lh.promote()
        # Bronze has 3 events; silver has 2 distinct order_ids.
        self.assertEqual(len(lh.bronze), 3)
        self.assertEqual(len(lh.silver), 2)
        # Gold: total amount per customer.
        rows = list(lh.silver.storage.values())
        lh.gold.aggregate(
            rows, group_by=["customer_id"], measure="amount", agg="sum"
        )
        self.assertEqual(len(lh.gold), 1)
        self.assertEqual(lh.gold.storage[0]["amount"], 135.0)

    def test_partition_path_format(self):
        lh = Lakehouse(key_fields=["id"])
        path = lh.partition_path("silver", "year", "2026")
        self.assertEqual(path, "silver/year=2026/")


if __name__ == "__main__":
    unittest.main()
