"""
transforms.py — shared transformation logic for the Dataflow course pipelines.

This module is deliberately split in two halves:

    * A **pure half** (parsing, validation, currency conversion, aggregation)
      that depends on nothing but the standard library. It is unit-tested in
      `tests/test_transforms.py` and runs even when Apache Beam is not
      installed.
    * A **Beam half** (`ParseOrderFn`, `RevenueByRegionFn`) that is only
      defined when `apache_beam` is importable.

The split exists because `apache-beam` is a heavy install. Course work should
not require it just to check that a field parses correctly.

Usage:
    from transforms import parse_order_line, RevenueByRegionFn

    # Pure logic — no Apache Beam required
    row = parse_order_line("o1,c2,2026-01-15T00:00:00+00:00,EMEA,web,EUR,complete,10.5,p1")

    # Beam logic
    (
        p
        | "Parse" >> beam.ParDo(ParseOrderFn())
        | "Revenue" >> beam.CombinePerKey(RevenueByRegionFn())
    )
"""
from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Sequence

log = logging.getLogger(__name__)

try:  # pragma: no cover - import guard is exercised only when Beam is absent
    import apache_beam as beam
    from apache_beam.coders import FastPrimitivesCoder
    from apache_beam.io.textio import WriteToText

    BEAM_AVAILABLE = True
except ImportError:  # pragma: no cover
    beam = None  # type: ignore[assignment]
    FastPrimitivesCoder = None  # type: ignore[assignment]
    WriteToText = None  # type: ignore[assignment]
    BEAM_AVAILABLE = False

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

VALID_REGIONS = frozenset({"EMEA", "AMER", "APAC", "LATAM"})
VALID_STATUSES = frozenset({"active", "complete", "cancelled", "refunded"})

#: Exchange rates into EUR. A real system would read these from a
#: periodically-refreshed rates table; the course keeps them static so the
#: expected outputs stay stable.
CURRENCY_TO_EUR: dict[str, float] = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "JPY": 0.0064,
}

ORDER_FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]

EVENT_FIELDS = [
    "event_id",
    "user_id",
    "event_ts",
    "event_type",
    "product_id",
    "region",
    "value",
]


# --------------------------------------------------------------------------
# Pure logic — no Apache Beam required
# --------------------------------------------------------------------------


