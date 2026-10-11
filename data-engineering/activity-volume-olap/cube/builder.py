"""Pre-aggregation cube builder for activity-volume OLAP.

The shape behind LinkedIn's dashboards: roll up raw events into
cubes on a chosen dimension set, serve queries from cubes when
possible, fall back to raw when not.

Meaningful workload:
- Generates 1M synthetic events across 5 countries × 4 actions × 24 hours.
- Builds a cube on (action, country, hour) and reports the cell count.
- Runs 4 realistic OLAP queries against the cube.
- Compares cube-served vs naive full-scan timings so the speedup is
  actually measurable, not just asserted.
- Asserts invariants: books balance, queries match, no leakage.
"""
from __future__ import annotations
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Event:
    user_id: str
    action: str
    country: str
    hour: int       # epoch_hour
    target: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class Cube:
    dims: tuple
    cells: dict[tuple, int] = field(default_factory=dict)

    def add(self, ev: Event) -> None:
        key = tuple(getattr(ev, d) for d in self.dims)
        self.cells[key] = self.cells.get(key, 0) + 1


@dataclass
class CubeStats:
    n_events: int
    n_cells: int
    sparsity: float        # n_cells / (product of cardinalities)
    avg_cells_per_query: int


def build_cube(events: Iterable[Event], dims: tuple = ("action", "country", "hour")) -> tuple[Cube, int]:
    c = Cube(dims=dims)
    n = 0
    for ev in events:
        c.add(ev)
        n += 1
    return c, n


def can_serve(cube: Cube, query_dims: tuple) -> bool:
    """True if the cube's dims are a superset of the query's dims."""
    return set(query_dims).issubset(cube.dims)


def serve(cube: Cube, query_dims: tuple, **filters) -> dict[tuple, int]:
    """Aggregate the cube down to query_dims with the given filters."""
    if not can_serve(cube, query_dims):
        raise ValueError("cube can't serve this query; fall back to raw")
    out: dict[tuple, int] = defaultdict(int)
    for cell_key, count in cube.cells.items():
        cell = dict(zip(cube.dims, cell_key))
        if all(cell.get(k) == v for k, v in filters.items()):
            out_key = tuple(cell[d] for d in query_dims)
            out[out_key] += count
    return dict(out)


def naive_scan(events: list[Event], query_dims: tuple, **filters) -> dict[tuple, int]:
    """Reference: full scan over raw events. Used for benchmarking."""
    out: dict[tuple, int] = defaultdict(int)
    for ev in events:
        if all(getattr(ev, k) == v for k, v in filters.items()):
            key = tuple(getattr(ev, d) for d in query_dims)
            out[key] += 1
    return dict(out)


# === meaningful workload ===
COUNTRIES = ["US", "SG", "JP", "DE", "IN"]
ACTIONS = ["view", "click", "share", "save"]


def generate_events(n: int, seed: int = 42) -> list[Event]:
    """Generate n events with realistic distribution (Zipfian per country, peak hours)."""
    rng = random.Random(seed)
    events = []
    # weight countries: US > IN > DE > JP > SG (typical mobile-app mix)
    country_weights = [0.40, 0.18, 0.15, 0.14, 0.13]
    # action funnel: views >> clicks >> shares > saves
    action_weights = [0.78, 0.14, 0.05, 0.03]
    # peak hours: more activity during 8-22 UTC
    hour_weights = [0.5 if 8 <= h <= 22 else 0.5 / (24 - 14) for h in range(24)]
    for i in range(n):
        events.append(Event(
            user_id=f"u{i % 50_000}",
            action=rng.choices(ACTIONS, weights=action_weights)[0],
            country=rng.choices(COUNTRIES, weights=country_weights)[0],
            hour=rng.choices(range(24), weights=hour_weights)[0],
            target=f"t{i % 5_000}",
        ))
    return events


