"""
cdc.py — the change-data-capture engine for the Datastream course.

This module is the heart of the course's working code. It is a **pure
implementation of what Google Cloud Datastream does on the BigQuery side of
the pipeline**: it takes a stream of change events and applies them to a
table, so that the table always reflects the source database's current state.

The module depends on nothing but the standard library. That is deliberate:

* it runs with no GCP account, no credentials and no bill;
* it can be unit-tested in milliseconds;
* every rule it implements is a rule you can point at in the Datastream
  documentation and explain in an interview.

What Datastream actually does, in three sentences: it reads the source
database's write-ahead log, converts each row change into an event carrying
*before* and *after* images, and writes those events into BigQuery, where
they are applied to the destination table according to the **merge keys** you
configured. The events are immutable and append-only; the table is not. That
distinction — immutable log, mutable table — is the single most important
idea in this course, and everything here is built around it.

Usage:
    from cdc import apply_event, apply_events, CdcState

    state = CdcState()
    state.apply({"op": "INSERT", "after": {"id": 1, "name": "Ada"}})
    state.apply({"op": "UPDATE", "before": {"id": 1}, "after": {"id": 1, "name": "Grace"}})
    state.apply({"op": "DELETE", "before": {"id": 1}})
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Mapping, Sequence

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Operation vocabulary
# --------------------------------------------------------------------------

#: The three change operations. Datastream's own API models them as
#: `INSERT`, `UPDATE` and `DELETE`. A `TRUNCATE` is modelled as a
#: `DELETE` in the BigQuery sink, which is worth knowing — see the chapter
#: on schema evolution.
INSERT = "INSERT"
UPDATE = "UPDATE"
DELETE = "DELETE"

VALID_OPS = frozenset({INSERT, UPDATE, DELETE})


def parse_op(value: str) -> str:
    """Normalise an operation string to its canonical uppercase form.

    Args:
        value: The raw operation name.

    Returns:
        One of `INSERT`, `UPDATE`, `DELETE`.

    Raises:
        ValueError: If the operation is not recognised.
    """
    op = str(value).strip().upper()
    if op not in VALID_OPS:
        raise ValueError(
            f"unknown operation: {value!r} (expected one of {sorted(VALID_OPS)})"
        )
    return op


# --------------------------------------------------------------------------
# The merge key
# --------------------------------------------------------------------------


def merge_key_of(
    row: Mapping[str, Any] | None,
    merge_keys: Sequence[str],
) -> tuple[Any, ...]:
    """Extract the merge key tuple from a row.

    The merge key is the set of columns that identify a row uniquely in the
    destination table. It is the *only* thing that makes an `UPDATE`
    distinguishable from an `INSERT`, and getting it wrong is the classic
    Datastream bug: with a non-unique merge key, a single update can
    silently match and overwrite several rows at once.

    Args:
        row: The row image, or None.
        merge_keys: The merge key column names.

    Returns:
        The tuple of key values, in the order given by `merge_keys`.

    Raises:
        ValueError: If the row is None, or a key column is missing.
    """
    if row is None:
        raise ValueError("cannot build a merge key from a missing row image")
    if not merge_keys:
        raise ValueError("merge_keys must not be empty")

    values: list[Any] = []
    for key in merge_keys:
        if key not in row:
            raise ValueError(f"merge key column {key!r} is missing from the row image")
        values.append(row[key])
    return tuple(values)


# --------------------------------------------------------------------------
# The change event
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChangeEvent:
    """One row change, in the shape Datastream delivers it.

    Datastream's `data` payload carries a `sourceType` of `TABLE`, a
    `sourceSchema`, `before` and `after` images, and a `op` field. This
    dataclass models the parts that matter for applying the change.

    Attributes:
        op: The operation — `INSERT`, `UPDATE` or `DELETE`.
        before: The row image before the change. Present for `UPDATE` and
            `DELETE`; `None` for `INSERT`.
        after: The row image after the change. Present for `INSERT` and
            `UPDATE`; `None` for `DELETE`.
        source_timestamp: When the source database committed the change.
        server_timestamp: When Datastream observed the change.
        key_values: The primary key of the source table, when known.
    """

    op: str
    before: Mapping[str, Any] | None = None
    after: Mapping[str, Any] | None = None
    source_timestamp: datetime | None = None
    server_timestamp: datetime | None = None
    key_values: Mapping[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ChangeEvent":
        """Build a `ChangeEvent` from a raw Datastream-shaped dict.

        Accepts either the full Datastream envelope — where the row images
        live under `data.before` / `data.after` — or a flattened dict where
        `before` and `after` are at the top level. The course's sample data
        uses the flattened form, because that is what a Kafka message
        carrying a Datastream payload looks like after extraction.

        Args:
            payload: The raw event dict.

        Returns:
            The parsed change event.

        Raises:
            ValueError: If the operation is missing or unrecognised.
        """
        data = payload.get("data") if isinstance(payload.get("data"), Mapping) else payload

        op_raw = data.get("op") or payload.get("op")
        if op_raw is None:
            raise ValueError("change event has no 'op' field")
        op = parse_op(op_raw)

        before = data.get("before")
        after = data.get("after")

        return cls(
            op=op,
            before=dict(before) if isinstance(before, Mapping) else None,
            after=dict(after) if isinstance(after, Mapping) else None,
            source_timestamp=_parse_ts(
                data.get("sourceTimestamp") or payload.get("sourceTimestamp")
            ),
            server_timestamp=_parse_ts(
                data.get("serverTimestamp") or payload.get("serverTimestamp")
            ),
            key_values=(
                dict(payload["keyValues"])
                if isinstance(payload.get("keyValues"), Mapping)
                else None
            ),
        )

    def image_for_apply(self) -> Mapping[str, Any] | None:
        """Return the row image that carries the resulting state.

        For an `INSERT` or `UPDATE` that is the `after` image; for a
        `DELETE` it is the `before` image, because the delete is expressed
        as "remove the row that has this key".

        Returns:
            The row image, or None when the event carries no image.
        """
        return self.after if self.op in (INSERT, UPDATE) else self.before


def _parse_ts(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# --------------------------------------------------------------------------
# The destination table
# --------------------------------------------------------------------------


@dataclass
class CdcState:
    """The destination table, and the merge logic that maintains it.

    This models the BigQuery table Datastream writes into: a mutable,
    primary-keyed table whose rows are maintained by applying a stream of
    changes.

    The class deliberately does *not* attempt to be a BigQuery emulator. It
    implements the **semantics** of a merge — insert when the key is new,
    update when the key exists, delete when the key is present and the
    operation says to remove it — which is exactly the contract Datastream
    gives you when you configure merge keys.

    Attributes:
        merge_keys: The columns that identify a row.
        rows: The current table contents, keyed by merge-key tuple.
        applied_count: How many events have been applied.
        skipped_count: How many events were skipped as duplicates.
        skipped_reasons: A tally of *why* events were skipped.
    """

    merge_keys: Sequence[str]
    rows: dict[tuple[Any, ...], dict[str, Any]] = field(default_factory=dict)
    applied_count: int = 0
    skipped_count: int = 0
    skipped_reasons: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the merge keys."""
        if not self.merge_keys:
            raise ValueError("merge_keys must not be empty")
        self.merge_keys = tuple(self.merge_keys)

    # -- reading ---------------------------------------------------------

    def get(self, row: Mapping[str, Any]) -> dict[str, Any] | None:
        """Look up a row by its merge key.

        Args:
            row: Any row image containing the merge key columns.

        Returns:
            A copy of the stored row, or None when the key is absent.
        """
        key = merge_key_of(row, self.merge_keys)
        stored = self.rows.get(key)
        return dict(stored) if stored is not None else None

    def snapshot(self) -> list[dict[str, Any]]:
        """Return the table contents as a list of row dicts.

        The rows are sorted by merge key, so the output is deterministic —
        which is what makes the course's expected outputs stable.

        Returns:
            The rows, ordered by merge key.
        """
        return [dict(self.rows[key]) for key in sorted(self.rows, key=repr)]

    def row_count(self) -> int:
        """Return the number of rows in the table."""
        return len(self.rows)

    # -- writing ---------------------------------------------------------

    def apply(self, event: ChangeEvent) -> bool:
        """Apply one change event to the table.

        The merge rules, in full:

        * `INSERT` — add the `after` image. If the key already exists, the
          insert is treated as an update (this is the "upsert" behaviour
          BigQuery's `MERGE` gives you), because a well-behaved source
          will never insert a duplicate key.
        * `UPDATE` — replace the `after` image. If the key does not exist,
          the update is *inserted* rather than dropped, because dropping it
          would lose data whenever the stream started mid-history.
        * `DELETE` — remove the row identified by the `before` image.

        Args:
            event: The change to apply.

        Returns:
            True when the table changed, False when the event was skipped.

        Raises:
            ValueError: If the event's image cannot produce a merge key.
        """
        if event.op not in VALID_OPS:
            raise ValueError(f"unknown operation: {event.op!r}")

        image = event.image_for_apply()
        if image is None:
            self._skip("no_row_image")
            return False

        try:
            key = merge_key_of(image, self.merge_keys)
        except ValueError:
            self._skip("missing_merge_key")
            return False

        if event.op == DELETE:
            if key in self.rows:
                del self.rows[key]
                self.applied_count += 1
                return True
            # Deleting a row that is not there is a no-op, not an error.
            # This happens legitimately whenever a stream starts
            # mid-history, or a source transaction is rolled back.
            self._skip("delete_of_absent_row")
            return False

        if event.op == INSERT and key in self.rows:
            # Duplicate insert — treat as an update so the table converges
            # on the latest image rather than erroring.
            self._skip("duplicate_insert")
            self.rows[key] = dict(event.after or {})
            self.applied_count += 1
            return True

        if event.op == UPDATE and key not in self.rows:
            # An update for a row we never saw. Insert it — the change is
            # still true, and dropping it would silently lose data.
            self._skip("update_of_absent_row")
            self.rows[key] = dict(event.after or {})
            self.applied_count += 1
            return True

        self.rows[key] = dict(event.after or {})
        self.applied_count += 1
        return True

    def apply_event(self, payload: Mapping[str, Any]) -> bool:
        """Parse and apply a raw event dict.

        Args:
            payload: The raw change event.

        Returns:
            True when the table changed, False when the event was skipped.
        """
        return self.apply(ChangeEvent.from_dict(payload))

    def apply_events(self, payloads: Iterable[Mapping[str, Any]]) -> int:
        """Apply a stream of raw event dicts.

        Args:
            payloads: The change events, in order.

        Returns:
            The number of events that changed the table.
        """
        changed = 0
        for payload in payloads:
            if self.apply_event(payload):
                changed += 1
        return changed

    def _skip(self, reason: str) -> None:
        """Record that an event was skipped, and why."""
        self.skipped_count += 1
        self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + 1
        log.debug("skipped change event: %s", reason)


