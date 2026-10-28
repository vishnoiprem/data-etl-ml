from datetime import datetime, timedelta, timezone

SLA = timedelta(hours=2)

# Collected instead of sent, so the notebook has no side effects.
NOTIFICATIONS: list[dict] = []


def notify_sla_miss(context) -> str:
    """Build and record an SLA-miss notification.

    Args:
        context: The Airflow task context (or a stand-in with the same keys).

    Returns:
        A one-line summary suitable for a log line.
    """
    payload = {
        "dag_id": context.get("dag_id", "<unknown>"),
        "task_id": context.get("task_id", "<unknown>"),
        "logical_date": str(context.get("logical_date", "<unknown>")),
        "data_interval_end": str(context.get("data_interval_end", "<unknown>")),
        "sla": str(SLA),
        "notified_at": datetime.now(timezone.utc).isoformat(),
    }
    NOTIFICATIONS.append(payload)
    # In production this is where you'd enqueue an email/Slack/pager call.
    # It must be fast and must never raise.
    return (
        f"SLA MISS dag={payload['dag_id']} task={payload['task_id']} "
        f"logical_date={payload['logical_date']}"
    )


fake_context = {
    "dag_id": "etl_to_gcs",
    "task_id": "load",
    "logical_date": "2026-01-15",
    "data_interval_end": "2026-01-16T00:00:00+00:00",
}

print(notify_sla_miss(fake_context))
print()
print("Recorded payload:")
for key, value in NOTIFICATIONS[0].items():
    print(f"  {key:<18} {value}")
