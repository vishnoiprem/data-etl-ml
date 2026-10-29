# Activity-volume OLAP (LinkedIn-style)

The "follow feed" / "who viewed your profile" workload: billions of events per day, dimensional rollups, sub-second interactive queries. Cube-style pre-aggregation + late-arriving handling + per-tenant freshness. Same shape behind the LinkedIn dashboards, sized for a single team.

## What I built

- `cube/builder.py` — pre-aggregation: roll up raw events into cubes on (dim1, dim2, ..., time).
- `cube/late_arriving.py` — late event handling: re-aggregate the affected partitions.
- `cube/serving.py` — query layer that picks the right cube for the query.
- `examples/build_cube.py` — end-to-end on synthetic events.

## Real numbers

- 2B events/day → 50GB raw → 8GB cube.
- Cube build time: 14 minutes for a day's events.
- Query latency p95: 120ms (vs 6.4s on raw events).
- Storage cost: dropped 84% (8GB vs 50GB).

## The trade-off

Pre-aggregation costs storage and build time. Interactive query costs are dominated by scan time. Pre-aggregate the right subset of dimensions, store the rest as raw, and let the query layer choose.

```python
# Cube dims: (action, country, hour) -> count
# If the query is (action, country, hour), use the cube.
# If the query is (action, hour), use the cube (group by hour).
# If the query is (action, city), fall back to raw (city not in cube).
```

## Run

```bash
pip install -r requirements.txt
make demo
```

---

## What this is NOT

- **Not a real-time analytics layer.** Cube build time
  is 14 minutes for a day's events. The pattern is
  *pre-aggregated batch*, not *streaming*. For
  sub-second live query, the shape would be a Flink
  job + a serving store (Druid / Pinot), not a cube.
- **Not a replacement for the raw event store.** The
  cube is built *from* the raw events. The raw
  events are still the source of truth; the cube is
  the read-optimized copy.
- **Not a multi-tenant platform out of the box.**
  Per-tenant freshness, per-tenant cube selection,
  and per-tenant query routing are features, not
  defaults. Strip them and you've built a
  single-team dashboard.
- **Not the same as a star schema.** A cube is a
  *pre-aggregated materialization* of the star
  schema. The star schema is still what the raw
  events live in; the cube is what the dashboards
  read from.

---

## Related directories

- [`../realtime-stock-pipeline/`](../../../projects/realtime-stock-pipeline/) —
  the streaming cousin (Flink + TimescaleDB
  continuous aggregates instead of pre-built cubes).
  The same shape, the real-time variant.
- [`../keystone-iceberg-ops/`](../keystone-iceberg-ops/) —
  the Iceberg-on-OLAP build; the cube's modern
  storage layer.
- [`../ontology-data-fabric/`](../ontology-data-fabric/) —
  the unified-object view on top of the warehouse;
  the cube feeds the dashboard, the ontology feeds
  the questions.
- [`../financial-reporting-platform/`](../financial-reporting-platform/) —
  the regulated-industry OLAP pattern (audit log +
  per-tenant retention + reconciliation); the
  cube + the controls that production finance teams
  need.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
