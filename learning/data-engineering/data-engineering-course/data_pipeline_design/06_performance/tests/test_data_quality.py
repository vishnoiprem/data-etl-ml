"""Tests for the data quality reference implementation (Lesson 28).

These tests pin down the behavior of the 5 standard quality
checks: row count, null rate, distribution drift, freshness, and
schema conformance.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make the course root importable so we can import the module
HERE = os.path.dirname(os.path.abspath(__file__))
COURSE_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, COURSE_ROOT)
sys.path.insert(
    0, os.path.abspath(os.path.join(HERE, "..", "code"))
)

from data_quality import CheckResult, QualityCheck  # type: ignore  # noqa: E402


class TestRowCountCheck(unittest.TestCase):
    def test_within_tolerance_passes(self):
        qc = QualityCheck()
        r = qc.run_row_count(actual=98, expected=100, tolerance_pct=5.0)
        self.assertTrue(r.passed)
        self.assertEqual(r.name, "row_count")

    def test_outside_tolerance_fails(self):
        qc = QualityCheck()
        r = qc.run_row_count(actual=80, expected=100, tolerance_pct=5.0)
        self.assertFalse(r.passed)

    def test_zero_expected_passes_if_actual_zero(self):
        qc = QualityCheck()
        r = qc.run_row_count(actual=0, expected=0, tolerance_pct=5.0)
        self.assertTrue(r.passed)


class TestNullRateCheck(unittest.TestCase):
    def test_low_null_rate_passes(self):
        qc = QualityCheck()
        r = qc.run_null_rate("col", [1, 2, 3, None], threshold_pct=50.0)
        self.assertTrue(r.passed)
        self.assertEqual(r.actual, 25.0)

    def test_high_null_rate_fails(self):
        qc = QualityCheck()
        r = qc.run_null_rate("col", [None, None, None, 1], threshold_pct=10.0)
        self.assertFalse(r.passed)
        self.assertEqual(r.actual, 75.0)

    def test_empty_input_passes(self):
        qc = QualityCheck()
        r = qc.run_null_rate("col", [], threshold_pct=5.0)
        self.assertTrue(r.passed)


class TestDistributionDriftCheck(unittest.TestCase):
    def test_stable_distribution_passes(self):
        qc = QualityCheck()
        ref = [10.0, 11.0, 12.0, 13.0, 14.0]
        cur = [10.5, 10.8, 11.2, 11.5, 12.0]
        r = qc.run_distribution_drift(ref, cur, max_mean_delta_pct=20.0)
        self.assertTrue(r.passed)

    def test_drifted_distribution_fails(self):
        qc = QualityCheck()
        ref = [10.0, 11.0, 12.0, 13.0, 14.0]
        cur = [100.0, 110.0, 120.0, 130.0, 140.0]
        r = qc.run_distribution_drift(ref, cur, max_mean_delta_pct=10.0)
        self.assertFalse(r.passed)

    def test_empty_input_passes(self):
        qc = QualityCheck()
        r = qc.run_distribution_drift([], [1.0], max_mean_delta_pct=10.0)
        self.assertTrue(r.passed)


class TestFreshnessCheck(unittest.TestCase):
    def test_fresh_data_passes(self):
        qc = QualityCheck()
        r = qc.run_freshness(max_ts=100, now_ts=200, sla_seconds=300)
        self.assertTrue(r.passed)
        self.assertEqual(r.actual, 100.0)

    def test_stale_data_fails(self):
        qc = QualityCheck()
        r = qc.run_freshness(max_ts=100, now_ts=10_000, sla_seconds=300)
        self.assertFalse(r.passed)


class TestSchemaCheck(unittest.TestCase):
    def test_matching_schema_passes(self):
        qc = QualityCheck(expected_schema={"id": "int", "name": "str"})
        r = qc.run_schema({"id": "INTEGER", "name": "TEXT"})
        self.assertTrue(r.passed, r.message)

    def test_missing_column_fails(self):
        qc = QualityCheck(expected_schema={"id": "int", "name": "str"})
        r = qc.run_schema({"id": "INTEGER"})
        self.assertFalse(r.passed)
        self.assertIn("name", r.message)

    def test_type_mismatch_fails(self):
        qc = QualityCheck(expected_schema={"id": "int"})
        r = qc.run_schema({"id": "TEXT"})
        self.assertFalse(r.passed)


class TestRunAll(unittest.TestCase):
    """End-to-end: the 5 checks in one call."""

    def test_run_all_happy_path(self):
        qc = QualityCheck(expected_schema={"id": "int", "name": "str"})
        results = qc.run_all(
            actual_row_count=98,
            expected_row_count=100,
            column_values={"id": [1, 2, 3, 4, 5], "name": ["a", "b", "c", "d", "e"]},
            reference_distributions={"v": [10.0, 11.0, 12.0]},
            current_distributions={"v": [10.2, 10.8, 11.5]},
            max_ts=1_700_000_000,
            now_ts=1_700_000_100,
            sla_seconds=300,
            actual_schema={"id": "INTEGER", "name": "TEXT"},
        )
        self.assertEqual(len(results), 6)
        self.assertTrue(all(r.passed for r in results), [r.to_dict() for r in results])

    def test_run_all_flags_failure(self):
        qc = QualityCheck(expected_schema={"id": "int"})
        results = qc.run_all(
            actual_row_count=10,                       # way under
            expected_row_count=100,
            column_values={"id": [None, None, None, 1]},  # high nulls
            reference_distributions={},
            current_distributions={},
            max_ts=1_700_000_000,
            now_ts=1_700_000_000 + 10_000,            # 10000s stale
            sla_seconds=300,
            actual_schema={"id": "TEXT"},             # wrong type
        )
        # 5 checks: row_count, null_rate, freshness, schema = 4 results
        # (no distribution since both empty, plus row_count + null + freshness + schema = 4)
        # Actually: row_count (1) + null_rate per col (1) + freshness (1) + schema (1) = 4
        self.assertEqual(len(results), 4)
        self.assertFalse(any(r.passed for r in results))


if __name__ == "__main__":
    unittest.main()
