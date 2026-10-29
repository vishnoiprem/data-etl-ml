"""
pipeline_logic.py — the pure half of the Composer course project.

Every business rule the DAGs implement lives here, and **this module imports
nothing from Airflow**. That is deliberate:

    * Airflow is a heavy, version-sensitive install. The course premise is
      that you can learn Composer without a local Airflow install.
    * Business logic that lives inside a DAG file is nearly impossible to
      unit-test, because importing a DAG file requires Airflow.
    * When the logic is pure, `pytest` runs in well under a second with
      Airflow absent, and the same function can be called from a task, from
      a sensor, or from a test.

The DAG files in ``project/dags/`` are thin: they define dependencies and
operators, then call into this module. That is the pattern you want in a
real code base too.

Usage:
    from pipeline_logic import (
        transform_orders,
        summarise_by_region,
        render_summary_csv,
        classify_row,
    )

    clean, rejected = transform_orders(raw_lines)
    summary = summarise_by_region(clean)
    print(render_summary_csv(summary))
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Iterator, Sequence

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

VALID_REGIONS = frozenset({"EMEA", "AMER", "APAC", "LATAM"})
VALID_STATUSES = frozenset({"active", "complete", "cancelled", "refunded"})
REVENUE_STATUSES = ("complete",)

#: Exchange rates into EUR. A production system reads these from a
#: periodically-refreshed rates table (usually a BigQuery lookup joined in
#: the DAG, or a Variable). The course keeps them static so the expected
#: outputs printed in the chapters and notebooks stay correct.
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

SUMMARY_HEADER = "region,order_count,revenue_eur"

#: Reason codes emitted by `classify_row`. A reject reason must be a stable,
#: low-cardinality string — it ends up as a partition key or a metric label.
REJECT_MISSING_ORDER_ID = "missing_order_id"
REJECT_MISSING_CUSTOMER_ID = "missing_customer_id"
REJECT_BAD_TIMESTAMP = "bad_timestamp"
REJECT_UNKNOWN_REGION = "unknown_region"
REJECT_UNKNOWN_STATUS = "unknown_status"
REJECT_UNKNOWN_CURRENCY = "unknown_currency"
REJECT_BAD_AMOUNT = "bad_amount"
REJECT_NEGATIVE_AMOUNT = "negative_amount"
REJECT_WRONG_FIELD_COUNT = "wrong_field_count"


class RowRejected(Exception):
    """Raised when a row fails validation.

    Carries a stable ``reason`` code so callers can route the row to a
    dead-letter path, count it by reason, and alert on a reason appearing
    that never appeared before.

    Args:
        reason: A stable, low-cardinality reason code.
        detail: Optional human-readable detail. Never put raw payloads in
            here — it ends up in logs.
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason if not detail else f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


# --------------------------------------------------------------------------
# Pure helpers
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

    A timestamp with no explicit offset is assumed to be UTC. That is a
    production decision, not a convenience: it must be consistent across
    every producer, or the Airflow data-interval semantics silently drift.

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

    Airflow's ``{{ ds }}`` template renders the *logical date* as
    ``YYYY-MM-DD`` in UTC. This helper renders a full timestamp the same
    way — UTC, always — so a run date and a data date never disagree
    because of a machine's local timezone.

    Args:
        value: The datetime to format.

    Returns:
        An ISO-8601 string with a ``+00:00`` offset.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


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


def try_parse_order_line(line: str) -> dict[str, Any] | None:
    """Parse one CSV line into an order dict, returning None when malformed.

    Args:
        line: A CSV line.

    Returns:
        The order dict, or None when the line cannot be parsed at all.
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
    try:
        row["amount"] = float(row["amount"])
    except (TypeError, ValueError):
        return None
    return row


def parse_order_line(line: str) -> dict[str, Any]:
    """Parse one CSV line into an order dict, raising on malformed input.

    Use this when a malformed row should fail the task. Use
    :func:`try_parse_order_line` when it should be routed to a
    dead-letter path instead.

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


def classify_row(row: dict[str, Any]) -> str:
    """Classify a parsed order row as ``"valid"`` or a reject reason.

    This is the single source of truth for row validity. The DAG, the unit
    tests, and the local runner all call it, so a rule can never be enforced
    in one place and forgotten in another.

    Args:
        row: A parsed order dict.

    Returns:
        ``"valid"``, or one of the ``REJECT_*`` reason codes.
    """
    if not row.get("order_id"):
        return REJECT_MISSING_ORDER_ID
    if not row.get("customer_id"):
        return REJECT_MISSING_CUSTOMER_ID
    if row.get("region") not in VALID_REGIONS:
        return REJECT_UNKNOWN_REGION
    if row.get("status") not in VALID_STATUSES:
        return REJECT_UNKNOWN_STATUS
    if str(row.get("currency", "")).upper() not in CURRENCY_TO_EUR:
        return REJECT_UNKNOWN_CURRENCY
    try:
        parse_timestamp(str(row.get("order_ts", "")))
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


