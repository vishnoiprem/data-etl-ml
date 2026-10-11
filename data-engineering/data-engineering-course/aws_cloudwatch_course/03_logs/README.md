# Section 3 — CloudWatch Logs

> 5 lectures, ~60 minutes. Log groups, streams, retention, ingestion
> costs, boto3 + moto working demo, and a Logs Insights primer.

| L# | Title | File |
|---|---|---|
| L10 | Logs 101 — Log Groups, Log Streams, Retention | `lecture_scripts/L10_logs_101.md` |
| L11 | Log Events, Timestamps, Ingestion, Storage Costs | `lecture_scripts/L11_log_events.md` |
| L12 | `create_log_group` + `put_log_events` + `filter_log_events` | `lecture_scripts/L12_boto3_logs.md` |
| L13 | CloudWatch Logs Insights — query language primer | `lecture_scripts/L13_insights.md` |
| L14 | Hands-on: `create_log_group.py` + 5 moto tests | `lecture_scripts/L14_hands_on.md` |

**Working demo:** `code/create_log_group.py` (idempotent, `--dry-run`)
+ `code/test_create_log_group.py` (5 moto tests).
