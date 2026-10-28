# 1.8 — Branching and Dynamic Tasks

> **Section 1 · Composer Fundamentals & Model · Lecture 1.8 · 10:00**

## 🎯 What you will learn

- `BranchOperator`: how it works, and the rule that trips everyone up — **branching is about downstream skip, not skipping yourself**
- `trigger_rule`: all six values, what each means, and how they interact with `skipped` and `failed`
- The skip semantics: how a skipped dependency propagates
- `ShortCircuitOperator` — skipping a whole subtree in one step
- The **join point pattern** — the correct way to converge after a branch
- The classic branch bug: a DAG that looks correct and quietly does nothing
- `task.skip()` — skipping a task from your own Python code
- Dynamic task mapping (Airflow 2.3+) — fanning out over a runtime-sized list

---

## 🧠 Concept

### The problem branches solve

Sometimes the right thing to do depends on data that is only known at
run time. Today's order count might be small enough for an incremental
partition load, or large enough to need a full reload. Yesterday's
error rate might be zero or catastrophic.

You cannot decide this at DAG-parse time. You can only decide it at run
time, and then the DAG has to **choose a path**.

Airflow gives you two tools for this:

| Tool | Effect |
|---|---|
| `BranchOperator` | runs *one* of several downstream paths, skips the rest |
| `ShortCircuitOperator` | skips *everything* downstream, or nothing |

### How `BranchOperator` works

```python
from airflow.operators.python import BranchOperator

def choose_strategy(**context) -> list[str]:
    ti = context["ti"]
    row_count = int(ti.xcom_pull(task_ids="count_rows") or 0)
    threshold = int(ti.xcom_pull(task_ids="count_rows", key="threshold") or FULL_LOAD_THRESHOLD)

    force = bool(context["params"].get("force_full_load", False))
    chosen = "full_load" if (row_count > threshold or force) else "incremental_load"

    log.info("row_count=%d threshold=%d force=%s -> %s", row_count, threshold, force, chosen)
    return [chosen]


branch = BranchOperator(
    task_id="choose_strategy",
    python_callable=choose_strategy,
)
```

The callable returns a **list of task ids**. Those tasks run. Everything
else downstream of the branch is marked `skipped`.

Here is the critical mental model:

```text
                    ┌──────────────┐
                    │ count_rows   │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │ choose_strategy│  ← returns ["incremental_load"]
                    └──────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐       ┌────────▼────────┐
     │   full_load     │       │ incremental_load│
     │   → SKIPPED     │       │   → RUNS        │
     └────────┬────────┘       └────────┬────────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────▼────────┐
                    │ load_complete │  ← needs trigger_rule!
                    └───────────────┘
```

**The branch task itself succeeds.** It does not skip itself. It runs,
decides, and *its downstream tasks* are the ones that get skipped.

This is the detail that causes the classic bug, and the chapter comes
back to it below.

### `ShortCircuitOperator`

```python
from airflow.operators.python import ShortCircuitOperator

def check(**context) -> bool:
    return context["params"].get("enabled", True)


short = ShortCircuitOperator(
    task_id="check_enabled",
    python_callable=check,
    ignore_downstream_trigger_rules=True,
)
```

`ShortCircuitOperator` returns a boolean:

- `True` → the task succeeds and **everything downstream runs normally**.
- `False` → the task is marked `skipped` and **all downstream tasks are
  skipped** (except those with `ignore_downstream_trigger_rules=True`).

The difference from `BranchOperator`: `ShortCircuitOperator` has one
outcome (skip everything) rather than a choice among paths. It is
Airflow's implementation of the "if not applicable, do nothing" pattern.

`ignore_downstream_trigger_rules=True` means the downstream tasks are
skipped *regardless* of their own trigger rules. Leave it `False` (the
default) if you want a downstream `always` task (like a cleanup or
notification) to still run.

### Trigger rules

The trigger rule decides whether a task runs, given the states of its
dependencies.

| Rule | Runs when |
|---|---|
| `all_success` (default) | **all** dependencies succeeded |
| `none_failed` | no dependency **failed** (skipped is OK) |
| `none_failed_min_one_success` | no dependency failed, **and** at least one succeeded |
| `none_skipped` | no dependency was **skipped** |
| `all_done` | **all** dependencies finished, whatever their state |
| `always` | always |

