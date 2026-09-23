# SLA Monitoring + Alerting

## Problem
Define and monitor SLAs for production pipelines.

## How to Think
1. **Per-DAG SLA** – e.g., "complete by 06:00 UTC".
2. **Tiered alerts** – warn at 80% SLA, page at 100% miss.
3. **Track SLO** – 30-day hit rate as a health metric.
4. **Alert on lag** – not just failure.
5. **Correlate** misses with upstream incidents.

## How to Remember
- **"warn at 80%, page at 100%, track SLO over 30d."**
- **"Alert on lag too, not just failure."**

## Code (Airflow SLA + Alert Ladder)
```python
from datetime import timedelta

default_args = {
    "owner":  "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "sla":    timedelta(hours=4),
}

ALERT_TIERS = {
    "warn":  {"threshold_pct_sla": 80,  "channel": "#data-eng-warn", "page": False},
    "page":  {"threshold_pct_sla": 100, "channel": "pagerduty",      "page": True},
    "sev1":  {"threshold_pct_sla": 150, "channel": "pagerduty+exec", "page": True},
}
```

## SQL (SLO Hit Rate over 30 Days)
```sql
SELECT dag_id,
       COUNT(*) AS total_runs,
       SUM(CASE WHEN finished_at <= sla_deadline THEN 1 ELSE 0 END) AS hits,
       SUM(CASE WHEN finished_at <= sla_deadline THEN 1 ELSE 0 END) * 1.0
         / COUNT(*) AS slo_30d
FROM dag_run_history
WHERE start_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY dag_id
ORDER BY slo_30d ASC;
```

## Common Mistakes
- Single alert tier (warn == page == ignore).
- No SLO tracking -> misses invisibly accumulate.
- Only alerting on failure, not lag.

## AI Use Cases
- Anomaly detection on pipeline duration trends.
- Smart paging (group correlated SLA misses).
- Predictive SLA breach warnings.
