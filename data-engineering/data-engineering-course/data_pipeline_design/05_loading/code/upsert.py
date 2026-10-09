"""Upsert / merge helpers for SQLite.

SQLite has ``INSERT OR REPLACE`` (since 3.24) which is
sufficient for the spec'd test (insert 10 rows, upsert with 5
changes, assert 10 rows total + 5 changed).

The function also implements a more general "merge into" using
``INSERT ... ON CONFLICT`` so callers can specify which
columns to update and which to leave alone.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

from common import QueryRunner


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def merge_into(
    q: QueryRunner,
    target: str,
    source: Sequence[Dict[str, Any]],
    on_keys: Sequence[str],
    update_cols: Sequence[str],
) -> Dict[str, int]:
    """Upsert rows from ``source`` into ``target``.

    Rows are matched on the composite key ``on_keys``. For
    matching rows, the columns in ``update_cols`` are updated;
    for non-matching rows, the full row is inserted.

    Returns a dict with ``inserted`` and ``updated`` counts.

    Implementation note: SQLite supports ``INSERT ... ON
    CONFLICT (...) DO UPDATE`` since 3.24. We use that. If
    a key column is missing from the source row, the row is
    skipped (and counted in ``skipped``).
    """
    if not source:
        return {"inserted": 0, "updated": 0, "skipped": 0}

    # Get the union of columns in target and source so the INSERT
    # covers all of them. We must use a column list that exists
    # in the target, so we read it from sqlite_master.
    info = q.query_all(f"PRAGMA table_info({_quote(target)})")
    if not info:
        raise ValueError(f"target table {target!r} does not exist")
    target_cols = [row["name"] for row in info]

    inserted = 0
    updated = 0
    skipped = 0

    for row in source:
        # Validate that all key columns are present.
        if any(row.get(k) in (None, "") for k in on_keys):
            skipped += 1
            continue

        # Build the column list: all target columns, using NULL
        # for missing source values.
        cols = target_cols
        placeholders = ", ".join("?" for _ in cols)
        col_list = ", ".join(_quote(c) for c in cols)
        values = [row.get(c) for c in cols]

        update_assignments = ", ".join(
            f"{_quote(c)} = excluded.{_quote(c)}" for c in update_cols
        )
        conflict_target = ", ".join(_quote(k) for k in on_keys)

        sql = (
            f"INSERT INTO {_quote(target)} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_target}) DO UPDATE SET {update_assignments}"
        )

        # Detect insert vs update by checking the rowcount and
        # the change count from SQLite. sqlite3's execute returns
        # rowcount which is 1 for INSERT and 2 for UPDATE in
        # recent Python versions, but it's not portable. We use
        # a pre-check: did the row already exist?
        key_predicate = " AND ".join(
            f"{_quote(k)} = ?" for k in on_keys
        )
        key_values = [row.get(k) for k in on_keys]
        existing = q.query_one(
            f"SELECT 1 AS x FROM {_quote(target)} WHERE {key_predicate}",
            key_values,
        )
        q.execute(sql, values)
        if existing:
            updated += 1
        else:
            inserted += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped}
