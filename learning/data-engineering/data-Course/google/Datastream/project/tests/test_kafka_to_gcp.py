"""
test_kafka_to_gcp.py — unit tests for the Kafka → Cloud Run → Cloud SQL path.

These tests need no broker, no Cloud Run service and no PostgreSQL. The
functions are exercised directly, and the database interaction is tested
against a fake connection object that records the SQL it was given — which
is how you prove the statement is parameterised rather than string-built.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kafka_to_gcp import (  # noqa: E402
    build_insert_sql,
    fetch_secret,
    parse_timestamp,
    parse_transaction,
    replay_messages,
)


# --------------------------------------------------------------------------
# A fake DB-API connection
# --------------------------------------------------------------------------


class FakeCursor:
    """A DB-API cursor that records what it was asked to do."""

    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self._closed = False

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *exc_info) -> None:
        self._closed = True

    def execute(self, statement: str, values=None) -> None:
        """Record the statement and its parameters."""
        self.connection.statements.append((statement, values))

    def close(self) -> None:
        self._closed = True


class FakeConnection:
    """A DB-API connection that records statements and commits."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.commits = 0

    def cursor(self) -> FakeCursor:
        """Return a recording cursor."""
        return FakeCursor(self)

    def commit(self) -> None:
        """Record a commit."""
        self.commits += 1


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture()
def transaction() -> dict:
    """A valid transaction payload."""
    return {
        "transaction_id": "t00000001",
        "customer_id": "c000001",
        "amount": 42.50,
        "currency": "EUR",
        "product_id": "p0001",
        "channel": "web",
        "timestamp": "2026-01-15T10:30:00Z",
    }


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


