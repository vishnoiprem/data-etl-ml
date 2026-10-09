"""Small, dependency-free analytics helpers.

These cover the kinds of operations that come up over and over in
SQL interviews and pipeline exercises: running totals, ranking with
ties, deduplication, and percentile reporting.

All functions are pure — they take a list, return a list (or tuple)
— so they're trivially testable.
"""

from __future__ import annotations

import statistics
from typing import Any, Callable, Dict, Hashable, List, Sequence, Tuple


def running_total(values: Sequence[float]) -> List[float]:
    """Cumulative sum: each element is the sum of all prior elements + self.

    >>> running_total([1, 2, 3, 4])
    [1, 3, 6, 10]
    """
    out: List[float] = []
    total = 0.0
    for v in values:
        total += float(v)
        out.append(total)
    return out


def rank_desc(values: Sequence[float]) -> List[int]:
    """Rank values in descending order, 1-based, dense rank with ties.

    Dense rank: tied values share a rank, and the next distinct value
    gets the next integer (no gaps between ranks).

    >>> rank_desc([10, 30, 20, 30, 5])
    [3, 1, 2, 1, 4]
    """
    indexed = sorted(enumerate(values), key=lambda iv: -float(iv[1]))
    ranks: List[int] = [0] * len(values)
    current_dense_rank = 0
    last_val: Any = None
    for orig_idx, val in indexed:
        if last_val is None or val != last_val:
            current_dense_rank += 1
            last_val = val
        ranks[orig_idx] = current_dense_rank
    return ranks


def dedupe_by_key(
    rows: Sequence[Dict[str, Any]], key: str
) -> List[Dict[str, Any]]:
    """Deduplicate by ``key``, keeping the first occurrence.

    >>> dedupe_by_key([{"id": 1, "v": "a"}, {"id": 2, "v": "b"},
    ...                {"id": 1, "v": "c"}], "id")
    [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}]
    """
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for r in rows:
        k = r.get(key)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def p50_p95_p99(values: Sequence[float]) -> Tuple[float, float, float]:
    """Return the 50th, 95th, and 99th percentiles.

    Uses :func:`statistics.quantiles` under the hood. Empty input
    raises ``statistics.StatisticsError`` — callers that want a
    softer fallback should check ``len(values)`` first.
    """
    if not values:
        raise ValueError("p50_p95_p99 requires at least one value")
    sorted_vals = sorted(float(v) for v in values)
    # `quantiles` with n=100 gives the 1..99 percentiles.
    qs = statistics.quantiles(sorted_vals, n=100, method="inclusive")
    return (qs[49], qs[94], qs[98])


def top_k_by(
    rows: Sequence[Dict[str, Any]],
    key: str,
    k: int = 10,
    descending: bool = True,
) -> List[Dict[str, Any]]:
    """Return the top ``k`` rows by ``key`` value.

    >>> top_k_by([{"a": 1}, {"a": 3}, {"a": 2}], "a", k=2)
    [{'a': 3}, {'a': 2}]
    """
    return sorted(rows, key=lambda r: r.get(key), reverse=descending)[:k]


def group_count(
    rows: Sequence[Dict[str, Any]], key: str
) -> Dict[Hashable, int]:
    """Group by ``key`` and return a dict of counts."""
    out: Dict[Hashable, int] = {}
    for r in rows:
        k = r.get(key)
        out[k] = out.get(k, 0) + 1
    return out


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Numerator / denominator, returning ``default`` on zero divisor."""
    if denominator == 0:
        return default
    return numerator / denominator