def normalise_currency(amount: float, currency: str) -> float:
    """Convert an amount into EUR using the static rate table.

    Args:
        amount: The amount in the source currency.
        currency: The ISO currency code, e.g. "GBP".

    Returns:
        The amount in EUR, rounded to two decimal places.

    Raises:
        ValueError: If the currency is not in the rate table.
    """
    rate = CURRENCY_TO_EUR.get(currency.upper())
    if rate is None:
        raise ValueError(f"unknown currency: {currency!r}")
    return round(amount * rate, 2)


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into a timezone-aware datetime.

    A timestamp without an explicit offset is assumed to be UTC. That
    assumption is a production decision, not a convenience: it must be
    consistent across every producer, or windowing will be subtly wrong.

    Args:
        value: The timestamp string.

    Returns:
        A timezone-aware datetime.

    Raises:
        ValueError: If the timestamp cannot be parsed.
    """
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_valid_order(row: dict[str, Any]) -> bool:
    """Check that an order row satisfies every business rule.

    The rules are deliberately explicit rather than schema-driven, because a
    production pipeline needs to distinguish "this row is bad" from "this row
    is a different shape than I expected". The second is a bug; the first is
    data.

    Args:
        row: A parsed order dict.

    Returns:
        True when the row passes every rule.
    """
    if not row.get("order_id"):
        return False
    if not row.get("customer_id"):
        return False
    if row.get("region") not in VALID_REGIONS:
        return False
    if row.get("status") not in VALID_STATUSES:
        return False
    if row.get("currency", "").upper() not in CURRENCY_TO_EUR:
        return False
    try:
        parse_timestamp(str(row.get("order_ts", "")))
    except ValueError:
        return False
    try:
        amount = float(row.get("amount"))
    except (TypeError, ValueError):
        return False
    if amount < 0:
        return False
    return True


def parse_order_line(line: str) -> dict[str, Any]:
    """Parse one CSV line into an order dict, raising on malformed input.

    Use this when malformed rows should fail the bundle. Use
    `try_parse_order_line` when they should be routed to a dead-letter queue
    instead.

    Args:
        line: A CSV line, with or without a trailing newline.

    Returns:
        The order dict.

    Raises:
        ValueError: If the line does not have the expected number of fields.
    """
    row = try_parse_order_line(line)
    if row is None:
        raise ValueError(f"malformed order line: {line!r}")
    return row


def try_parse_order_line(line: str) -> dict[str, Any] | None:
    """Parse one CSV line into an order dict, returning None when malformed.

    Args:
        line: A CSV line.

    Returns:
        The order dict, or None when the line cannot be parsed.
    """
    text = line.strip()
    if not text:
        return None
    try:
        values = next(csv.reader(io.StringIO(text)))
    except (csv.Error, StopIteration):
        return None
    if len(values) != len(ORDER_FIELDS):
        return None
    row = dict(zip(ORDER_FIELDS, values))

    # Coerce the numeric field so downstream code can trust its type.
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
    return row


def parse_event_payload(payload: bytes | str) -> dict[str, Any]:
    """Parse a Pub/Sub message payload into an event dict.

    Args:
        payload: The raw message bytes or a decoded string.

    Returns:
        The event dict.

    Raises:
        ValueError: If the payload is not a JSON object with the expected
            fields.
    """
    if isinstance(payload, bytes):
        text = payload.decode("utf-8")
    else:
        text = payload

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("payload is not a JSON object")

    missing = [field for field in EVENT_FIELDS if field not in data]
    if missing:
        raise ValueError(f"payload missing fields: {', '.join(missing)}")

    try:
        data["value"] = float(data["value"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"payload has a non-numeric value: {data['value']!r}") from exc

    return data


def build_revenue_summary(
    rows: Iterable[dict[str, Any]],
    *,
    statuses: Sequence[str] = ("complete",),
) -> dict[str, dict[str, float]]:
    """Aggregate revenue per region from a collection of orders.

    This is the reference implementation of what `RevenueByRegionFn` does
    inside a Beam pipeline. Keeping a pure twin makes the combiner testable
    without a runner, and makes the combiner's correctness self-evident.

    Args:
        rows: Order dicts.
        statuses: Which order statuses count toward revenue. Orders in any
            other status are ignored.

    Returns:
        A dict of region -> {"order_count": n, "revenue_eur": amount}.
    """
    wanted = set(statuses)
    summary: dict[str, dict[str, float]] = {}

    for row in rows:
        if not is_valid_order(row):
            continue
        if row["status"] not in wanted:
            continue
        region = row["region"]
        bucket = summary.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
        bucket["order_count"] += 1
        bucket["revenue_eur"] += normalise_currency(float(row["amount"]), row["currency"])

    for bucket in summary.values():
        bucket["revenue_eur"] = round(bucket["revenue_eur"], 2)
    return summary


def dedup_key(event: dict[str, Any]) -> str:
    """Return the deduplication key for an event.

    Pub/Sub is at-least-once, so the same event can arrive twice. The
    deduplication key must be derived from the payload's own identity, never
    from arrival time.

    Args:
        event: A parsed event dict.

    Returns:
        The deduplication key.
    """
    return str(event.get("event_id") or event.get("user_id", ""))


def window_key(event: dict[str, Any], window_seconds: int = 3600) -> int:
    """Return the window index an event belongs to.

    Args:
        event: A parsed event dict.
        window_seconds: Window width in seconds. Must be positive.

    Returns:
        The integer window index.

    Raises:
        ValueError: If the window width is not positive.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    timestamp = parse_timestamp(str(event["event_ts"]))
    return int(timestamp.timestamp()) // window_seconds


def flatten_csv_header(rows: Iterable[dict[str, Any]]) -> Iterator[str]:
    """Yield the union of keys across rows, preserving first-seen order.

    Beam's `WriteToText` with `header=True` needs a consistent column set.
    When a source is ragged, the union of keys is the only correct answer.

    Args:
        rows: Row dicts.

    Yields:
        Column names.
    """
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            seen.setdefault(key, None)
    yield from seen


# --------------------------------------------------------------------------
# Beam logic — only available when apache-beam is installed
# --------------------------------------------------------------------------

