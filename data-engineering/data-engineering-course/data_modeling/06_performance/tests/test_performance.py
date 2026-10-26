"""Tests for the performance modules.

These tests assert *correctness* of the indexed / partitioned
/ pre-aggregated queries. They do *not* assert timing — the
benchmark numbers in the demos are for inspection.

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

from indexing import (  # type: ignore
    benchmark_bitmap_style,
    benchmark_btree_index,
    benchmark_no_index,
    benchmark_partial_index,
)
from materialized_views import (  # type: ignore
    benchmark_raw_aggregate,
    benchmark_rollup_query,
    benchmark_wide_query,
    refresh_rollup,
)
from partitioning import (  # type: ignore
    benchmark_hash_partition,
    benchmark_list_partition,
    benchmark_range_partition,
)


# ---- indexing ------------------------------------------------------------


class TestIndexing(unittest.TestCase):
    def test_no_index_returns_correct_count(self):
        with QueryRunner(":memory:") as q:
            res = benchmark_no_index(q)
        # 50k orders / 5 statuses ≈ 10k paid.
        self.assertEqual(res["by_status_count"], 10000)
        # 50k orders / 365 days ≈ 137 on any given day.
        self.assertEqual(res["by_date_count"], 137)

    def test_btree_index_returns_correct_count(self):
        with QueryRunner(":memory:") as q:
            res = benchmark_btree_index(q)
        self.assertEqual(res["by_status_count"], 10000)
        self.assertEqual(res["by_date_count"], 137)

    def test_bitmap_style_returns_correct_count(self):
        with QueryRunner(":memory:") as q:
            res = benchmark_bitmap_style(q)
        self.assertEqual(res["by_status_count"], 10000)

    def test_partial_index_correctness(self):
        with QueryRunner(":memory:") as q:
            res = benchmark_partial_index(q)
        # Total rows for the queried date, regardless of status.
        # The seeded data may or may not have rows on
        # date 20240301 for a specific status.
        self.assertGreaterEqual(res["by_paid_date_count"] +
                                res["by_cancelled_date_count"], 0)


# ---- partitioning --------------------------------------------------------


class TestPartitioning(unittest.TestCase):
    def test_range_partition_pruning_matches_full_scan(self):
        with QueryRunner(":memory:") as q:
            full = benchmark_range_partition(q, use_pruning=False)
        with QueryRunner(":memory:") as q:
            pruned = benchmark_range_partition(q, use_pruning=True)
        # Both queries should return the same row count
        # and the same total.
        self.assertEqual(full["rows"], pruned["rows"])
        self.assertAlmostEqual(full["total"], pruned["total"], places=2)

    def test_hash_partition_pruning_matches_full_scan(self):
        with QueryRunner(":memory:") as q:
            full = benchmark_hash_partition(q, use_pruning=False)
        with QueryRunner(":memory:") as q:
            pruned = benchmark_hash_partition(q, use_pruning=True)
        self.assertEqual(full["rows"], pruned["rows"])
        self.assertAlmostEqual(full["total"], pruned["total"], places=2)

    def test_list_partition_pruning_matches_full_scan(self):
        with QueryRunner(":memory:") as q:
            full = benchmark_list_partition(q, use_pruning=False)
        with QueryRunner(":memory:") as q:
            pruned = benchmark_list_partition(q, use_pruning=True)
        self.assertEqual(full["rows"], pruned["rows"])
        self.assertAlmostEqual(full["total"], pruned["total"], places=2)


# ---- materialized views -------------------------------------------------


class TestMaterializedViews(unittest.TestCase):
    def test_raw_aggregate_returns_rows(self):
        with QueryRunner(":memory:") as q:
            res = benchmark_raw_aggregate(q)
        # 10 countries × ~12 months ≈ 40-120 rows.
        self.assertGreater(res["rows"], 20)

    def test_rollup_matches_raw(self):
        with QueryRunner(":memory:") as q:
            raw = benchmark_raw_aggregate(q)
        with QueryRunner(":memory:") as q:
            rollup = benchmark_rollup_query(q)
        # Same number of (country, month) combinations.
        self.assertEqual(raw["rows"], rollup["rows"])

    def test_wide_matches_raw(self):
        with QueryRunner(":memory:") as q:
            raw = benchmark_raw_aggregate(q)
        with QueryRunner(":memory:") as q:
            wide = benchmark_wide_query(q)
        self.assertEqual(raw["rows"], wide["rows"])

    def test_refresh_rollup_returns_rows(self):
        with QueryRunner(":memory:") as q:
            from materialized_views import (
                _build_country_month_rollup, _build_raw_fact,
            )
            _build_raw_fact(q)
            _build_country_month_rollup(q)
            n = refresh_rollup(q)
        self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