class TestParseTransaction:
    """The message parser."""

    def test_parses_a_valid_transaction(self, transaction):
        row = parse_transaction(json.dumps(transaction))
        assert row["transaction_id"] == "t00000001"
        assert row["amount"] == 42.50
        assert row["currency"] == "EUR"

    def test_accepts_bytes(self, transaction):
        row = parse_transaction(json.dumps(transaction).encode("utf-8"))
        assert row["transaction_id"] == "t00000001"

    def test_normalises_currency_case(self, transaction):
        transaction["currency"] = "eur"
        assert parse_transaction(json.dumps(transaction))["currency"] == "EUR"

    def test_normalises_channel_case(self, transaction):
        transaction["channel"] = "WEB"
        assert parse_transaction(json.dumps(transaction))["channel"] == "web"

    def test_rejects_invalid_json(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_transaction("{not json")

    def test_rejects_a_json_array(self):
        with pytest.raises(ValueError, match="not a JSON object"):
            parse_transaction("[1, 2, 3]")

    def test_rejects_a_missing_field(self, transaction):
        del transaction["amount"]
        with pytest.raises(ValueError, match="missing fields: amount"):
            parse_transaction(json.dumps(transaction))

    def test_rejects_a_non_numeric_amount(self, transaction):
        transaction["amount"] = "lots"
        with pytest.raises(ValueError, match="not numeric"):
            parse_transaction(json.dumps(transaction))

    def test_rejects_a_negative_amount(self, transaction):
        transaction["amount"] = -1.0
        with pytest.raises(ValueError, match="negative"):
            parse_transaction(json.dumps(transaction))

    def test_rejects_an_unknown_currency(self, transaction):
        transaction["currency"] = "XYZ"
        with pytest.raises(ValueError, match="unknown currency"):
            parse_transaction(json.dumps(transaction))

    def test_rejects_an_unknown_channel(self, transaction):
        transaction["channel"] = "carrier-pigeon"
        with pytest.raises(ValueError, match="unknown channel"):
            parse_transaction(json.dumps(transaction))

    def test_adds_an_ingestion_timestamp(self, transaction):
        row = parse_transaction(json.dumps(transaction))
        assert row["ingested_at"]
        parse_timestamp(row["ingested_at"])


# --------------------------------------------------------------------------
# Timestamps
# --------------------------------------------------------------------------


class TestParseTimestamp:
    """Timestamp parsing."""

    def test_parses_a_z_suffixed_timestamp(self):
        parsed = parse_timestamp("2026-01-15T10:30:00Z")
        assert parsed.year == 2026
        assert parsed.tzinfo is not None

    def test_parses_an_offset_timestamp(self):
        """An offset timestamp is normalised to UTC."""
        parsed = parse_timestamp("2026-01-15T10:30:00+02:00")
        assert parsed.tzinfo is not None
        assert parsed.utcoffset().total_seconds() == 0
        assert parsed.hour == 8

    def test_assumes_utc_when_the_offset_is_missing(self):
        parsed = parse_timestamp("2026-01-15T10:30:00")
        assert parsed.tzinfo is not None
        assert parsed.utcoffset().total_seconds() == 0

    def test_rejects_a_nonsense_timestamp(self):
        with pytest.raises(ValueError, match="invalid timestamp"):
            parse_timestamp("not-a-time")


# --------------------------------------------------------------------------
# SQL
# --------------------------------------------------------------------------


class TestInsertSql:
    """The INSERT statement."""

    def test_uses_placeholders_not_interpolated_values(self):
        sql = build_insert_sql()
        assert "%s" in sql
        assert "INSERT INTO transactions" in sql

    def test_has_one_placeholder_per_column(self):
        sql = build_insert_sql()
        assert sql.count("%s") == 8

    def test_the_table_name_is_configurable(self):
        assert "INSERT INTO other_table" in build_insert_sql(table="other_table")


# --------------------------------------------------------------------------
# Ingest
# --------------------------------------------------------------------------


class TestIngest:
    """The database write path."""

    def test_executes_a_parameterised_statement(self, transaction):
        from kafka_to_gcp import ingest_transaction

        row = parse_transaction(json.dumps(transaction))
        connection = FakeConnection()
        ingest_transaction(row, connection=connection)

        assert len(connection.statements) == 1
        statement, values = connection.statements[0]
        assert "%s" in statement
        assert "t00000001" in values
        assert connection.commits == 1

    def test_a_quote_in_the_payload_stays_data(self, transaction):
        """The SQL-injection test: a quote must not escape the statement."""
        from kafka_to_gcp import ingest_transaction

        transaction["product_id"] = "p0001'; DROP TABLE transactions; --"
        row = parse_transaction(json.dumps(transaction))
        connection = FakeConnection()
        ingest_transaction(row, connection=connection)

        statement, values = connection.statements[0]
        assert "DROP TABLE" not in statement
        assert any("DROP TABLE" in str(value) for value in values)

    def test_dry_run_writes_nothing(self, transaction):
        from kafka_to_gcp import ingest_transaction

        row = parse_transaction(json.dumps(transaction))
        assert ingest_transaction(row, connection=None) is True


# --------------------------------------------------------------------------
# Replay
# --------------------------------------------------------------------------


class TestReplay:
    """The end-to-end local replay."""

    def test_counts_ingested_and_rejected(self, transaction):
        messages = [
            json.dumps(transaction),
            "{not json",
            json.dumps(transaction),
        ]
        summary = replay_messages(messages)
        assert summary["messages"] == 3
        assert summary["ingested"] == 2
        assert summary["rejected"] == 1

    def test_the_rejection_carries_a_reason(self):
        summary = replay_messages(["{not json"])
        assert summary["rejections"][0]["reason"]
        assert "JSON" in summary["rejections"][0]["reason"]

    def test_a_bad_message_does_not_stop_the_stream(self, transaction):
        messages = [
            "{bad",
            json.dumps(transaction),
            "also bad",
            json.dumps(transaction),
        ]
        summary = replay_messages(messages)
        assert summary["ingested"] == 2

    def test_writes_to_the_connection_when_one_is_given(self, transaction):
        connection = FakeConnection()
        summary = replay_messages([json.dumps(transaction)], connection=connection)
        assert summary["ingested"] == 1
        assert len(connection.statements) == 1


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------


class TestFetchSecret:
    """The Secret Manager lookup."""

    def test_reads_the_environment_when_no_client_is_installed(self, monkeypatch):
        monkeypatch.setenv("SECRET_VALUE", "local-dev-password")
        assert fetch_secret("db-password") == "local-dev-password"

    def test_requires_a_project_when_the_name_is_not_a_full_path(self, monkeypatch):
        """With the client installed, a bare name needs a project id."""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("SECRET_VALUE", raising=False)
        pytest.importorskip(
            "google.cloud.secretmanager",
            reason="the project-id check only applies when the client is installed",
        )
        with pytest.raises(RuntimeError, match="no project id"):
            fetch_secret("db-password")

    def test_raises_when_the_secret_cannot_be_resolved(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("SECRET_VALUE", raising=False)
        with pytest.raises(RuntimeError):
            fetch_secret("projects/p/secrets/s/versions/1")