The subtle and important part is how **skipped** interacts with them.

```text
Dependency state    all_success   none_failed   none_failed_min_one_success   none_skipped   all_done   always
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
success            ✓ runs        ✓ runs        ✓ runs                        ✓ runs         ✓ runs     ✓ runs
failed             ✗ upstream_failed  ✗ upstream_failed  ✗ upstream_failed      ✗ upstream_failed  ✓ runs  ✓ runs
skipped            ✗ skipped     ✓ runs        ✗ unless another succeeded    ✗ skipped     ✓ runs     ✓ runs
```

Two things to internalise:

1. **A `failed` dependency blocks the task entirely** — it becomes
   `upstream_failed`, regardless of the trigger rule, *except* for
   `all_done` and `always`, which exist precisely to run even when
   things failed.
2. **A `skipped` dependency is not a failure.** It is a "not
   applicable" signal. `none_failed` treats it as "fine, carry on".
   `all_success` treats it as "cannot run". And
   `none_failed_min_one_success` asks a third question: "did *anything*
   succeed?"

That second row is the whole reason the join-point pattern exists.

### The join point pattern

A task that depends on **both** branches has one dependency that was
skipped. With the default `all_success`, it is skipped too — and now
your DAG looks correct but silently does nothing.

```python
# WRONG — the join point is skipped, because one branch was skipped
join = EmptyOperator(task_id="load_complete")
```

```python
# RIGHT — "run as long as nothing failed"
join = EmptyOperator(
    task_id="load_complete",
    trigger_rule="none_failed",
)
```

This is exactly what the course's `branching_load` DAG does:

```python
Task(
    "finalise",
    lambda run, context: (
        run.pull("full_load") or run.pull("incremental_load") or "nothing"
    ),
    dependencies=["full_load", "incremental_load"],
    trigger_rule="none_failed",
),
```

Note the `or` chain: it pulls from the branch that ran, and falls back
to `"nothing"` if neither produced a value. It has to check **both**,
because it does not know which branch was chosen.

The choice of trigger rule for a join point:

| Rule | When to use it |
|---|---|
| `none_failed` | the join should run if *either* branch succeeded |
| `none_failed_min_one_success` | stricter — require at least one success |
| `all_done` | the join should run even if a branch *failed* (cleanup) |
| `always` | same as `all_done` in practice, but also ignores the "upstream failed" block |

`none_failed` is the default choice for a load-complete join.
`all_done` is the right choice for a **notification or cleanup** task
that must run whether or not the pipeline succeeded.

### The classic branch bug

This is worth spelling out in full, because it is the single most common
branching defect and it is *silent*.

```python
with DAG(dag_id="branching_bug") as dag:
    check = PythonOperator(task_id="check", python_callable=check)

    fast = PythonOperator(task_id="fast_path", python_callable=fast)
    slow = PythonOperator(task_id="slow_path", python_callable=slow)

    notify = PythonOperator(task_id="notify", python_callable=notify)

    check >> fast >> notify
    check >> slow >> notify
```

What the author intended: "run `fast` or `slow`, then notify."

What actually happens:

- `check` returns `["fast_path"]`.
- `fast_path` runs, `slow_path` is **skipped**.
- `notify` depends on both. One is skipped. `all_success` → **`notify`
  is skipped**.
- The DAG run succeeds. Nobody is notified. The pipeline quietly did
  nothing.

The graph *looks* right in the UI — the edges are exactly what was
intended. The failure is only visible in the task states, and only if
someone looks.

The fix:

```python
    notify = PythonOperator(
        task_id="notify",
        python_callable=notify,
        trigger_rule="none_failed",   # ← the missing piece
    )
```

**A join point after a branch must have `trigger_rule="none_failed"` (or
`"all_done"`).** There is no exception to this rule.

### `task.skip()` — skipping from your own code

Sometimes the decision to skip is made deep inside your task's logic,
not at a branch point. Airflow lets you skip a task explicitly:

```python
from airflow.exceptions import AirflowSkipException


def load_if_present(**context) -> None:
    ti = context["ti"]
    uri = ti.xcom_pull(task_ids="find_source", key="uri")
    if uri is None:
        log.info("no source object for %s — skipping", context["ds"])
        raise AirflowSkipException(f"no source object for {context['ds']}")
    load(uri)
```

