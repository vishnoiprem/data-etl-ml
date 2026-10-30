"""
date_helpers.py — date spines, timeframes and date filters.

Every date problem in BI is the same problem wearing a different hat:
**a fact table has no rows for the periods in which nothing happened.**

A store that sold nothing on 3 March has no row for 3 March. Chart it
raw and the chart shows a *gap* where it should show a zero. The gap
reads as "we have no data" when it actually means "we had no sales" —
and the difference matters enormously to a dashboard owner.

The fix is a **date spine**: a generated table with one row per day,
joined to the fact table. The spine supplies the missing days, and a
`COALESCE` turns their null measures into zeros.

This module implements that, in pure standard library, along with the
timeframe logic that a Looker date dimension gives you for free:

    * ``day``      — the day itself
    * ``week``     — the Monday of that week
    * ``month``    — the first of the month
    * ``quarter``  — the first of the quarter
    * ``year``     — the first of January

Usage:
    from date_helpers import (
        build_date_spine,
        truncate_date,
        date_filter_bounds,
    )

    spine = build_date_spine("2026-01-01", "2026-12-31")
    bounds = date_filter_bounds("2026-03-15", "2026-03-15", "month")
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable

#: The timeframe granularities a time dimension can support. These are the
#: names Looker uses, and also the names Looker Studio's date grains use.
TIMEFRAMES = ("raw", "day", "week", "month", "quarter", "year")

#: The granularities that actually roll a date up. ``raw`` does not.
TRUNCATED_TIMEFRAMES = ("day", "week", "month", "quarter", "year")


@dataclass(frozen=True)
class DateSpineRow:
    """One row of a date spine.

    Attributes:
        date: The calendar date this row represents.
        year: The calendar year.
        quarter: The quarter number, 1 to 4.
        month: The month number, 1 to 12.
        week: The ISO week number, 1 to 53.
        day_of_week: The ISO day of week, Monday is 1.
        year_month: The ``YYYY-MM`` label.
        year_quarter: The ``YYYY-Qn`` label.
    """

    date: date
    year: int
    quarter: int
    month: int
    week: int
    day_of_week: int
    year_month: str
    year_quarter: str


def parse_date(value: Any) -> date:
    """Parse a value into a ``date``.

    Accepts a ``date``, an ISO ``YYYY-MM-DD`` string, and the common
    ``YYYY/MM/DD`` and ``MM/DD/YYYY`` forms. Anything else raises.

    Args:
        value: The value to parse.

    Returns:
        The parsed date.

    Raises:
        ValueError: If the value cannot be parsed.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"cannot parse {value!r} as a date")


