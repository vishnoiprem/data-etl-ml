"""
cloud_function.py — the Google Cloud Run Function for the Kafka → Cloud SQL path.

This is the deployable artifact the course builds in the second half. It is
a standard **HTTP** Cloud Run Function: Confluent's Google Cloud Functions
sink connector POSTs each Kafka message to it, and the function parses the
message and writes it into Cloud SQL PostgreSQL.

Three concerns, three functions, in the order the course teaches them:

1. `fetch_secret`  — resolve the database password from Secret Manager
2. `parse_transaction` — validate and flatten the JSON payload
3. `ingest_transaction` — insert the row into PostgreSQL

The credentials are fetched **per invocation** and cached in module scope,
which is the pattern that keeps a function fast without ever putting a
secret in the image or in an environment variable.

Usage (local):
    python -c "from cloud_function import handle_event; print(handle_event(body))"

Usage (deployed):
    gcloud functions deploy ingest-transaction \\
        --gen2 \\
        --runtime python312 \\
        --region us-central1 \\
        --source . \\
        --entry-point handle_event \\
        --trigger-http \\
        --no-allow-unauthenticated \\
        --set-env-vars DATABASE_URL=... \\
        --set-secrets DB_PASSWORD=db-password:latest
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping

from kafka_to_gcp import (
    build_insert_sql,
    fetch_secret,
    parse_transaction,
)

log = logging.getLogger("cloud_function")

#: The database URL. In production this is assembled at runtime from the
#: instance connection name and the secret value — never stored whole.
DATABASE_URL = os.environ.get("DATABASE_URL", "")

#: Cached database connection. Module scope survives between invocations
#: of the same instance, so the connection is reused rather than rebuilt
#: on every request.
_CONNECTION: Any | None = None

#: Cached secret value, for the same reason.
_SECRET: str | None = None


def get_secret(name: str = "db-password") -> str:
    """Return the secret value, fetching it at most once per instance.

    Args:
        name: The Secret Manager secret name.

    Returns:
        The secret's string value.
    """
    global _SECRET
    if _SECRET is None:
        _SECRET = fetch_secret(name)
        log.info("secret %s fetched and cached", name)
    return _SECRET


def get_connection(database_url: str | None = None) -> Any:
    """Return the database connection, opening it at most once per instance.

    Args:
        database_url: An explicit connection URL. Defaults to the
            `DATABASE_URL` environment variable.

    Returns:
        A live DB-API connection.

    Raises:
        RuntimeError: If no connection URL is configured.
    """
    global _CONNECTION
    if _CONNECTION is not None:
        return _CONNECTION

    url = database_url or DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure it with --set-env-vars at "
            "deploy time, or pass it to get_connection()."
        )

    import psycopg2  # type: ignore[import-not-found]

    _CONNECTION = psycopg2.connect(url)
    log.info("database connection opened and cached")
    return _CONNECTION


def insert_transaction(row: Mapping[str, Any], connection: Any) -> bool:
    """Insert one parsed transaction into PostgreSQL.

    Args:
        row: The parsed transaction.
        connection: A live DB-API connection.

    Returns:
        True on success.
    """
    statement = build_insert_sql()
    columns = (
        "transaction_id",
        "customer_id",
        "amount",
        "currency",
        "product_id",
        "channel",
        "timestamp",
        "ingested_at",
    )
    values = tuple(row.get(column) for column in columns)
    with connection.cursor() as cursor:
        cursor.execute(statement, values)
    connection.commit()
    return True


def handle_event(request: Any = None, body: str | None = None) -> dict[str, Any]:
    """The function's HTTP entry point.

    The function is written so it can be called three ways, which is what
    makes it testable without a cloud:

    * as an HTTP handler, with the `requests`-style `request` object;
    * with an explicit `body` string;
    * with no arguments at all, in which case it reads `sys.stdin`.

    Args:
        request: An HTTP request object carrying the message body.
        body: The raw message body.

    Returns:
        A response dict with a status and a short message.

    Raises:
        ValueError: If the payload cannot be parsed. The function is
            deployed to return 400 for this, not to crash.
    """
    if body is None:
        if request is not None:
            body = request.get_data(as_text=True)
        else:
            import sys

            body = sys.stdin.read()

    log.info("received message of %d bytes", len(body or ""))

    try:
        row = parse_transaction(body or "")
    except ValueError as exc:
        log.warning("rejecting message: %s", exc)
        return {"status": "rejected", "reason": str(exc)}

    try:
        connection = get_connection()
        insert_transaction(row, connection)
    except Exception as exc:  # pragma: no cover - needs a live database
        log.error("ingest failed: %s", exc)
        return {"status": "error", "reason": str(exc)}

    return {"status": "ok", "transaction_id": row["transaction_id"]}


def load_local_event(path: str) -> dict[str, Any]:
    """Read one message from a file and run it through the handler.

    Args:
        path: The file to read.

    Returns:
        The handler's response.
    """
    with open(path, "r", encoding="utf-8") as handle:
        body = handle.read()
    return handle_event(body=body)


if __name__ == "__main__":
    print(json.dumps(load_local_event(os.environ.get("EVENT_FILE", "")), indent=2))
