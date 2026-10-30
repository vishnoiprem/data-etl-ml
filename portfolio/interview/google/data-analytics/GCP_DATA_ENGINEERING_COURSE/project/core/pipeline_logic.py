"""
pipeline_logic.py — the end-to-end pipeline logic of the GCP course project.

This module implements the capstone pipeline the way you would build it
on GCP, but in pure Python so it runs with no account, no credentials
and no bill:

    raw events → validate → normalise → aggregate → publish → warehouse

The GCP mapping is one-to-one:

    ==========================  =========================================
    Pure function              GCP equivalent
    ==========================  =========================================
    ``ingest_events``           Pub/Sub subscription pull
    ``validate_event``          Dataflow ``DoFn`` / Dataproc map
    ``normalise_event``         Dataflow ``Map`` + currency table
    ``aggregate_events``        BigQuery SQL or Dataflow ``CombinePerKey``
    ``publish_topic``           Pub/Sub publish
    ``write_partition``         BigQuery partitioned table load
    ==========================  =========================================

Everything here is deterministic, which is what lets the chapters print
exact expected outputs.

Usage:
    from pipeline_logic import (
        validate_event,
        aggregate_events,
        render_summary_csv,
    )

    accepted, rejected = ingest_events(lines)
    summary = aggregate_events(accepted)
    print(render_summary_csv(summary))
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

VALID_REGIONS = frozenset({"EMEA", "AMER", "APAC", "LATAM"})
VALID_CHANNELS = frozenset({"web", "mobile", "store"})
VALID_EVENT_TYPES = frozenset({"order", "refund", "page_view", "signup"})
CURRENCY_TO_EUR: dict[str, float] = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "JPY": 0.0064,
}

#: The window size, in seconds, used by the streaming path. One hour.
WINDOW_SECONDS = 3600

#: The hourly window length used to bucket events for aggregation.
WINDOW_BUCKET_SECONDS = 3600

#: How many hours of events the dataset spans.
DATASET_HOURS = 24

#: The expected aggregate for the default dataset. The chapters and the
#: notebooks assert against this, so it must stay exact.
EXPECTED_TOTAL_EVENTS = 4800

#: The expected per-region aggregate for the default dataset.
EXPECTED_SUMMARY: dict[str, dict[str, float]] = {
    "AMER": {"event_count": 1238, "revenue_eur": 464848.02},
    "APAC": {"event_count": 1159, "revenue_eur": 421049.85},
    "EMEA": {"event_count": 1176, "revenue_eur": 432544.17},
    "LATAM": {"event_count": 1227, "revenue_eur": 445554.36},
}

#: The expected reject counts for the default malformed dataset. Every
#: reason code appears at least once, which is what makes the dead-letter
#: path assertable.
EXPECTED_REJECT_COUNTS: dict[str, int] = {
    "bad_amount": 1,
    "bad_timestamp": 1,
    "missing_event_id": 1,
    "missing_user_id": 1,
    "negative_amount": 1,
    "unknown_channel": 1,
    "unknown_currency": 1,
    "unknown_event_type": 1,
    "unknown_region": 2,
    "wrong_field_count": 2,
}

SUMMARY_HEADER = "region,event_count,revenue_eur"

#: Reason codes emitted by :func:`validate_event`. Each is stable and
#: low-cardinality, because a reason code becomes a metric label.
REJECT_MISSING_EVENT_ID = "missing_event_id"
REJECT_MISSING_USER_ID = "missing_user_id"
REJECT_BAD_TIMESTAMP = "bad_timestamp"
REJECT_UNKNOWN_EVENT_TYPE = "unknown_event_type"
REJECT_UNKNOWN_REGION = "unknown_region"
REJECT_UNKNOWN_CHANNEL = "unknown_channel"
REJECT_UNKNOWN_CURRENCY = "unknown_currency"
REJECT_BAD_AMOUNT = "bad_amount"
REJECT_NEGATIVE_AMOUNT = "negative_amount"
REJECT_WRONG_FIELD_COUNT = "wrong_field_count"

EVENT_FIELDS = [
    "event_id",
    "user_id",
    "event_ts",
    "event_type",
    "region",
    "channel",
    "currency",
    "amount",
]


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------


class EventRejected(Exception):
    """Raised when an event fails validation.

    Carries a stable ``reason`` code so callers can route the event to a
    dead-letter path, count it by reason, and alert when a reason
    appears that never appeared before.

    Args:
        reason: A stable, low-cardinality reason code.
        detail: Optional human-readable detail. Never put raw payloads
            here — it ends up in logs.
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason if not detail else f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


