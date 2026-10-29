"""The validator, exercised against environments that are wrong.

Each of these is a mistake that costs real money or real debugging time,
and every one of them is caught *before* the environment is created.
"""

from dataclasses import replace


def show(title, env):
    """Validate an environment and print the problems.

    Args:
        title: A short description of the scenario.
        env: The environment to validate.
    """
    print(f"--- {title} " + "-" * max(0, 60 - len(title)))
    problems = env.validate()
    if not problems:
        print("    no problems")
    for problem in problems:
        print(f"    ! {problem}")
    print()


# ---------------------------------------------------------------------
# 1. The DAG bucket and the log bucket are the same bucket
# ---------------------------------------------------------------------
show("the same bucket for DAGs and logs", replace(
    ENV,
    log_bucket="gs://YOUR_PROJECT_ID-dags",
))

# ---------------------------------------------------------------------
# 2. A bucket in another region
# ---------------------------------------------------------------------
show("the log bucket in another region", replace(
    ENV,
    bucket_regions={
        "gs://YOUR_PROJECT_ID-dags": "europe-west1",
        "gs://YOUR_PROJECT_ID-logs": "us-central1",
    },
))

# ---------------------------------------------------------------------
# 3. A private web server with no subnet
# ---------------------------------------------------------------------
show("a network with no subnetwork", replace(
    ENV,
    subnetwork="",
))

# ---------------------------------------------------------------------
# 4. No explicit timezone
# ---------------------------------------------------------------------
no_tz_vars = {k: v for k, v in ENV.env_vars.items()
              if k != "AIRFLOW__CORE__DEFAULT_TIMEZONE"}
show("no AIRFLOW__CORE__DEFAULT_TIMEZONE", replace(
    ENV,
    env_vars=no_tz_vars,
))

# ---------------------------------------------------------------------
# 5. Log retention set to a year
# ---------------------------------------------------------------------
show("a year of log retention", replace(
    ENV,
    log_retention_days=365,
))

# ---------------------------------------------------------------------
# 6. Composer 3 on a SMALL environment
# ---------------------------------------------------------------------
show("Composer 3 with a SMALL environment", replace(
    ENV,
    generation="composer-3",
    size="SMALL",
))

# ---------------------------------------------------------------------
# 7. A service account that is not an email address
# ---------------------------------------------------------------------
show("a service account that is not an email", replace(
    ENV,
    service_account="composer-sa",
))

print("=" * 78)
print("What the validator is for")
print("=" * 78)
print()
print("Every one of the seven problems above is:")
print()
print("  * invisible in the `gcloud` command's own validation,")
print("  * a real cost or a real outage once the environment exists, and")
print("  * free to catch before you create anything.")
print()
print("This is the argument for describing an environment as data. A")
print("description can be reviewed, diffed, tested and rendered into a")
print("command. A YAML file you typed by hand can only be eyeballed.")

# ---------------------------------------------------------------------
# The comparison table, from the model
# ---------------------------------------------------------------------
print()
print("=" * 78)
print("Composer 2 vs Composer 3, computed from the model")
print("=" * 78)
print()

for generation in ("composer-2", "composer-3"):
    env = replace(ENV, generation=generation, size="MEDIUM")
    info = env.version_info
    print(f"  {generation}")
    print(f"    executor         : {info['executor']}")
    print(f"    Airflow version  : {info['airflow_version']}")
    print(f"    image version    : {info['image_version']}")
    print(f"    task startup     : {info['task_startup_seconds']}s")
    print(f"    workers          : {env.workers_min}-{env.workers_max}")
    print(f"    parallelism      : {env.parallelism}")
    print()

# --- the startup tax, measured against the course's DAGs ---------------
print("=" * 78)
print("THE STARTUP TAX, against the course's DAGs")
print("=" * 78)
print()

from local_runner import DAGS  # noqa: E402

POD_STARTUP = COMPOSER_GENERATIONS["composer-3"]["task_startup_seconds"]
CELERY_DISPATCH = COMPOSER_GENERATIONS["composer-2"]["task_startup_seconds"]
# The course's pure compute, measured in milliseconds.
TASK_WORK_SECONDS = 0.02

print(f"{'dag':<18} {'tasks':>6} {'celery wall':>12} {'k8s wall':>10} "
      f"{'k8s overhead':>13}")
print("-" * 72)
for name in sorted(DAGS):
    dag = DAGS[name]()
    n = len(dag.tasks)
    celery = n * (CELERY_DISPATCH + TASK_WORK_SECONDS)
    k8s = n * (POD_STARTUP + TASK_WORK_SECONDS)
    overhead = (k8s - celery) / celery * 100
    print(f"{name:<18} {n:>6} {celery:>11.2f}s {k8s:>9.2f}s "
          f"{overhead:>12.0f}%")

print()
print("Every course DAG is a chain — at most one task is ever ready at a")
print("time — so the pod startup is paid *sequentially*.")
print()
print("The KubernetesExecutor is right for heavy tasks and wrong for")
print("chatty ones. These DAGs are the latter.")
print()

# --- the crossover ----------------------------------------------------
print("Crossover: the task duration at which the 45s pod tax is < 10% "
      "of the total.")
crossover = POD_STARTUP / 0.10 - POD_STARTUP
print(f"  pod startup {POD_STARTUP}s -> crossover at "
      f"{crossover / 60:.1f} minutes of task duration")
print()

# --- the environment's own startup cost --------------------------------
print("=" * 78)
print("What the choice costs the ENVIRONMENT, per task")
print("=" * 78)
print()
for generation in ("composer-2", "composer-3"):
    env = replace(ENV, generation=generation)
    startup = env.version_info["task_startup_seconds"]
    print(f"  {generation:<12} {env.executor:<20} "
          f"{startup:>3}s per task, "
          f"{env.workers_min}-{env.workers_max} workers")
print()
print("Rule: use Composer 3 when tasks need their own resources or their")
print("own images AND take more than ~8 minutes. Otherwise stay on 2.")
