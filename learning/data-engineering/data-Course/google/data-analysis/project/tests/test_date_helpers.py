"""Tests for the date spine, the timeframes and the date filters."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parent.parent / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from date_helpers import (  # noqa: E402
    TRUNCATED_TIMEFRAMES,
    build_date_spine,
    date_filter_bounds,
    describe_timeframe,
    fill_missing_periods,
    month_label,
    months_between,
    parse_date,
    period_over_period,
    previous_period,
    truncate_date,
)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def test_parse_date_accepts_an_iso_string():
    """An ISO date string parses."""
    assert parse_date("2026-03-15") == date(2026, 3, 15)


def test_parse_date_accepts_a_date_object():
    """A date object passes through."""
    assert parse_date(date(2026, 3, 15)) == date(2026, 3, 15)


def test_parse_date_accepts_a_datetime():
    """A datetime is truncated to its date."""
    from datetime import datetime

    assert parse_date(datetime(2026, 3, 15, 14, 30)) == date(2026, 3, 15)


def test_parse_date_rejects_nonsense():
    """An unparseable value raises."""
    with pytest.raises(ValueError, match="cannot parse"):
        parse_date("not a date")


# --------------------------------------------------------------------------
# Truncation — the timeframe logic
# --------------------------------------------------------------------------


def test_truncate_to_day_is_the_day_itself():
    """Day truncation changes nothing."""
    assert truncate_date("2026-03-15", "day") == date(2026, 3, 15)


def test_truncate_to_month_is_the_first_of_the_month():
    """Month truncation gives 1 March."""
    assert truncate_date("2026-03-15", "month") == date(2026, 3, 1)


def test_truncate_to_quarter_is_the_first_of_the_quarter():
    """March is in Q1, so it truncates to 1 January."""
    assert truncate_date("2026-03-15", "quarter") == date(2026, 1, 1)
    assert truncate_date("2026-05-15", "quarter") == date(2026, 4, 1)
    assert truncate_date("2026-08-15", "quarter") == date(2026, 7, 1)
    assert truncate_date("2026-11-15", "quarter") == date(2026, 10, 1)


def test_truncate_to_year_is_the_first_of_january():
    """Year truncation gives 1 January."""
    assert truncate_date("2026-08-15", "year") == date(2026, 1, 1)


def test_truncate_to_week_is_the_monday():
    """The week starts on Monday — the ISO convention, and Looker's.

    15 March 2026 is a Sunday, so it truncates back to Monday the 9th.
    """
    assert truncate_date("2026-03-15", "week") == date(2026, 3, 9)


def test_a_monday_truncates_to_itself():
    """A Monday is already the start of its week."""
    assert truncate_date("2026-03-09", "week") == date(2026, 3, 9)


def test_truncate_rejects_an_unknown_timeframe():
    """An unknown timeframe raises."""
    with pytest.raises(ValueError, match="unknown timeframe"):
        truncate_date("2026-03-15", "fortnight")


def test_truncate_rejects_the_raw_timeframe():
    """`raw` is not a rollup, so it is not a truncation."""
    with pytest.raises(ValueError, match="unknown timeframe"):
        truncate_date("2026-03-15", "raw")


# --------------------------------------------------------------------------
# The date spine
# --------------------------------------------------------------------------


def test_a_date_spine_has_one_row_per_day():
    """The spine covers the range inclusively."""
    spine = build_date_spine("2026-03-01", "2026-03-07")
    assert len(spine) == 7
    assert spine[0].date == date(2026, 3, 1)
    assert spine[-1].date == date(2026, 3, 7)


def test_a_date_spine_has_one_row_for_a_single_day():
    """A one-day range gives one row."""
    spine = build_date_spine("2026-03-01", "2026-03-01")
    assert len(spine) == 1


def test_a_date_spine_carries_the_calendar_columns():
    """The spine carries the year, quarter, month and week."""
    spine = build_date_spine("2026-03-01", "2026-03-01")
    row = spine[0]
    assert row.year == 2026
    assert row.quarter == 1
    assert row.month == 3
    assert row.week == 9
    assert row.day_of_week == 7
    assert row.year_month == "2026-03"
    assert row.year_quarter == "2026-Q1"


def test_a_date_spine_spans_a_leap_year():
    """2028 is a leap year — February has 29 days."""
    spine = build_date_spine("2028-02-01", "2028-03-01")
    assert len(spine) == 30


def test_a_date_spine_rejects_an_inverted_range():
    """An end before the start is an error."""
    with pytest.raises(ValueError, match="is before start"):
        build_date_spine("2026-03-01", "2026-02-01")


# --------------------------------------------------------------------------
# Filling the gaps
# --------------------------------------------------------------------------


def test_filling_missing_periods_adds_the_empty_buckets():
    """A gap in the fact table becomes a bucket with no rows."""
    rows = [
        {"created_at": "2026-03-01"},
        {"created_at": "2026-03-04"},
    ]
    filled = fill_missing_periods(rows, timeframe="day")
    assert len(filled) == 4
    assert [bucket["rows"] for bucket in filled] == [
        [rows[0]],
        [],
        [],
        [rows[1]],
    ]


def test_filling_missing_periods_at_the_month_grain():
    """At the month grain, the buckets are months."""
    rows = [
        {"created_at": "2026-01-15"},
        {"created_at": "2026-03-15"},
    ]
    filled = fill_missing_periods(rows, timeframe="month")
    assert len(filled) == 3
    assert filled[1]["date"] == date(2026, 2, 1)
    assert filled[1]["rows"] == []


def test_filling_missing_periods_needs_a_range_when_there_are_no_rows():
    """Zero rows carry no range, so one must be supplied."""
    with pytest.raises(ValueError, match="cannot infer a date range"):
        fill_missing_periods([], timeframe="day")


def test_filling_missing_periods_accepts_an_explicit_range():
    """An explicit range works even with no rows."""
    filled = fill_missing_periods(
        [], timeframe="day", start="2026-03-01", end="2026-03-03"
    )
    assert len(filled) == 3


# --------------------------------------------------------------------------
# Date filters
# --------------------------------------------------------------------------


def test_a_month_filter_covers_the_whole_month():
    """A month filter starts on the 1st and ends on the last day."""
    bounds = date_filter_bounds("2026-03-01", "2026-03-01", "month")
    assert bounds.start == date(2026, 3, 1)
    assert bounds.end == date(2026, 3, 31)


def test_a_february_filter_handles_the_leap_year():
    """February 2028 has 29 days, and the filter knows it."""
    bounds = date_filter_bounds("2028-02-01", "2028-02-01", "month")
    assert bounds.end == date(2028, 2, 29)


def test_a_february_filter_handles_a_common_year():
    """February 2026 has 28 days."""
    bounds = date_filter_bounds("2026-02-01", "2026-02-01", "month")
    assert bounds.end == date(2026, 2, 28)


def test_a_quarter_filter_covers_the_whole_quarter():
    """A quarter filter runs to the end of the quarter."""
    bounds = date_filter_bounds("2026-02-10", "2026-02-10", "quarter")
    assert bounds.start == date(2026, 1, 1)
    assert bounds.end == date(2026, 3, 31)


def test_a_week_filter_covers_the_whole_week():
    """A week filter runs from Monday to Sunday."""
    bounds = date_filter_bounds("2026-03-11", "2026-03-11", "week")
    assert bounds.start == date(2026, 3, 9)
    assert bounds.end == date(2026, 3, 15)


def test_a_year_filter_covers_the_whole_year():
    """A year filter runs from 1 January to 31 December."""
    bounds = date_filter_bounds("2026-05-05", "2026-05-05", "year")
    assert bounds.start == date(2026, 1, 1)
    assert bounds.end == date(2026, 12, 31)


def test_a_day_filter_is_exact():
    """A day filter does not expand."""
    bounds = date_filter_bounds("2026-03-15", "2026-03-15", "day")
    assert bounds.start == date(2026, 3, 15)
    assert bounds.end == date(2026, 3, 15)


def test_a_date_range_contains_a_date():
    """The range knows what is inside it."""
    bounds = date_filter_bounds("2026-03-01", "2026-03-31", "month")
    assert bounds.contains("2026-03-15")
    assert not bounds.contains("2026-04-01")


def test_a_date_range_renders_sql():
    """The range renders as an inclusive SQL predicate."""
    bounds = date_filter_bounds("2026-03-01", "2026-03-31", "month")
    sql = bounds.to_sql("created_at")
    assert "created_at >= DATE('2026-03-01')" in sql
    assert "created_at <= DATE('2026-03-31')" in sql


def test_an_inverted_date_filter_is_rejected():
    """A filter that ends before it starts is an error."""
    with pytest.raises(ValueError, match="is before start"):
        date_filter_bounds("2026-03-31", "2026-03-01", "month")


# --------------------------------------------------------------------------
# Previous period
# --------------------------------------------------------------------------


def test_the_previous_month_is_the_whole_previous_month():
    """The previous month is not "30 days ago"."""
    previous = previous_period("2026-03-01", "2026-03-31", "month")
    assert previous.start == date(2026, 2, 1)
    assert previous.end == date(2026, 2, 28)


def test_the_previous_month_handles_a_leap_february():
    """February 2028 has 29 days."""
    previous = previous_period("2028-03-01", "2028-03-31", "month")
    assert previous.end == date(2028, 2, 29)


def test_the_previous_quarter_is_the_whole_previous_quarter():
    """Q2's previous quarter is Q1."""
    previous = previous_period("2026-04-01", "2026-06-30", "quarter")
    assert previous.start == date(2026, 1, 1)
    assert previous.end == date(2026, 3, 31)