def is_valid_order(row: dict[str, Any]) -> bool:
    """Return True when the row passes every business rule.

    Args:
        row: A parsed order dict.

    Returns:
        True when the row is valid.
    """
    return classify_row(row) == "valid"


def transform_orders(
    lines: Iterable[str],
    *,
    statuses: Sequence[str] = REVENUE_STATUSES,
    reject: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split raw CSV lines into accepted orders and rejected rows.

    This is the heart of the ETL DAG, and it is pure: given the same input
    it always returns the same output, which is what makes the pipeline
    re-runnable and the result auditable.

    Args:
        lines: Raw CSV lines, with or without a header.
        statuses: Which order statuses count as revenue-bearing. Rows in any
            other status are accepted but excluded from revenue.
        reject: When True, raise :class:`RowRejected` on the first bad row
            instead of collecting it. Use this when a single malformed row
            should fail the task; use the default (False) when rows should
            be routed to a dead-letter path.

    Returns:
        A ``(accepted, rejected)`` tuple. Each rejected entry is a dict
        with ``reason``, ``detail``, and ``raw`` keys.

    Raises:
        RowRejected: When ``reject`` is True and a row fails validation.
    """
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    wanted = set(statuses)

    for line in lines:
        text = line.strip()
        if not text:
            continue
        # Skip a header row if one is present.
        if text.lower().startswith("order_id,"):
            continue

        row = try_parse_order_line(text)
        if row is None:
            # `try_parse_order_line` returns None for two different
            # reasons: the wrong number of fields, or an amount that is
            # not a number. Recover which one it was so the reject
            # reason code is accurate — a reason code becomes a metric
            # label, and "wrong_field_count" on a row that had the right
            # number of fields sends you looking in the wrong place.
            reason = (
                REJECT_WRONG_FIELD_COUNT
                if _field_count(text) != len(ORDER_FIELDS)
                else REJECT_BAD_AMOUNT
            )
            if reject:
                raise RowRejected(reason, text[:120])
            rejected.append({"reason": reason, "detail": "", "raw": text})
            continue

        classification = classify_row(row)
        if classification != "valid":
            if reject:
                raise RowRejected(classification, str(row.get("order_id", "")))
            rejected.append(
                {"reason": classification, "detail": str(row.get("order_id", "")), "raw": text}
            )
            continue

        # A valid row. Status filtering happens here, not in the validator,
        # so that "invalid" and "not revenue-bearing" stay distinct.
        if row["status"] not in wanted:
            continue

        row["amount_eur"] = normalise_currency(float(row["amount"]), row["currency"])
        row["order_dt"] = format_timestamp(parse_timestamp(str(row["order_ts"])))
        accepted.append(row)

    return accepted, rejected


def summarise_by_region(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Aggregate order count and revenue per region.

    This is the reference implementation of what the DAG's aggregation task
    does. Keeping a pure twin means the aggregation is testable without a
    runner and its correctness is self-evident.

    Args:
        rows: Accepted order dicts.

    Returns:
        A dict of region -> {"order_count": n, "revenue_eur": amount}.
    """
    summary: dict[str, dict[str, float]] = {}
    for row in rows:
        region = row["region"]
        bucket = summary.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
        bucket["order_count"] += 1
        bucket["revenue_eur"] += float(row["amount_eur"])
    for bucket in summary.values():
        bucket["revenue_eur"] = round(bucket["revenue_eur"], 2)
    return summary


def render_summary_csv(summary: dict[str, dict[str, float]]) -> str:
    """Render the region summary as a CSV document with a header row.

    ``csv.writer`` is used rather than an f-string so that a region name
    containing a comma cannot corrupt the output.

    Args:
        summary: The output of :func:`summarise_by_region`.

    Returns:
        The CSV text, header first, newline-terminated.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SUMMARY_HEADER.split(","))
    for region in sorted(summary):
        bucket = summary[region]
        writer.writerow(
            [region, int(bucket["order_count"]), f"{bucket['revenue_eur']:.2f}"]
        )
    return buffer.getvalue()


def render_rejects_csv(rejected: Sequence[dict[str, Any]]) -> str:
    """Render rejected rows as a CSV document for the dead-letter path.

    Args:
        rejected: The output of :func:`transform_orders`.

    Returns:
        The CSV text with a header row.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["reason", "detail", "raw"])
    for item in rejected:
        writer.writerow([item.get("reason", ""), item.get("detail", ""), item.get("raw", "")])
    return buffer.getvalue()