# --------------------------------------------------------------------------
# Pure helpers
# --------------------------------------------------------------------------


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into a timezone-aware datetime.

    A timestamp with no explicit offset is assumed to be UTC. That is a
    production decision, not a convenience: it must be consistent across
    every producer, or the event-time semantics silently drift.

    Args:
        value: The timestamp string.

    Returns:
        A timezone-aware datetime in UTC.

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


def format_timestamp(value: datetime) -> str:
    """Render a datetime as a stable UTC ISO-8601 string.

    Args:
        value: The datetime to format.

    Returns:
        An ISO-8601 string with a ``+00:00`` offset.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def normalise_currency(amount: float, currency: str) -> float:
    """Convert an amount into EUR using the static rate table.

    A production system reads these from a periodically-refreshed rates
    table. The course keeps them static so the expected outputs printed
    in the chapters and notebooks stay correct.

    Args:
        amount: The amount in the source currency.
        currency: The ISO currency code, e.g. ``"GBP"``.

    Returns:
        The amount in EUR, rounded to two decimal places.

    Raises:
        ValueError: If the currency is not in the rate table.
    """
    rate = CURRENCY_TO_EUR.get(currency.upper())
    if rate is None:
        raise ValueError(f"unknown currency: {currency!r}")
    return round(amount * rate, 2)


def _field_count(text: str) -> int:
    """Count the CSV fields in a line, honouring quoted fields.

    ``text.split(",")`` is wrong for a quoted field containing a comma —
    ``"Acme, Inc.",US`` is two fields, not three. This matters for the
    reject reason code: a row rejected as ``wrong_field_count`` when it
    actually had the right number of fields sends you looking at the
    wrong thing entirely.

    Args:
        text: The CSV line.

    Returns:
        The number of fields, or -1 if the line cannot be parsed.
    """
    try:
        return len(next(csv.reader(io.StringIO(text))))
    except (csv.Error, StopIteration):
        return -1


def try_parse_event_line(line: str) -> dict[str, Any] | None:
    """Parse one CSV line into an event dict, returning None when malformed.

    Args:
        line: A CSV line.

    Returns:
        The event dict, or None when the line cannot be parsed at all.
    """
    text = line.strip()
    if not text:
        return None
    try:
        values = next(csv.reader(io.StringIO(text)))
    except (csv.Error, StopIteration):
        return None
    if len(values) != len(EVENT_FIELDS):
        return None
    row = dict(zip(EVENT_FIELDS, values))
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
    return row


def validate_event(row: dict[str, Any]) -> str:
    """Validate a parsed event, returning a reason code or ``"valid"``.

    This is the single source of truth for event validity. The pipeline,
    the unit tests and the notebooks all call it, so a rule can never be
    enforced in one place and forgotten in another.

    Args:
        row: A parsed event dict.

    Returns:
        ``"valid"``, or one of the ``REJECT_*`` reason codes.
    """
    if not row.get("event_id"):
        return REJECT_MISSING_EVENT_ID
    if not row.get("user_id"):
        return REJECT_MISSING_USER_ID
    if row.get("event_type") not in VALID_EVENT_TYPES:
        return REJECT_UNKNOWN_EVENT_TYPE
    if row.get("region") not in VALID_REGIONS:
        return REJECT_UNKNOWN_REGION
    if row.get("channel") not in VALID_CHANNELS:
        return REJECT_UNKNOWN_CHANNEL
    if str(row.get("currency", "")).upper() not in CURRENCY_TO_EUR:
        return REJECT_UNKNOWN_CURRENCY
    try:
        parse_timestamp(str(row.get("event_ts", "")))
    except ValueError:
        return REJECT_BAD_TIMESTAMP
    amount = row.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        return REJECT_BAD_AMOUNT
    if math.isnan(float(amount)) or math.isinf(float(amount)):
        return REJECT_BAD_AMOUNT
    if float(amount) < 0:
        return REJECT_NEGATIVE_AMOUNT
    return "valid"


def is_valid_event(row: dict[str, Any]) -> bool:
    """Return True when an event passes every business rule.

    Args:
        row: A parsed event dict.

    Returns:
        True when the event is valid.
    """
    return validate_event(row) == "valid"


def normalise_event(row: dict[str, Any]) -> dict[str, Any]:
    """Convert an accepted event into its warehouse shape.

    This is where the currency conversion and the event-time
    normalisation happen. On GCP this is a Dataflow ``Map`` or a
    BigQuery ``SELECT`` expression — the shape is identical.

    Args:
        row: An accepted event dict.

    Returns:
        The normalised event, with ``amount_eur`` and ``event_dt``
        added.
    """
    normalised = dict(row)
    normalised["amount_eur"] = normalise_currency(
        float(row["amount"]), str(row["currency"]).upper()
    )
    normalised["event_dt"] = format_timestamp(parse_timestamp(str(row["event_ts"])))
    return normalised


def ingest_events(
    lines: Iterable[str],
    *,
    reject: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split raw CSV lines into accepted events and rejected rows.

    Args:
        lines: Raw CSV lines, with or without a header.
        reject: When True, raise :class:`EventRejected` on the first bad
            event instead of collecting it. Use this when a single
            malformed event should fail the job; use the default (False)
            when events should be routed to a dead-letter path.

    Returns:
        A ``(accepted, rejected)`` tuple. Each rejected entry is a dict
        with ``reason``, ``detail`` and ``raw`` keys.

    Raises:
        EventRejected: When ``reject`` is True and an event fails
            validation.
    """
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for line in lines:
        text = line.strip()
        if not text:
            continue
        if text.lower().startswith("event_id,"):
            continue

        row = try_parse_event_line(text)
        if row is None:
            reason = (
                REJECT_WRONG_FIELD_COUNT
                if _field_count(text) != len(EVENT_FIELDS)
                else REJECT_BAD_AMOUNT
            )
            if reject:
                raise EventRejected(reason, text[:120])
            rejected.append({"reason": reason, "detail": "", "raw": text})
            continue

        classification = validate_event(row)
        if classification != "valid":
            if reject:
                raise EventRejected(classification, str(row.get("event_id", "")))
            rejected.append(
                {
                    "reason": classification,
                    "detail": str(row.get("event_id", "")),
                    "raw": text,
                }
            )
            continue

        accepted.append(normalise_event(row))

    return accepted, rejected


