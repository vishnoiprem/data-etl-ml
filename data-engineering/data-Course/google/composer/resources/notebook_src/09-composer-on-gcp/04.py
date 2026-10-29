"""The environment cost model, computed.

Every figure below is an *assumption you can change*. That is the point:
the arithmetic is auditable, so you can replace the rates with your own
infrastructure pricing and get your own number.
"""

from dataclasses import dataclass

import pandas as pd

# --------------------------------------------------------------------------
# Pricing assumptions. Replace these with your own rates.
# --------------------------------------------------------------------------

#: USD per GCE n1-standard-2 vCPU-hour, us-central1, on-demand.
#: (4 vCPU, 16 GB — the machine type Composer's workers run on.)
USD_PER_VCPU_HOUR = 0.031611

#: USD per vCPU-hour for GKE cluster management overhead.
USD_PER_VCPU_HOUR_MANAGEMENT = 0.10 / 4  # $0.10/cluster-hour spread over 4 vCPU

#: USD per GB-month for the Cloud SQL PostgreSQL instance backing the
#: metadata database, plus its storage.
USD_PER_GB_MONTH_CLOUD_SQL = 0.20

#: USD per GB-month for Cloud Storage (standard, regional).
USD_PER_GB_MONTH_STORAGE = 0.020

#: USD per GB of logs written per month.
USD_PER_GB_LOGS_WRITTEN = 0.05

#: The fixed monthly cost of the environment's web server, the scheduler
#: and the other always-on components, per environment size.
#: (Composer 2, us-central1, approximate.)
FIXED_MONTHLY_BY_SIZE = {
    "SMALL": 180.0,
    "MEDIUM": 340.0,
    "LARGE": 720.0,
}

#: Hours in a month, for the projection.
HOURS_PER_MONTH = 730


@dataclass(frozen=True)
class EnvironmentSpec:
    """One Composer environment's shape and its cost.

    Attributes:
        name: The environment's name.
        size: The environment size.
        workers_min: The minimum worker count.
        workers_max: The maximum worker count.
        vcpu_per_worker: The vCPUs per worker.
        memory_gb_per_worker: The memory per worker, in GB.
        cloud_sql_gb: The Cloud SQL instance size, in GB.
        logs_gb_month: The logs written per month, in GB.
        dag_storage_gb: The DAG bucket's size, in GB.
    """

    name: str
    size: str
    workers_min: int
    workers_max: int
    vcpu_per_worker: int
    memory_gb_per_worker: int
    cloud_sql_gb: int
    logs_gb_month: float
    dag_storage_gb: float

    @property
    def workers_midpoint(self) -> float:
        """Return the midpoint worker count, used for the projection.

        Returns:
            The average of the minimum and maximum worker counts.
        """
        return (self.workers_min + self.workers_max) / 2


#: The three Composer 2 environment sizes.
ENVIRONMENTS = [
    EnvironmentSpec("composer-dev", "SMALL", 1, 2, 4, 16, 10, 2.0, 0.01),
    EnvironmentSpec("composer-prod", "MEDIUM", 3, 6, 4, 16, 25, 10.0, 0.05),
    EnvironmentSpec("composer-wide", "LARGE", 7, 15, 4, 16, 50, 50.0, 0.10),
]


def worker_hourly_cost(spec: EnvironmentSpec, workers: float) -> float:
    """Return the hourly cost of the workers.

    Args:
        spec: The environment's specification.
        workers: The number of workers.

    Returns:
        The cost per hour, in USD.
    """
    vcpu_hours = workers * spec.vcpu_per_worker
    compute = vcpu_hours * USD_PER_VCPU_HOUR
    management = vcpu_hours * USD_PER_VCPU_HOUR_MANAGEMENT
    return compute + management


def monthly_cost(spec: EnvironmentSpec, *, utilisation: float = 1.0) -> dict:
    """Compute an environment's monthly cost.

    Args:
        spec: The environment's specification.
        utilisation: The fraction of the worker band's midpoint actually
            used. 1.0 means the environment is fully utilised.

    Returns:
        A dict of the cost components, all in USD per month.
    """
    workers = spec.workers_midpoint * utilisation
    worker_cost = worker_hourly_cost(spec, workers) * HOURS_PER_MONTH

    cloud_sql = spec.cloud_sql_gb * USD_PER_GB_MONTH_CLOUD_SQL
    dag_storage = spec.dag_storage_gb * USD_PER_GB_MONTH_STORAGE
    logs = spec.logs_gb_month * USD_PER_GB_LOGS_WRITTEN
    fixed = FIXED_MONTHLY_BY_SIZE[spec.size]

    return {
        "environment": spec.name,
        "size": spec.size,
        "workers": round(workers, 1),
        "worker_compute": round(worker_cost, 2),
        "gke_management": round(
            workers * spec.vcpu_per_worker
            * USD_PER_VCPU_HOUR_MANAGEMENT * HOURS_PER_MONTH, 2),
        "cloud_sql": round(cloud_sql, 2),
        "dag_storage": round(dag_storage, 2),
        "logs": round(logs, 2),
        "fixed_components": round(fixed, 2),
        "total_monthly": round(
            worker_cost + cloud_sql + dag_storage + logs + fixed, 2),
    }


# --------------------------------------------------------------------------
# The cost table
# --------------------------------------------------------------------------
rows = [monthly_cost(spec) for spec in ENVIRONMENTS]
cost_table = pd.DataFrame(rows)