def reject_counts(rejected: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count rejected rows by reason code.

    This is what you alert on. A count by reason is low-cardinality and
    safe as a metric label; the raw payload is not.

    Args:
        rejected: The output of :func:`transform_orders`.

    Returns:
        A dict of reason code -> count.
    """
    counts: dict[str, int] = {}
    for item in rejected:
        reason = item.get("reason", "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts


# --------------------------------------------------------------------------
# Data interval semantics
# --------------------------------------------------------------------------


def logical_date_window(
    logical_date: str,
    *,
    data_interval_days: int = 1,
    include_end: bool = False,
) -> tuple[str, str]:
    """Convert an Airflow logical date into a ``[start, end)`` data window.

    Airflow's ``{{ ds }}`` is the *logical date* of the DAG run — for a
    daily schedule, it is the start of the interval being processed. The
    interval is half-open: ``[ds, ds + 1 day)``. A data warehouse filter
    must match that exactly, or a partition gets processed twice (or not at
    all).

    Args:
        logical_date: An ISO date or datetime string, e.g. ``"2026-01-15"``.
        data_interval_days: Width of the interval in days.
        include_end: When True, return an inclusive end date instead of a
            half-open boundary. Use this for systems whose filters are
            inclusive (some legacy SQL warehouses, some APIs).

    Returns:
        A ``(start_date, end_date)`` tuple of ``YYYY-MM-DD`` strings.

    Raises:
        ValueError: If the logical date cannot be parsed.
    """
    text = logical_date.strip()
    if "T" in text:
        start = parse_timestamp(text)
    else:
        start = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = start + timedelta(days=data_interval_days)
    if include_end:
        end = end - timedelta(days=1)
    return start.date().isoformat(), end.date().isoformat()


def gcs_object_path(bucket: str, prefix: str, filename: str) -> str:
    """Build the GCS URI for an output object.

    Args:
        bucket: The bucket name, without the ``gs://`` scheme.
        prefix: A path prefix, with or without leading/trailing slashes.
        filename: The object name.

    Returns:
        A fully-qualified ``gs://`` URI.
    """
    clean_prefix = prefix.strip("/")
    if clean_prefix:
        return f"gs://{bucket}/{clean_prefix}/{filename}"
    return f"gs://{bucket}/{filename}"


def build_bigquery_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape accepted orders into rows ready for a BigQuery load job.

    BigQuery load jobs want a fixed set of columns with primitive types.
    This function enforces that shape so the DAG never has to.

    Args:
        rows: Accepted order dicts.

    Returns:
        A list of flat, BigQuery-shaped dicts.
    """
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "order_ts": row["order_ts"],
                "region": row["region"],
                "channel": row["channel"],
                "currency": row["currency"],
                "status": row["status"],
                "amount": float(row["amount"]),
                "amount_eur": float(row["amount_eur"]),
                "product_id": row["product_id"],
            }
        )
    return output


def write_jsonl(rows: Iterable[dict[str, Any]], path: str) -> int:
    """Write rows as newline-delimited JSON.

    Args:
        rows: The rows to write.
        path: The destination path.

    Returns:
        The number of rows written.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    count = 0
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
            count += 1
    return count


def read_lines(path: str) -> list[str]:
    """Read a file into a list of lines.

    Args:
        path: The file path.

    Returns:
        The lines, without trailing newlines.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    with open(path, "r", encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


# --------------------------------------------------------------------------
# Branching logic
# --------------------------------------------------------------------------


def should_run_full_load(row_count: int, threshold: int) -> bool:
    """Decide whether a run should take the full-load path or the incremental path.

    This is the decision a :class:`~airflow.operators.branch.BranchOperator`
    makes in the branching DAG. Keeping it pure means the branch condition
    can be unit-tested against every threshold boundary, which is exactly
    where branch bugs live: off-by-one on ``>`` versus ``>=``.

    Args:
        row_count: The number of rows available in this run.
        threshold: The threshold at which the full-load path is taken.

    Returns:
        True when the full-load path should be taken.
    """
    return row_count > threshold


def partition_for_date(logical_date: str) -> str:
    """Derive a BigQuery partition decorator from a logical date.

    Args:
        logical_date: An ISO date string, e.g. ``"2026-01-15"``.

    Returns:
        A partition decorator such as ``"20260115"``.
    """
    start, _ = logical_date_window(logical_date)
    return start.replace("-", "")


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
        stamp = str(row.get("order_dt", ""))
        if not stamp:
            continue
        # order_dt is an ISO timestamp: 2026-01-15T09:30:00+00:00
        if stamp[:10].replace("-", "") == partition:
            matched.append(row)
    return matched


def dedup_key(order_id: str, partition: str) -> str:
    """Return the deterministic identity of a row for idempotent loads.

    The identity must be derived from the data, never from arrival time.
    A load-time timestamp would make a retry produce *different* rows rather
    than the same rows, which defeats deduplication entirely.

    Args:
        order_id: The order's business key.
        partition: The partition the row belongs to.

    Returns:
        A stable identity string.
    """
    return f"{partition}:{order_id}"