if BEAM_AVAILABLE:  # pragma: no cover - requires the optional dependency

    class ParseOrderFn(beam.DoFn):
        """Parse CSV lines into order dicts, skipping malformed rows.

        The malformed rows are logged rather than raised, because one bad
        line in a 10-million-line file should not fail the entire bundle.
        A pipeline that must not lose data should route them to a
        dead-letter topic instead — see the "Error Handling and DLQ"
        chapter.
        """

        def process(self, line: str, timestamp=beam.DoFn.TimestampParam) -> Iterable[Any]:
            """Parse one line and emit the resulting order dict."""
            row = try_parse_order_line(line)
            if row is None:
                log.warning("skipping malformed order line: %.120s", line)
                return
            if not is_valid_order(row):
                log.warning("skipping invalid order: %s", row.get("order_id"))
                return
            yield row

    class RevenueByRegionFn(beam.CombineFn):
        """Aggregate order count and revenue per region.

        A `CombineFn` must be *associative* and *commutative*, because Beam
        merges partial accumulators from different workers in an arbitrary
        order. `add_input` accumulates one order, `merge_accumulators` merges
        two partial sums, and the merge must produce the same result as
        adding the inputs in any other order.
        """

        def create_accumulator(self) -> dict[str, float]:
            """Create an empty accumulator."""
            return {"order_count": 0.0, "revenue_eur": 0.0}

        def add_input(self, accumulator: dict[str, float], order: dict[str, Any]) -> dict[str, float]:
            """Add one order to the accumulator."""
            accumulator["order_count"] += 1
            accumulator["revenue_eur"] += normalise_currency(
                float(order["amount"]), order["currency"]
            )
            return accumulator

        def merge_accumulators(
            self, accumulators: Iterable[dict[str, float]]
        ) -> dict[str, float]:
            """Merge partial accumulators from different workers."""
            total = self.create_accumulator()
            for partial in accumulators:
                total["order_count"] += partial["order_count"]
                total["revenue_eur"] += partial["revenue_eur"]
            return total

        def extract_output(self, accumulator: dict[str, float]) -> dict[str, float]:
            """Produce the final output from the accumulator."""
            return {
                "order_count": int(accumulator["order_count"]),
                "revenue_eur": round(accumulator["revenue_eur"], 2),
            }

    def to_summary_row(item: tuple[str, dict[str, float]]) -> dict[str, Any]:
        """Flatten a (region, summary) pair into a flat output row.

        The function takes a single tuple because it is used as a
        `beam.Map` function, and `Map` applies its function to one element
        at a time. A two-argument function would need `beam.Map(lambda kv:
        ...)` instead.

        Args:
            item: The (region, summary) pair.

        Returns:
            A flat dict ready for a tabular sink.
        """
        key, value = item
        return {
            "region": key,
            "order_count": value["order_count"],
            "revenue_eur": value["revenue_eur"],
        }

    def write_summary_to_csv(records: Any, output_path: str) -> Any:
        """Write summary records to a sharded CSV output path.

        Args:
            records: A PCollection of flat summary dicts.
            output_path: The output path, local or gs://.

        Returns:
            The write transform.
        """
        header = "region,order_count,revenue_eur"
        return records | "WriteToCsv" >> WriteToText(
            output_path,
            header=header,
            num_shards=1,
            shard_name_template="",
        )

    def format_summary_csv(row: dict[str, Any]) -> str:
        """Format one summary row as a CSV line.

        `WriteToText` writes whatever string it is given, so the dict must
        be formatted explicitly. Using `csv.writer` rather than an f-string
        means a region name containing a comma cannot corrupt the output.

        Args:
            row: A flat summary dict.

        Returns:
            The CSV line, without a trailing newline.
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                row.get("region", ""),
                row.get("order_count", 0),
                row.get("revenue_eur", 0.0),
            ]
        )
        return buffer.getvalue().rstrip("\r\n")

else:  # pragma: no cover - exercised only when Beam is absent

    class ParseOrderFn:  # type: ignore[no-redef]
        """Placeholder raised when Apache Beam is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "ParseOrderFn requires apache-beam. Install it with: "
                "pip install apache-beam[gcp]"
            )

    class RevenueByRegionFn:  # type: ignore[no-redef]
        """Placeholder raised when Apache Beam is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "RevenueByRegionFn requires apache-beam. Install it with: "
                "pip install apache-beam[gcp]"
            )

    def to_summary_row(item: tuple[str, dict[str, float]]) -> dict[str, Any]:
        """Flatten a (region, summary) pair into a flat output row."""
        key, value = item
        return {
            "region": key,
            "order_count": value["order_count"],
            "revenue_eur": value["revenue_eur"],
        }

    def write_summary_to_csv(records: Any, output_path: str) -> Any:
        """Raise a clear error when Apache Beam is not installed."""
        raise ImportError(
            "write_summary_to_csv requires apache-beam. Install it with: "
            "pip install apache-beam[gcp]"
        )

    def format_summary_csv(row: dict[str, Any]) -> str:
        """Format one summary row as a CSV line."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                row.get("region", ""),
                row.get("order_count", 0),
                row.get("revenue_eur", 0.0),
            ]
        )
        return buffer.getvalue().rstrip("\r\n")
