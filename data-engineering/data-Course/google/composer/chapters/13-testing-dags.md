# 5.13 — Testing DAGs

> **Section 5 · Engineering Practice · Lecture 5.13 · 7:30**

## 🎯 What you will learn

- The three-layer testing strategy: pure logic, DAG structure, integration
- Unit-testing DAG *structure* — asserting task counts and dependencies without running anything
- `dag.test()` and `dag.run()` in Airflow 2.5+, and what each actually executes
- The `DAG` assertion idiom in `unittest.TestCase`
- Testing with `pytest`, including `dagbag` and `DagBag` import-error checks
- The pure-logic split: why the course's `core/` directory makes 90% of testing trivial
- Integration testing against a dev environment — and what it is actually worth
- What **not** to test, and why testing Airflow itself is a waste of your time
- CI linting of DAG files: catching import errors before Composer does

---

## 🧠 Concept

### The three-layer strategy

Testing an Airflow DAG is not one activity. It is three, and they have very different costs and different failure modes.

```text
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1 — Pure logic                                             │
│   "Is the transformation correct?"                               │
│   Tests: pipeline_logic.py, templating.py                        │
│   Needs: pytest. No Airflow. Runs in < 1 second.                 │
│   Catches: 90% of real bugs.                                     │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2 — DAG structure                                          │
│   "Is the graph wired the way I intended?"                        │
│   Tests: task count, dependencies, operator types, params        │
│   Needs: Airflow installed (or a parser). Runs in ~5 seconds.     │
│   Catches: wiring mistakes, renames, missing tasks.              │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3 — Integration                                             │
│   "Does it work against real GCS / BigQuery / APIs?"             │
│   Tests: a manual DAG in a dev Composer environment              │
│   Needs: a GCP project, credentials, money. Runs in ~minutes.    │
│   Catches: credential problems, IAM gaps, API contract changes.  │
└─────────────────────────────────────────────────────────────────┘
```

**The ratio of effort to value is not close.** Layer 1 catches most bugs for a fraction of the cost. The dominant mistake in Airflow teams is spending their testing budget on Layer 3 and discovering that a `>` should have been a `>=`.

### Layer 1 — pure logic, and why the split matters

The course's premise is that the business rules live in `project/core/pipeline_logic.py` and `project/core/templating.py`, and that **those modules import nothing from Airflow**. Look at the imports:

```python
# project/core/pipeline_logic.py
from __future__ import annotations

import csv
import io
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Iterator, Sequence
```

No `airflow`. The module's own docstring says why:

```text
Business logic that lives inside a DAG file is nearly impossible to
unit-test, because importing a DAG file requires Airflow.
```

That is the whole argument. If your validation rule is inside a `PythonOperator`'s callable, then:
- You cannot test it without installing Airflow (~500 MB of dependencies).
- You cannot test it without a database, because importing a DAG file touches the Airflow metadata DB.
- You cannot test it in a fast CI loop, because the Airflow import dominates the runtime.

If the same rule lives in `core/pipeline_logic.py`:
- `pytest` runs it in milliseconds.
- No Airflow, no database, no credentials.
- The test is a pure function of inputs and outputs.

```bash
python3 -m pytest project/tests/test_pipeline_logic.py -q
```

The course's `project/tests/conftest.py` makes this work by putting `project/core` and `project/dags` on `sys.path`:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COURSE_ROOT = PROJECT_ROOT.parent
CORE_DIR = PROJECT_ROOT / "core"
DAGS_DIR = PROJECT_ROOT / "dags"
SAMPLE_DIR = COURSE_ROOT / "sample_data"

