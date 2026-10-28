"""Deduplicate rows by their deterministic key."""
from __future__ import annotations

from typing import Iterable, Mapping

from pipeline_logic import dedup_key


def dedup_rows(
    rows: Iterable[Mapping[str, object]],
    partition: str,
) -> list[dict[str, object]]:
    """Keep the last row for each business key.

    A row's identity is derived from the data (``partition:order_id``),
    never from when it arrived. That is what makes the deduplication
    work on a retry: the same input produces the same keys, and the
    same keys resolve to the same surviving row.

    Args:
        rows: The candidate rows.
        partition: The partition the rows belong to.

    Returns:
        The deduplicated rows, in first-seen order.
    """
    seen: dict[str, dict[str, object]] = {}
    order: list[str] = []

    for row in rows:
        key = dedup_key(str(row.get("order_id", "")), partition)
        if key not in seen:
            order.append(key)
        seen[key] = dict(row)

    return [seen[key] for key in order]