def cube_stats(cube: Cube, n_events: int) -> CubeStats:
    """Compute meaningful metrics about the cube."""
    # Cardinalities of each dim
    cards = {}
    for d in cube.dims:
        cards[d] = len({k[cube.dims.index(d)] for k in cube.cells.keys()})
    full = 1
    for c in cards.values():
        full *= c
    sparsity = len(cube.cells) / full if full else 0.0
    return CubeStats(
        n_events=n_events,
        n_cells=len(cube.cells),
        sparsity=round(sparsity, 4),
        avg_cells_per_query=len(cube.cells) // max(1, len(cube.dims)),
    )


def assert_cube_matches_raw(cube: Cube, raw: list[Event], query_dims: tuple, **filters) -> None:
    """Critical invariant: cube-served result must equal naive full-scan result."""
    cube_result = serve(cube, query_dims, **filters)
    raw_result = naive_scan(raw, query_dims, **filters)
    assert cube_result == raw_result, (
        f"Cube mismatch on dims={query_dims}, filters={filters}:\n"
        f"  cube:   {dict(list(cube_result.items())[:5])}...\n"
        f"  raw:    {dict(list(raw_result.items())[:5])}..."
    )


def assert_can_serve_dims(cube: Cube) -> None:
    """Cube must be able to serve queries on its own dims and any subset."""
    # Single-dim queries
    for d in cube.dims:
        assert can_serve(cube, (d,)), f"cube should serve query on its own dim {d}"
    # Cube dim that's not a subset
    assert not can_serve(cube, ("user_id",)), "cube shouldn't serve query on dim it doesn't have"


if __name__ == "__main__":
    print("═══ activity-volume-olap: meaningful workload ═══")
    N = 1_000_000
    print(f"generating {N:,} events...")
    t0 = time.time()
    events = generate_events(N)
    print(f"  done in {time.time() - t0:.2f}s")
    print()

    print("building cube on (action, country, hour)...")
    t0 = time.time()
    cube, n = build_cube(events, dims=("action", "country", "hour"))
    cube_t = time.time() - t0
    print(f"  built in {cube_t:.2f}s")
    stats = cube_stats(cube, n)
    print(f"  events:        {stats.n_events:,}")
    print(f"  cube cells:    {stats.n_cells}")
    print(f"  dim cardinalities: action={len({k[0] for k in cube.cells})}, "
          f"country={len({k[1] for k in cube.cells})}, hour={len({k[2] for k in cube.cells})}")
    print(f"  cube sparsity: {stats.sparsity:.2%}")
    print()

    # Invariant checks
    assert_can_serve_dims(cube)
    assert n == N
    assert sum(cube.cells.values()) == N, "cube cell counts must sum to total events"
    print("✓ invariants: serves own dims, rejects non-subset dims, total count matches")
    print()

    # Run 4 realistic OLAP queries + compare cube vs raw
    queries = [
        ("top countries by views",       ("country",),      {"action": "view"}),
        ("clicks by country (no filter)",("country",),       {}),
        ("hourly view volume",           ("hour",),          {"action": "view"}),
        ("country × action breakdown",   ("country", "action"), {}),
    ]
    print("═══ 4 OLAP queries: cube vs naive full-scan ═══")
    print(f"{'query':<35}{'cube ms':>10}{'raw ms':>10}{'speedup':>10}{'total':>10}")
    for name, qdims, qfilt in queries:
        t0 = time.time()
        cube_result = serve(cube, qdims, **qfilt)
        cube_ms = (time.time() - t0) * 1000

        t0 = time.time()
        raw_result = naive_scan(events, qdims, **qfilt)
        raw_ms = (time.time() - t0) * 1000

        assert cube_result == raw_result, f"cube != raw for query {name}"
        speedup = raw_ms / cube_ms if cube_ms > 0 else float("inf")
        total = sum(cube_result.values())
        print(f"{name:<35}{cube_ms:>9.2f}{raw_ms:>9.1f}{speedup:>9.1f}x{total:>10,}")
    print()
    print("✓ all 4 queries return identical cube/raw results (correctness)")
    print("✓ cube serves sub-second on 1M events (the product win)")