The task is marked `skipped`, the message you passed appears in the log,
and downstream tasks are evaluated against the trigger rules exactly as
if a `ShortCircuitOperator` had skipped.

The difference from `ShortCircuitOperator`:

| | `task.skip()` | `ShortCircuitOperator` |
|---|---|---|
| **Where the decision is made** | inside your own code | in a dedicated task |
| **Scope of the skip** | this task only | this task + all downstream (by default) |
| **Message** | you supply it | "Task is skipped" |

Use `task.skip()` when the "not applicable" condition is discovered
*after* the task starts doing work. Use `ShortCircuitOperator` when the
condition is known up front and you want to skip a whole subtree.

In Airflow 2.x the API is `ti.skip()`; `raise AirflowSkipException` is
the equivalent and is what most code uses.

### Dynamic task mapping

Branching is for a **fixed, small** number of paths. When the number of
paths is only known at run time and could be hundreds, you want
**dynamic task mapping** (Airflow 2.3+).

```python
from airflow.decorators import task


@task
def extract_regions() -> list[str]:
    return ["AMER", "EMEA", "APAC", "LATAM"]


@task
def load_region(region: str) -> str:
    log.info("loading region %s", region)
    return region


regions = extract_regions()
results = load_region.expand(region=regions)
```

`expand` creates one mapped task instance per element of the list, all
running in parallel. The upstream task's return value is the list; the
downstream task is instantiated once per element.

Reading the mapped outputs:

```python
@task
def summarise(results: list[str]) -> str:
    return f"loaded {len(results)} regions"


summary = summarise(results)
```

In Airflow 2.4+, `results` is a lazy `XComArg` that resolves to the
list of mapped outputs. You can also pull a specific index with
`ti.xcom_pull(task_ids='load_region', map_indexes=0)`.

Mapping over a dict:

```python
load_region.expand(region=regions)                    # over a list
load_region.expand_kwargs([{"region": r} for r in regions])   # over kwargs
```

Dynamic task mapping and branching solve different problems:

| | Branching | Dynamic mapping |
|---|---|---|
| **Number of paths** | fixed, small | unknown until run time |
| **Paths run** | exactly one | all of them, in parallel |
| **Declared at** | parse time | parse time (the *count* is dynamic) |
| **Use for** | "full load **or** incremental" | "load **each** of 500 customers" |

If you find yourself writing a `BranchOperator` with 20 branches, you
want dynamic mapping instead.

### The `should_run_full_load` decision, made pure

The course's branching decision is a pure function, which means it can
be unit-tested at every threshold boundary — exactly where branch bugs
live.

```python
from pipeline_logic import should_run_full_load

should_run_full_load(1245, 1000000)      # False
should_run_full_load(1000000, 1000000)   # False  ← note: strictly greater
should_run_full_load(1000001, 1000000)   # True
```

The implementation is `row_count > threshold` — **strictly greater**.
The boundary case `row_count == threshold` takes the incremental path.
That is a decision, and it must be made once, in a testable place,
rather than being re-derived in a DAG file.

---

## 🛠️ Hands-On

### Step 1: Run the branching DAG

```bash
python project/local_runner.py --dag branching_load --verbose
```

Expected output:

```text
▶ Running branching_load @ 2026-01-15

  Run summary for branching_load @ 2026-01-15
  ----------------------------------------------------
    ✓ read_orders            success
    ✓ transform_orders       success
    ✓ choose_strategy        success
    ○ full_load              skipped
    ✓ incremental_load       success
    ✓ finalise               success

  ✓ branching_load succeeded
```

Look at `full_load`: it is **skipped**, not failed. That is the correct
outcome — the branch chose a different path.

And look at `finalise`: it **ran**, even though one of its dependencies
(`full_load`) was skipped. That works because `finalise` has
`trigger_rule="none_failed"`.

### Step 2: See the branch decision

```bash
python project/local_runner.py --dag branching_load --verbose 2>&1 | grep -E 'rows=|branched|incremental'
```

Expected output:

```text
INFO       rows=1245 threshold=1000000 -> incremental_load
INFO   ✓ incremental_load       success
INFO       incremental load: appending 1245 rows to partition 20260115
```

