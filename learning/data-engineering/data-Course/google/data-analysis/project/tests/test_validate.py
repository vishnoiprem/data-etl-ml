"""Tests for the validation gate."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parent.parent / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from model import build_customer_model, build_sales_model  # noqa: E402
from validate import (  # noqa: E402
    ERROR,
    WARNING,
    ValidationReport,
    check_completeness,
    check_freshness,
    check_grain,
    check_no_negative_revenue,
    check_referential_integrity,
    validate_dataset,
)


# --------------------------------------------------------------------------
# Grain
# --------------------------------------------------------------------------


def test_a_unique_primary_key_passes():
    """A unique key is not a finding."""
    rows = [{"line_id": "l1"}, {"line_id": "l2"}]
    report = check_grain(rows, "line_id")
    assert report.passed
    assert not report.errors


def test_a_duplicated_primary_key_fails():
    """A duplicated key is an error — every measure is inflated."""
    rows = [{"line_id": "l1"}, {"line_id": "l1"}]
    report = check_grain(rows, "line_id")
    assert not report.passed
    assert report.by_severity(ERROR)
    assert report.errors[0].code == "grain.not_unique"


def test_a_null_primary_key_fails():
    """A null key is an error."""
    rows = [{"line_id": "l1"}, {"line_id": None}]
    report = check_grain(rows, "line_id")
    assert not report.passed
    assert any(f.code == "grain.null_key" for f in report.errors)


def test_a_repeated_order_id_is_not_a_grain_error():
    """The orders model's grain is the line, so `order_id` repeating is
    correct — and the gate must not flag it."""
    rows = [
        {"line_id": "l1", "order_id": "o1"},
        {"line_id": "l2", "order_id": "o1"},
    ]
    report = check_grain(rows, "line_id")
    assert report.passed


# --------------------------------------------------------------------------
# Referential integrity
# --------------------------------------------------------------------------


def test_an_unresolved_foreign_key_fails():
    """A foreign key with no matching row is an error."""
    rows = [{"customer_id": "c1"}, {"customer_id": "c9999"}]
    lookup = [{"customer_id": "c1"}]
    report = check_referential_integrity(rows, "customer_id", lookup, "customer_id")
    assert not report.passed
    assert report.errors[0].code == "referential.unresolved"
    assert report.errors[0].count == 1


def test_a_resolved_foreign_key_passes():
    """Every foreign key resolving is not a finding."""
    rows = [{"customer_id": "c1"}, {"customer_id": "c2"}]
    lookup = [{"customer_id": "c1"}, {"customer_id": "c2"}]
    report = check_referential_integrity(rows, "customer_id", lookup, "customer_id")
    assert report.passed


def test_a_null_foreign_key_is_not_a_referential_error():
    """A null foreign key is a completeness issue, not a referential one."""
    rows = [{"customer_id": None}]
    lookup = [{"customer_id": "c1"}]
    report = check_referential_integrity(rows, "customer_id", lookup, "customer_id")
    assert report.passed


# --------------------------------------------------------------------------
# Completeness
# --------------------------------------------------------------------------


def test_a_missing_id_is_an_error():
    """A missing identifier is an error."""
    rows = [{"customer_id": "c1"}, {"customer_id": ""}]
    report = check_completeness(rows, ["customer_id"])
    assert not report.passed
    assert report.errors[0].severity == ERROR


def test_a_missing_non_id_is_a_warning():
    """A missing descriptive field is a warning, not a failure."""
    rows = [{"region": "EMEA"}, {"region": None}]
    report = check_completeness(rows, ["region"])
    assert report.passed
    assert report.by_severity(WARNING)


def test_a_complete_field_is_not_a_finding():
    """A fully populated field produces nothing."""
    rows = [{"region": "EMEA"}, {"region": "AMER"}]
    report = check_completeness(rows, ["region"])
    assert not report.findings


# --------------------------------------------------------------------------
# Freshness
# --------------------------------------------------------------------------


def test_fresh_data_passes():
    """Data from today is fresh."""
    rows = [{"created_at": "2026-03-15"}]
    report = check_freshness(
        rows, "created_at", max_age_days=2, today=date(2026, 3, 15)
    )
    assert report.passed


def test_stale_data_fails():
    """Data from last week is stale, and that is an error."""
    rows = [{"created_at": "2026-03-01"}]
    report = check_freshness(
        rows, "created_at", max_age_days=2, today=date(2026, 3, 15)
    )
    assert not report.passed
    assert report.errors[0].code == "freshness.stale"


def test_data_with_no_dates_is_a_warning():
    """A dataset with no dates cannot be checked for freshness."""
    rows = [{"created_at": None}]
    report = check_freshness(rows, "created_at", today=date(2026, 3, 15))
    assert report.passed
    assert report.by_severity(WARNING)


# --------------------------------------------------------------------------
# Negative values
# --------------------------------------------------------------------------


def test_a_negative_revenue_row_is_a_warning():
    """A refund is legitimate, so it warns rather than fails."""
    rows = [{"total_amount": -50.0}, {"total_amount": 100.0}]
    report = check_no_negative_revenue(rows)
    assert report.passed
    assert report.by_severity(WARNING)[0].count == 1


# --------------------------------------------------------------------------
# The whole gate
# --------------------------------------------------------------------------


def test_the_gate_passes_on_clean_data():
    """Clean data passes every check."""
    model = build_sales_model()
    rows = [
        {
            "line_id": "l1",
            "order_id": "o1",
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
        {
            "line_id": "l2",
            "order_id": "o2",
            "customer_id": "c2",
            "created_at": "2026-03-15",
            "total_amount": 200.0,
        },
    ]
    report = validate_dataset(
        rows,
        model,
        required=["line_id", "customer_id"],
        today=date(2026, 3, 15),
    )
    assert report.passed, report.to_text()


def test_the_gate_fails_on_the_planted_sample_data():
    """The sample data's duplicate row is caught."""
    model = build_sales_model()
    rows = [
        {
            "line_id": "l1",
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
        {
            "line_id": "l1",
            "customer_id": "c1",
            "created_at": "2026-03-15",
            "total_amount": 100.0,
        },
    ]
    report = validate_dataset(rows, model, today=date(2026, 3, 15))
    assert not report.passed
    assert any(f.code == "grain.not_unique" for f in report.errors)


def test_the_report_renders_as_text():
    """The text report is readable."""
    report = ValidationReport(rows_checked=3, source="orders.csv")
    report.add(ERROR, "test.code", "Something is wrong", count=2)
    text = report.to_text()
    assert "PASS" not in text
    assert "FAIL" in text
    assert "Something is wrong" in text
    assert "orders.csv" in text


def test_the_report_serialises_to_json():
    """The report is JSON-serialisable."""
    report = ValidationReport(rows_checked=3, source="orders.csv")
    report.add(ERROR, "test.code", "Something is wrong", count=2)
    payload = report.to_dict()
    assert payload["rows_checked"] == 3
    assert payload["passed"] is False
    assert payload["findings"][0]["code"] == "test.code"


def test_the_customer_model_is_validated_too():
    """The gate works on any model."""
    model = build_customer_model()
    rows = [
        {
            "customer_id": "c1",
            "signup_date": "2026-03-14",
            "segment": "smb",
        },
    ]
    report = validate_dataset(
        rows, model, required=["customer_id"], today=date(2026, 3, 15)
    )
    assert report.passed, report.to_text()
