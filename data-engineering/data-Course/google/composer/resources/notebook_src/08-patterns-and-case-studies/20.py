"""Case study B: a backfill, and the property that makes it safe."""

from local_runner import run_dag
from pipeline_logic import partition_for_date, render_summary_csv

LOGICAL_DATE = "2026-01-15"


def read_orders(run, context):
    """Read the raw orders for this run's date.

    In a real backfill this reads the *specific* date's file, not
    "whatever is in the bucket now". Here the sample dataset is a single
    day, so every date reads the same source — and the point of the
    exercise is the *destination* behaviour, not the source.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def validate_and_stage(run, context):
    """Validate the rows and stage them for the run's partition.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A dict describing the staging.
    """
    from pipeline_logic import summarise_by_region, transform_orders

    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("validate_and_stage", "accepted", accepted)
    run.xcom.push("validate_and_stage", "summary", summarise_by_region(accepted))
    return {
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "partition": partition_for_date(context["ds"]),
    }


def load_to_bigquery(run, context):
    """Load the staged partition, replacing what is already there.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of the load.
    """
    staging = run.pull("validate_and_stage") or {}
    return (
        f"WRITE_TRUNCATE into {staging['partition']} "
        f"({staging['accepted_count']} rows)"
    )


def aggregate_by_region(run, context):
    """Aggregate the loaded rows.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The region summary.
    """
    summary = run.pull("validate_and_stage", "summary") or {}
    run.xcom.push("aggregate_by_region", "summary", summary)
    return summary


from local_runner import DAG, Task  # noqa: E402

BACKFILL_DAG = DAG(
    "case_study_backfill",
    tasks=[
        Task("read_orders", read_orders),
        Task("validate_and_stage", validate_and_stage, dependencies=["read_orders"]),
        Task("load_to_bigquery", load_to_bigquery, dependencies=["validate_and_stage"]),
        Task("aggregate_by_region", aggregate_by_region,
             dependencies=["load_to_bigquery"]),
    ],
    # catchup=False: a backfill is triggered explicitly, one date at a time.
    schedule="@daily",
    start_date="2026-01-01",
    description="One run per date; the write replaces the partition.",
)

print(BACKFILL_DAG.describe())
print()
print(f"catchup          : {BACKFILL_DAG.catchup}")
print(f"max_active_runs  : {BACKFILL_DAG.max_active_runs}")
print()

# ---------------------------------------------------------------------
# A backfill: one run per date
# ---------------------------------------------------------------------
BACKFILL_DATES = ["2026-01-08", "2026-01-09", "2026-01-10", "2026-01-11"]

print("=" * 70)
print("THE BACKFILL: one DAG run per date")
print("=" * 70)

results = {}
for day in BACKFILL_DATES:
    run = run_dag(BACKFILL_DAG, day)
    assert run.state["load_to_bigquery"] == "success", run.state
    partition = run.pull("validate_and_stage")["partition"]
    results[day] = run.pull("aggregate_by_region", "summary")
    print(f"  {day}  partition={partition}  "
          f"rows={run.pull('validate_and_stage')['accepted_count']}  "
          f"state={'ok' if all(s == 'success' for s in run.state.values()) else 'FAILED'}")

print()
print("PASS: every backfilled date produced a successful run.")
print()

# ---------------------------------------------------------------------
# The property: a backfilled date gives the same answer as an original run
# ---------------------------------------------------------------------
print("=" * 70)
print("THE PROPERTY: backfill == original run")
print("=" * 70)

original = run_dag(BACKFILL_DAG, LOGICAL_DATE)
original_summary = original.pull("aggregate_by_region", "summary")
backfilled_summary = results[BACKFILL_DATES[0]]

assert original_summary == backfilled_summary, (
    f"backfill changed the answer: {original_summary} != {backfilled_summary}"
)
print("PASS: the backfilled run produced exactly the same table as the")
print("      original run. That is what makes a backfill safe.")
print()

# ---------------------------------------------------------------------
# The failure a non-idempotent backfill produces
# ---------------------------------------------------------------------
print("=" * 70)
print("THE FAILURE: what an append-mode backfill does")
print("=" * 70)
from idempotent_load import apply_load  # noqa: E402

table = {}
table = apply_load(table, original_summary, mode="append")   # original run
table = apply_load(table, backfilled_summary, mode="append")  # backfill
table = apply_load(table, backfilled_summary, mode="append")  # retry

print(f"  revenue after one original + two backfills: "
      f"{table['AMER']['revenue_eur']:.2f}")
print(f"  correct revenue                            : "
      f"{original_summary['AMER']['revenue_eur']:.2f}")
print()
print("  The backfill ran twice, so the revenue is three times the truth.")
print("  The numbers look plausible — which is exactly why this bug")
print("  survives for weeks before anyone notices.")
print()

# The correct behaviour, for contrast.
safe = apply_load({}, original_summary, mode="truncate")
safe = apply_load(safe, backfilled_summary, mode="truncate")
safe = apply_load(safe, backfilled_summary, mode="truncate")
assert safe == original_summary
print("  With WRITE_TRUNCATE, the same three writes leave the table")
print("  exactly as the original run left it:")
print()
print(render_summary_csv(safe), end="")
print("PASS: truncate is idempotent; append is not.")