1245 rows against a threshold of 1,000,000 → the incremental path.

### Step 3: Flip the threshold and take the other branch

The threshold is a Variable, so you can change it without editing the
DAG:

```bash
python project/local_runner.py --dag branching_load --vars '{"full_load_threshold": 100}' --verbose
```

Expected output:

```text
  Run summary for branching_load @ 2026-01-15
  ----------------------------------------------------
    ✓ read_orders            success
    ✓ transform_orders       success
    ✓ choose_strategy        success
    ✓ full_load              success
    ○ incremental_load       skipped
    ✓ finalise               success

  ✓ branching_load succeeded
```

The branches swapped. `finalise` still ran. The join point works.

### Step 4: Reproduce the classic branch bug

This is the most important exercise in the chapter. Build the buggy
graph and watch it silently do nothing:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def check(run, context):
    return ['fast_path']

dag = DAG(
    'branching_bug',
    tasks=[
        Task('check', check, dependencies=[], branch=True),
        Task('fast_path', lambda run, context: 'fast', dependencies=['check']),
        Task('slow_path', lambda run, context: 'slow', dependencies=['check']),
        # BUG: default trigger rule is 'all_success'
        Task('notify', lambda run, context: 'NOTIFIED', dependencies=['fast_path', 'slow_path']),
    ],
)
run = run_dag(dag, '2026-01-15', verbose=True)
print()
print('notify ran?', run.state.get('notify') == 'success')
"
```

Expected output:

```text
  Run summary for branching_bug @ 2026-01-15
  ----------------------------------------------------
    ✓ check                  success
    ○ slow_path              skipped
    ○ notify                 skipped
    ✓ fast_path              success

notify ran? False
```

**The DAG "succeeded". `notify` never ran.** This is the bug, and it
produces no error, no alert, and no failed run.

> **Note the `branch=True` flag** on the `check` task. That is how the
> local runner knows a task is a `BranchOperator` — it reads the
> returned list and marks the non-chosen downstream tasks as skipped.
> Without it, the runner treats `check` as an ordinary task and every
> downstream task runs. In Airflow, the equivalent marker is the
> operator *class* (`BranchOperator` vs `PythonOperator`).

### Step 5: Fix the branch bug

The only change is the trigger rule:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def check(run, context):
    return ['fast_path']

dag = DAG(
    'branching_fixed',
    tasks=[
        Task('check', check, dependencies=[], branch=True),
        Task('fast_path', lambda run, context: 'fast', dependencies=['check']),
        Task('slow_path', lambda run, context: 'slow', dependencies=['check']),
        # FIX: 'none_failed' — a skipped dependency is not a failure
        Task('notify', lambda run, context: 'NOTIFIED',
             dependencies=['fast_path', 'slow_path'], trigger_rule='none_failed'),
    ],
)
run = run_dag(dag, '2026-01-15', verbose=True)
print()
print('notify ran?', run.state.get('notify') == 'success')
print('notify output:', run.pull('notify'))
"
```

Expected output:

```text
  Run summary for branching_fixed @ 2026-01-15
  ----------------------------------------------------
    ✓ check                  success
    ○ slow_path              skipped
    ✓ fast_path              success
    ✓ notify                 success

notify ran? True
notify output: NOTIFIED
```

One keyword. That is the entire fix — and the entire class of bug.

### Step 6: Compare the trigger rules side by side

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

RULES = ['all_success', 'none_failed', 'none_failed_min_one_success', 'all_done', 'always']

for rule in RULES:
    dag = DAG(
        f'rule_{rule}',
        tasks=[
            Task('check', lambda run, context: ['fast_path'], dependencies=[]),
            Task('fast_path', lambda run, context: 'fast', dependencies=['check']),
            Task('slow_path', lambda run, context: 'slow', dependencies=['check']),
            Task('join', lambda run, context: 'joined',
                 dependencies=['fast_path', 'slow_path'], trigger_rule=rule),
        ],
    )
    run = run_dag(dag, '2026-01-15')
    print(f'{rule:<32} join -> {run.state.get(\"join\")}')
