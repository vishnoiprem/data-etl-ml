"""The 'wait for data' pattern, built on project/core/sensor_conditions.py.

The sensor's *condition* is pure and unit-tested. The sensor's *loop* is
Airflow's job: it re-evaluates the condition every `poke_interval` until
it returns True or the timeout fires.
"""

from local_runner import DAG, Task

#: The pure readiness condition.
from sensor_conditions import source_is_ready


def sensor_poll(run, context):
    """Simulate one poke of the sensor loop.

    A sensor does not block. It is re-evaluated on a schedule until the
    condition is true. This function performs one evaluation and records
    the outcome, so the loop can be inspected.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A dict describing the poll.
    """
    lines = run.pull("read_orders") or []
    expected_rows = int(context["params"].get("expected_rows", 0))
    reject_threshold = int(context["params"].get("reject_threshold", 0))
    ready = source_is_ready(lines, expected_rows=expected_rows,
                            reject_threshold=reject_threshold)
    attempts = int(run.pull("sensor_poll", "attempts") or 0) + 1
    run.xcom.push("sensor_poll", "attempts", attempts)
    return {"attempt": attempts, "ready": ready}


def process_when_ready(run, context):
    """The work that runs once the data is ready.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of the work done.
    """
    return "processed"


def build_wait_dag():
    """Build the wait-for-data DAG.

    Returns:
        The DAG.
    """
    return DAG(
        "patterns_wait_for_data",
        tasks=[
            Task("read_orders", read_orders),
            Task("sensor_poll", sensor_poll, dependencies=["read_orders"]),
            Task("process", process_when_ready, dependencies=["sensor_poll"]),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Wait for the source data, then process it.",
    )


WAIT_DAG = build_wait_dag()
print(WAIT_DAG.describe())
print()

# ---------------------------------------------------------------------
# The condition, exercised against real data
# ---------------------------------------------------------------------
from sensor_conditions import source_is_ready  # noqa: E402

CLEAN = (COURSE_ROOT / "sample_data" / "orders.csv").read_text(
    encoding="utf-8").splitlines()
MALFORMED = (COURSE_ROOT / "sample_data" / "malformed_orders.csv").read_text(
    encoding="utf-8").splitlines()

print("The pure condition, `source_is_ready`, against real data:")
print()

cases = [
    ("no expectations, clean data", CLEAN, 0, 0),
    ("expect 1000 rows, clean data", CLEAN, 1000, 0),
    ("expect 100000 rows, clean data", CLEAN, 100_000, 0),
    ("no expectations, malformed data", MALFORMED, 0, 0),
    ("expect 1000 rows, malformed data", MALFORMED, 1000, 0),
    ("tolerate 8 rejects, malformed data", MALFORMED, 0, 8),
]

for label, lines, expected, threshold in cases:
    ready = source_is_ready(lines, expected_rows=expected,
                            reject_threshold=threshold)
    print(f"  {label:<38} expected_rows={expected:<7} "
          f"reject_threshold={threshold:<3} -> ready={ready}")

print()
print("Read the table as the sensor's decision rule:")
print("  * too few accepted rows  -> not ready")
print("  * too many rejected rows -> not ready")
print("  * otherwise              -> ready")
print()

# The three cases the sensor's timeout would fire on.
assert source_is_ready(CLEAN, expected_rows=1000, reject_threshold=0) is True
assert source_is_ready(CLEAN, expected_rows=100_000, reject_threshold=0) is False
assert source_is_ready(MALFORMED, expected_rows=0, reject_threshold=0) is False
assert source_is_ready(MALFORMED, expected_rows=0, reject_threshold=8) is True

print("PASS: the condition behaves as documented.")
print()

# ---------------------------------------------------------------------
# Run the wait-for-data DAG
# ---------------------------------------------------------------------
from local_runner import run_dag  # noqa: E402

print("=" * 70)
print("WAIT FOR DATA: the sensor fires immediately")
print("=" * 70)
run = run_dag(WAIT_DAG, "2026-01-15",
              params={"expected_rows": 1000, "reject_threshold": 0},
              verbose=True)
assert run.state["sensor_poll"] == "success", run.state
assert run.state["process"] == "success", run.state
print("PASS: the sensor succeeded and the work ran.")
print()

print("=" * 70)
print("WAIT FOR DATA: the sensor never fires")
print("=" * 70)
timeout_run = run_dag(WAIT_DAG, "2026-01-15",
                      params={"expected_rows": 100_000, "reject_threshold": 0},
                      verbose=True)
poll = timeout_run.pull("sensor_poll")
print(f"poll outcome: {poll}")
print()
print("The condition returned False — the data was not ready.")
print()
print("In Airflow the difference is what happens NEXT: a `PythonSensor`")
print("re-raises the poke, so the task stays in the running state and is")
print("re-evaluated every `poke_interval` until the timeout expires, at")
print("which point it fails with:")
print("    airflow.exceptions.SensorTimeout: ...")
print("The mini-runner has no poke loop, so it simply records the False")
print("and finishes. The important part is the DECISION: the condition")
print("said 'not ready', and the pipeline had no business proceeding.")
print("Better a failed run than a run that processed half a file.")
