"""The fan-out / fan-in DAG, expressed in the mini-runner's vocabulary.

Every task here has a one-line counterpart in a real Airflow DAG:

    mini-runner Task            Airflow equivalent
    -----------------           ------------------
    Task(...)                   PythonOperator(...)
    dependencies=[...]          upstream >> downstream
    trigger_rule="none_failed"  trigger_rule=TriggerRule.NONE_FAILED
    branch=True                 BranchOperator
    return value                ti.xcom_push(key="return_value")

The mini-runner has no `.expand()`, so this notebook models dynamic task
mapping explicitly with `run_mapped_task` — a helper that runs the mapped
body once per element and collects the returns, which is precisely the
semantics Airflow gives a mapped task:

  * one task *definition*,
  * N task *instances*, created at run time,
  * the instance's own return value,
  * all returns collected into one list under the unmapped task_id.
"""

from local_runner import DAG, Task

#: The fan-out helpers, from project/core/fanout.py.
from fanout import load_tasks, region_summary_csv, regions_to_process

#: The pure pipeline logic, from project/core/pipeline_logic.py.
from pipeline_logic import summarise_by_region, transform_orders


def read_orders(run, context):
    """Read the raw CSV lines for this run.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def validate(run, context):
    """Validate the raw rows and push the accepted set downstream.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The accepted rows.
    """
    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("validate", "accepted", accepted)
    run.xcom.push("validate", "rejected", rejected)
    run.xcom.push("validate", "summary", summarise_by_region(accepted))
    return accepted


def list_regions(run, context):
    """Return the regions that produced revenue.

    This is the value that `.expand()` would map over in Airflow.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A sorted list of region codes.
    """
    summary = run.pull("validate", "summary") or {}
    return regions_to_process(summary)


def build_load_tasks(run, context):
    """Return one dict per region, for `.expand_kwargs()`.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A list of dicts with `region` and `partition` keys.
    """
    summary = run.pull("validate", "summary") or {}
    partition = context["ds_nodash"]
    return load_tasks(summary, partition)


def transform_region(run, context, region, partition):
    """Transform one region. This is a mapped task's body.

    In Airflow the mapped parameters arrive in `context["params"]`; here
    they are ordinary arguments, so the body reads the same either way.

    Args:
        run: The run context.
        context: The Jinja context.
        region: The region code.
        partition: The partition decorator being loaded.

    Returns:
        A dict describing what was transformed.
    """
    summary = run.pull("validate", "summary") or {}
    csv_text = region_summary_csv(summary, region)
    return {
        "status": "success",
        "region": region,
        "partition": partition,
        "csv": csv_text,
    }


def run_mapped_task(run, context):
    """Run the mapped body once per element and collect the returns.

    This models Airflow's dynamic task mapping:

      * the elements come from `build_load_tasks` — the list `.expand()`
        or `.expand_kwargs()` would map over;
      * each element produces one task instance with its own return value;
      * the returns are collected into a list — which Airflow stores under
        the *unmapped* task_id, so `xcom_pull(task_ids="load_region")`
        returns the whole list.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The list of per-instance return values.
    """
    task_id = "transform_region"
    elements = run.pull("build_load_tasks") or []
    results = []
    for index, element in enumerate(elements):
        value = transform_region(run, context, **element)
        results.append(value)
        run.xcom.push(task_id, f"instance[{index}]", value)
    # Airflow pushes the collected list under the unmapped task_id.
    run.xcom.push(task_id, "results", results)
    return results


def join_regions(run, context):
    """Join the branches' results.

    In Airflow the join pulls the mapped task's collected list under the
    *unmapped* task_id. The static DAG has no such list, so we fall back
    to the four static branch results.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A summary of the join.
    """
    results = run.pull("transform_region", "results")
    if results is None:
        results = [
            run.pull(task_id)
            for task_id in ("transform_amer", "transform_apac",
                            "transform_emea", "transform_latam")
        ]
    results = [r for r in results if r]
    succeeded = [r for r in results if r.get("status") == "success"]
    return {
        "joined": len(succeeded),
        "regions": [r["region"] for r in succeeded],
    }


def build_static_fanout_dag():
    """Build the static fan-out / fan-in DAG.

    Returns:
        The DAG.
    """
    return DAG(
        "patterns_fanout_static",
        tasks=[
            Task("read_orders", read_orders),
            Task("validate", validate, dependencies=["read_orders"]),
            # --- the fan-out: one task per branch -------------------
            Task("transform_amer", transform_region, dependencies=["validate"],
                 params={"region": "AMER", "partition": "20260115"}),
            Task("transform_apac", transform_region, dependencies=["validate"],
                 params={"region": "APAC", "partition": "20260115"}),
            Task("transform_emea", transform_region, dependencies=["validate"],
                 params={"region": "EMEA", "partition": "20260115"}),
            Task("transform_latam", transform_region, dependencies=["validate"],
                 params={"region": "LATAM", "partition": "20260115"}),
            # --- the fan-in: the join ------------------------------
            Task("join_regions", join_regions,
                 dependencies=["transform_amer", "transform_apac",
                               "transform_emea", "transform_latam"],
                 trigger_rule="none_failed"),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Static fan-out over regions, joined by one task.",
    )


def build_mapped_dag():
    """Build the dynamic-mapping DAG.

    The `transform_region` task is a *single* definition. Its instances
    are created at run time by `run_mapped_task`, from the payload that
    `build_load_tasks` produces — which is the whole point of dynamic task
    mapping.

    Returns:
        The DAG.
    """
    return DAG(
        "patterns_fanout_mapped",
        tasks=[
            Task("read_orders", read_orders),
            Task("validate", validate, dependencies=["read_orders"]),
            Task("list_regions", list_regions, dependencies=["validate"]),
            Task("build_load_tasks", build_load_tasks, dependencies=["validate"]),
            # One definition; N instances, decided at run time.
            Task("transform_region", run_mapped_task,
                 dependencies=["build_load_tasks"]),
            Task("join_regions", join_regions, dependencies=["transform_region"],
                 trigger_rule="none_failed"),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Dynamic fan-out over regions, one task instance each.",
    )


STATIC_FANOUT_DAG = build_static_fanout_dag()
MAPPED_DAG = build_mapped_dag()

print(STATIC_FANOUT_DAG.describe())
print()
print(MAPPED_DAG.describe())
