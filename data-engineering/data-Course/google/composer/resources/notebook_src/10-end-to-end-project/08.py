"""Run every DAG in the local runner and cross-validate each one.

For each DAG we check three things:

  1. every task reached a terminal state (nothing left `upstream_failed`),
  2. the DAG's summary equals the pure reference summary, and
  3. the DAG's row counts equal the reference row counts.

If any of these fail, the orchestration disagrees with the logic — which
is the bug class the local runner exists to catch.
"""

from local_runner import DAGS, run_dag

print("=" * 78)
print("THE DAGs THE RUNNER KNOWS")
print("=" * 78)
print()

for name in sorted(DAGS):
    dag = DAGS[name]()
    print(dag.describe())
    print()

# --------------------------------------------------------------------------
# Run them all
# --------------------------------------------------------------------------
print("=" * 78)
print("RUNNING ALL FOUR")
print("=" * 78)
print()

runs = {}

for name in sorted(DAGS):
    dag = DAGS[name]()
    print(f"▶ {name} @ {TARGET_DATE}")
    run = run_dag(dag, TARGET_DATE, verbose=True)
    runs[name] = run

    failed = [t for t, s in run.state.items() if s == "failed"]
    blocked = [t for t, s in run.state.items() if s == "upstream_failed"]
    skipped = [t for t, s in run.state.items() if s == "skipped"]

    print(f"  tasks: {len(dag.tasks)}   failed: {len(failed)}   "
          f"blocked: {len(blocked)}   skipped: {len(skipped)}")
    assert not failed, f"{name} failed: {failed}"
    assert not blocked, f"{name} had blocked tasks: {blocked}"
    print()

# --------------------------------------------------------------------------
# Cross-validate every DAG against the reference
# --------------------------------------------------------------------------
print("=" * 78)
print("CROSS-VALIDATION AGAINST THE REFERENCE")
print("=" * 78)
print()

reference_summary = summarise_by_region(accepted)
reference_accepted = len(accepted)
reference_rejected = len(rejected)

print(f"{'dag':<20} {'summary':<10} {'rows':<8} {'accept':>8} {'reject':>8}")
print("-" * 70)

for name in sorted(runs):
    run = runs[name]

    # Each DAG names its aggregate task differently; find the summary
    # wherever it was pushed. `branching_load` has no aggregate task at
    # all — it branches on the row count — so it is checked on its rows.
    summary = (
        run.pull("aggregate", "summary")
        or run.pull("publish_summary", "summary")
    )

    stats = (
        run.pull("transform_orders")
        or run.pull("validate_and_stage")
        or {}
    )
    accept_count = int(stats.get("accepted_count", 0))
    reject_count = int(stats.get("rejected_count", 0))

    summary_ok = summary is None or summary == reference_summary
    rows_ok = accept_count == reference_accepted

    summary_label = "-" if summary is None else (
        "MATCH" if summary == reference_summary else "DIFFER")

    print(f"{name:<20} {summary_label:<10} "
          f"{'MATCH' if rows_ok else 'DIFFER':<8} "
          f"{accept_count:>8} {reject_count:>8}")

    assert summary_ok, f"{name}: summary != reference\n{summary}\n{reference_summary}"
    assert rows_ok, f"{name}: accepted count != {reference_accepted}"
    assert reject_count == reference_rejected, f"{name}: rejected count != {reference_rejected}"

print()
print("Every DAG produced the reference summary, from the same input,")
print("through four different orchestration shapes.")
print()
print("`branching_load` shows '-' in the summary column because it has")
print("no aggregate task — it branches on the row count instead. Its")
print("row counts are still checked against the reference.")
print()

# --------------------------------------------------------------------------
# The summary they all agree on
# --------------------------------------------------------------------------
print("=" * 78)
print("THE OUTPUT")
print("=" * 78)
print()

final_summary = runs["etl_to_gcs"].pull("aggregate", "summary")
print(render_summary_csv(final_summary), end="")

stats = runs["etl_to_gcs"].pull("transform_orders")
print(f"accepted={stats['accepted_count']} rejected={stats['rejected_count']}")
print()

# The exact strings the course promises.
assert render_summary_csv(final_summary) == (
    "region,order_count,revenue_eur\n"
    "AMER,318,113592.19\n"
    "APAC,285,108194.92\n"
    "EMEA,322,118423.22\n"
    "LATAM,320,110646.18\n"
), render_summary_csv(final_summary)

assert stats["accepted_count"] == 1245
assert stats["rejected_count"] == 0

print("PASS: the output is exactly")
print()
print("  region,order_count,revenue_eur")
print("  AMER,318,113592.19")
print("  APAC,285,108194.92")
print("  EMEA,322,118423.22")
print("  LATAM,320,110646.18")
print()
print("  accepted=1245 rejected=0")
print()

# --------------------------------------------------------------------------
# The artefacts each DAG produced
# --------------------------------------------------------------------------
print("=" * 78)
print("THE ARTEFACTS")
print("=" * 78)
print()

etl_run = runs["etl_to_gcs"]
print(f"etl_to_gcs  wrote   : {etl_run.pull('write_summary', 'local_path')}")
print(f"            gcs uri : {etl_run.pull('write_summary', 'gcs_uri')}")
print()

xcom_run = runs["xcom_pipeline"]
print(f"xcom_pipeline pushed : "
      f"{sorted(xcom_run.xcom.all_for('publish_summary'))}")
print()

branch_run = runs["branching_load"]
print(f"branching_load chose : "
      f"{branch_run.pull('choose_strategy', 'branch')}")
print(f"            finalise : {branch_run.pull('finalise')}")
print()
