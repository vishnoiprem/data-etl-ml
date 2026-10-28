```python
# Exercise 1
import json


def xcom_budget(payload):
    return len(json.dumps(payload, default=str).encode("utf-8"))


row = {
    "order_id": "o00000000",
    "customer_id": "c000914",
    "order_ts": "2026-01-15T00:54:38+00:00",
    "region": "AMER",
    "channel": "web",
    "currency": "GBP",
    "status": "complete",
    "amount": 700.97,
    "product_id": "p0173",
}

print(xcom_budget([row] * 1245))           # ~300,000+ bytes - way over 48 KB
print(48 * 1024 // xcom_budget([row]))     # ~160 rows fit
```

You would push the **GCS path** of the written file (plus a row count) —
a few dozen bytes — and let the downstream task read the data from GCS or
BigQuery.

```python
# Exercise 2
from local_runner import DAG, Task


def make_join_dag(rule):
    return DAG(
        f"join_{rule}",
        tasks=[
            Task("read_orders", read_orders, dependencies=[]),
            Task("transform", transform, dependencies=["read_orders"]),
            Task(
                "choose_strategy",
                choose_strategy,
                dependencies=["transform"],
                branch=True,
            ),
            Task("full_load", full_load, dependencies=["choose_strategy"]),
            Task("incremental_load", incremental_load, dependencies=["choose_strategy"]),
            Task(
                "finalise",
                finalise,
                dependencies=["full_load", "incremental_load"],
                trigger_rule=rule,
            ),
        ],
    )


r = local_runner.run_dag(
    make_join_dag("all_done"),
    logical_date="2026-01-15",
    variables={**local_runner.DEFAULT_VARIABLES, "full_load_threshold": 100},
)
for task_id, state in r.state.items():
    print(f"{task_id:<20} {state}")
```

`full_load` runs, `incremental_load` is skipped, and `finalise` runs
because `all_done` means "run once all upstream tasks have *finished*,
whatever their outcome". `all_success` would have skipped `finalise`
(skipped is not success), and `none_failed` would also have run it (skip is
not failure) — but `all_done` is the stronger statement, because it also
covers the case where one of the branches *failed*.

```python
# Exercise 3
def make_nested(rule):
    return DAG(
        f"nested_{rule}",
        tasks=[
            Task("read_orders", read_orders, dependencies=[]),
            Task("transform", transform, dependencies=["read_orders"]),
            Task(
                "choose_a",
                choose_strategy,
                dependencies=["transform"],
                branch=True,
            ),
            Task("path_x", full_load, dependencies=["choose_a"]),
            Task("path_y", incremental_load, dependencies=["choose_a"]),
            Task(
                "choose_b",
                choose_strategy_with_override,
                dependencies=["path_x", "path_y"],
                branch=True,
                trigger_rule=rule,
            ),
            Task("final_1", full_load, dependencies=["choose_b"]),
            Task("final_2", incremental_load, dependencies=["choose_b"]),
        ],
    )
```

With `path_x` chosen, `path_y` is skipped. Now `choose_b` depends on both:
- `all_success` — `choose_b` is **skipped**, because `path_y` was skipped.
  Nothing downstream runs.
- `none_failed` — `choose_b` **runs** (a skip is not a failure) and can
  branch to `final_1` / `final_2`.
- `all_done` — `choose_b` **runs**, and additionally would run even if
  `path_x` had failed.

For a nested branch I would use `none_failed`: the semantic you want is
"proceed as long as nothing actually broke", and `all_done` would mask a
genuine failure of `path_x` by letting `choose_b` proceed on a skipped and
failed input.
