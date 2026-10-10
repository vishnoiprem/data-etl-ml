# Section 2 — CloudWatch Metrics

> 5 lectures, ~60 minutes. The deepest dive of the course: namespaces,
> dimensions, standard vs. high-resolution, statistics, percentiles, and
> a complete `boto3` + `moto` working demo.

| L# | Title | File |
|---|---|---|
| L05 | Metrics 101 — Namespaces, Metric Names, Dimensions | `lecture_scripts/L05_metrics_101.md` |
| L06 | Standard vs. High-Resolution Metrics, Storage Resolution | `lecture_scripts/L06_resolution.md` |
| L07 | Statistics: Average, Sum, Min, Max, p99, Percentile | `lecture_scripts/L07_statistics.md` |
| L08 | `put_metric_data` + `get_metric_data` with boto3 | `lecture_scripts/L08_put_metric_data.md` |
| L09 | Hands-on: `put_metric_data.py` + 5 moto tests | `lecture_scripts/L09_hands_on.md` |

**Working demo:** `code/put_metric_data.py` (idempotent, `--dry-run`) +
`code/test_put_metric_data.py` (5 moto tests).
