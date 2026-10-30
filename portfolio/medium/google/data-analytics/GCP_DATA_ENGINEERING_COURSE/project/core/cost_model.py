"""
cost_model.py — a pure pricing estimator for the GCP services in the course.

Real GCP billing is complicated. This module implements the **shape** of
each pricing model faithfully — per-TB-scanned, per-vCPU-hour, per-GB-
stored with a retrieval charge — using published list prices for the
region the course uses. That is enough to teach the decisions that
matter:

    * A query that scans 1 TB of a table that is not partitioned is
      twenty times more expensive than the same query against a
      partitioned table.
    * A streaming job that idles overnight still bills every hour.
    * Moving data out of GCP costs money; moving it in does not.
    * Storage is cheap; egress is what surprises people.

Usage:
    from cost_model import estimate, EstimateLine

    result = estimate("bigquery", scanned_tb=1.0)
    print(result.total, result.lines)
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

# --------------------------------------------------------------------------
# Configuration — list prices, USD
# --------------------------------------------------------------------------

#: The region the course prices in. GCP prices differ per region; these
#: are the us-central1 list prices.
PRICING_REGION = "us-central1"

#: Storage prices per GB-month, by class.
STORAGE_CLASS_PRICES: dict[str, float] = {
    "standard": 0.020,
    "nearline": 0.010,
    "coldline": 0.004,
    "archive": 0.0012,
}

#: Retrieval prices per GB, by class. This is the cost that surprises
#: people: storing in Nearline is cheap, *reading* it back is not free.
STORAGE_RETRIEVAL_PRICES: dict[str, float] = {
    "standard": 0.0,
    "nearline": 0.01,
    "coldline": 0.02,
    "archive": 0.05,
}

#: BigQuery on-demand price per TB scanned.
BIGQUERY_ONDEMAND_PER_TB = 6.25

#: BigQuery flat-rate price per slot-hour.
BIGQUERY_SLOT_HOUR = 0.06

#: Bytes in one TiB and one GB, for unit conversion.
BYTES_PER_TB = 1024**4
BYTES_PER_GB = 1024**3

#: Hours in a month, for monthly billing.
HOURS_PER_MONTH = 730

#: Per-service unit prices.
COMPUTE_ENGINE_PER_VCPU_HOUR = 0.031611
COMPUTE_ENGINE_PER_GB_MONTH = 0.040
KUBERNETES_MANAGEMENT_FEE_HOUR = 0.10
CLOUD_RUN_PER_REQUEST = 0.00
CLOUD_RUN_PER_CPU_SECOND = 0.000024
CLOUD_RUN_PER_GB_SECOND = 0.0000025
CLOUD_FUNCTIONS_PER_INVOCATION = 0.0000004
CLOUD_FUNCTIONS_PER_GB_SECOND = 0.0000025
PUBSUB_PER_GB_INGEST = 0.40
PUBSUB_PER_GB_DELIVERY = 0.40
DATAFLOW_PER_VCPU_HOUR = 0.0595
DATAPROC_PER_VCPU_HOUR = 0.0476
COMPOSER_PER_ENV_NODE_HOUR = 0.0564
SPANNER_PER_NODE_HOUR = 0.70
SPANNER_PER_PROCESSING_UNIT_HOUR = 0.30
CLOUD_SQL_PER_VCPU_HOUR = 0.205
CLOUD_SQL_PER_GB_STORAGE = 0.17
MEMORYSTORE_PER_GB_HOUR = 0.017
BIGTABLE_PER_NODE_GB_HOUR = 0.030
DATASTREAM_PER_CDC_ROW = 0.0000075
DATASTREAM_PER_STREAM_HOUR = 0.015
DATAPREP_PER_USER_HOUR = 0.60
DATA_CATALOG_PER_TIB = 0.10
DATAPLEX_PER_TIB = 0.02
SENSITIVE_DATA_PROTECTION_PER_GB = 0.10
VERTEX_AI_TRAINING_PER_NODE_HOUR = 3.67

#: The network egress price per GB from us-central1 to the internet.
NETWORK_EGRESS_PER_GB = 0.12

#: The free tier every new GCP account gets. These are the numbers the
#: courses reference when someone asks "will this cost me money?".
FREE_TIER = {
    "storage_gb_month": 5.0,
    "egress_gb": 1.0,
    "bigquery_query_tb": 1.0,
    "compute_vcpu_hours": 0.25,
    "cloud_run_requests": 2_000_000,
    "cloud_run_cpu_seconds": 180_000,
    "cloud_functions_invocations": 2_000_000,
    "pubsub_gb": 10.0,
    "cloud_sql_eur": 0.30,
}


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class EstimateLine:
    """One line of a cost estimate.

    Attributes:
        label: What is being charged for.
        quantity: The unit quantity, e.g. 1.0 for "1 TB scanned".
        unit: The unit name, e.g. ``"TB"``.
        unit_price: The price of one unit.
        cost: The line cost in USD.
        note: An optional explanatory note.
    """

    label: str
    quantity: float
    unit: str
    unit_price: float
    cost: float
    note: str = ""

    def __str__(self) -> str:
        """Render the line for a console table.

        Returns:
            A one-line description.
        """
        suffix = f"  ({self.note})" if self.note else ""
        return f"{self.label}: {self.quantity:g} {self.unit} x ${self.unit_price:.6g} = ${self.cost:.4f}{suffix}"


@dataclasses.dataclass(frozen=True)
class Estimate:
    """A complete cost estimate.

    Attributes:
        service: The service the estimate is for.
        lines: The individual charge lines.
        free_tier_applied: Whether the free tier reduced the total.
        monthly: Whether the estimate covers a month of runtime.
    """

    service: str
    lines: tuple[EstimateLine, ...]
    free_tier_applied: bool = False
    monthly: bool = False

    @property
    def total(self) -> float:
        """The total cost in USD."""
        return round(sum(line.cost for line in self.lines), 6)

    def __str__(self) -> str:
        """Render the estimate for a console.

        Returns:
            A multi-line description.
        """
        header = f"{self.service} estimate ({'monthly' if self.monthly else 'one run'})"
        body = "\n".join(f"  {line}" for line in self.lines)
        return f"{header}\n{body}\n  TOTAL: ${self.total:.4f}"


# --------------------------------------------------------------------------
# Estimators
# --------------------------------------------------------------------------


def _line(
    label: str,
    quantity: float,
    unit: str,
    unit_price: float,
    note: str = "",
) -> EstimateLine:
    """Build one estimate line.

    Args:
        label: What is being charged for.
        quantity: The unit quantity.
        unit: The unit name.
        unit_price: The price of one unit.
        note: An optional explanatory note.

    Returns:
        The estimate line.
    """
    return EstimateLine(
        label=label,
        quantity=round(quantity, 6),
        unit=unit,
        unit_price=unit_price,
        cost=round(quantity * unit_price, 6),
        note=note,
    )


def estimate(
    service: str,
    *,
    storage_gb: float = 0.0,
    storage_class: str = "standard",
    retrieval_gb: float = 0.0,
    egress_gb: float = 0.0,
    scanned_tb: float = 0.0,
    slot_hours: float = 0.0,
    vcpu_hours: float = 0.0,
    gb_months: float = 0.0,
    messages: float = 0.0,
    pubsub_gb: float = 0.0,
    requests: float = 0.0,
    cpu_seconds: float = 0.0,
    invocations: float = 0.0,
    environment_nodes: float = 0.0,
    rows: float = 0.0,
    stream_hours: float = 0.0,
    processing_units: float = 0.0,
    nodes: float = 0.0,
    node_gb: float = 0.0,
    users: float = 0.0,
    user_hours: float = 0.0,
    inspected_gb: float = 0.0,
    training_node_hours: float = 0.0,
    monthly: bool = True,
    apply_free_tier: bool = True,
) -> Estimate:
    """Estimate the cost of a workload on a GCP service.

    Only the parameters relevant to the chosen service are used; the
    others are ignored. That keeps the call sites readable — a reader
    sees exactly which knob drives which price.

    Args:
        service: The service id, e.g. ``"bigquery"``.
        storage_gb: GB stored.
        storage_class: The storage class, from :data:`STORAGE_CLASS_PRICES`.
        retrieval_gb: GB read back out of storage.
        egress_gb: GB sent out to the internet.
        scanned_tb: TB scanned by BigQuery.
        slot_hours: BigQuery slot-hours.
        vcpu_hours: vCPU-hours for Compute Engine, Dataflow, Dataproc.
        gb_months: GB-months of provisioned storage.
        messages: Number of Pub/Sub messages.
        pubsub_gb: GB of Pub/Sub message data.
        requests: Number of Cloud Run requests.
        cpu_seconds: CPU-seconds of Cloud Run or functions time.
        invocations: Function invocations.
        environment_nodes: Composer environment nodes.
        rows: Number of CDC rows processed.
        stream_hours: Datastream stream-hours.
        processing_units: Spanner processing units.
        nodes: Spanner nodes or Bigtable nodes.
        node_gb: Bigtable node-GB.
        users: Dataprep users.
        user_hours: Dataprep user-hours.
        inspected_gb: GB inspected by Sensitive Data Protection.
        training_node_hours: Vertex AI training node-hours.
        monthly: Whether the estimate covers a month.
        apply_free_tier: Whether to apply the free-tier allowance.

    Returns:
        The :class:`Estimate`.

    Raises:
        KeyError: If the service id is not recognised.
    """
    lines: list[EstimateLine] = []
    free_tier_applied = False

    if service == "cloud-storage":
        price = STORAGE_CLASS_PRICES[storage_class]
        lines.append(_line("Storage", storage_gb, "GB-month", price, storage_class))
        if retrieval_gb:
            price = STORAGE_RETRIEVAL_PRICES[storage_class]
            lines.append(_line("Retrieval", retrieval_gb, "GB", price, storage_class))
        if egress_gb:
            lines.append(_line("Network egress", egress_gb, "GB", NETWORK_EGRESS_PER_GB))
        if apply_free_tier and storage_gb:
            allowance = FREE_TIER["storage_gb_month"]
            free_tier_applied = True
            lines.append(
                _line("Free tier allowance", -min(allowance, storage_gb), "GB-month", price)
            )

    elif service == "bigquery":
        if scanned_tb:
            lines.append(
                _line("On-demand scan", scanned_tb, "TB", BIGQUERY_ONDEMAND_PER_TB)
            )
            if apply_free_tier:
                free_tier_applied = True
                lines.append(
                    _line(
                        "Free tier allowance",
                        -min(FREE_TIER["bigquery_query_tb"], scanned_tb),
                        "TB",
                        BIGQUERY_ONDEMAND_PER_TB,
                    )
                )
        if slot_hours:
            lines.append(_line("Flat-rate slots", slot_hours, "slot-hour", BIGQUERY_SLOT_HOUR))
        if storage_gb:
            lines.append(_line("Storage", storage_gb, "GB-month", 0.02))

    elif service == "compute-engine":
        lines.append(_line("Compute", vcpu_hours, "vCPU-hour", COMPUTE_ENGINE_PER_VCPU_HOUR))
        if gb_months:
            lines.append(
                _line("Disk", gb_months, "GB-month", COMPUTE_ENGINE_PER_GB_MONTH)
            )

    elif service == "kubernetes-engine":
        lines.append(_line("Cluster management", vcpu_hours, "node-hour", KUBERNETES_MANAGEMENT_FEE_HOUR))
        if gb_months:
            lines.append(_line("Node disk", gb_months, "GB-month", COMPUTE_ENGINE_PER_GB_MONTH))

    elif service == "cloud-run":
        if requests:
            lines.append(_line("Requests", requests, "request", CLOUD_RUN_PER_REQUEST))
        if cpu_seconds:
            lines.append(_line("CPU", cpu_seconds, "CPU-second", CLOUD_RUN_PER_CPU_SECOND))
        if apply_free_tier and requests:
            free_tier_applied = True
            lines.append(
                _line(
                    "Free tier allowance",
                    -min(FREE_TIER["cloud_run_requests"], requests),
                    "request",
                    CLOUD_RUN_PER_REQUEST,
                )
            )

    elif service == "cloud-functions":
        if invocations:
            lines.append(
                _line("Invocations", invocations, "invocation", CLOUD_FUNCTIONS_PER_INVOCATION)
            )
        if cpu_seconds:
            lines.append(
                _line("Compute", cpu_seconds, "GB-second", CLOUD_FUNCTIONS_PER_GB_SECOND)
            )

    elif service == "pubsub":
        if pubsub_gb:
            lines.append(_line("Ingest", pubsub_gb, "GB", PUBSUB_PER_GB_INGEST))
            if apply_free_tier:
                free_tier_applied = True
                lines.append(
                    _line(
                        "Free tier allowance",
                        -min(FREE_TIER["pubsub_gb"], pubsub_gb),
                        "GB",
                        PUBSUB_PER_GB_INGEST,
                    )
                )
        if messages:
            lines.append(_line("Delivery", messages, "message", 0.0000001))

    elif service == "dataflow":
        lines.append(_line("Compute", vcpu_hours, "vCPU-hour", DATAFLOW_PER_VCPU_HOUR))

    elif service == "dataproc":
        lines.append(_line("Compute", vcpu_hours, "vCPU-hour", DATAPROC_PER_VCPU_HOUR))

    elif service == "composer":
        lines.append(
            _line(
                "Environment", environment_nodes, "node-hour", COMPOSER_PER_ENV_NODE_HOUR
            )
        )

    elif service == "cloud-sql":
        lines.append(_line("Compute", vcpu_hours, "vCPU-hour", CLOUD_SQL_PER_VCPU_HOUR))
        if gb_months:
            lines.append(_line("Storage", gb_months, "GB-month", CLOUD_SQL_PER_GB_STORAGE))

    elif service == "cloud-spanner":
        if nodes:
            lines.append(_line("Nodes", nodes, "node-hour", SPANNER_PER_NODE_HOUR))
        if processing_units:
            lines.append(
                _line(
                    "Processing units",
                    processing_units,
                    "processing-unit-hour",
                    SPANNER_PER_PROCESSING_UNIT_HOUR,
                )
            )

    elif service == "memorystore":
        lines.append(_line("Cache", gb_months, "GB-hour", MEMORYSTORE_PER_GB_HOUR))

    elif service == "bigtable":
        lines.append(_line("Nodes", node_gb, "node-GB-hour", BIGTABLE_PER_NODE_GB_HOUR))

    elif service == "datastream":
        if rows:
            lines.append(_line("CDC processing", rows, "row", DATASTREAM_PER_CDC_ROW))
        if stream_hours:
            lines.append(_line("Streams", stream_hours, "stream-hour", DATASTREAM_PER_STREAM_HOUR))

    elif service == "dataprep":
        if user_hours:
            lines.append(_line("Dataprep", user_hours, "user-hour", DATAPREP_PER_USER_HOUR))

    elif service == "data-catalog":
        lines.append(_line("Catalog", storage_gb, "TiB", DATA_CATALOG_PER_TIB))

    elif service == "dataplex":
        lines.append(_line("Governance", storage_gb, "TiB", DATAPLEX_PER_TIB))

    elif service == "sensitive-data-protection":
        if inspected_gb:
            lines.append(
                _line("Inspection", inspected_gb, "GB", SENSITIVE_DATA_PROTECTION_PER_GB)
            )

    elif service == "vertex-ai":
        lines.append(
            _line("Training", training_node_hours, "node-hour", VERTEX_AI_TRAINING_PER_NODE_HOUR)
        )

    else:
        raise KeyError(f"no pricing model for service: {service!r}")

    if egress_gb and service != "cloud-storage":
        lines.append(_line("Network egress", egress_gb, "GB", NETWORK_EGRESS_PER_GB))

    return Estimate(
        service=service,
        lines=tuple(lines),
        free_tier_applied=free_tier_applied,
        monthly=monthly,
    )


def compare_architectures(
    scanned_tb: float = 1.0,
    *,
    partition_factor: float = 0.01,
    streaming_hours: float = 0.0,
    batch_runs: int = 1,
) -> list[tuple[str, float]]:
    """Compare the cost of the same workload in different architectures.

    This is the function the cost chapter turns into a decision table.
    It answers the question a data engineer actually asks: *does the
    partitioned, streaming version cost more than the simple batch
    version?* — and the answer is almost always "no, because the
    unpartitioned scan is so expensive".

    Args:
        scanned_tb: The TB a full unpartitioned scan would read.
        partition_factor: The fraction of the table a partitioned query
            actually reads. The default of 0.01 models a query that
            prunes to a single day out of a hundred.
        streaming_hours: Hours the streaming pipeline runs.
        batch_runs: How many times the batch pipeline runs.

    Returns:
        A list of ``(architecture, monthly_cost)`` pairs, cheapest first.
    """
    options: list[tuple[str, float]] = []

    batch_scan = estimate(
        "bigquery",
        scanned_tb=scanned_tb * batch_runs,
        monthly=False,
        apply_free_tier=False,
    )
    options.append(("Batch on BigQuery (unpartitioned)", batch_scan.total))

    partitioned_scan = estimate(
        "bigquery",
        scanned_tb=scanned_tb * partition_factor * batch_runs,
        monthly=False,
        apply_free_tier=False,
    )
    options.append(("Batch on BigQuery (partitioned)", partitioned_scan.total))

    streaming = estimate(
        "dataflow",
        vcpu_hours=streaming_hours,
        monthly=False,
        apply_free_tier=False,
    )
    options.append(("Streaming on Dataflow", streaming.total))

    spark = estimate(
        "dataproc",
        vcpu_hours=streaming_hours * 0.5,
        monthly=False,
        apply_free_tier=False,
    )
    options.append(("Spark on Dataproc", spark.total))

    return sorted(options, key=lambda pair: pair[1])


def monthly_runway(
    service: str,
    *,
    hours_per_month: float = HOURS_PER_MONTH,
    **kwargs: object,
) -> float:
    """Estimate the monthly cost of a service running continuously.

    Args:
        service: The service id.
        hours_per_month: How many hours per month the service runs.
        **kwargs: Extra parameters passed to :func:`estimate`.

    Returns:
        The monthly cost in USD.
    """
    kwargs.setdefault("monthly", True)
    kwargs.setdefault("apply_free_tier", False)
    kwargs.update({"vcpu_hours": hours_per_month})
    return estimate(service, **kwargs).total  # type: ignore[arg-type]


def format_comparison(options: Iterable[tuple[str, float]]) -> str:
    """Render an architecture comparison as a Markdown table.

    Args:
        options: The ``(architecture, cost)`` pairs.

    Returns:
        The Markdown table.
    """
    lines = ["| Architecture | Monthly cost |", "|---|---|"]
    for name, cost in options:
        lines.append(f"| {name} | ${cost:.4f} |")
    return "\n".join(lines)