def test_the_previous_quarter_crosses_the_year_boundary():
    """Q1's previous quarter is Q4 of the previous year."""
    previous = previous_period("2026-01-01", "2026-03-31", "quarter")
    assert previous.start == date(2025, 10, 1)
    assert previous.end == date(2025, 12, 31)


def test_the_previous_year_is_the_whole_previous_year():
    """The previous year runs 1 January to 31 December."""
    previous = previous_period("2026-01-01", "2026-12-31", "year")
    assert previous.start == date(2025, 1, 1)
    assert previous.end == date(2025, 12, 31)


def test_the_previous_period_has_the_same_length_as_the_current_one():
    """A daily comparison covers the same number of days."""
    previous = previous_period("2026-03-10", "2026-03-19", "day")
    assert previous.start == date(2026, 2, 28)
    assert previous.end == date(2026, 3, 9)
    assert (previous.end - previous.start).days == 9


# --------------------------------------------------------------------------
# Percentage change
# --------------------------------------------------------------------------


def test_period_over_period_computes_the_percentage_change():
    """A 25% rise reads as 0.25."""
    assert period_over_period(125, 100) == 0.25


def test_period_over_period_handles_a_decline():
    """A decline is negative."""
    assert period_over_period(75, 100) == -0.25


def test_period_over_period_from_zero_is_undefined():
    """A percentage change from zero has no answer."""
    assert period_over_period(100, 0) is None


# --------------------------------------------------------------------------
# Labels and months
# --------------------------------------------------------------------------


def test_a_month_label_is_readable():
    """March 2026 reads as `Mar 2026`."""
    assert month_label("2026-03-15") == "Mar 2026"


def test_months_between_lists_the_month_starts():
    """The list runs from January to March."""
    months = months_between("2026-01-05", "2026-03-20")
    assert months == [
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


def test_every_truncated_timeframe_has_a_description():
    """Each timeframe can explain itself."""
    for timeframe in TRUNCATED_TIMEFRAMES:
        assert describe_timeframe(timeframe)


def test_describe_rejects_an_unknown_timeframe():
    """An unknown timeframe raises."""
    with pytest.raises(ValueError, match="unknown timeframe"):
        describe_timeframe("fortnight")