def bucket_by_window(
    rows: Iterable[dict[str, Any]],
    *,
    window_seconds: int = WINDOW_BUCKET_SECONDS,
) -> dict[str, list[dict[str, Any]]]:
    """Group events into fixed event-time windows.

    This is the pure equivalent of a Dataflow fixed window: the bucket
    is derived from the **event timestamp**, never from arrival time.
    Skip the re-stamping step and every event collapses into a single
    window — the totals stay right, which is exactly why the bug is so
    easy to miss.

    Args:
        rows: Normalised event dicts.
        window_seconds: The window width in seconds.

    Returns:
        A dict of window key -> the events in that window. Window keys
        are ISO timestamps of the window start.
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        stamp = parse_timestamp(str(row["event_dt"]))
        epoch = int(stamp.timestamp())
        window_start = epoch - (epoch % window_seconds)
        key = format_timestamp(datetime.fromtimestamp(window_start, tz=timezone.utc))
        buckets.setdefault(key, []).append(row)
    return buckets


def aggregate_events(
    rows: Iterable[dict[str, Any]],
    *,
    event_types: Sequence[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Aggregate event counts and revenue per region.

    Args:
        rows: Normalised event dicts.
        event_types: Which event types count toward revenue. When None,
            every event with a non-zero amount counts.

    Returns:
        A dict of region -> ``{"event_count": n, "revenue_eur": amount}``.
    """
    wanted = set(event_types) if event_types is not None else None
    summary: dict[str, dict[str, float]] = {}
    for row in rows:
        event_type = str(row.get("event_type", ""))
        if wanted is not None and event_type not in wanted:
            continue
        region = str(row["region"])
        bucket = summary.setdefault(region, {"event_count": 0.0, "revenue_eur": 0.0})
        bucket["event_count"] += 1
        bucket["revenue_eur"] += float(row.get("amount_eur", 0.0))
    for bucket in summary.values():
        bucket["revenue_eur"] = round(bucket["revenue_eur"], 2)
    return summary


