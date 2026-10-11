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