"
```

Expected output:

```text
all_success                     join -> skipped
none_failed                     join -> success
none_failed_min_one_success     join -> skipped
all_done                        join -> success
always                          join -> success
```

The default rule (`all_success`) skips the join point, as does
`none_failed_min_one_success` — because one dependency was skipped and
none succeeded, so "at least one success" is not satisfied.

> **A note on the local runner.** The runner's `_trigger_allows()` models
> `all_success`, `none_failed`, `all_done` and `always` explicitly.
> `none_failed_min_one_success` falls through to its default branch,
> which behaves like `all_success`. Real Airflow 2.x implements it
> faithfully: it runs when no dependency failed **and** at least one
> succeeded. The distinction is small, but it is exactly the case
> exercised in Step 7.

### Step 7: The `none_failed_min_one_success` difference

`none_failed` and `none_failed_min_one_success` differ only when
*every* branch was skipped. Build that case — a branch that names a
task id which does not exist, so nothing downstream of it runs:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

for rule in ['none_failed', 'none_failed_min_one_success']:
    dag = DAG(
        f'all_skipped_{rule}',
        tasks=[
            # The branch names a task that does not exist -> nothing downstream runs
            Task('check', lambda run, context: ['nonexistent'], dependencies=[], branch=True),
            Task('fast_path', lambda run, context: 'fast', dependencies=['check']),
            Task('join', lambda run, context: 'joined',
                 dependencies=['fast_path'], trigger_rule=rule),
        ],
    )
    run = run_dag(dag, '2026-01-15')
    print(f'{rule:<32} join -> {run.state.get(\"join\")}')
"
```

Expected output:

```text
none_failed                     join -> success
none_failed_min_one_success     join -> skipped
```

Here the distinction shows up:

- **`none_failed`** — "nothing failed, so carry on". The join runs even
  though *nothing* upstream succeeded.
- **`none_failed_min_one_success`** — "nothing failed **and** something
  succeeded". Nothing succeeded, so the join is skipped.

That is the semantic you want for a report task that should not run
when no branch produced data: `none_failed_min_one_success` says
"run if at least one branch actually did the work", while `none_failed`
says "run unless something broke".

### Step 7: The `none_failed_min_one_success` difference

`none_failed` and `none_failed_min_one_success` differ only when
*every* branch was skipped. Build that case:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

for rule in ['none_failed', 'none_failed_min_one_success']:
    dag = DAG(
        f'all_skipped_{rule}',
        tasks=[
            # The branch names a task that does not exist -> nothing downstream runs
            Task('check', lambda run, context: ['nonexistent'], dependencies=[]),
            Task('fast_path', lambda run, context: 'fast', dependencies=['check']),
            Task('join', lambda run, context: 'joined',
                 dependencies=['fast_path'], trigger_rule=rule),
        ],
    )
    run = run_dag(dag, '2026-01-15')
    print(f'{rule:<32} join -> {run.state.get(\"join\")}')
"
```

Expected output:

```text
none_failed                     join -> success
none_failed_min_one_success     join -> success
```

In the local runner's model, `none_failed_min_one_success` behaves the
same as `none_failed` — the runner's `_trigger_allows` treats a skipped
dependency as "not failed" without additionally requiring a success.
**Real Airflow 2.x distinguishes them**: `none_failed_min_one_success`
requires at least one upstream to have *succeeded*, so if all
dependencies were skipped, it is skipped too.

Use `none_failed_min_one_success` when "everything was skipped" should
mean "there was nothing to do, so do nothing" — for example, a report
task that should not run when no branch produced data.

### Step 8: `task.skip()` from inside a task

```bash
cd project
python3 -c "
from local_runner import DAG, Task, TaskSkip, run_dag

def load_if_present(run, context):
    uri = run.pull('find_source', 'uri')
    if uri is None:
        raise TaskSkip(f'no source object for {context[\"logical_date\"]}')
    return uri

dag = DAG(
    'skip_demo',
    tasks=[
        Task('find_source', lambda run, context: None, dependencies=[]),
        Task('load', load_if_present, dependencies=['find_source']),
    ],
)
run = run_dag(dag, '2026-01-15', verbose=True)
print()
print('load state:', run.state.get('load'))
"
```

Expected output:

```text
  Run summary for skip_demo @ 2026-01-15
  ----------------------------------------------------
    ✓ find_source            success
    ○ load                   skipped

