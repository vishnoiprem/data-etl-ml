**1.**

```python
@pytest.mark.parametrize("row_count,threshold,expected", [
    (0, 100, False),
    (100, 100, False),
    (101, 100, True),
    (1000, 100, True),
])
def test_should_run_full_load(row_count, threshold, expected):
    assert should_run_full_load(row_count, threshold) is expected
```

The `100 == 100` case must be included because the implementation uses a strict `>`; an off-by-one that changed it to `>=` would flip exactly that case and nowhere else. A table containing only `0` and `1000` would let that bug through.

**2.** Track, for each task, whether it appears in any other task's `upstream_task_ids`. Any task with no downstream is a candidate sink; flag it unless it is in an explicit `sinks` set. A violating DAG has `extract -> transform` with nothing downstream of `transform`.

`upstream_task_ids == set()` is not itself an error: a root task (the first task of a DAG) legitimately has no upstream. Roots are exactly what you want. The rule is about *sinks*, and even sinks are legitimate — a DAG that ends in a terminal task is the normal case — so the rule exists to make the choice explicit rather than to forbid it.

**3.**

```python
def test_etl_load_is_truncate(dagbag):
    dag = dagbag.dags["etl_orders_to_bigquery"]
    load = dag.get_task("load_to_bigquery")
    assert load.configuration["query"]["writeDisposition"] == "WRITE_TRUNCATE"
```

It belongs in the structure layer because `WRITE_TRUNCATE` is a property of the *task's configuration* — it lives in the DAG definition, not in any function under `core/`. The pure-logic layer cannot see it, because the pure-logic layer never touches the DAG. Testing it there would require inventing a fake, and the test would then assert only that the fake behaves as the fake was written — which is why "don't mock the thing you are verifying" is a rule and not a preference.
