"""Case study C: a three-DAG dependency chain, wired with a push trigger."""

import json
from dataclasses import dataclass, field
from typing import Any

from local_runner import DAG, Task, run_dag
from pipeline_logic import render_summary_csv, summarise_by_region, transform_orders

LOGICAL_DATE = "2026-01-15"


@dataclass
class ChainState:
    """The shared state the chain's DAGs read and write.

    In Airflow this state lives in three places: the metadata database
    (run states), XCom (small control data), and the warehouse (the
    artefacts). Here we model it with one object so the chain is
    readable.

    Attributes:
        artefacts: The artefacts each DAG has produced, by DAG id.
        runs: The run records, by DAG id.
    """

    artefacts: dict[str, Any] = field(default_factory=dict)
    runs: dict[str, str] = field(default_factory=dict)

    def record(self, dag_id, artefact):
        """Record a DAG's artefact.

        Args:
            dag_id: The DAG that produced it.
            artefact: The artefact.
        """
        self.artefacts[dag_id] = artefact
        self.runs[dag_id] = "success"


#: The chain's shared state.
CHAIN = ChainState()


# ---------------------------------------------------------------------
# DAG 1: ingest
# ---------------------------------------------------------------------
def ingest_read(run, context):
    """Read the raw orders.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def ingest_write_raw(run, context):
    """Write the raw orders to the raw table.

    The artefact boundary: `raw.orders` is a table another DAG can read.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The artefact reference.
    """
    raw = run.pull("ingest_read") or []
    table = "raw.orders"
    CHAIN.record("dag_ingest", {"table": table, "row_count": len(raw)})
    print(f"      wrote {len(raw)} rows to {table}")
    return {"table": table, "row_count": len(raw)}


# ---------------------------------------------------------------------
# DAG 2: transform
# ---------------------------------------------------------------------
def transform_read_raw(run, context):
    """Read the raw table produced by the ingest DAG.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def transform_validate(run, context):
    """Validate and transform the raw rows.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A dict with the accepted and rejected counts.
    """
    raw = run.pull("transform_read_raw") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("transform_validate", "accepted", accepted)
    run.xcom.push("transform_validate", "summary", summarise_by_region(accepted))
    return {"accepted_count": len(accepted), "rejected_count": len(rejected)}


def transform_write_curated(run, context):
    """Write the curated table — the second artefact boundary.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The artefact reference.
    """
    stats = run.pull("transform_validate") or {}
    table = "analytics.orders_enriched"
    partition = context["ds_nodash"]
    CHAIN.record("dag_transform", {"table": table, "partition": partition,
                                   "row_count": stats.get("accepted_count", 0)})
    print(f"      wrote {stats.get('accepted_count', 0)} rows to "
          f"{table}${partition}")
    return {"table": table, "partition": partition,
            "row_count": stats.get("accepted_count", 0)}


# ---------------------------------------------------------------------
# DAG 3: publish
# ---------------------------------------------------------------------
def publish_read_curated(run, context):
    """Read the curated table.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The accepted rows.
    """
    raw = (COURSE_ROOT / "sample_data" / "orders.csv").read_text(
        encoding="utf-8").splitlines()
    accepted, _ = transform_orders(raw)
    return accepted


def publish_write_summary(run, context):
    """Write the summary to GCS.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The artefact reference.
    """
    accepted = run.pull("publish_read_curated") or []
    summary = summarise_by_region(accepted)
    bucket = context["__variables__"].get("target_bucket", "demo-target-bucket")
    uri = f"gs://{bucket}/summary/{context['ds']}/summary.csv"
    CHAIN.record("dag_publish", {"uri": uri, "summary": summary})
    print(f"      wrote {uri}")
    return {"uri": uri, "summary": summary}


# ---------------------------------------------------------------------
# The DAGs
# ---------------------------------------------------------------------
INGEST_DAG = DAG(
    "dag_ingest",
    tasks=[
        Task("ingest_read", ingest_read),
        Task("ingest_write_raw", ingest_write_raw, dependencies=["ingest_read"]),
    ],
    schedule="@daily",
    start_date="2026-01-01",
    description="Land the raw orders in raw.orders.",
)

TRANSFORM_DAG = DAG(
    "dag_transform",
    tasks=[
        Task("transform_read_raw", transform_read_raw),
        Task("transform_validate", transform_validate,
             dependencies=["transform_read_raw"]),
        Task("transform_write_curated", transform_write_curated,
             dependencies=["transform_validate"]),
    ],
    schedule=None,          # triggered by the ingest DAG
    start_date="2026-01-01",
    description="Validate and curate raw.orders into analytics.orders_enriched.",
)

PUBLISH_DAG = DAG(
    "dag_publish",
    tasks=[
        Task("publish_read_curated", publish_read_curated),
        Task("publish_write_summary", publish_write_summary,
             dependencies=["publish_read_curated"]),
    ],
    schedule=None,          # triggered by the transform DAG
    start_date="2026-01-01",
    description="Publish the per-region summary to Cloud Storage.",
)

print("The chain:")
print()
for dag in (INGEST_DAG, TRANSFORM_DAG, PUBLISH_DAG):
    print(f"  {dag.dag_id:<16} schedule={dag.schedule!r:<10} "
          f"tasks={len(dag.tasks)}")
print()
print("  dag_ingest --raw.orders--> dag_transform "
      "--analytics.orders_enriched--> dag_publish")
print()

# ---------------------------------------------------------------------
# Run the chain
# ---------------------------------------------------------------------
print("=" * 70)
print("RUNNING THE CHAIN")
print("=" * 70)

for dag in (INGEST_DAG, TRANSFORM_DAG, PUBLISH_DAG):
    run = run_dag(dag, LOGICAL_DATE, verbose=True)
    failed = [t for t, s in run.state.items() if s != "success"]
    assert not failed, f"{dag.dag_id} failed: {failed}"
    print()

print("Artefacts produced:")
for dag_id, artefact in CHAIN.artefacts.items():
    printable = {k: v for k, v in artefact.items() if k != "summary"}
    print(f"  {dag_id:<16} {printable}")
print()

published = CHAIN.artefacts["dag_publish"]
print("The published summary:")
print()
print(render_summary_csv(published["summary"]), end="")

EXPECTED = {
    "AMER": {"order_count": 318, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320, "revenue_eur": 110646.18},
}
assert published["summary"] == EXPECTED, published["summary"]
print("PASS: the three-DAG chain produces the expected summary.")
print()

# ---------------------------------------------------------------------
# The conf contract
# ---------------------------------------------------------------------
print("=" * 70)
print("THE CONF CONTRACT")
print("=" * 70)
conf = {
    "conf_version": 1,
    "source_partition": "20260115",
    "parent_run_id": "scheduled__2026-01-15T00:00:00+00:00",
}
serialised = json.dumps(conf, sort_keys=True)
print(f"  conf as stored in the metadata DB: {serialised}")
print(f"  size: {len(serialised)} bytes")
print()
print("  Rules:")
print("   1. JSON-serialisable — a datetime raises TypeError.")
print("   2. Small — one copy per run, in the metadata database.")
print("   3. Versioned — bump conf_version rather than changing the shape.")
print("   4. reset_dag_run=True for anything a backfill touches.")
print()

try:
    from datetime import datetime
    json.dumps({"when": datetime(2026, 1, 15)})
except TypeError as exc:
    print(f"  a datetime in the conf -> TypeError: {exc}")