load state: skipped
```

In real Airflow this is `raise AirflowSkipException("...")` (or
`ti.skip()`), and the message appears in the task log exactly as it
does here.

### Step 9: The `ShortCircuitOperator` shape

```python
from airflow.operators.python import ShortCircuitOperator

short_circuit = ShortCircuitOperator(
    task_id="check_enabled",
    python_callable=lambda **context: bool(context["params"].get("enabled", True)),
    ignore_downstream_trigger_rules=True,
)
```

The task succeeds and everything downstream is skipped when it returns
`False`. In the local runner, `ShortCircuitOperator` is not modelled as
a distinct operator — the runner's `TaskSkip` exception (raised by a
task's callable) is the equivalent, and the skip propagates to
downstream tasks that use the default `all_success` rule.

### Step 10: The pure decision function

```bash
cd project/core
python3 -c "
from pipeline_logic import should_run_full_load

threshold = 1000000
for count in [0, 999999, 1000000, 1000001, 5000000]:
    chosen = 'full_load' if should_run_full_load(count, threshold) else 'incremental_load'
    print(f'{count:>8} -> {chosen}')
"
```

Expected output:

```text
       0 -> incremental_load
  999999 -> incremental_load
 1000000 -> incremental_load
 1000001 -> full_load
 5000000 -> full_load
```

Note the boundary: exactly `1000000` takes the **incremental** path,
because the rule is `>` and not `>=`. That is a deliberate, testable
decision. If you want the opposite, change the pure function — and its
test — not the DAG.

---

## 🛠️ Common Errors and Fixes

### `Task is in the 'skipped' state` on a task that should have run

The classic branch bug. The task depends on a branch that was skipped,
and its trigger rule is the default `all_success`.

```python
join = EmptyOperator(task_id="load_complete", trigger_rule="none_failed")
```

Check the **upstream** task's state — a skipped dependency is the
cause.

### `Task is in the 'upstream_failed' state`

An upstream task **failed** (not skipped). This task never ran. Fix the
upstream failure.

If the upstream task is *meant* to be allowed to fail — say, an
optional enrichment step — give the downstream task
`trigger_rule="all_done"` or `"always"`.

### `BranchOperator` returned the task id but the task did not run

The returned task id must be an **exact, case-sensitive** task id in the
same DAG. A typo means Airflow skips every downstream task (because
none of them was named) and the branch succeeds with nothing done.

```python
return ["incremental_load"]   # must match task_id="incremental_load"
```

Also: the returned task must be a **direct or indirect downstream** of
the branch. A branch can only choose its own descendants.

### `BranchOperator` returned an empty list and everything was skipped

`return []` is legal — it means "run none of the paths". If that is
not what you meant, check your condition logic.

### The branch task itself is skipped

A `BranchOperator` skips itself only if one of *its* dependencies was
skipped. The branch does not skip itself because of its own return
value.

### `AirflowSkipException: Task is skipped` appears as a failure in your logs

`AirflowSkipException` is a control-flow signal, not an error. It
appears in the log because it is raised, but the task's state is
`skipped`, and the DAG run is not failed by it.

If you are raising it in your own code, be aware it aborts the task
immediately — anything after the raise does not run.

### `TypeError: BranchOperator.__init__() missing 1 required positional argument: 'task_id'`

Every operator needs a `task_id`, and it must be unique within the DAG.

### The mapped task did not expand

Dynamic task mapping requires:

1. An Airflow version of **2.3 or later** (2.4+ recommended).
2. The upstream task must have **returned** the list — a task that
   returns `None` maps to zero instances.
3. The list must be a real list, not a generator or a dict (use
   `expand_kwargs` for dicts).

### `AssertionError: unmapped or unmappable arguments` in `expand`

Every parameter of the mapped function must either be mapped or be a
plain value. You cannot mix a mapped and an unmapped argument in one
`expand` call.

```python
# WRONG
load_region.expand(region=regions, mode="full")