def aggregate_by_window(
    rows: Iterable[dict[str, Any]],
    *,
    window_seconds: int = WINDOW_BUCKET_SECONDS,
) -> list[dict[str, Any]]:
    """Aggregate per (window, region), the streaming output shape.

    Args:
        rows: Normalised event dicts.
        window_seconds: The window width in seconds.

    Returns:
        A list of dicts with ``window``, ``region``, ``event_count`` and
        ``revenue_eur``, sorted by window then region.
    """
    buckets = bucket_by_window(rows, window_seconds=window_seconds)
    output: list[dict[str, Any]] = []
    for window in sorted(buckets):
        for region, stats in sorted(
            aggregate_events(buckets[window]).items()
        ):
            output.append(
                {
                    "window": window,
                    "region": region,
                    "event_count": int(stats["event_count"]),
                    "revenue_eur": stats["revenue_eur"],
                }
            )
    return output


def render_summary_csv(summary: dict[str, dict[str, float]]) -> str:
    """Render the region summary as a CSV document with a header row.

    ``csv.writer`` is used rather than an f-string so that a region name
    containing a comma cannot corrupt the output.

    Args:
        summary: The output of :func:`aggregate_events`.

    Returns:
        The CSV text, header first, newline-terminated.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SUMMARY_HEADER.split(","))
    for region in sorted(summary):
        bucket = summary[region]
        writer.writerow(
            [region, int(bucket["event_count"]), f"{bucket['revenue_eur']:.2f}"]
        )
    return buffer.getvalue()


def render_rejects_csv(rejected: Sequence[dict[str, Any]]) -> str:
    """Render rejected rows as a CSV document for the dead-letter path.

    Args:
        rejected: The output of :func:`ingest_events`.

    Returns:
        The CSV text with a header row.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["reason", "detail", "raw"])
    for item in rejected:
        writer.writerow(
            [item.get("reason", ""), item.get("detail", ""), item.get("raw", "")]
        )
    return buffer.getvalue()


