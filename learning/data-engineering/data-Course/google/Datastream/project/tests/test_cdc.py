"""
test_cdc.py — unit tests for the CDC engine.

These tests depend on nothing but the standard library and pytest. They
run in well under a second and need no GCP account, no credentials and no
bill — which is the whole point of splitting the logic out of `cdc.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdc import (  # noqa: E402
    DELETE,
    INSERT,
    UPDATE,
    ChangeEvent,
    CdcState,
    apply_changes,
    bigquery_create_table_sql,
    build_bigquery_merge_sql,
    merge_key_of,
    parse_op,
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture()
def customer() -> dict:
    """A minimal customer row."""
    return {
        "customer_id": "c000001",
        "first_name": "Ada",
        "region": "EMEA",
        "tier": "gold",
    }


# --------------------------------------------------------------------------
# Operation vocabulary
# --------------------------------------------------------------------------


class TestParseOp:
    """The operation vocabulary."""

    def test_accepts_the_three_valid_operations(self):
        assert parse_op("INSERT") == INSERT
        assert parse_op("UPDATE") == UPDATE
        assert parse_op("DELETE") == DELETE

    def test_normalises_case_and_whitespace(self):
        assert parse_op("insert") == INSERT
        assert parse_op("  Update  ") == UPDATE

    def test_rejects_an_unknown_operation(self):
        with pytest.raises(ValueError, match="unknown operation"):
            parse_op("TRUNCATE")

    def test_rejects_an_empty_operation(self):
        with pytest.raises(ValueError):
            parse_op("")


# --------------------------------------------------------------------------
# Merge keys
# --------------------------------------------------------------------------


class TestMergeKey:
    """The merge key extraction."""

    def test_extracts_the_key_tuple_in_order(self, customer):
        assert merge_key_of(customer, ["customer_id"]) == ("c000001",)

    def test_supports_composite_keys(self, customer):
        key = merge_key_of(customer, ["customer_id", "region"])
        assert key == ("c000001", "EMEA")

    def test_rejects_an_empty_merge_key_list(self, customer):
        with pytest.raises(ValueError, match="must not be empty"):
            merge_key_of(customer, [])

    def test_rejects_a_missing_key_column(self, customer):
        with pytest.raises(ValueError, match="missing from the row image"):
            merge_key_of(customer, ["customer_id", "not_a_column"])

    def test_rejects_a_none_row(self):
        with pytest.raises(ValueError, match="missing row image"):
            merge_key_of(None, ["customer_id"])


# --------------------------------------------------------------------------
# ChangeEvent parsing
# --------------------------------------------------------------------------


class TestChangeEvent:
    """Parsing raw event payloads."""

    def test_parses_a_flattened_event(self):
        event = ChangeEvent.from_dict(
            {"op": "INSERT", "before": None, "after": {"customer_id": "c1"}}
        )
        assert event.op == INSERT
        assert event.before is None
        assert event.after == {"customer_id": "c1"}

    def test_parses_a_full_datastream_envelope(self, customer):
        event = ChangeEvent.from_dict(
            {
                "data": {
                    "op": "UPDATE",
                    "before": {"customer_id": "c1", "tier": "silver"},
                    "after": customer,
                }
            }
        )
        assert event.op == UPDATE
        assert event.before == {"customer_id": "c1", "tier": "silver"}
        assert event.after == customer

    def test_parses_a_z_suffixed_timestamp(self):
        event = ChangeEvent.from_dict(
            {
                "op": "INSERT",
                "after": {"customer_id": "c1"},
                "sourceTimestamp": "2026-01-15T10:30:00Z",
            }
        )
        assert event.source_timestamp is not None
        assert event.source_timestamp.tzinfo is not None

    def test_rejects_an_event_with_no_op(self):
        with pytest.raises(ValueError, match="no 'op' field"):
            ChangeEvent.from_dict({"after": {"customer_id": "c1"}})

    def test_rejects_an_unknown_op(self):
        with pytest.raises(ValueError, match="unknown operation"):
            ChangeEvent.from_dict({"op": "UPSERT", "after": {"customer_id": "c1"}})

    def test_image_for_apply_uses_after_for_writes(self, customer):
        event = ChangeEvent(op=INSERT, after=customer)
        assert event.image_for_apply() == customer

    def test_image_for_apply_uses_before_for_deletes(self, customer):
        event = ChangeEvent(op=DELETE, before=customer)
        assert event.image_for_apply() == customer


# --------------------------------------------------------------------------
# The merge
# --------------------------------------------------------------------------


class TestCdcState:
    """The merge semantics."""

    def test_insert_adds_a_row(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        assert state.apply_event({"op": "INSERT", "after": customer}) is True
        assert state.row_count() == 1
        assert state.get(customer) == customer

    def test_update_replaces_the_row(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        state.apply_event({"op": "INSERT", "after": customer})
        updated = {**customer, "tier": "platinum"}
        state.apply_event(
            {"op": "UPDATE", "before": customer, "after": updated}
        )
        assert state.row_count() == 1
        assert state.get(customer)["tier"] == "platinum"

    def test_delete_removes_the_row(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        state.apply_event({"op": "INSERT", "after": customer})
        state.apply_event({"op": "DELETE", "before": customer})
        assert state.row_count() == 0

    def test_delete_of_an_absent_row_is_a_no_op(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        assert state.apply_event({"op": "DELETE", "before": customer}) is False
        assert state.skipped_reasons.get("delete_of_absent_row") == 1

    def test_duplicate_insert_converges_instead_of_duplicating(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        state.apply_event({"op": "INSERT", "after": customer})
        state.apply_event({"op": "INSERT", "after": {**customer, "tier": "gold"}})
        assert state.row_count() == 1
        assert state.get(customer)["tier"] == "gold"

    def test_update_of_an_absent_row_is_inserted_not_dropped(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        assert state.apply_event({"op": "UPDATE", "after": customer}) is True
        assert state.row_count() == 1
        assert state.skipped_reasons.get("update_of_absent_row") == 1

    def test_an_event_with_no_image_is_skipped(self):
        state = CdcState(merge_keys=["customer_id"])
        assert state.apply_event({"op": "UPDATE", "before": None, "after": None}) is False
        assert state.skipped_reasons.get("no_row_image") == 1

    def test_an_event_missing_the_merge_key_is_skipped(self):
        state = CdcState(merge_keys=["customer_id"])
        assert state.apply_event({"op": "INSERT", "after": {"email": "x@y.z"}}) is False
        assert state.skipped_reasons.get("missing_merge_key") == 1

    def test_rejects_an_empty_merge_key_list(self):
        with pytest.raises(ValueError, match="must not be empty"):
            CdcState(merge_keys=[])

    def test_rejects_an_unknown_operation_on_the_state(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        with pytest.raises(ValueError, match="unknown operation"):
            state.apply(ChangeEvent(op="UPSERT", after=customer))


# --------------------------------------------------------------------------
# Idempotency
# --------------------------------------------------------------------------


class TestIdempotency:
    """The property that makes a CDC pipeline safe to retry."""

    def test_replaying_the_same_stream_gives_the_same_table(self, customer):
        events = [
            {"op": "INSERT", "after": customer},
            {"op": "UPDATE", "before": customer, "after": {**customer, "tier": "gold"}},
            {"op": "DELETE", "before": {**customer, "tier": "gold"}},
        ]
        first = apply_changes(events, ["customer_id"])
        second = apply_changes(events, ["customer_id"])
        assert first.snapshot() == second.snapshot()

    def test_replaying_a_duplicated_event_does_not_change_the_table(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        state.apply_event({"op": "INSERT", "after": customer})
        before = state.snapshot()
        state.apply_event({"op": "INSERT", "after": customer})
        assert state.snapshot() == before
        assert state.row_count() == 1


# --------------------------------------------------------------------------
# Ordering
# --------------------------------------------------------------------------


class TestOrdering:
    """The stream order determines the final state."""

    def test_insert_then_delete_leaves_no_rows(self, customer):
        state = apply_changes(
            [
                {"op": "INSERT", "after": customer},
                {"op": "DELETE", "before": customer},
            ],
            ["customer_id"],
        )
        assert state.row_count() == 0

    def test_delete_then_insert_leaves_one_row(self, customer):
        state = apply_changes(
            [
                {"op": "DELETE", "before": customer},
                {"op": "INSERT", "after": customer},
            ],
            ["customer_id"],
        )
        assert state.row_count() == 1

    def test_the_before_image_is_not_used_to_overwrite_the_after_image(self, customer):
        """The classic merge bug: writing the `before` image on an UPDATE."""
        state = apply_changes(
            [
                {"op": "INSERT", "after": customer},
                {
                    "op": "UPDATE",
                    "before": {**customer, "tier": "silver"},
                    "after": {**customer, "tier": "gold"},
                },
            ],
            ["customer_id"],
        )
        assert state.get(customer)["tier"] == "gold"


# --------------------------------------------------------------------------
# Composite keys
# --------------------------------------------------------------------------


class TestCompositeKeys:
    """Merge keys can be more than one column."""

    def test_two_rows_with_the_same_first_key_are_distinct(self):
        state = CdcState(merge_keys=["tenant_id", "customer_id"])
        state.apply_event(
            {"op": "INSERT", "after": {"tenant_id": "t1", "customer_id": "c1"}}
        )
        state.apply_event(
            {"op": "INSERT", "after": {"tenant_id": "t2", "customer_id": "c1"}}
        )
        assert state.row_count() == 2

    def test_the_update_targets_the_right_row(self):
        state = CdcState(merge_keys=["tenant_id", "customer_id"])
        state.apply_event(
            {"op": "INSERT", "after": {"tenant_id": "t1", "customer_id": "c1", "v": 1}}
        )
        state.apply_event(
            {"op": "INSERT", "after": {"tenant_id": "t2", "customer_id": "c1", "v": 2}}
        )
        state.apply_event(
            {
                "op": "UPDATE",
                "before": {"tenant_id": "t1", "customer_id": "c1", "v": 1},
                "after": {"tenant_id": "t1", "customer_id": "c1", "v": 99},
            }
        )
        assert state.get({"tenant_id": "t1", "customer_id": "c1"})["v"] == 99
        assert state.get({"tenant_id": "t2", "customer_id": "c1"})["v"] == 2


# --------------------------------------------------------------------------
# Snapshot determinism
# --------------------------------------------------------------------------


class TestSnapshot:
    """The snapshot is deterministic, so expected outputs stay stable."""

    def test_snapshot_is_sorted_by_merge_key(self):
        state = CdcState(merge_keys=["customer_id"])
        for cid in ("c003", "c001", "c002"):
            state.apply_event({"op": "INSERT", "after": {"customer_id": cid}})
        ids = [row["customer_id"] for row in state.snapshot()]
        assert ids == ["c001", "c002", "c003"]

    def test_snapshot_rows_are_copies_not_references(self, customer):
        state = CdcState(merge_keys=["customer_id"])
        state.apply_event({"op": "INSERT", "after": customer})
        row = state.snapshot()[0]
        row["tier"] = "mutated"
        assert state.get(customer)["tier"] == "gold"


# --------------------------------------------------------------------------
# SQL generation
# --------------------------------------------------------------------------


class TestSqlGeneration:
    """The generated SQL mirrors what Datastream runs."""

    def test_merge_sql_contains_the_on_clause(self):
        sql = build_bigquery_merge_sql("customers", ["customer_id"])
        assert "ON target.customer_id = source.customer_id" in sql

    def test_merge_sql_handles_composite_keys(self):
        sql = build_bigquery_merge_sql("customers", ["tenant_id", "customer_id"])
        assert "ON target.tenant_id = source.tenant_id" in sql
        assert "AND target.customer_id = source.customer_id" in sql

    def test_merge_sql_handles_insert_update_and_delete(self):
        sql = build_bigquery_merge_sql("customers", ["customer_id"])
        assert "WHEN NOT MATCHED BY TARGET THEN" in sql
        assert "UPDATE SET" in sql
        assert "THEN\n    DELETE" in sql

    def test_create_table_sql_marks_merge_keys_not_null(self):
        sql = bigquery_create_table_sql(
            "customers",
            ["customer_id", "first_name", "region"],
            ["customer_id"],
        )
        assert "customer_id STRING NOT NULL" in sql
        assert "first_name STRING" in sql
        assert "CLUSTER BY customer_id" in sql

    def test_create_table_sql_clusters_on_composite_keys(self):
        sql = bigquery_create_table_sql(
            "customers",
            ["tenant_id", "customer_id"],
            ["tenant_id", "customer_id"],
        )
        assert "CLUSTER BY tenant_id, customer_id" in sql
