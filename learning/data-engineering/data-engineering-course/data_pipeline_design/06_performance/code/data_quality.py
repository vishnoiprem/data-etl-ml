"""Data quality helper: the 5 standard checks every pipeline should run.

Used in Lesson 28 (`design/28_data_quality.md`). This module is
the reference implementation; the tests in
`tests/test_data_quality.py` pin down the behavior.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


@dataclass
class CheckResult:
    """The outcome of one quality check."""

    name: str
    passed: bool
    actual: Any
    expected: Any
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "actual": self.actual,
            "expected": self.expected,
            "message": self.message,
        }


@dataclass
class QualityCheck:
    """Run the 5 standard data-quality checks against a tiny in-memory dataset.

    The class is deliberately small — it is the *reference
    implementation* used in Lesson 28 and pinned by
    `tests/test_data_quality.py`. Real-world usage would call
    Great Expectations / dbt tests / Soda, but the *categories*
    of checks are the same.

    The 5 checks:
    1. Row count vs. source (delta within tolerance)
    2. Null rate per column (under threshold)
    3. Distribution drift (KS-style 2-sample summary)
    4. Freshness (max(ts) within SLA of now)
    5. Schema conformance (column presence + dtype)
    """

    # Mapping column name -> expected dtype. ``int``, ``float``,
    # ``str``, ``bool`` are the supported types.
    expected_schema: Dict[str, str] = field(default_factory=dict)

    def _row_count_check(
        self,
        actual: int,
        expected: int,
        tolerance_pct: float = 5.0,
    ) -> CheckResult:
        if expected == 0:
            return CheckResult(
                "row_count",
                actual == 0,
                actual,
                expected,
                "expected zero rows; cannot compute tolerance",
            )
        delta_pct = abs(actual - expected) / expected * 100
        return CheckResult(
            "row_count",
            delta_pct <= tolerance_pct,
            actual,
            expected,
            f"row-count delta {delta_pct:.1f}% > {tolerance_pct}%",
        )

    def _null_rate_check(
        self,
        column: str,
        values: Sequence[Any],
        threshold_pct: float = 5.0,
    ) -> CheckResult:
        if not values:
            return CheckResult(
                f"null_rate[{column}]",
                True,
                0.0,
                0.0,
                "empty input; no nulls to check",
            )
        null_count = sum(1 for v in values if v is None)
        rate_pct = null_count / len(values) * 100
        return CheckResult(
            f"null_rate[{column}]",
            rate_pct <= threshold_pct,
            round(rate_pct, 2),
            threshold_pct,
            f"null rate {rate_pct:.1f}% > {threshold_pct}%",
        )

    def _distribution_drift_check(
        self,
        reference: Sequence[float],
        current: Sequence[float],
        max_mean_delta_pct: float = 10.0,
    ) -> CheckResult:
        if not reference or not current:
            return CheckResult(
                "distribution_drift",
                True,
                None,
                None,
                "one side empty; skipping",
            )
        ref_mean = sum(reference) / len(reference)
        cur_mean = sum(current) / len(current)
        if ref_mean == 0:
            delta_pct = 0.0 if cur_mean == 0 else 100.0
        else:
            delta_pct = abs(cur_mean - ref_mean) / abs(ref_mean) * 100
        return CheckResult(
            "distribution_drift",
            delta_pct <= max_mean_delta_pct,
            round(cur_mean, 4),
            round(ref_mean, 4),
            f"mean delta {delta_pct:.1f}% > {max_mean_delta_pct}%",
        )

    def _freshness_check(
        self,
        max_ts: float,
        now_ts: float,
        sla_seconds: float = 3600.0,
    ) -> CheckResult:
        age = now_ts - max_ts
        return CheckResult(
            "freshness",
            age <= sla_seconds,
            round(age, 1),
            sla_seconds,
            f"data is {age:.0f}s old; SLA is {sla_seconds:.0f}s",
        )

    def _schema_check(
        self,
        actual: Dict[str, str],
    ) -> CheckResult:
        missing = set(self.expected_schema) - set(actual)
        type_mismatches: List[str] = []
        for col, want in self.expected_schema.items():
            got = actual.get(col)
            if got is None:
                continue
            # Normalize SQLite-style "INTEGER"/"TEXT"/"REAL" to our short names.
            norm = self._normalize_type(got)
            if norm != want:
                type_mismatches.append(f"{col}:{got}!={want}")
        passed = not missing and not type_mismatches
        return CheckResult(
            "schema",
            passed,
            actual,
            dict(self.expected_schema),
            f"missing={sorted(missing)} mismatches={type_mismatches}",
        )

    @staticmethod
    def _normalize_type(t: str) -> str:
        t = (t or "").lower()
        if "int" in t:
            return "int"
        if "char" in t or "text" in t or "varchar" in t:
            return "str"
        if "real" in t or "float" in t or "double" in t or "numeric" in t:
            return "float"
        if "bool" in t:
            return "bool"
        return t

    # ---- public API -----------------------------------------------------

    def run_row_count(
        self, actual: int, expected: int, tolerance_pct: float = 5.0
    ) -> CheckResult:
        return self._row_count_check(actual, expected, tolerance_pct)

    def run_null_rate(
        self,
        column: str,
        values: Sequence[Any],
        threshold_pct: float = 5.0,
    ) -> CheckResult:
        return self._null_rate_check(column, values, threshold_pct)

    def run_distribution_drift(
        self,
        reference: Sequence[float],
        current: Sequence[float],
        max_mean_delta_pct: float = 10.0,
    ) -> CheckResult:
        return self._distribution_drift_check(
            reference, current, max_mean_delta_pct
        )

    def run_freshness(
        self,
        max_ts: float,
        now_ts: float,
        sla_seconds: float = 3600.0,
    ) -> CheckResult:
        return self._freshness_check(max_ts, now_ts, sla_seconds)

    def run_schema(self, actual: Dict[str, str]) -> CheckResult:
        return self._schema_check(actual)

    def run_all(
        self,
        *,
        actual_row_count: int,
        expected_row_count: int,
        column_values: Dict[str, Sequence[Any]],
        reference_distributions: Dict[str, Sequence[float]],
        current_distributions: Dict[str, Sequence[float]],
        max_ts: float,
        now_ts: float,
        sla_seconds: float = 3600.0,
        actual_schema: Optional[Dict[str, str]] = None,
    ) -> List[CheckResult]:
        results: List[CheckResult] = []
        results.append(
            self.run_row_count(actual_row_count, expected_row_count)
        )
        for col, vals in column_values.items():
            results.append(self.run_null_rate(col, vals))
        for col, ref in reference_distributions.items():
            cur = current_distributions.get(col, [])
            results.append(self.run_distribution_drift(ref, cur))
        results.append(self.run_freshness(max_ts, now_ts, sla_seconds))
        if actual_schema is not None:
            results.append(self.run_schema(actual_schema))
        return results


if __name__ == "__main__":
    # Demo: a tiny end-to-end run.
    qc = QualityCheck(expected_schema={"id": "int", "name": "str"})
    results = qc.run_all(
        actual_row_count=100,
        expected_row_count=102,
        column_values={"id": [1, 2, 3, 4, None], "name": ["a", "b", "c", "d", "e"]},
        reference_distributions={"value": [10.0, 11.0, 12.0, 13.0, 14.0]},
        current_distributions={"value": [10.5, 10.8, 11.2, 11.5, 12.0]},
        max_ts=1_700_000_000,
        now_ts=1_700_000_300,
        sla_seconds=600,
        actual_schema={"id": "INTEGER", "name": "TEXT"},
    )
    for r in results:
        print(r.to_dict())