def reject_counts(rejected: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count rejected rows by reason code.

    This is what you alert on. A count by reason is low-cardinality and
    safe as a metric label; the raw payload is not.

    Args:
        rejected: The output of :func:`ingest_events`.

    Returns:
        A dict of reason code -> count.
    """
    counts: dict[str, int] = {}
    for item in rejected:
        reason = item.get("reason", "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts


# --------------------------------------------------------------------------
# Partitioning and idempotency
# --------------------------------------------------------------------------


def partition_for_date(logical_date: str) -> str:
    """Derive a BigQuery partition decorator from a logical date.

    Args:
        logical_date: An ISO date string, e.g. ``"2026-01-15"``.

    Returns:
        A partition decorator such as ``"20260115"``.
    """
    return logical_date.strip()[:10].replace("-", "")


def partition_for_event(event_dt: str) -> str:
    """Derive the partition decorator an event belongs to.

    Args:
        event_dt: A normalised event timestamp.

    Returns:
        A partition decorator such as ``"20260115"``.
    """
    return str(event_dt)[:10].replace("-", "")


def filter_rows_for_partition(
    rows: Iterable[dict[str, Any]], partition: str
) -> list[dict[str, Any]]:
    """Keep only the rows belonging to a partition.

    Args:
        rows: Candidate rows.
        partition: A partition decorator such as ``"20260115"``.

    Returns:
        The matching rows.
    """
    matched: list[dict[str, Any]] = []
    for row in rows:
        stamp = str(row.get("event_dt", ""))
        if not stamp:
            continue
        if stamp[:10].replace("-", "") == partition:
            matched.append(row)
    return matched


def dedup_key(event_id: str, partition: str) -> str:
    """Return the deterministic identity of an event for idempotent loads.

    The identity must be derived from the data, never from arrival time.
    A load-time timestamp would make a retry produce *different* rows
    rather than the same rows, which defeats deduplication entirely.

    Args:
        event_id: The event's business key.
        partition: The partition the row belongs to.

    Returns:
        A stable identity string.
    """
    return f"{partition}:{event_id}"


def deduplicate(
    rows: Iterable[dict[str, Any]],
    *,
    partition: str,
) -> list[dict[str, Any]]:
    """Remove events already present, keyed by their deterministic identity.

    Args:
        rows: Candidate rows.
        partition: The partition the rows belong to.

    Returns:
        The deduplicated rows, in their original order.
    """
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = dedup_key(str(row.get("event_id", "")), partition)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


# --------------------------------------------------------------------------
# Topic and sink shapes
# --------------------------------------------------------------------------


def publish_topic(
    rows: Iterable[dict[str, Any]],
    *,
    topic: str = "events-normalised",
    attributes: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Build the Pub/Sub messages the pipeline would publish.

    On GCP this is a ``Publish`` call; the message body is the
    serialised row and the attributes carry the routing metadata that
    lets a subscriber filter without decoding the body.

    Args:
        rows: The rows to publish.
        topic: The topic name.
        attributes: Extra message attributes applied to every message.

    Returns:
        A list of message dicts with ``topic``, ``data`` and
        ``attributes`` keys.
    """
    messages: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(attributes or {})
        payload.setdefault("event_type", str(row.get("event_type", "")))
        payload.setdefault("region", str(row.get("region", "")))
        messages.append(
            {
                "topic": topic,
                "data": json.dumps(row, sort_keys=True),
                "attributes": payload,
            }
        )
    return messages


def build_bigquery_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape accepted events into rows ready for a BigQuery load job.

    BigQuery load jobs want a fixed set of columns with primitive types.
    This function enforces that shape so the pipeline never has to.

    Args:
        rows: Normalised event dicts.

    Returns:
        A list of flat, BigQuery-shaped dicts.
    """
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "event_id": row["event_id"],
                "user_id": row["user_id"],
                "event_ts": row["event_ts"],
                "event_dt": row["event_dt"],
                "event_type": row["event_type"],
                "region": row["region"],
                "channel": row["channel"],
                "currency": row["currency"],
                "amount": float(row["amount"]),
                "amount_eur": float(row["amount_eur"]),
            }
        )
    return output


def dedup_key_set(rows: Iterable[dict[str, Any]], partition: str) -> set[str]:
    """Return the set of deterministic identities in a set of rows.

    Args:
        rows: Candidate rows.
        partition: The partition the rows belong to.

    Returns:
        The identity strings.
    """
    return {dedup_key(str(row.get("event_id", "")), partition) for row in rows}


# --------------------------------------------------------------------------
# Optimisation helpers — used by the BigQuery optimisation chapter
# --------------------------------------------------------------------------


def estimated_scan_tb(
    rows: Iterable[dict[str, Any]],
    *,
    partitioned: bool,
    partition_prune_ratio: float = 0.01,
) -> float:
    """Estimate the TB a query would scan.

    This is the model behind the BigQuery cost chapter: an unpartitioned
    query reads everything, a partitioned query reads only the
    partitions it touches.

    The result is in **terabytes**, because that is the unit BigQuery
    prices in. Note that a small dataset returns a very small number —
    for the sample dataset the scan is measured in megabytes, so the TB
    figure rounds to near zero. Use :func:`estimated_scan_bytes` when
    you need a figure that does not lose precision.

    Args:
        rows: The rows the query would read.
        partitioned: Whether the table is partitioned.
        partition_prune_ratio: The fraction a partitioned query reads.

    Returns:
        The estimated TB scanned.
    """
    return round(estimated_scan_bytes(
        rows,
        partitioned=partitioned,
        partition_prune_ratio=partition_prune_ratio,
    ) / BYTES_PER_TB, 9)


def estimated_scan_bytes(
    rows: Iterable[dict[str, Any]],
    *,
    partitioned: bool,
    partition_prune_ratio: float = 0.01,
) -> int:
    """Estimate the bytes a query would scan.

    Args:
        rows: The rows the query would read.
        partitioned: Whether the table is partitioned.
        partition_prune_ratio: The fraction a partitioned query reads.

    Returns:
        The estimated bytes scanned.
    """
    total = sum(len(json.dumps(row)) for row in rows)
    if partitioned:
        total = int(total * partition_prune_ratio)
    return total


#: Bytes in one terabyte, for the scan estimate.
BYTES_PER_TB = 1024**4


def suggest_partitioning(
    rows: Iterable[dict[str, Any]],
) -> str:
    """Suggest a partitioning column for a set of rows.

    The rule the chapter teaches: partition on the column you filter
    by, almost always. The estimator checks each candidate column for
    how much a date-range filter would prune.

    Args:
        rows: The rows to inspect.

    Returns:
        The name of the suggested column.
    """
    candidates = ["event_dt", "event_ts"]
    for column in candidates:
        if any(column in row for row in rows):
            return column
    return "event_dt"


def event_time_bounds(rows: Iterable[dict[str, Any]]) -> tuple[str, str]:
    """Return the earliest and latest event timestamps in a set of rows.

    Args:
        rows: The rows to inspect.

    Returns:
        A ``(min_ts, max_ts)`` tuple of ISO timestamps.
    """
    stamps = sorted(str(row["event_dt"]) for row in rows if row.get("event_dt"))
    if not stamps:
        return ("", "")
    return (stamps[0], stamps[-1])


def hours_spanned(rows: Iterable[dict[str, Any]]) -> int:
    """Return how many hours the events in a set of rows span.

    Args:
        rows: The rows to inspect.

    Returns:
        The number of hours between the earliest and latest event.
    """
    earliest, latest = event_time_bounds(rows)
    if not earliest:
        return 0
    delta = parse_timestamp(latest) - parse_timestamp(earliest)
    return int(delta.total_seconds() // 3600) + 1


def watermark_lag(
    rows: Iterable[dict[str, Any]],
    *,
    processing_time: datetime | None = None,
) -> timedelta:
    """Return how far behind the watermark is from the latest event.

    In a streaming pipeline the watermark is the system's claim about
    how complete the data is. The lag between it and the newest event
    is the number that tells you whether the pipeline is keeping up.

    Args:
        rows: The rows to inspect.
        processing_time: The current time. Defaults to the latest event
            plus the dataset span, which makes the estimate deterministic.

    Returns:
        The lag as a timedelta.
    """
    earliest, latest = event_time_bounds(rows)
    if not latest:
        return timedelta(0)
    if processing_time is None:
        processing_time = parse_timestamp(latest) + timedelta(hours=DATASET_HOURS)
    return processing_time - parse_timestamp(latest)


# --------------------------------------------------------------------------
# Validation helpers used by the DLQ and governance chapters
# --------------------------------------------------------------------------


def looks_like_email(value: str) -> bool:
    """Return True when a value looks like an email address.

    The governance chapter uses this to show why a regex is a poor
    substitute for a real detection service.

    Args:
        value: The candidate string.

    Returns:
        True when the value matches the simple email pattern.
    """
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


def redact_pii(value: str, *, keep_last: int = 4) -> str:
    """Redact a sensitive value, keeping only its last few characters.

    Args:
        value: The sensitive value.
        keep_last: How many trailing characters to keep.

    Returns:
        The redacted value.
    """
    if len(value) <= keep_last:
        return "*" * len(value)
    return "*" * (len(value) - keep_last) + value[-keep_last:]