# RIGHT — map one, or split into two calls
load_region.expand(region=regions)
```

---

## 💡 Production Notes

- **Every join point after a branch needs `trigger_rule="none_failed"`
  (or `"all_done"`).** No exceptions. This is the single highest-value
  rule in this chapter.
- **Make the branch decision a pure, tested function.**
  `should_run_full_load()` in `pipeline_logic.py` exists so the
  threshold boundary is unit-tested rather than re-derived in a DAG.
- **A skipped task is not a failure.** Do not page on it. Alert on
  `failed` and `upstream_failed`; report `skipped` as information.
- **Use `none_failed_min_one_success`** for a join that should not run
  when nothing produced data.
- **Use `all_done` for cleanup and notification** tasks that must run
  whether or not the pipeline succeeded.
- **Prefer dynamic task mapping over a branch with many paths.** If you
  are writing the twentieth branch, you want `expand`.
- **Keep branch logic out of the DAG file.** Put the *decision* in a
  pure function and the *wiring* in the DAG.
- **Test your branches.** Write a test for each path. A branch is the
  part of a DAG most likely to be silently wrong, and the UI will not
  tell you.
- **Log the decision.** `log.info("rows=%d threshold=%d -> %s", ...)` is
  what makes a branch auditable after the fact.
- **Be careful with `depends_on_past` and branches.** A task with
  `depends_on_past=True` that was skipped in a previous run blocks the
  next run. This is a classic source of "the DAG stopped running" bugs.

---

## 🔑 Key Takeaways

- `BranchOperator` returns a **list of task ids**; those run, and every
  other downstream task is **skipped**. **The branch itself succeeds.**
- `ShortCircuitOperator` returns a **boolean**: `False` skips the task
  and everything downstream.
- Six trigger rules: `all_success`, `none_failed`,
  `none_failed_min_one_success`, `none_skipped`, `all_done`, `always`.
- A **skipped dependency is not a failure** — that is why `none_failed`
  exists and why `all_success` (the default) skips a join point.
- **The join point pattern**: a task depending on multiple branches must
  use `trigger_rule="none_failed"` or `"all_done"`.
- **The classic branch bug**: a join point with the default rule is
  skipped, the DAG "succeeds", and nothing happens. It is silent.
- `task.skip()` / `raise AirflowSkipException` skips a task from inside
  your own logic.
- **Dynamic task mapping** (`expand`) handles an unknown number of
  parallel paths; branching handles a fixed choice between a few.
- Make branch decisions **pure and tested** — `should_run_full_load()`
  is the model.

---

## 📚 Practice Exercises

1. **Boundary tests.** Write tests for `should_run_full_load` at
   `threshold - 1`, `threshold`, and `threshold + 1`. Then decide
   whether `>` is the right operator for your business, and change the
   function (and its callers) if not.

2. **Reproduce and fix.** Recreate the classic branch bug from Step 4,
   then fix it. Write down the *one-line* difference and explain why a
   DAG-structure review would not have caught the original.

3. **Trigger rule matrix.** For each of the six trigger rules, describe
   a real pipeline situation where it is the right choice. Include one
   case where `none_skipped` is the only correct answer.

4. **All-skipped branch.** Build a branch that names a task id that does
   not exist. Describe exactly what happens in Airflow 2.x, and how you
   would defend against it in code review.

5. **ShortCircuit vs Branch.** Write the same requirement twice — once
   with a `ShortCircuitOperator` and once with a `BranchOperator` —
   for the case "if the input file is missing, do nothing". Which do
   you prefer, and when would the answer change?

6. **Dynamic mapping.** Rewrite the "load each region" idea using
   `expand` over `["AMER", "EMEA", "APAC", "LATAM"]`, with each mapped
   task calling `summarise_by_region()` on its own region. Then
   describe how you would aggregate the four mapped results.

7. **Audit the DAGs.** For every DAG in `project/dags/`, identify every
   task that depends on more than one upstream, and state whether it
   needs a non-default trigger rule. `04_branching_and_xcom.py` is the
   one to look at hardest.

8. **Reflection.** Explain, in your own words, why "a skipped dependency
   is not a failure" is a *design decision* rather than an accident, and
   what would break if Airflow treated skipped as failed.

---

## 📖 Further Reading

- Airflow branching — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/branching.html
- Airflow trigger rules — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#trigger-rules
- Airflow task states — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskinstance
- Airflow dynamic task mapping — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html
- Airflow `BaseOperator` (`skip`, `trigger_rule`) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html
- Airflow `AirflowSkipException` — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/exceptions/index.html
- Google Cloud Composer: dynamic task mapping — https://cloud.google.com/composer/docs/how-to/using/dynamic-task-mapping