# --------------------------------------------------------------------------
# Reference implementation
# --------------------------------------------------------------------------


def apply_changes(
    payloads: Iterable[Mapping[str, Any]],
    merge_keys: Sequence[str],
) -> CdcState:
    """Apply a stream of changes to a fresh table.

    This is the reference implementation used to cross-validate the
    pipeline. It is deliberately simple: create a table, apply everything,
    return the table.

    Args:
        payloads: The change events, in order.
        merge_keys: The merge key columns.

    Returns:
        The resulting table state.
    """
    state = CdcState(merge_keys=merge_keys)
    state.apply_events(payloads)
    return state


def build_bigquery_merge_sql(
    table: str,
    merge_keys: Sequence[str],
    *,
    project: str = "YOUR_PROJECT_ID",
    dataset: str = "your_dataset",
) -> str:
    """Generate the BigQuery `MERGE` statement Datastream effectively runs.

    You do not write this SQL by hand — Datastream generates and runs
    something equivalent behind the scenes. But you *should* understand it,
    because when a Datastream pipeline misbehaves, the fastest way to
    diagnose it is to run the equivalent `MERGE` yourself in BigQuery and
    see what it does with the same rows.

    The generated statement is deliberately written the way BigQuery's own
    `MERGE` documentation recommends: a `MERGE` on the merge key, an
    `INSERT` for unseen keys, an `UPDATE` for changed keys, and a `DELETE`
    for rows the source removed.

    Args:
        table: The unqualified table name.
        merge_keys: The merge key columns.
        project: The project id.
        dataset: The dataset name.

    Returns:
        The SQL statement, with placeholders for the source table.
    """
    keys = list(merge_keys)
    key_list = ", ".join(keys)
    on_clause = " AND ".join(f"target.{k} = source.{k}" for k in keys)

    insert_cols = ", ".join(keys)
    update_cols = ", ".join(
        f"target.{k} = source.{k}" for k in keys
    )
    # The `WHEN NOT MATCHED BY SOURCE` delete is what turns a MERGE into a
    # synchronised table: it removes rows that exist in the target but no
    # longer in the source. Datastream does not use it for streaming
    # (the source is a stream, not a snapshot), but it is the right
    # operator for a backfill, and it is worth knowing the difference.
    return f"""-- Synchronise the destination table from a change-event table.
-- Generated by cdc.build_bigquery_merge_sql(); the placeholder source
-- table is where Datastream writes the raw change events.
MERGE `{project}.{dataset}.{table}` AS target
USING `{project}.{dataset}.{table}_stream` AS source
    ON {on_clause}
WHEN NOT MATCHED BY TARGET THEN
    INSERT ({insert_cols})
    VALUES (source.{", source.".join(keys)})
WHEN MATCHED AND source.__op__ != 'DELETE' THEN
    UPDATE SET
        {update_cols}
WHEN MATCHED AND source.__op__ = 'DELETE' THEN
    DELETE""".strip()