def truncate_date(value: Any, timeframe: str) -> date:
    """Truncate a date to the start of its timeframe bucket.

    This is what Looker does when you drag a date dimension into a
    chart and pick "Month" instead of "Day": every row in March becomes
    1 March, and the rows collapse into one bucket.

    The week bucket starts on **Monday**. That is the ISO convention and
    it is what Looker uses; starting on Sunday is a source of
    off-by-one-week discrepancies between two dashboards that should
    agree.

    Args:
        value: The date to truncate.
        timeframe: The granularity — ``day``, ``week``, ``month``,
            ``quarter`` or ``year``.

    Returns:
        The first date of the bucket.

    Raises:
        ValueError: If the timeframe is unknown.
    """
    if timeframe not in TRUNCATED_TIMEFRAMES:
        raise ValueError(
            f"unknown timeframe {timeframe!r}; expected one of "
            f"{list(TRUNCATED_TIMEFRAMES)}"
        )

    parsed = parse_date(value)

    if timeframe == "day":
        return parsed
    if timeframe == "week":
        return parsed - timedelta(days=parsed.weekday())
    if timeframe == "month":
        return parsed.replace(day=1)
    if timeframe == "quarter":
        first_month = 3 * ((parsed.month - 1) // 3) + 1
        return parsed.replace(month=first_month, day=1)
    return parsed.replace(month=1, day=1)


def build_date_spine(start: Any, end: Any) -> list[DateSpineRow]:
    """Build a date spine covering an inclusive date range.

    The spine is the calendar. It has a row for every day between
    ``start`` and ``end``, inclusive of both.

    Args:
        start: The first date in the range.
        end: The last date in the range.

    Returns:
        The spine rows, in ascending date order.

    Raises:
        ValueError: If the range is empty — an end before the start.
    """
    first = parse_date(start)
    last = parse_date(end)
    if last < first:
        raise ValueError(
            f"date spine end {last} is before start {first}"
        )

    rows: list[DateSpineRow] = []
    current = first
    while current <= last:
        quarter = (current.month - 1) // 3 + 1
        rows.append(
            DateSpineRow(
                date=current,
                year=current.year,
                quarter=quarter,
                month=current.month,
                week=current.isocalendar().week,
                day_of_week=current.isoweekday(),
                year_month=f"{current.year}-{current.month:02d}",
                year_quarter=f"{current.year}-Q{quarter}",
            )
        )
        current += timedelta(days=1)
    return rows


def fill_missing_periods(
    rows: Iterable[dict[str, Any]],
    date_field: str = "created_at",
    timeframe: str = "day",
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Fill gaps in a fact table using a date spine.

    Rows are grouped by the truncated date. Every bucket between the
    earliest and latest row gets an entry; a bucket with no rows gets a
    row whose measures are zero rather than absent.

    This is the whole point of the spine, and it is why a chart shows a
    flat line at zero on a day with no sales instead of a gap.

    Args:
        rows: The fact rows.
        date_field: The field holding the date.
        timeframe: The granularity to group by.
        start: An optional explicit start date. Defaults to the earliest
            date present in ``rows``.
        end: An optional explicit end date. Defaults to the latest date
            present in ``rows``.

    Returns:
        The filled rows, one per bucket, in ascending date order.

    Raises:
        ValueError: If ``rows`` is empty and no explicit range is given.
    """
    materialised = list(rows)
    dates = [
        truncate_date(row.get(date_field), timeframe) for row in materialised
    ]

    if start is None:
        if not dates:
            raise ValueError(
                "cannot infer a date range from zero rows; pass start and end"
            )
        first = min(dates)
    else:
        first = truncate_date(start, timeframe)

    if end is None:
        if not dates:
            raise ValueError(
                "cannot infer a date range from zero rows; pass start and end"
            )
        last = max(dates)
    else:
        last = truncate_date(end, timeframe)

    grouped: dict[date, list[dict[str, Any]]] = {}
    for row, bucket in zip(materialised, dates):
        grouped.setdefault(bucket, []).append(row)

    filled: list[dict[str, Any]] = []
    current = first
    while current <= last:
        bucket_rows = grouped.get(current, [])
        if bucket_rows:
            filled.append({"date": current, "rows": bucket_rows})
        else:
            filled.append({"date": current, "rows": []})
        current = _advance(current, timeframe)
    return filled


def _advance(current: date, timeframe: str) -> date:
    """Move to the first day of the next bucket.

    Args:
        current: The current bucket start.
        timeframe: The granularity.

    Returns:
        The next bucket start.

    Raises:
        ValueError: If the timeframe is unknown.
    """
    if timeframe == "day":
        return current + timedelta(days=1)
    if timeframe == "week":
        return current + timedelta(days=7)
    if timeframe == "month":
        if current.month == 12:
            return date(current.year + 1, 1, 1)
        return date(current.year, current.month + 1, 1)
    if timeframe == "quarter":
        month = current.month + 3
        year = current.year
        if month > 12:
            month -= 12
            year += 1
        return date(year, month, 1)
    if timeframe == "year":
        return date(current.year + 1, 1, 1)
    raise ValueError(f"unknown timeframe {timeframe!r}")


@dataclass(frozen=True)
class DateRange:
    """A resolved date range, with the bounds a filter needs.

    Attributes:
        start: The inclusive lower bound.
        end: The inclusive upper bound.
        timeframe: The granularity the range was expressed in.
    """

    start: date
    end: date
    timeframe: str

    def contains(self, value: Any) -> bool:
        """Whether a date falls inside the range.

        Args:
            value: The date to test.

        Returns:
            True when the date is within the inclusive bounds.
        """
        parsed = parse_date(value)
        return self.start <= parsed <= self.end

    def to_sql(self, column: str = "created_at") -> str:
        """Render the range as a SQL predicate.

        Args:
            column: The date column to filter.

        Returns:
            The SQL predicate string.
        """
        return (
            f"{column} >= DATE('{self.start.isoformat()}') "
            f"AND {column} <= DATE('{self.end.isoformat()}')"
        )


def date_filter_bounds(
    start: Any,
    end: Any,
    timeframe: str = "day",
) -> DateRange:
    """Resolve a date filter into a concrete range.

    A filter like "March 2026" at the ``month`` timeframe means every
    day in March — not March 1st. Getting this wrong is why a
    "last month" report is off by one day at each end.

    Args:
        start: The lower bound, at any granularity.
        end: The upper bound, at any granularity.
        timeframe: The granularity of the filter.

    Returns:
        The resolved range, with both bounds expanded to whole buckets.

    Raises:
        ValueError: If the range is inverted.
    """
    raw_start = parse_date(start)
    raw_end = parse_date(end)

    if raw_end < raw_start:
        raise ValueError(
            f"date filter end {raw_end} is before start {raw_start}"
        )

    start_date = truncate_date(raw_start, timeframe)
    end_date = truncate_date(raw_end, timeframe)

    if timeframe == "day":
        return DateRange(start_date, end_date, timeframe)

    last_day = calendar.monthrange(end_date.year, end_date.month)[1]
    if timeframe == "month":
        return DateRange(start_date, date(end_date.year, end_date.month, last_day), timeframe)
    if timeframe == "quarter":
        quarter_end_month = 3 * ((end_date.month - 1) // 3) + 3
        last_day = calendar.monthrange(end_date.year, quarter_end_month)[1]
        return DateRange(
            start_date,
            date(end_date.year, quarter_end_month, last_day),
            timeframe,
        )
    if timeframe == "week":
        return DateRange(start_date, end_date + timedelta(days=6), timeframe)
    return DateRange(start_date, date(end_date.year, 12, 31), timeframe)


def previous_period(
    start: Any,
    end: Any,
    timeframe: str = "month",
) -> DateRange:
    """Compute the period immediately before a range.

    "Revenue this month versus last month" needs the previous month. If
    the current month is 1 to 31 March, the previous month is 1 to 28
    (or 29) February — not 1 to 31 February, and not 28 March to 28
    April.

    Args:
        start: The current period's start.
        end: The current period's end.
        timeframe: The granularity.

    Returns:
        The previous period's range.

    Raises:
        ValueError: If the range is inverted or the timeframe is unknown.
    """
    current = date_filter_bounds(start, end, timeframe)

    if timeframe == "day":
        length = (current.end - current.start).days + 1
        previous_end = current.start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=length - 1)
        return DateRange(previous_start, previous_end, timeframe)

    if timeframe == "week":
        previous_end = current.start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)
        return DateRange(previous_start, previous_end, timeframe)

    if timeframe == "month":
        previous_end = current.start - timedelta(days=1)
        previous_start = previous_end.replace(day=1)
        return DateRange(previous_start, previous_end, timeframe)

    if timeframe == "quarter":
        previous_end = current.start - timedelta(days=1)
        previous_start = previous_end.replace(
            month=3 * ((previous_end.month - 1) // 3) + 1, day=1
        )
        return DateRange(previous_start, previous_end, timeframe)

    if timeframe == "year":
        previous_end = current.start - timedelta(days=1)
        return DateRange(
            date(previous_end.year, 1, 1), previous_end, timeframe
        )

    raise ValueError(f"unknown timeframe {timeframe!r}")


def period_over_period(
    current: Any,
    previous: Any,
) -> float | None:
    """Compute the percentage change between two periods.

    Args:
        current: The current period's value.
        previous: The previous period's value.

    Returns:
        The percentage change as a fraction (``0.25`` is +25%), or None
        when the previous value is zero — because a percentage change
        from zero is undefined, and returning ``inf`` would put an
        infinite axis label on a chart.
    """
    if previous in (None, 0):
        return None
    if current is None:
        return None
    return round((current - previous) / previous, 4)


def month_label(value: Any) -> str:
    """Render a date as a human-readable month label.

    Args:
        value: The date.

    Returns:
        A label like ``Mar 2026``.
    """
    parsed = parse_date(value)
    return f"{calendar.month_abbr[parsed.month]} {parsed.year}"


def months_between(start: Any, end: Any) -> list[date]:
    """List the first day of every month between two dates.

    Args:
        start: The first date.
        end: The last date.

    Returns:
        The month starts, in ascending order.

    Raises:
        ValueError: If the range is inverted.
    """
    first = truncate_date(start, "month")
    last = truncate_date(end, "month")
    if last < first:
        raise ValueError(f"end {last} is before start {first}")

    months: list[date] = []
    current = first
    while current <= last:
        months.append(current)
        current = _advance(current, "month")
    return months


def describe_timeframe(timeframe: str) -> str:
    """Describe a timeframe in one sentence.

    Args:
        timeframe: The timeframe name.

    Returns:
        A human-readable description.

    Raises:
        ValueError: If the timeframe is unknown.
    """
    descriptions = {
        "raw": "the exact timestamp, with no rollup",
        "day": "the calendar day",
        "week": "the Monday of the ISO week",
        "month": "the first day of the calendar month",
        "quarter": "the first day of the calendar quarter",
        "year": "the first of January",
    }
    if timeframe not in descriptions:
        raise ValueError(
            f"unknown timeframe {timeframe!r}; expected one of {list(TIMEFRAMES)}"
        )
    return descriptions[timeframe]
