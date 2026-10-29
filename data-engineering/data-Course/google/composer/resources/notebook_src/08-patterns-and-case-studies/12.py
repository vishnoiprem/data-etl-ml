"""Model the three cross-DAG mechanisms, executably.

  * `TriggerDagRunOperator` — push. The parent *creates* the child's run.
  * `ExternalTaskSensor`    — pull. The child *polls* for the parent's run.
  * `Dataset`              — declarative. The producer *records an update*,
                              and every consumer of that URI is queued.

The mini-runner has none of these, so we model the *semantics*: what gets
created, what gets observed, and what happens when the producer never
runs.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class DagRunRecord:
    """A record of one DAG run, in the metadata database.

    Attributes:
        dag_id: The DAG's identifier.
        run_id: The run's identifier.
        logical_date: The run's logical date.
        state: The run's state.
        conf: The config passed to the run.
    """

    dag_id: str
    run_id: str
    logical_date: str
    state: str = "queued"
    conf: dict[str, Any] = field(default_factory=dict)

    def as_json(self):
        """Render the record the way `dag_run.conf` would be stored.

        Returns:
            A JSON document.
        """
        return json.dumps(self.conf, sort_keys=True)


class MetadataDb:
    """A tiny stand-in for Airflow's metadata database.

    It stores DAG runs and dataset update events, which is all the three
    cross-DAG mechanisms need.

    Attributes:
        runs: The DAG runs, keyed by ``(dag_id, logical_date)``.
        dataset_events: The dataset update events, keyed by dataset URI.
    """

    def __init__(self) -> None:
        self.runs: dict[tuple[str, str], DagRunRecord] = {}
        self.dataset_events: dict[str, list[dict[str, Any]]] = {}

    def create_run(self, dag_id, logical_date, conf=None):
        """Create a DAG run — what `TriggerDagRunOperator` does.

        Args:
            dag_id: The DAG to run.
            logical_date: The run's logical date.
            conf: The config for the run.

        Returns:
            The run record.

        Raises:
            ValueError: When a run already exists for that logical date.
        """
        key = (dag_id, logical_date)
        if key in self.runs:
            raise ValueError(f"run already exists for {dag_id} @ {logical_date}")
        run_id = f"manual__{logical_date}T00:00:00+00:00"
        record = DagRunRecord(dag_id, run_id, logical_date, conf=dict(conf or {}))
        self.runs[key] = record
        return record

    def reset_run(self, dag_id, logical_date, conf=None):
        """Create a run, clearing any existing one — `reset_dag_run=True`.

        Args:
            dag_id: The DAG to run.
            logical_date: The run's logical date.
            conf: The config for the run.

        Returns:
            The run record.
        """
        key = (dag_id, logical_date)
        if key in self.runs:
            del self.runs[key]
        return self.create_run(dag_id, logical_date, conf)

    def find_run(self, dag_id, logical_date):
        """Find a run — what `ExternalTaskSensor` polls for.

        Args:
            dag_id: The DAG to look for.
            logical_date: The logical date to look for.

        Returns:
            The run record, or None when there is no such run.
        """
        return self.runs.get((dag_id, logical_date))

    def record_dataset_update(self, uri, *, producer_dag_id, logical_date, extra=None):
        """Record a dataset update — what a task with `outlets` does.

        Args:
            uri: The dataset URI.
            producer_dag_id: The DAG that produced the update.
            logical_date: The producer's logical date.
            extra: Optional event metadata (Airflow 2.9+ `Metadata.extra`).

        Returns:
            The recorded event.
        """
        event = {
            "uri": uri,
            "producer_dag_id": producer_dag_id,
            "producer_logical_date": logical_date,
            "extra": dict(extra or {}),
        }
        self.dataset_events.setdefault(uri, []).append(event)
        return event

    def consumers_for(self, uri):
        """Return the update events for a dataset URI.

        Args:
            uri: The dataset URI.

        Returns:
            The list of events, oldest first.
        """
        return list(self.dataset_events.get(uri, []))


#: The dataset URI shared by the producer and the consumer.
ORDERS_DATASET_URI = "gs://YOUR_BUCKET/datasets/orders"


def trigger_dag_run(db, *, trigger_dag_id, logical_date, conf=None,
                    reset_dag_run=False, wait_for_completion=False):
    """Model `TriggerDagRunOperator`.

    Args:
        db: The metadata database.
        trigger_dag_id: The DAG to trigger.
        logical_date: The logical date to trigger for.
        conf: The config to pass. Must be JSON-serialisable.
        reset_dag_run: Whether to clear an existing run.
        wait_for_completion: Whether the parent blocks.

    Returns:
        A dict describing what happened.

    Raises:
        TypeError: When the conf is not JSON-serialisable.
    """
    # Airflow serialises the conf when it stores it — so a datetime in the
    # conf is a TypeError at trigger time, not at task time.
    json.dumps(conf or {})

    if reset_dag_run:
        record = db.reset_run(trigger_dag_id, logical_date, conf)
    else:
        record = db.create_run(trigger_dag_id, logical_date, conf)

    return {
        "triggered": record.dag_id,
        "run_id": record.run_id,
        "conf": record.as_json(),
        "parent_slot_held": bool(wait_for_completion),
    }


def external_task_sensor_poll(db, *, external_dag_id, logical_date,
                              execution_delta_hours=0):
    """Model `ExternalTaskSensor` — one poll of the metadata database.

    Args:
        db: The metadata database.
        external_dag_id: The DAG being waited on.
        logical_date: The logical date being waited for.
        execution_delta_hours: How far apart the two runs' dates are.

    Returns:
        A dict with the poll result.
    """
    target = datetime.strptime(logical_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc)
    target = target - timedelta(hours=execution_delta_hours)
    target_date = target.date().isoformat()

    record = db.find_run(external_dag_id, target_date)
    return {
        "external_dag_id": external_dag_id,
        "looked_for": target_date,
        "found": record is not None,
        "state": record.state if record else None,
    }


def dataset_consumer_queue(db, *, uri, consumer_dag_id):
    """Model a Dataset consumer being queued by an update.

    Args:
        db: The metadata database.
        uri: The dataset URI.
        consumer_dag_id: The consuming DAG.

    Returns:
        A dict describing the queued run.
    """
    events = db.consumers_for(uri)
    if not events:
        return {"queued": False, "reason": "no dataset update recorded"}
    latest = events[-1]
    # A dataset-triggered run gets its OWN logical date — the time it was
    # queued — not the producer's. The producer's date travels in the
    # event metadata instead.
    run = db.create_run(
        consumer_dag_id,
        latest["producer_logical_date"],
        conf={"producer_logical_date": latest["producer_logical_date"]},
    )
    return {
        "queued": True,
        "consumer": consumer_dag_id,
        "run_id": run.run_id,
        "producer_logical_date": latest["producer_logical_date"],
        "event_extra": latest["extra"],
    }


# ---------------------------------------------------------------------
# Exercise the three mechanisms
# ---------------------------------------------------------------------
db = MetadataDb()

print("=" * 70)
print("1. TriggerDagRunOperator — push")
print("=" * 70)
result = trigger_dag_run(
    db,
    trigger_dag_id="orders_ingest",
    logical_date="2026-01-15",
    conf={"parent_run_id": "scheduled__2026-01-15", "source": "gcs"},
)
print(f"  triggered  : {result['triggered']}")
print(f"  run_id     : {result['run_id']}")
print(f"  conf stored: {result['conf']}")
print(f"  parent slot held: {result['parent_slot_held']}")
print()

# A second trigger for the same date fails without reset_dag_run.
try:
    trigger_dag_run(db, trigger_dag_id="orders_ingest",
                    logical_date="2026-01-15")
except ValueError as exc:
    print(f"  second trigger without reset_dag_run -> {type(exc).__name__}: {exc}")

reset = trigger_dag_run(db, trigger_dag_id="orders_ingest",
                        logical_date="2026-01-15", reset_dag_run=True)
print(f"  with reset_dag_run=True -> {reset['run_id']} (recreated)")
print()

# A non-serialisable conf is rejected at trigger time.
try:
    trigger_dag_run(db, trigger_dag_id="orders_ingest",
                    logical_date="2026-01-16",
                    conf={"when": datetime(2026, 1, 15)})
except TypeError as exc:
    print(f"  non-JSON conf -> {type(exc).__name__}: {exc}")
print()

print("=" * 70)
print("2. ExternalTaskSensor — pull")
print("=" * 70)
poll = external_task_sensor_poll(db, external_dag_id="orders_ingest",
                                 logical_date="2026-01-15")
print(f"  poll 1: {poll}")
# Mark it complete, then poll again.
db.runs[("orders_ingest", "2026-01-15")].state = "success"
poll = external_task_sensor_poll(db, external_dag_id="orders_ingest",
                                 logical_date="2026-01-15")
print(f"  poll 2: {poll}")
# A date that was never run: the sensor would keep polling until it timed out.
poll = external_task_sensor_poll(db, external_dag_id="orders_ingest",
                                 logical_date="2026-01-14")
print(f"  poll for a date that never ran: {poll}")
print("  -> the sensor would keep polling until its timeout fired.")
print()

print("=" * 70)
print("3. Dataset — declarative")
print("=" * 70)
event = db.record_dataset_update(
    ORDERS_DATASET_URI,
    producer_dag_id="orders_ingest",
    logical_date="2026-01-15",
    extra={"logical_date": "2026-01-15", "row_count": 1245},
)
print(f"  update recorded: {event['uri']}")
print(f"  producer date  : {event['producer_logical_date']}")
print(f"  event metadata : {event['extra']}")
print()

queued = dataset_consumer_queue(db, uri=ORDERS_DATASET_URI,
                                consumer_dag_id="consume_orders")
print(f"  consumer queued: {queued['queued']}")
print(f"  producer date carried through: {queued['producer_logical_date']}")
print(f"  event metadata available      : {queued['event_extra']}")
print()

# --- the gap: a dataset cannot time out -------------------------------
print("  Scenario: the producer never runs.")
no_update = db.consumers_for("gs://YOUR_BUCKET/datasets/never_updated")
print(f"  dataset updates recorded: {len(no_update)}")
print("  -> the consumer simply never runs, and nothing reports it.")
print("     A Dataset cannot time out. This needs a monitoring check.")