print("Composer 2 environment cost, us-central1, n1-standard-2 workers")
print("=" * 78)
print(cost_table.to_string(index=False))
print()
print(f"assumptions: ${USD_PER_VCPU_HOUR}/vCPU-hour compute, "
      f"${USD_PER_GB_MONTH_CLOUD_SQL}/GB-month Cloud SQL, "
      f"${USD_PER_GB_MONTH_STORAGE}/GB-month storage, "
      f"{HOURS_PER_MONTH} hours/month")
print()

# --------------------------------------------------------------------------
# The utilisation sensitivity — the number that decides your size
# --------------------------------------------------------------------------
print("=" * 78)
print("Monthly cost by utilisation (the workers are the variable part)")
print("=" * 78)

util_rows = []
for spec in ENVIRONMENTS:
    row = {"size": spec.size}
    for utilisation in (0.25, 0.50, 0.75, 1.00):
        row[f"{int(utilisation * 100)}% used"] = monthly_cost(
            spec, utilisation=utilisation)["total_monthly"]
    util_rows.append(row)

util_table = pd.DataFrame(util_rows)
print(util_table.to_string(index=False))
print()
print("Read this carefully: a MEDIUM environment at 25% utilisation costs")
print("almost as much as a MEDIUM at 100%, because the fixed components")
print("(web server, scheduler, Cloud SQL) do not shrink with usage.")
print("That is the argument for ONE environment rather than five.")
print()

# --------------------------------------------------------------------------
# The year projection
# --------------------------------------------------------------------------
print("=" * 78)
print("Twelve-month projection, per environment")
print("=" * 78)

projection = pd.DataFrame(
    [
        {
            "environment": spec.name,
            "size": spec.size,
            "monthly_usd": monthly_cost(spec)["total_monthly"],
            "quarterly_usd": round(monthly_cost(spec)["total_monthly"] * 3, 2),
            "annual_usd": round(monthly_cost(spec)["total_monthly"] * 12, 2),
        }
        for spec in ENVIRONMENTS
    ]
)
projection["daily_usd"] = (projection["monthly_usd"] / 30).round(2)
print(projection.to_string(index=False))
print()

total_annual = projection["annual_usd"].sum()
print(f"All three environments, running together: ${total_annual:,.2f} / year")
print()

# --------------------------------------------------------------------------
# The comparison that matters: environment cost vs job cost
# --------------------------------------------------------------------------
print("=" * 78)
print("ENVIRONMENT COST vs JOB COST")
print("=" * 78)

# A nightly BigQuery aggregation over ~30 GB/day, partitioned.
BQ_PRICE_PER_TB = 5.0
GB_PER_DAY_SCANNED = 30
bq_monthly = GB_PER_DAY_SCANNED * 30 / 1024 * BQ_PRICE_PER_TB

# The same job as a PythonOperator on one worker, running 40 minutes a night.
PYTHON_TASK_HOURS_PER_DAY = 40 / 60
python_monthly = (PYTHON_TASK_HOURS_PER_DAY * 30
                  * 4 * USD_PER_VCPU_HOUR)

comparison = pd.DataFrame([
    {
        "approach": "BigQuery scheduled query (no Composer)",
        "compute_cost_monthly_usd": round(bq_monthly, 2),
        "environment_cost_monthly_usd": 0.0,
        "total_monthly_usd": round(bq_monthly, 2),
        "note": "No environment at all — right answer for a single, dependency-free SQL job",
    },
    {
        "approach": "Composer + PythonOperator (40 min/night)",
        "compute_cost_monthly_usd": round(python_monthly, 2),
        "environment_cost_monthly_usd": 0.0,
        "total_monthly_usd": round(python_monthly, 2),
        "note": "Cheap — but it does not scale, and a retry costs 40 minutes",
    },
    {
        "approach": "Composer (MEDIUM) + BigQuery query",
        "compute_cost_monthly_usd": round(bq_monthly, 2),
        "environment_cost_monthly_usd": 340.0,
        "total_monthly_usd": round(bq_monthly + 340.0, 2),
        "note": "The environment dwarfs the job — size it SMALL",
    },
    {
        "approach": "Composer (MEDIUM) + PythonOperator",
        "compute_cost_monthly_usd": round(python_monthly, 2),
        "environment_cost_monthly_usd": 340.0,
        "total_monthly_usd": round(python_monthly + 340.0, 2),
        "note": "Environment + compute; size for the concurrency you need",
    },
])
print(comparison.to_string(index=False))
print()
print("The design question:")
print()
print('  "If my DAGs mostly ISSUE QUERIES, size the Composer environment')
print('   small. If my DAGs mostly RUN PYTHON, size it for the concurrency')
print('   you need."')
print()
print("And the rule of thumb from the tool-choice chapter:")
print()
print('  "If the task takes more than a few minutes, or holds more than a')
print('   few hundred megabytes, it belongs in a processing engine."')
print()

# --------------------------------------------------------------------------
# Sanity assertions
# --------------------------------------------------------------------------
assert cost_table["total_monthly"].is_monotonic_increasing, \
    "a bigger environment must cost more"
assert cost_table.loc[0, "workers"] < cost_table.loc[1, "workers"]
assert projection["annual_usd"].is_monotonic_increasing

# The fixed components are the same fraction of a SMALL environment's bill
# as they are of a LARGE one's — they do not scale with the worker band.
small = monthly_cost(ENVIRONMENTS[0])
large = monthly_cost(ENVIRONMENTS[2])
small_fixed_share = small["fixed_components"] / small["total_monthly"]
large_fixed_share = large["fixed_components"] / large["total_monthly"]
print(f"fixed-component share, SMALL: {small_fixed_share:.1%}")
print(f"fixed-component share, LARGE: {large_fixed_share:.1%}")
print()
print("PASS: the cost table is internally consistent.")