# --------------------------------------------------------------------------
# BigQuery helpers
# --------------------------------------------------------------------------


def bigquery_create_table_sql(
    table: str,
    columns: Sequence[str],
    merge_keys: Sequence[str],
    *,
    project: str = "YOUR_PROJECT_ID",
    dataset: str = "your_dataset",
) -> str:
    """Generate the `CREATE TABLE` DDL for a CDC destination table.

    A BigQuery table maintained by Datastream has one extra requirement
    over an ordinary table: the merge key columns must be declared
    `NOT NULL`, because the merge is keyed on them and a NULL key cannot
    be matched.

    Args:
        table: The table name.
        columns: Every column in the table.
        merge_keys: The merge key columns, which are made `NOT NULL`.
        project: The project id.
        dataset: The dataset name.

    Returns:
        The DDL statement.
    """
    key_set = set(merge_keys)
    col_sql = []
    for column in columns:
        if column in key_set:
            col_sql.append(f"  {column} STRING NOT NULL")
        else:
            col_sql.append(f"  {column} STRING")
    body = ",\n".join(col_sql)
    return (
        f"CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (\n"
        f"{body}\n)\n"
        f"CLUSTER BY {', '.join(merge_keys)};"
    )


# --------------------------------------------------------------------------
# Streaming
# --------------------------------------------------------------------------


def iter_change_events(ndjson_path: str) -> Iterator[dict[str, Any]]:
    """Read change events from a newline-delimited JSON file.

    Args:
        ndjson_path: Path to the NDJSON file.

    Yields:
        One parsed event dict per line.
    """
    with open(ndjson_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def stream_events(events: Iterable[Mapping[str, Any]]) -> Iterator[ChangeEvent]:
    """Convert raw event dicts into `ChangeEvent` objects.

    Args:
        events: The raw events.

    Yields:
        The parsed change events. Malformed events are logged and skipped
        rather than raising — the same thing a production consumer does,
        because one bad message must not stop the stream.
    """
    for raw in events:
        try:
            yield ChangeEvent.from_dict(raw)
        except (ValueError, TypeError) as exc:
            log.warning("skipping malformed change event: %s", exc)
