#!/usr/bin/env python3
"""
kafka_to_gcp.py — the Confluent Kafka → GCP half of the course.

This script models the second pipeline shape in the course: a Kafka topic
carrying transaction-shaped JSON, consumed by a Cloud Run Function, parsed,
and written into Cloud SQL PostgreSQL.

It runs locally against a **recorded Kafka message log** — an NDJSON file
where each line is one message that came off a topic. That makes the whole
path testable with no cluster, no broker and no bill, while the production
path is the same three functions with a Kafka consumer in front of them and
a PostgreSQL driver behind.

The three functions here are the course's `cloud_function.py` handlers, in
extracted form:

    1. `fetch_secret`  — pull the database password from Secret Manager
    2. `parse_transaction` — turn the raw JSON into flat columns
    3. `ingest_transaction` — insert into PostgreSQL

Usage:
    python project/kafka_to_gcp.py \\
        --messages ./sample_data/transactions.ndjson \\
        --dry-run

    python project/kafka_to_gcp.py \\
        --messages ./sample_data/transactions.ndjson \\
        --dry-run --verbose
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger("kafka_to_gcp")

#: The fields the Datagen-style transaction payload carries. The course
#: expects these to be present; a missing field is a validation error, not
#: a crash.
REQUIRED_FIELDS = (
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "product_id",
    "channel",
    "timestamp",
)

VALID_CURRENCIES = frozenset({"EUR", "USD", "GBP", "JPY"})
VALID_CHANNELS = frozenset({"web", "mobile", "store"})


# --------------------------------------------------------------------------
# Step 1 — the secret
# --------------------------------------------------------------------------


def fetch_secret(
    secret_name: str = "YOUR_SECRET",
    *,
    version: str = "latest",
    project: str | None = None,
) -> str:
    """Fetch a secret value from Google Secret Manager.

    In production this is the first thing the Cloud Run Function does, and
    it is the reason the database password never appears in the function's
    source code, its environment variables, or its container image.

    Locally the same function reads the `SECRET_VALUE` environment variable
    and falls back to a clearly-labelled development value. That fallback
    is the thing you must never ship — it is why this function takes the
    secret name as an argument and never hard-codes a default for it.

    Args:
        secret_name: The Secret Manager secret name or full resource path.
        version: The secret version to fetch.
        project: The project id, when the secret name is not a full path.

    Returns:
        The secret's string value.

    Raises:
        RuntimeError: If the secret cannot be resolved.
    """
    try:
        from google.cloud import secretmanager  # type: ignore[import-not-found]
    except ImportError:
        # Local development path: read the value from the environment.
        local = os.environ.get("SECRET_VALUE")
        if local:
            log.info("using SECRET_VALUE from the environment")
            return local
        raise RuntimeError(
            "google-cloud-secret-manager is not installed and SECRET_VALUE "
            "is not set. Install the client library or export SECRET_VALUE "
            "for local development."
        )

    # A full resource path: projects/P/secrets/S/versions/V
    if secret_name.startswith("projects/"):
        path = secret_name
    else:
        project_id = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise RuntimeError(
                "no project id available — set GOOGLE_CLOUD_PROJECT or pass "
                "a full secret resource path"
            )
        path = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"

    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": path})
    return response.payload.data.decode("utf-8")


# --------------------------------------------------------------------------
# Step 2 — parse
# --------------------------------------------------------------------------


def parse_transaction(payload: str | bytes) -> dict[str, Any]:
    """Parse a raw Kafka message into flat transaction columns.

    This is the function the Cloud Run Function calls. It is deliberately
    strict: it raises on a missing field rather than inserting a NULL,
    because a transaction with no amount is not a transaction with a zero
    amount, and the difference matters downstream.

    Args:
        payload: The raw message body.

    Returns:
        The parsed, flattened transaction dict.

    Raises:
        ValueError: If the payload is not a JSON object, is missing a
            required field, or has an invalid value.
    """
    if isinstance(payload, bytes):
        text = payload.decode("utf-8")
    else:
        text = payload

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"message is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("message is not a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"message missing fields: {', '.join(missing)}")

    try:
        amount = float(data["amount"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"amount is not numeric: {data['amount']!r}") from exc

    if amount < 0:
        raise ValueError(f"amount is negative: {amount}")

    currency = str(data["currency"]).upper()
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"unknown currency: {currency!r}")

    channel = str(data["channel"]).lower()
    if channel not in VALID_CHANNELS:
        raise ValueError(f"unknown channel: {channel!r}")

    timestamp = parse_timestamp(str(data["timestamp"]))

    return {
        "transaction_id": str(data["transaction_id"]),
        "customer_id": str(data["customer_id"]),
        "amount": round(amount, 2),
        "currency": currency,
        "product_id": str(data["product_id"]),
        "channel": channel,
        "timestamp": timestamp.isoformat(),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware datetime.

    Args:
        value: The timestamp string.

    Returns:
        A timezone-aware datetime.

    Raises:
        ValueError: If the timestamp cannot be parsed.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# --------------------------------------------------------------------------
# Step 3 — ingest
# --------------------------------------------------------------------------


def build_insert_sql(
    table: str = "transactions",
    columns: tuple[str, ...] = REQUIRED_FIELDS + ("ingested_at",),
) -> str:
    """Build the parameterised INSERT statement.

    The statement is **parameterised**, never built by string formatting of
    values. That is the single most important security property of this
    function: a transaction whose `product_id` contains a quote must be
    stored as data, never executed as SQL.

    Args:
        table: The destination table.
        columns: The columns, in insert order.

    Returns:
        The SQL statement, with `%s` placeholders.
    """
    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    return f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"


def ingest_transaction(
    row: Mapping[str, Any],
    *,
    connection: Any | None = None,
    sql: str | None = None,
) -> bool:
    """Insert one transaction into PostgreSQL.

    Args:
        row: The parsed transaction.
        connection: A live DB-API connection. When None, the function
            validates the row and reports what it *would* do — which is
            how the course runs it locally.
        sql: The INSERT statement. Defaults to `build_insert_sql()`.

    Returns:
        True when a row was written (or would have been, in dry-run mode).
    """
    statement = sql or build_insert_sql()
    values = tuple(row.get(column) for column in REQUIRED_FIELDS + ("ingested_at",))

    if connection is None:
        log.debug("dry run — would execute: %s %s", statement, values)
        return True

    with connection.cursor() as cursor:
        cursor.execute(statement, values)
    connection.commit()
    return True


# --------------------------------------------------------------------------
# The local replay
# --------------------------------------------------------------------------


def replay_messages(
    messages: list[str],
    *,
    connection: Any | None = None,
) -> dict[str, Any]:
    """Consume a list of Kafka messages end to end.

    Args:
        messages: The raw message bodies.
        connection: An optional live PostgreSQL connection.

    Returns:
        A summary dict with the ingested and rejected counts.
    """
    ingested = 0
    rejected: list[dict[str, str]] = []

    for index, raw in enumerate(messages):
        try:
            row = parse_transaction(raw)
            ingest_transaction(row, connection=connection)
            ingested += 1
        except ValueError as exc:
            log.warning("message %d rejected: %s", index, exc)
            rejected.append({"index": str(index), "reason": str(exc)})

    return {
        "messages": len(messages),
        "ingested": ingested,
        "rejected": len(rejected),
        "rejections": rejected,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--messages", required=True, help="NDJSON file of Kafka messages")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without writing to a database",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL connection URL (e.g. postgresql://user:pass@host/db)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the local replay.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The process exit code.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    messages_path = Path(args.messages)
    if not messages_path.exists():
        log.error("messages file not found: %s", messages_path)
        return 2

    lines = [
        line.strip()
        for line in messages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    connection = None
    if not args.dry_run:
        if not args.database_url:
            log.error("--database-url is required unless --dry-run is given")
            return 2
        try:
            import psycopg2  # type: ignore[import-not-found]
        except ImportError:
            log.error(
                "psycopg2 is not installed. Run with --dry-run to validate "
                "the messages locally, or install psycopg2-binary."
            )
            return 2
        connection = psycopg2.connect(args.database_url)

    summary = replay_messages(lines, connection=connection)

    print()
    print("Kafka → GCP replay summary")
    print("-" * 52)
    print(f"  messages read    : {summary['messages']}")
    print(f"  ingested         : {summary['ingested']}")
    print(f"  rejected         : {summary['rejected']}")
    if summary["rejections"]:
        print("  rejections:")
        for rejection in summary["rejections"][:10]:
            print(f"    [{rejection['index']:>4}] {rejection['reason']}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
