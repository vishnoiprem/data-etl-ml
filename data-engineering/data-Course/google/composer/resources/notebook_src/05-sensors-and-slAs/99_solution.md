**1.** `timeout=timedelta(minutes=30)` on the sensor, `execution_timeout=timedelta(minutes=45)` on the transform task, `retries=3` with `retry_delay=timedelta(minutes=5)`, `sla=timedelta(hours=2)` on the DAG's final task. If the source never arrives, the **sensor timeout** fires first — after 30 minutes — and the task fails; that failure then consumes one of the three retries.

**2.**

```python
def ready_for_load(lines):
    accepted, rejected = transform_orders(lines)
    return len(accepted) >= 1000 and len(rejected) < 100
```

Against `orders.csv` this returns True (1 245 accepted, 0 rejected); against `malformed_orders.csv` it returns False (0 accepted, 5 rejected). A "file exists" check is wrong for both: for the malformed file the file *does* exist, so an existence check would pass and the pipeline would load garbage; for the good file an existence check would also pass even if the upload were truncated to a header plus ten rows, because the file is still there.

**3.** The deadline for logical date `2026-01-15` is the interval end `2026-01-16 00:00 UTC` plus two hours, i.e. `2026-01-16 02:00 UTC`. The run finished at `2026-01-20 04:00 UTC`, so it **missed** the SLA. The answer depends only on the logical date and the finish time of the *data interval*, never on when the backfill was executed — otherwise every backfill would be automatically "late" for the crime of repairing history, and the metric would measure operator behaviour instead of pipeline health.
