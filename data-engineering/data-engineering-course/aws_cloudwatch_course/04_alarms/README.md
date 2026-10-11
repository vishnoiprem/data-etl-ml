# Section 4 — CloudWatch Alarms

> 5 lectures, ~55 minutes. Metric alarms, threshold math, SNS actions,
> composite alarms, anomaly detection, and a complete `boto3 + moto`
> working demo.

| L# | Title | File |
|---|---|---|
| L15 | Metric Alarms 101 — OK / ALARM / INSUFFICIENT_DATA | `lecture_scripts/L15_metric_alarms_101.md` |
| L16 | Threshold types, Period, Evaluation Periods, Datapoints-to-Alarm | `lecture_scripts/L16_threshold_period.md` |
| L17 | SNS as Alarm Action — wiring the on-call pager | `lecture_scripts/L17_sns_actions.md` |
| L18 | Composite Alarms & Anomaly Detection Alarms | `lecture_scripts/L18_composite_anomaly.md` |
| L19 | Hands-on: `put_metric_alarm.py` + 5 moto tests | `lecture_scripts/L19_hands_on.md` |

**Working demo:** `code/put_metric_alarm.py` (idempotent, `--dry-run`)
+ `code/test_put_metric_alarm.py` (5 moto tests).
