"""Slowly Changing Dimension (SCD) implementations.

The three SCD types you'll see in any data modeling interview:

  * SCD Type 1 — overwrite the old value with the new one.
    No history is kept.
  * SCD Type 2 — add a new row, mark the old one as expired.
    History is kept via ``effective_date``, ``expiry_date``,
    and ``is_current``.
  * SCD Type 3 — add a new column to track the *previous*
    value. Only one level of history.

The functions in this module implement each one against an
existing `QueryRunner` that already has a dimension table
populated.

The SCD convention we use here:

  * The dimension has a surrogate key (e.g. ``customer_key``).
  * The natural key is something like ``customer_id``.
  * SCD 2 columns: ``effective_date``, ``expiry_date``,
    ``is_current`` (1 = current row, 0 = expired).
  * ``expiry_date`` is set to ``'9999-12-31'`` for the
    current row.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from common import QueryRunner


# Sentinel for the "still current" expiry.
FOREVER = "9999-12-31"


def _to_iso(d: Any) -> str:
    """Coerce a date-like to ISO ``YYYY-MM-DD``."""
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _next_surrogate_key(q: QueryRunner, table: str, key_col: str) -> int:
    """Return MAX(key_col) + 1 (or 1 if the table is empty)."""
    row = q.query_one(f'SELECT MAX("{key_col}") AS m FROM "{table}"')
    return (row["m"] or 0) + 1


def scd1_update(
    q: QueryRunner,
    dim_table: str,
    key_col: str,
    key_val: Any,
    updated_fields: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """SCD Type 1: overwrite the existing row in place.

    No history is kept. Use this when:

    * the change is non-historical (e.g., a typo in the
      user's display name), or
    * the analytics team only cares about the *current*
      value (e.g., a free-text comment).

    Args:
        q: a `QueryRunner`.
        dim_table: name of the dimension table.
        key_col: the natural-key column (e.g.,
            ``"customer_id"``). The row to update is
            identified by ``key_col = key_val``.
        key_val: the value of ``key_col`` to match.
        updated_fields: a dict of column -> new value.

    Returns:
        The updated row as a list of dicts (length 1).

    Example:
        >>> import tempfile, os
        >>> from common import QueryRunner, Table, Column
        >>> with QueryRunner(":memory:") as q:
        ...     q.execute(Table("dim_users", [
        ...         Column("customer_id", "INTEGER", primary_key=True),
        ...         Column("name", "TEXT"),
        ...     ]).to_ddl())
        ...     q.execute("INSERT INTO dim_users VALUES (1, 'Alice')")
        ...     out = scd1_update(q, "dim_users", "customer_id", 1,
        ...                        {"name": "Alice Smith"})
        ...     out[0]["name"]
        'Alice Smith'
    """
    if not updated_fields:
        raise ValueError("updated_fields is empty; nothing to do")

    set_clause = ", ".join(f'"{c}" = ?' for c in updated_fields)
    params = list(updated_fields.values()) + [key_val]
    q.execute(
        f'UPDATE "{dim_table}" SET {set_clause} WHERE "{key_col}" = ?',
        params,
    )
    rows = q.query_all(
        f'SELECT * FROM "{dim_table}" WHERE "{key_col}" = ?',
        [key_val],
    )
    return rows


def scd2_insert(
    q: QueryRunner,
    dim_table: str,
    key_col: str,
    key_val: Any,
    new_fields: Dict[str, Any],
    effective_date: Any = None,
    surrogate_col: str = "id",
) -> List[Dict[str, Any]]:
    """SCD Type 2: expire the current row, insert a new one.

    The "current" row (the one with ``is_current = 1`` and
    ``key_col = key_val``) is expired: its ``expiry_date`` is
    set to ``effective_date - 1 day`` and ``is_current`` to 0.
    A new row is inserted with ``is_current = 1``,
    ``expiry_date = '9999-12-31'``, and the ``new_fields``
    applied.

    Args:
        q: a `QueryRunner`.
        dim_table: name of the dimension table.
        key_col: the natural-key column.
        key_val: the value of ``key_col`` to match.
        new_fields: a dict of column -> new value to apply
            to the new row. Should include the
            natural-key column.
        effective_date: the date the new version becomes
            active. Defaults to today.
        surrogate_col: the name of the surrogate key
            column (default ``"id"``).

    Returns:
        All rows for the natural key, in order of
        ``effective_date`` (oldest first).

    Example:
        >>> with QueryRunner(":memory:") as q:
        ...     q.execute(Table("dim_users", [
        ...         Column("id", "INTEGER", primary_key=True),
        ...         Column("customer_id", "INTEGER", nullable=False),
        ...         Column("plan", "TEXT"),
        ...         Column("effective_date", "TEXT", nullable=False),
        ...         Column("expiry_date", "TEXT", nullable=False),
        ...         Column("is_current", "INTEGER", nullable=False),
        ...     ]).to_ddl())
        ...     q.execute("INSERT INTO dim_users VALUES "
        ...                "(1, 100, 'free', '2024-01-01', '9999-12-31', 1)")
        ...     out = scd2_insert(q, "dim_users", "customer_id", 100,
        ...                        {"customer_id": 100, "plan": "pro"},
        ...                        effective_date="2024-06-01")
        ...     [(r["plan"], r["is_current"]) for r in out]
        [('free', 0), ('pro', 1)]
    """
    eff = _to_iso(effective_date) if effective_date is not None else (
        datetime.utcnow().date().isoformat()
    )
    if key_col not in new_fields:
        raise ValueError(
            f"new_fields must include the natural key {key_col!r}"
        )

    # 1. Expire the current row.
    # Expiry is the day before the new effective date.
    eff_date = datetime.strptime(eff, "%Y-%m-%d").date()
    prev_expiry = eff_date.replace()  # placeholder
    from datetime import timedelta
    prev_expiry = (eff_date - timedelta(days=1)).isoformat()
    q.execute(
        f'UPDATE "{dim_table}" '
        f'SET "expiry_date" = ?, "is_current" = 0 '
        f'WHERE "{key_col}" = ? AND "is_current" = 1',
        [prev_expiry, key_val],
    )

    # 2. Insert the new row.
    new_id = _next_surrogate_key(q, dim_table, surrogate_col)
    all_fields = dict(new_fields)
    all_fields[surrogate_col] = new_id
    all_fields["effective_date"] = eff
    all_fields["expiry_date"] = FOREVER
    all_fields["is_current"] = 1

    cols = ", ".join(f'"{c}"' for c in all_fields)
    placeholders = ", ".join("?" for _ in all_fields)
    q.execute(
        f'INSERT INTO "{dim_table}" ({cols}) VALUES ({placeholders})',
        list(all_fields.values()),
    )

    return q.query_all(
        f'SELECT * FROM "{dim_table}" WHERE "{key_col}" = ? '
        f'ORDER BY "effective_date"',
        [key_val],
    )


def scd3_add_column(
    q: QueryRunner,
    dim_table: str,
    key_col: str,
    key_val: Any,
    prev_value_col: str,
    new_value: Any,
) -> List[Dict[str, Any]]:
    """SCD Type 3: store the *previous* value in a side column.

    Only one level of history is kept (the *previous* value).
    Use this when:

    * the change is rare and you only need to know "what was
      it before?",
    * the cost of SCD 2 (extra rows) is not justified, or
    * the analysis is simple (e.g., "did this customer
      upgrade?").

    Args:
        q: a `QueryRunner`.
        dim_table: name of the dimension table.
        key_col: the natural-key column.
        key_val: the value of ``key_col`` to match.
        prev_value_col: the name of the column to add
            (e.g., ``"previous_plan"``). If the column
            doesn't exist, it is added via ALTER TABLE.
        new_value: the new value to set on the row.

    Returns:
        The updated row as a list of dicts (length 1).

    Example:
        >>> with QueryRunner(":memory:") as q:
        ...     q.execute(Table("dim_users", [
        ...         Column("customer_id", "INTEGER", primary_key=True),
        ...         Column("plan", "TEXT"),
        ...     ]).to_ddl())
        ...     q.execute("INSERT INTO dim_users VALUES (1, 'free')")
        ...     out = scd3_add_column(q, "dim_users", "customer_id", 1,
        ...                            "previous_plan", "pro")
        ...     out[0]["previous_plan"], out[0]["plan"]
        ('free', 'pro')
    """
    # 1. Get the current value of the column (this becomes the
    #    "previous" value).
    row = q.query_one(
        f'SELECT * FROM "{dim_table}" WHERE "{key_col}" = ?',
        [key_val],
    )
    if row is None:
        raise ValueError(
            f"no row with {key_col} = {key_val!r} in {dim_table!r}"
        )
    current_value = row.get(prev_value_col.replace("previous_", ""))
    if current_value is None:
        # Fallback: try the column name as-is.
        current_value = row.get(prev_value_col)

    # 2. Add the column if it doesn't exist. SQLite doesn't
    #    support `IF NOT EXISTS` on ALTER TABLE ADD COLUMN in
    #    all versions, so we catch the error.
    try:
        q.execute(
            f'ALTER TABLE "{dim_table}" ADD COLUMN '
            f'"{prev_value_col}" TEXT'
        )
    except Exception:
        # Column already exists.
        pass

    # 3. Update the row: previous = current value, current = new.
    #    On subsequent updates, the "previous" should hold the
    #    most recent value (not be sticky), so we always overwrite.
    target_col = prev_value_col.replace("previous_", "")
    q.execute(
        f'UPDATE "{dim_table}" '
        f'SET "{prev_value_col}" = "{target_col}", '
        f'    "{target_col}" = ? '
        f'WHERE "{key_col}" = ?',
        [new_value, key_val],
    )

    return q.query_all(
        f'SELECT * FROM "{dim_table}" WHERE "{key_col}" = ?',
        [key_val],
    )


# ---- conformed & role-playing dimensions --------------------------------


def mark_conformed(dims: List[str]) -> str:
    """Return a label that marks a list of dimensions as *conformed*.

    A conformed dimension is one that is shared across multiple
    fact tables with the *same* key and semantics.
    `dim_date` is the canonical example. This helper just
    returns a printable string — it's documentation, not logic.
    """
    return (
        "Conformed dimension — same key, same semantics, "
        "shared across fact tables:\n  - "
        + "\n  - ".join(dims)
    )


def role_playing_dim_note(role: str, base_dim: str) -> str:
    """Documentation helper for a *role-playing* dimension.

    A role-playing dimension is one logical dim used in
    multiple roles on the same fact. The classic example is
    `dim_date` playing the roles of `order_date`,
    `ship_date`, and `delivery_date` on an `fact_orders`
    table.
    """
    return (
        f"Role: {role!r} is played by {base_dim!r}. "
        f"The fact has multiple FKs to the same dim, each "
        f"labeled with a role-playing alias."
    )


# ---- junk & degenerate dimensions ----------------------------------------


def is_junk_dim_cardinality(n_distinct: int) -> bool:
    """Heuristic: is this dimension a *junk* dim?

    A junk dim holds low-cardinality flags (yes/no, true/false,
    status). The rule of thumb: if there are < 50 distinct
    values and no obvious hierarchy, it's a junk dim candidate.
    """
    return 0 < n_distinct <= 50


def is_degenerate_dim(n_columns: int, n_distinct: int) -> bool:
    """Heuristic: is this dimension a *degenerate* dim?

    A degenerate dim is a transaction id (e.g., ``order_id``)
    that lives on the fact table itself rather than in its
    own dim. The rule: if the "dim" is a single key with no
    attributes, keep it on the fact.
    """
    return n_columns == 1 and n_distinct > 1
