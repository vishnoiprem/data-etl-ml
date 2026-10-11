"""Pre-aggregation cube builder for activity-volume OLAP.

The shape behind LinkedIn's dashboards: roll up raw events into
cubes on a chosen dimension set, serve queries from cubes when
possible, fall back to raw when not.
"""
from __future__ import annotations
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


def build_cube(events: Iterable[Event], dims: tuple = ("action", "country", "hour")) -> Cube:
    c = Cube(dims=dims)
    for ev in events:
        c.add(ev)
    return c


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


if __name__ == "__main__":
    import random
    events = [
        Event(user_id=f"u{i%100}", action="view", country=random.choice(["US", "SG", "JP"]),
              hour=i % 24, target=f"t{i%50}")
        for i in range(10_000)
    ]
    cube = build_cube(events)
    print(f"cube size: {len(cube.cells)} cells")
    print(f"view counts by country: {serve(cube, ('country',), action='view')}")