for _path in (str(CORE_DIR), str(DAGS_DIR), str(PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)
```

And it provides a fixture that skips gracefully if the sample data has not been generated:

```python
@pytest.fixture(scope="session")
def orders_csv(sample_dir: Path) -> Path:
    """Return the path to the sample orders CSV."""
    path = sample_dir / "orders.csv"
    if not path.exists():
        pytest.skip(
            "sample data not found. Generate it with:\n"
            "  python resources/sample_data.py --output-dir ./sample_data"
        )
    return path
```

That skip is a design decision worth copying: a missing fixture should *skip*, not *fail*, so that a fresh checkout has a green test suite.

### Layer 2 — testing DAG structure

DAG structure tests assert things about the *graph*, not about behaviour. They are cheap, they run in CI on every commit, and they catch a specific and surprisingly common class of bug: **the wiring is wrong**.

The kinds of thing to assert:

| Assertion | Catches |
|---|---|
| `len(dag.tasks) == 5` | a task was deleted or duplicated during a refactor |
| `dag.task_dict["aggregate"].upstream_task_ids == {"transform_orders"}` | a dependency was changed by accident |
| `isinstance(dag.get_task("load"), BigQueryInsertJobOperator)` | someone swapped the operator for a no-op |
| `dag.get_task("load").retries == 3` | a retry policy was lost in a copy-paste |
| `dag.get_task("x").trigger_rule == "none_failed"` | a join point lost its trigger rule |
| `dag.schedule == "@daily"` | the schedule changed |
| `dag.catchup is False` | catchup was turned on accidentally (this one has caused real incidents) |
| `"{{ ds }}" in dag.get_task("x").bash_command` | a template was hard-coded |
| `set(dag.task_ids) == {...}` | a whole-task-set guard against accidental additions |

The last one is the most valuable and the least used. An exact set comparison catches both deletions and additions.

### The `DAG` assertion in `unittest.TestCase`

Airflow ships a base class for this: `airflow.test_case.DAGTestCase` (older) and, more usefully, the `DAG` assertion available in `unittest.TestCase` via `airflow.models.dag.DAG`'s `assertDag` — but in practice most teams write their own small helper.

The canonical Airflow idiom for structure tests:

```python
import unittest

from airflow.models import DAG
from airflow.operators.bash import BashOperator


class TestETLDAG(unittest.TestCase):
    """Structure tests for the ETL DAG."""

    def test_dag_is_valid(self) -> None:
        """The DAG loads and has the expected shape."""
        with DAG(
            dag_id="test_dag",
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            schedule="@daily",
        ) as dag:
            pass
        self.assertIsNotNone(dag)
```

And a helper that loads a real DAG file:

```python
def load_dag(dag_id: str) -> DAG:
    """Load a DAG by id from the course's dags/ directory.

    Args:
        dag_id: The DAG's identifier.

    Returns:
        The DAG object.

    Raises:
        KeyError: If the DAG is not found.
    """
    from airflow.models import DagBag

    bag = DagBag(dag_folder=DAGS_DIR, include_examples=False)
    if dag_id not in bag.dags:
        raise KeyError(f"{dag_id} not found. Import errors: {bag.import_errors}")
    return bag.dags[dag_id]
```

**The `DAG` assertion that catches the most:** `bag.import_errors`. A DAG that fails to import does not appear in `bag.dags` — it appears in `bag.import_errors`. If your test only checks that a DAG *exists*, an import error means "DAG not found", which is a confusing failure. Checking `bag.import_errors` first gives you the real traceback.

### `dag.test()` and `dag.run()` (Airflow 2.5+)

Airflow 2.5 added two methods that run a DAG's tasks **in the local process**, without a scheduler, without a worker, and (in `dag.test()`'s case) without a metadata database.

**`dag.test()`** — runs the DAG's tasks locally, in dependency order, executing the real callables.

```python
from airflow.models.dagbag import DagBag
from airflow.utils import timezone

dagbag = DagBag(dag_folder="project/dags", include_examples=False)
dag = dagbag.get_dag("etl_orders_to_bigquery")

dag.test(execution_date=timezone.datetime(2026, 1, 15))
```

Characteristics:
- Runs tasks in **dependency order**, in the current process.
- Executes the **real** callables — including `BigQueryInsertJobOperator`, which will try to talk to BigQuery.
- Returns a `DagRun` whose `get_task_instance` states you can assert on.
- `execution_date` is the logical date to run for; it is deprecated in favour of `logical_date` in newer versions, but `execution_date` is the name in 2.5–2.9.

**`dag.run()`** — runs a DAG for a set of logical dates, also locally.

```python
dag.run(start_date=timezone.datetime(2026, 1, 1), end_date=timezone.datetime(2026, 1, 3))
```

`dag.run()` is essentially `dag.test()` over a date range, and it exists so you can run a backfill locally.

**What they are good for:**
- Verifying a DAG's *control flow* — branch decisions, trigger rules, skip propagation.
- Testing a DAG whose tasks are all pure or mocked.
- Getting a fast feedback loop while developing.

**What they are NOT good for:**

> **`dag.test()` executes the real operators.** A `BigQueryInsertJobOperator` in a `dag.test()` call will attempt a real BigQuery load.

This is the single most common surprise. `dag.test()` is not a mock — it is a local executor. If your DAG talks to GCP, `dag.test()` either talks to GCP (and needs credentials) or fails with an auth error.

The mitigation is to **override the operator's callable** before running:

```python
dag.test(
    execution_date=timezone.datetime(2026, 1, 15),
    session=mock_session,
)
```

...or, more commonly, to test the DAG's *logic* through a `PythonOperator` that calls a pure function, and test the operator wiring separately. Which is exactly the course's design.

### Testing with `pytest`

pytest works well with Airflow; the only friction is that DAG files are not importable as normal modules (they are parsed, and their top-level code runs).

**Pattern 1 — `DagBag`, once per session.**

```python
# project/tests/test_dag_structure.py
"""Structure tests for the course's DAGs."""
from __future__ import annotations

from pathlib import Path

import pytest

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"


@pytest.fixture(scope="session")
def dagbag():
    """Return a DagBag containing the course's DAGs.

    Returns:
        The DagBag.
    """
    from airflow.models import DagBag

    return DagBag(dag_folder=str(DAGS_DIR), include_examples=False)
```

**Pattern 2 — `pytest.mark.parametrize` over the DAGs.**

```python
@pytest.mark.parametrize(
    "dag_id",
    ["hello_world", "templating_and_variables", "etl_orders_to_bigquery", "branching_and_xcom"],
)
def test_dag_imports_cleanly(dagbag, dag_id: str) -> None:
    """Every course DAG imports without an error."""
    assert dag_id in dagbag.dags, (
        f"{dag_id} failed to import: {dagbag.import_errors.get(dag_id)}"
    )


def test_no_import_errors(dagbag) -> None:
    """No DAG file raises on import."""
    assert dagbag.import_errors == {}, f"Import errors: {dagbag.import_errors}"
```

**Pattern 3 — parameterise over the `default_args`.**

```python
@pytest.mark.parametrize("dag_id", [...])
def test_default_args(dagbag, dag_id: str) -> None:
    """Every DAG sets the same reliability defaults."""
    dag = dagbag.dags[dag_id]
    assert dag.default_args["owner"] == "data-platform"
    assert dag.default_args["retries"] >= 1
    assert dag.catchup is False
```

### The pure-logic split, applied

This is the most important idea in the chapter, so let us make it concrete with the course's own code.

**The rule:** every *decision* lives in `core/` and is tested there. Every *mechanism* (the Airflow operator, the dependency edge) lives in the DAG file and is tested structurally.

| Decision | Mechanism |
|---|---|
| Is this row valid? (`classify_row`) | `PythonOperator` calling it |
| Should we full-load? (`should_run_full_load`) | `BranchOperator` calling it |
| Which partition? (`partition_for_date`) | The template `{{ ds_nodash }}` |
| What is the data window? (`logical_date_window`) | The template `{{ data_interval_start }}` |
| What is the row's identity? (`dedup_key`) | The load job's `MERGE` key |
| How many rows? (`transform_orders` returns counts) | The row-count assertion task |

Look at `should_run_full_load` — its docstring literally names the reason it is pure:

```python
def should_run_full_load(row_count: int, threshold: int) -> bool:
    """Decide whether a run should take the full-load path or the incremental path.

    This is the decision a :class:`~airflow.operators.branch.BranchOperator`
    makes in the branching DAG. Keeping it pure means the branch condition
    can be unit-tested against every threshold boundary, which is exactly
    where branch bugs live: off-by-one on ``>`` versus ``>=``.
    """
    return row_count > threshold
```

And the local runner uses it exactly as the DAG does:

```python
def _branch_on_volume(run: DagRun, context: dict[str, Any]) -> list[str]:
    """Choose between the full-load and incremental paths."""
    from pipeline_logic import should_run_full_load

    stats = run.pull("transform_orders") or {}
    accepted = int(stats.get("accepted_count", 0))
    threshold = int(context["__variables__"].get("full_load_threshold", 1000000))
    chosen = "full_load" if should_run_full_load(accepted, threshold) else "incremental_load"
    log.info("      rows=%d threshold=%d -> %s", accepted, threshold, chosen)
    return [chosen]
```

One function, used by the DAG, the local runner, and the unit tests. **One definition of the rule.**

### Integration testing against a dev environment

Layer 3 is the "does it work for real" layer. It is worth doing, and it is worth doing *once per pipeline shape*, not once per DAG.

**The shape of an integration test in Airflow:**

1. A **separate environment** — a dev Composer environment, a dev project, a dev bucket. Never production.
2. A **dedicated test DAG** that exercises the same operators against dev resources, with a small dataset.
3. **Assertions inside the DAG** — the test DAG checks the output and fails if it is wrong.

```python
# project/dags/08_integration_check.py
"""
08_integration_check.py — an integration test, run manually.

This DAG touches real (dev) GCS and BigQuery resources. It is scheduled
to `None` so it only runs when triggered by a human or by CI.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 0,
}


def assert_orders_landed(**context) -> None:
    """Fail the run if the expected rows are not in the table.

    Args:
        context: The Airflow task context.

    Raises:
        AssertionError: If the row count does not match.
    """
    from google.cloud import bigquery

    client = bigquery.Client()
    project = context["var"].get("gcp_project_id", "YOUR_PROJECT_ID")
    dataset = context["var"].get("bq_dataset", "analytics")
    table = context["var"].get("bq_table", "orders_enriched")
    partition = context["ds_nodash"]

    query = (
        f"SELECT COUNT(*) FROM `{project}.{dataset}.{table}` "
        f"WHERE DATE(_PARTITIONTIME) = DATE('{context['ds']}')"
    )
    actual = int(list(client.query(query).result())[0][0])
    expected = int(context["params"].get("expected_rows", 0))

    log.info("expected=%d actual=%d", expected, actual)
    assert actual == expected, (
        f"integration check failed for partition {partition}: "
        f"expected {expected} rows, found {actual}"
    )


with DAG(
    dag_id="integration_check",
    description="Manual integration test against dev GCP resources.",
    schedule=None,               # manual trigger only
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    default_args=DEFAULT_ARGS,
    params={"expected_rows": 0},
    tags=["test", "integration"],
) as dag:
    check = PythonOperator(
        task_id="assert_orders_landed",
        python_callable=assert_orders_landed,
    )

    smoke = BigQueryExecuteQueryOperator(
        task_id="smoke_query",
        sql="SELECT 1 AS ok",
        location="US",
    )

    check >> smoke
```

**What integration testing is genuinely for:**

| Problem | Caught by integration? |
|---|---|
| The service account lacks `bigquery.jobs.create` | yes |
| The GCS bucket name is wrong in the Variables | yes |
| The BigQuery dataset does not exist | yes |
| The API's schema changed | yes |
| The IAM binding expired | yes |
| The business rule is wrong | **no — that is Layer 1** |
| The dependency is wrong | **no — that is Layer 2** |

That last pair is why integration tests are a poor substitute for the other two layers. They are slow, they cost money, they are flaky, and they only catch a narrow class of problems.

### What NOT to test

This section matters as much as the others, because wasted test effort is worse than no test effort.

**Do not test Airflow itself.** Do not write a test that asserts `PythonOperator` sets `task_id` correctly. Do not test that `>>` creates a dependency — Airflow's own test suite does that, far better than you can.

**Do not test the framework's retry behaviour.** "The task retries three times" is a configuration fact, not a logic fact. Assert `task.retries == 3` if you care; do not build a test that fails a task and watches it retry.

**Do not test template rendering with hard-coded strings.** `assert render_template("gs://b/{{ ds }}/f.csv", ctx) == "gs://b/2026-01-15/f.csv"` is brittle — it breaks when you change the template's shape. Assert the *properties* you care about: that the date appears, that the bucket variable was substituted, that an undefined variable raises.

**Do not test that a task "succeeds".** Assert the *output*. A task that succeeds and writes nothing is a failed pipeline.

**Do not test the DAG's business logic.** This is the most common mistake, and it is why the course splits `core/` out. If you find yourself needing a metadata database to test a validation rule, the rule is in the wrong place.

**Do not test private implementation details.** Assert on the public behaviour of `transform_orders` — the accepted/rejected split — not on how it parses CSV.

### CI linting of DAG files

The cheapest, highest-value check in the whole chapter: **does every DAG file import cleanly?**

A DAG that fails to import is invisible in Composer. It is not in the DAG list, and the failure surfaces only in the environment's DAG import-error log, where nobody looks.

```bash
# The CI gate — run this on every commit.
python3 - <<'PY'
import sys
from pathlib import Path

DAGS_DIR = Path("project/dags")
sys.path.insert(0, str(DAGS_DIR))

from airflow.models import DagBag

bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)

print(f"dags parsed : {len(bag.dags)}")
print(f"import errors: {len(bag.import_errors)}")

if bag.import_errors:
    for path, error in bag.import_errors.items():
        print(f"\n--- {path} ---")
        print(error)
    raise SystemExit(1)

print("OK")
PY
```

Expected output on a healthy tree:

```text
dags parsed : 4
import errors: 0
OK
```

**What else to lint.** Beyond import errors, the checks worth having in CI:

| Check | Catches |
|---|---|
| Every DAG has a `dag_id` matching its filename | A rename that breaks references |
| Every DAG has `owner` in `default_args` | An unowned DAG |
| `catchup` is explicitly set | An accidental catchup |
| `max_active_runs` is explicitly set | A thundering herd |
| No hard-coded bucket/project names | A dev environment pointing at prod |
| Every task has a `retries` value | A non-idempotent task retrying by accident |
| Task IDs are unique and snake_case | Typos in dependency edges |
| No `print()` calls | Log noise; use `logging` |

A DAG file that does not import is the failure mode that costs the most, because it is silent.

---

## 🛠️ Hands-On

### Step 1 — run the existing test suite

The course already has a test suite that requires no Airflow:

```bash
cd data-engineering/data-Course/google/composer
python3 -m pytest project/tests/ -q
```

Expected output:

```text
.......ssssssssss....................................................... [ 51%]
....................................................................     [100%]
130 passed, 10 skipped in 0.37s
```

The `s` characters are the Layer 2 structure tests skipping because Airflow is not installed — a skip, not a failure. The exact counts may vary; what matters is that it runs in **well under a second** and that **no Airflow is required**.

Verify that claim directly:

```bash
python3 -c "import airflow" 2>&1 | tail -1
```

Expected:

```text
ModuleNotFoundError: No module named 'airflow'
```

Airflow is not installed, and the test suite is green. That is the entire payoff of the pure-logic split.

### Step 2 — write a Layer 1 test for the branching threshold

The off-by-one boundary that `should_run_full_load`'s docstring warns about. This is the kind of test that is impossible to write if the rule lives in a DAG file.

```python
# project/tests/test_branch_threshold.py
"""Tests for the branch threshold decision.

This file imports nothing from Airflow. It runs in milliseconds.
"""
from __future__ import annotations

import pytest

from pipeline_logic import should_run_full_load


@pytest.mark.parametrize(
    "row_count,threshold,expected",
    [
        (0, 100, False),
        (99, 100, False),
        (100, 100, False),        # `>` not `>=` — the boundary
        (101, 100, True),
        (1_245, 100, True),
        (1_245, 1_000_000, False),
    ],
)
def test_should_run_full_load(row_count: int, threshold: int, expected: bool) -> None:
    """The full-load path is taken strictly above the threshold."""
    assert should_run_full_load(row_count, threshold) is expected


def test_threshold_boundary_is_strict():
    """Exactly at the threshold, the incremental path is taken."""
    assert should_run_full_load(1000, 1000) is False
    assert should_run_full_load(1001, 1000) is True
```

Run it:

```bash
python3 -m pytest project/tests/test_branch_threshold.py -q
```

Expected output:

```text
.......                                                                  [100%]
7 passed in 0.01s
```

### Step 3 — verify the decision matches what the local runner does

A test that only checks the function does not prove the DAG uses it. The local runner is the bridge, and the course's `branching_load` DAG lets us prove the two agree.

```bash
python3 project/local_runner.py --dag branching_load --date 2026-01-15 --vars "{\"full_load_threshold\": 100}"
```

Expected output (excerpt):

```text
INFO       rows=1245 threshold=100 -> full_load
INFO   ✓ choose_strategy          success
INFO   ✓ full_load                success
INFO   ○ incremental_load         skipped
INFO   ✓ finalise                 success
```

Now with a threshold above the row count:

```bash
python3 project/local_runner.py --dag branching_load --date 2026-01-15 --vars "{\"full_load_threshold\": 1000000}"
```

Expected output (excerpt):

```text
INFO       rows=1245 threshold=1000000 -> incremental_load
INFO   ✓ choose_strategy          success
INFO   ○ full_load                skipped
INFO   ✓ incremental_load         success
INFO   ✓ finalise                 success
```

Note `finalise` succeeds in **both** cases. That is `trigger_rule="none_failed"` doing its job — one of the two branches is skipped, and the join point still runs. A structure test should assert exactly this.

### Step 4 — write the Layer 2 structure tests

These need Airflow. When it is not installed, they should **skip**, not fail — that keeps the "no Airflow" promise intact.

```python
# project/tests/test_dag_structure.py
"""Structure tests for the course's DAGs.

These require Airflow. When Airflow is absent, the whole module skips
and the fast pure-logic suite still runs green.
"""
from __future__ import annotations

from pathlib import Path

import pytest

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"

EXPECTED_DAG_IDS = {
    "hello_world",
    "templating_and_variables",
    "etl_orders_to_bigquery",
    "branching_and_xcom",
}


def _require_airflow() -> None:
    """Skip the test if Airflow is not installed.

    Raises:
        pytest.skip: Always.
    """
    try:
        import airflow  # noqa: F401
    except ImportError:
        pytest.skip("Airflow is not installed — skipping structure tests")


@pytest.fixture(scope="session")
def dagbag():
    """Return a DagBag with the course's DAGs.

    Returns:
        The DagBag.
    """
    _require_airflow()
    from airflow.models import DagBag

    return DagBag(dag_folder=str(DAGS_DIR), include_examples=False)


def test_no_import_errors(dagbag) -> None:
    """No DAG file raises on import."""
    assert dagbag.import_errors == {}, (
        f"Import errors:\n{dagbag.import_errors}"
    )


@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAG_IDS))
def test_expected_dag_exists(dagbag, dag_id: str) -> None:
    """Every expected DAG is present."""
    assert dag_id in dagbag.dags


def test_etl_dag_shape(dagbag) -> None:
    """The ETL DAG has the tasks and dependencies we expect."""
    dag = dagbag.dags["etl_orders_to_bigquery"]

    assert len(dag.tasks) == 5
    assert dag.get_task("check_source_exists").upstream_task_ids == set()
    assert dag.get_task("validate_and_stage").upstream_task_ids == {
        "check_source_exists"
    }
    assert dag.get_task("load_to_bigquery").upstream_task_ids == {
        "validate_and_stage"
    }
    assert dag.get_task("export_to_gcs").upstream_task_ids == {
        "aggregate_by_region"
    }


def test_etl_dag_reliability_defaults(dagbag) -> None:
    """The ETL DAG sets the reliability defaults we depend on."""
    dag = dagbag.dags["etl_orders_to_bigquery"]

    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert dag.default_args["owner"] == "data-platform"
    assert dag.default_args["retries"] >= 1


def test_etl_load_is_truncate(dagbag) -> None:
    """The BigQuery load uses WRITE_TRUNCATE, not WRITE_APPEND."""
    from airflow.providers.google.cloud.operators.bigquery import (
        BigQueryInsertJobOperator,
    )

    dag = dagbag.dags["etl_orders_to_bigquery"]
    load = dag.get_task("load_to_bigquery")

    assert isinstance(load, BigQueryInsertJobOperator)
    disposition = load.configuration["query"]["writeDisposition"]
    assert disposition == "WRITE_TRUNCATE"


def test_branching_join_uses_none_failed(dagbag) -> None:
    """The join point uses the trigger rule that survives a skipped branch."""
    dag = dagbag.dags["branching_and_xcom"]
    join = dag.get_task("load_complete")

    assert join.trigger_rule in ("none_failed", "none_failed_min_one_success", "all_done")


def test_sensor_uses_reschedule(dagbag) -> None:
    """The long sensor releases its worker slot between checks."""
    dag = dagbag.dags["branching_and_xcom"]
    sensor = dag.get_task("wait_for_upstream_data")

    assert sensor.mode == "reschedule"
    assert sensor.soft_fail is True
```

Run them:

```bash
python3 -m pytest project/tests/test_dag_structure.py -q
```

Without Airflow:

```text
ssssssssss                                                               [100%]
10 skipped in 0.01s
```

With Airflow installed, they run and assert real structure.

### Step 5 — exercise the branch decision through the local runner, as a test

The local runner is a mini Airflow, and it is perfect for testing orchestration *behaviour* without Airflow. Let us turn the branching DAG's behaviour into a test.

```python
# project/tests/test_local_runner_behaviour.py
"""Behavioural tests of the orchestration, using the local runner.

The local runner models dependencies, trigger rules, branches, skips,
and upstream-failure propagation. That is enough to test the
*orchestration* of the course's DAGs without Airflow installed.
"""
from __future__ import annotations

import pytest

from local_runner import DAGS, run_dag


def test_etl_dag_succeeds_and_produces_the_expected_summary() -> None:
    """The ETL DAG runs end to end and produces the expected numbers."""
    run = run_dag(DAGS["etl_to_gcs"](), "2026-01-15")

    assert all(state == "success" for state in run.state.values())
    assert run.pull("transform_orders")["accepted_count"] == 1245
    assert run.pull("transform_orders")["rejected_count"] == 0

    summary = run.pull("aggregate", "summary")
    assert summary["AMER"] == {"order_count": 318, "revenue_eur": 113592.19}
    assert summary["EMEA"] == {"order_count": 322, "revenue_eur": 118423.22}


def test_branch_takes_full_load_above_threshold() -> None:
    """Above the threshold, the full-load branch runs and the other is skipped."""
    run = run_dag(
        DAGS["branching_load"](),
        "2026-01-15",
        variables={"full_load_threshold": 100},
    )

    assert run.state["full_load"] == "success"
    assert run.state["incremental_load"] == "skipped"
    assert run.state["finalise"] == "success"


def test_branch_takes_incremental_below_threshold() -> None:
    """Below the threshold, the incremental branch runs and the other is skipped."""
    run = run_dag(
        DAGS["branching_load"](),
        "2026-01-15",
        variables={"full_load_threshold": 1_000_000},
    )

    assert run.state["incremental_load"] == "success"
    assert run.state["full_load"] == "skipped"
    assert run.state["finalise"] == "success"


def test_join_point_runs_even_when_a_branch_is_skipped() -> None:
    """`none_failed` lets the join run despite a skipped dependency."""
    run = run_dag(
        DAGS["branching_load"](),
        "2026-01-15",
        variables={"full_load_threshold": 100},
    )

    # The join depends on BOTH branches; one was skipped.
    assert run.state["incremental_load"] == "skipped"
    assert run.state["finalise"] == "success"
```

Run them:

```bash
python3 -m pytest project/tests/test_local_runner_behaviour.py -q
```

Expected output:

```text
....                                                                     [100%]
4 passed in 0.08s
```

**This is the highest-value test file in the course.** It asserts the numbers the pipeline produces, the branch decision at both thresholds, and the trigger-rule behaviour that is the most common branching bug — all without Airflow and in a fifth of a second.

### Step 6 — write the CI lint gate

```bash
# scripts/lint_dags.py
"""Fail the build if any DAG file cannot be imported."""
from __future__ import annotations

import sys
from pathlib import Path

DAGS_DIR = Path(__file__).resolve().parent.parent / "project" / "dags"


def main() -> int:
    """Parse every DAG file and report import errors.

    Returns:
        0 when every DAG imports cleanly, 1 otherwise.
    """
    try:
        from airflow.models import DagBag
    except ImportError:
        print("Airflow is not installed — skipping the DAG lint.")
        return 0

    bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)

    print(f"dags parsed   : {len(bag.dags)}")
    print(f"import errors : {len(bag.import_errors)}")

    if bag.import_errors:
        for path, error in bag.import_errors.items():
            print(f"\n--- {path} ---")
            print(error)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:

```bash
python3 scripts/lint_dags.py
```

Without Airflow:

```text
Airflow is not installed — skipping the DAG lint.
```

### Step 7 — the CI pipeline

```yaml
# .github/workflows/dags.yml
name: dags

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest jinja2
          pip install "apache-airflow==2.9.3" \
            --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"

      - name: Generate sample data
        run: python resources/sample_data.py --output-dir ./sample_data

      - name: Run the fast test suite
        run: python -m pytest project/tests/ -q

      - name: Lint the DAG files
        run: python scripts/lint_dags.py
```

Two notes on the CI design:

1. **Pin Airflow with a constraints file.** The Airflow install is a notorious dependency-resolution problem; the constraint file makes it deterministic.
2. **The fast suite runs first.** If the pure logic is broken, you find out in seconds, not after a three-minute Airflow install.

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'airflow'` when running the tests

**Cause:** the tests import Airflow. The course's design keeps Airflow out of the fast suite, but a structure test needs it.

**Fix:** either install Airflow (with constraints), or make the structure tests skip cleanly. The `pytest.skip` in `_require_airflow()` is the pattern.

### `KeyError: 'etl_orders_to_bigquery' not found. Import errors: {...}`

**Cause:** the DAG file failed to import, so it is not in `bag.dags`. It is in `bag.import_errors`.

**Fix:** read the import error. Common causes:
- A missing provider package (`apache-airflow-providers-google`).
- A syntax error.
- A missing Variable or Connection at parse time (Airflow evaluates some Jinja at parse time).

```bash
python3 -c "
from airflow.models import DagBag
bag = DagBag(dag_folder='project/dags', include_examples=False)
for path, err in bag.import_errors.items():
    print(path); print(err)
"
```

### `dag.test()` tried to call BigQuery and failed with an auth error

**Cause:** `dag.test()` executes the **real** operators. It is a local executor, not a mock.

**Fix:** test the *decision* logic in `core/` (Layer 1) and the *wiring* structurally (Layer 2). If you must run the DAG locally, point it at a dev project with dev credentials, or override the operator before running.

### `dag.test()` raised `KeyError: 'tzinfo'`

**Cause:** passing a naive datetime.

**Fix:** use a timezone-aware datetime:
```python
from airflow.utils import timezone
dag.test(execution_date=timezone.datetime(2026, 1, 15))
```

### `dag.test()` did nothing because the DAG's `schedule` had not reached the date

**Cause:** `dag.test()` runs the tasks for the logical date you give it, but some behaviour (like catchup) can affect what is scheduled.

**Fix:** pass the logical date explicitly, and assert on the returned `DagRun`'s task instance states rather than assuming the run happened:

```python
run = dag.test(execution_date=timezone.datetime(2026, 1, 15))
ti = run.get_task_instance("load_to_bigquery")
assert ti.state == "success"
```

### `AssertionError: 1245 != 0` in a row-count test

**Cause:** the sample data has not been generated, or the test's expected value does not match the data.

**Fix:** the course's `orders_csv` fixture skips when the data is missing. For a hand-written test, generate the data first:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

Then confirm the accepted count:

```bash
python3 -c "
import sys; sys.path.insert(0, 'project/core')
from pipeline_logic import transform_orders
lines = open('sample_data/orders.csv').read().splitlines()
a, r = transform_orders(lines)
print(f'accepted={len(a)} rejected={len(r)}')
"
```

Expected:

```text
accepted=1245 rejected=0
```

### `Task is in the 'upstream_failed' state` in a `dag.test()` run

**Cause:** an upstream task failed, so downstream tasks were not run. The `upstream_failed` state is the *symptom*.

**Fix:** find the actual failure. In `dag.test()`, the failing task's state is `failed`; get its exception from the task instance:

```python
run = dag.test(execution_date=timezone.datetime(2026, 1, 15))
ti = run.get_task_instance("load_to_bigquery")
if ti.state == "failed":
    print(ti.state)
```

### The structure test passed but the pipeline is wrong

**Cause:** structure tests assert the graph, not the data. A DAG can be wired perfectly and still compute the wrong number.

**Fix:** add a Layer 1 test for the computation. The course's `test_local_runner_behaviour.py` does this — it asserts the actual summary values, which is the combination of "wired right" and "computed right".

### The tests are slow

**Cause:** Airflow is installed in the same environment, so every test session pays the Airflow import cost, and `DagBag` parsing is slow.

**Fix:** split the test suite into two commands — the fast pure-logic suite (no Airflow) and the structure suite (with Airflow). Run the fast one on every commit and the structure one on a schedule or before release.

### `dag.run()` did not create any runs

**Cause:** `dag.run()` needs a date range and a configured Airflow environment; in a bare environment it silently does nothing useful.

**Fix:** prefer `dag.test()` for a single logical date. If you need a range, drive it from the local runner, which implements a date-driven loop with no Airflow dependency:

```bash
for d in 2026-01-13 2026-01-14 2026-01-15; do
  python3 project/local_runner.py --dag etl_to_gcs --date "$d" --describe
done
```

---

## 💡 Production Notes

- **Test the logic, not the framework.** The moment you need a metadata database to test a business rule, the rule is in the wrong place.
- **The `core/` split is the single highest-leverage decision in an Airflow codebase.** It turns a 5-minute, 500 MB test suite into a 0.4-second, zero-dependency one.
- **Put the numbers in the tests.** `assert summary["AMER"] == {"order_count": 318, "revenue_eur": 113592.19}` catches far more than `assert len(dag.tasks) == 5`.
- **Test boundary values, not just the happy path.** `row_count == threshold` is where branch bugs live. The `should_run_full_load` docstring says so explicitly.
- **Use exact task-set assertions.** `set(dag.task_ids) == {...}` catches accidental deletions *and* additions, and it fails with a readable diff.
- **Assert on `bag.import_errors` first.** "DAG not found" is a misleading error; the real one is in the import errors.
- **A DAG that fails to import is silent in Composer.** Make "no import errors" a CI gate. It is the cheapest check in the whole pipeline.
- **`dag.test()` runs real operators.** Treat it as a local run, not a mock.
- **Integration-test once per pipeline *shape*, not once per DAG.** Every DAG that uses "GCS → validate → BigQuery" needs one integration check, not forty.
- **Do not test Airflow.** You are testing your orchestration, not the framework's.
- **Assert on outputs, not task states.** "The task succeeded" is a fact about the framework; "1,245 rows landed in partition 20260115" is a fact about your pipeline.
- **Pin Airflow in CI with a constraints file**, and run the fast suite before the Airflow install so failures surface in seconds.

---

## 🔑 Key Takeaways

- **Three layers:** pure logic (fast, catches most bugs), DAG structure (catches wiring mistakes), integration (catches environment problems). Budget your effort in that order.
- **The pure-logic split is the leverage.** Business rules in `core/` are testable in milliseconds with no Airflow; the same rules in a DAG file are effectively untestable.
- **Structure tests** assert task counts, dependencies, operator types, trigger rules, retry policies, and `catchup` — the wiring facts that silently break.
- **`DagBag.import_errors` is where the truth is.** A DAG that fails to import is absent from `bag.dags` and present in `bag.import_errors`.
- **`dag.test()` / `dag.run()` (Airflow 2.5+) run the real operators locally.** They are local executors, not mocks — they will call BigQuery.
- **pytest + `DagBag` + `parametrize`** is the ergonomic combination; `unittest.TestCase` also works, and Airflow's own `DAG` assertion is available.
- **Assert on the data, not the task state.** `success` is a framework fact; `1,245 rows with AMER revenue 113,592.19` is a pipeline fact.
- **Do not test Airflow, the retry mechanism, or private implementation details.**
- **CI must lint DAG imports.** It is the cheapest check and catches the silent failure.
- **Make Airflow-dependent tests skip, not fail,** when it is absent — that keeps the "no local Airflow" promise intact.

---

## 📚 Practice Exercises

1. **Write the full structure test suite for the ETL DAG.** Using `project/dags/03_etl_bigquery.py`, write tests that assert: the exact task set; every dependency edge; that `load_to_bigquery` is a `BigQueryInsertJobOperator`; that its `writeDisposition` is `WRITE_TRUNCATE`; that `aggregate_by_region`'s SQL uses `{{ data_interval_start }}` and `{{ data_interval_end }}` (and does **not** use `BETWEEN`); that the DAG has `sla` set; and that `sla_miss_callback` is not `None`. Then deliberately break one thing — change `WRITE_TRUNCATE` to `WRITE_APPEND` — and confirm the test fails with a readable message. *Expected answer:* the `BETWEEN` check is the interesting one: assert `"BETWEEN" not in sql` and `"<=" not in sql`, because a `BETWEEN` filter loads the boundary row into two days — an off-by-one that is invisible until the monthly totals are wrong.

2. **Prove the local runner is a sufficient test harness for the orchestration.** Write tests that assert the *entire* task-state map for the `branching_load` DAG under three variable configurations (threshold above, below, and equal to the row count). Then identify one Airflow behaviour the local runner does *not* model and explain why that is acceptable for the course. *Expected answer:* the expected maps are — above threshold: `read_orders` success, `transform_orders` success, `choose_strategy` success, `full_load` success, `incremental_load` skipped, `finalise` success; below threshold: the same with the two branches swapped. At exactly 1,245 the incremental path is taken because `should_run_full_load` uses strict `>`. The local runner does not model sensors, deferral, XCom backends, pools, priority weighting, or SLA callbacks — acceptable because those are Airflow behaviours, and the course's *logic* does not depend on them.

3. **Write a test that fails when the pipeline is wrong.** Deliberately change `should_run_full_load` to use `>=` instead of `>` and run the test suite. Then write the test that would catch the same class of bug in `classify_row` — specifically, that a row with a missing `order_id` is rejected with the reason code `missing_order_id` and not some other code. *Expected answer:* the `should_run_full_load` boundary test fails at `(100, 100, False)` and at `test_threshold_boundary_is_strict`. The `classify_row` test would be `assert classify_row({"order_id": "", "customer_id": "c1", ...}) == REJECT_MISSING_ORDER_ID`, and the value of asserting against the **named constant** rather than the string literal is that renaming the constant breaks the test loudly rather than silently.

4. **Design an integration test for the course's ETL pipeline.** Write the `integration_check` DAG from this chapter, plus a shell script that triggers it against a dev Composer environment and asserts the outcome. Explain what it would catch that the Layer 1 and Layer 2 tests cannot. *Expected answer:* the script uses `gcloud composer environments run` (or `curl` against the Airflow REST API) to trigger the DAG, polls the DAG run's state, and then runs a BigQuery query to assert the partition's row count. It catches: a missing IAM role on the service account (`bigquery.jobs.create`), a wrong bucket name in the Variables, a missing dataset, an expired credential, and an API contract change. It does not catch a wrong business rule or a wrong dependency — those are Layers 1 and 2.

5. **Write the CI lint checks as a table-driven test.** Implement `test_lint_dag_files.py` with one test per rule: every DAG has an explicit `catchup`; every DAG has an `owner` in `default_args`; every DAG has an explicit `max_active_runs`; no task has `retries > 0` without an idempotent write disposition; task IDs are unique and snake_case. Then decide which of these should be **errors** and which should be **warnings**, and justify each. *Expected answer:* missing `owner` should be an error (an unowned DAG is an operational risk); missing `catchup` should be an error (the default changed between Airflow versions and an accidental `True` causes a backfill storm); missing `max_active_runs` should be a warning (the default of 16 is often fine); `retries > 0` on a task with `WRITE_APPEND` should be an error (it is the exact double-count bug from chapter 12); snake_case task IDs should be a warning (style, not correctness).

6. **Write the "what NOT to test" list for your own DAG, with justifications.** Take a real DAG and list five things a naive test suite would test, then explain for each why it is a waste of effort. Then write down the three tests you would keep. *Expected answer:* typical wastes include "the operator sets `task_id`" (framework), "the task retries" (framework + slow), "the template renders to a specific string" (brittle), "the task succeeds" (assert nothing about the data), "the DAG has no cycles" (Airflow's parser already rejects cycles — and `DagBag` import errors cover it). The three to keep: a pure-logic unit test of the computation, a structure test of the critical dependency edges, and one end-to-end assertion on the output values.

---

## 📖 Further Reading

- Airflow's own testing documentation — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- Airflow: `dag.test()` and `dag.run()` (2.5+) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/debugging.html
- Airflow `DagBag` API — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/dagbag/index.html
- Airflow `DAG` API — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/dag/index.html
- Airflow `airflow.test_case` module — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/test_case/index.html
- pytest documentation — https://docs.pytest.org/en/stable/
- Airflow best practices: testing DAGs — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#test-dags
- Google Cloud Composer: environment configuration and DAG import errors — https://cloud.google.com/composer/docs/how-to/managing/creating
