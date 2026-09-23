"""
Problem 05: SLA monitoring + alerting.

Meta flavor: Each pipeline has an SLA. Misses page the on-call.

How to Think:
- Define SLAs per DAG (e.g., "complete by 06:00 UTC").
- Tiered alerting: warn at 80% SLA, page at 100% miss.
- Track SLA miss rate as a SLO metric.
- Auto-correlate SLA misses with upstream incidents.

How to Remember:
- "warn at 80%, page at 100%, track SLO over 30d."
- "Alert on lag, not just failure."

AI Use Cases:
- Anomaly detection on pipeline duration.
- Smart paging (group correlated SLA misses).
- Predictive SLA breach warnings.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta

default_args = {
    "owner":  "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "sla":    timedelta(hours=4),
}

# Alert ladder (Tiered)
ALERT_TIERS = {
    "warn":  {"threshold_pct_sla": 80,  "channel": "#data-eng-warn",  "page": False},
    "page":  {"threshold_pct_sla": 100, "channel": "pagerduty",       "page": True},
    "sev1":  {"threshold_pct_sla": 150, "channel": "pagerduty+exec",  "page": True},
}

def alert(dag_id, ds, tier, msg):
    """Send alert. In real code, integrate with PagerDuty/Slack."""
    t = ALERT_TIERS[tier]
    print(f"[{tier.upper()}] {dag_id} {ds}: {msg} -> {t['channel']}")

# SLO tracking query (Presto)
SQL_SLO = """
SELECT
  dag_id,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN finished_at <= sla_deadline THEN 1 ELSE 0 END) AS hits,
  SUM(CASE WHEN finished_at >  sla_deadline THEN 1 ELSE 0 END) AS misses,
  SUM(CASE WHEN finished_at <= sla_deadline THEN 1 ELSE 0 END) * 1.0
    / COUNT(*) AS slo_30d
FROM dag_run_history
WHERE start_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY dag_id
ORDER BY slo_30d ASC;
"""
