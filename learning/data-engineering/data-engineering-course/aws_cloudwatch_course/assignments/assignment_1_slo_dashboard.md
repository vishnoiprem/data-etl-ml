# Assignment 1 — SLO Dashboard with Burn-Rate Alerts

> **Section:** 7 — Real-World Patterns
> **Estimated time:** 6–8 hours
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

## Goal

Build an **end-to-end SLO monitoring solution** for a synthetic
web-service API. You will:

1. Define an **SLI** (Service Level Indicator) — `availability` measured
   as `1 - (5xx / total_requests)`.
2. Define an **SLO** — `99.9% availability over 30 days` (≈ 43 minutes of
   allowed downtime).
3. Use CloudWatch **metric math** to compute the error budget.
4. Build a **CloudWatch Dashboard** that visualizes:
   - The SLI value (number widget)
   - 1h and 6h burn rates (line widgets)
   - A Logs Insights table of recent 5xx events.
5. Author **two composite alarms** that page on-call when:
   - The 1h burn rate exceeds 14.4× the SLO budget *for 5 minutes*
   - The 6h burn rate exceeds 6× the SLO budget *for 30 minutes*
   (the canonical Google SRE workbook fast-burn / slow-burn pair).

## Deliverables

1. A Python module `slo_dashboard/build.py` that creates the dashboard and
   alarms (idempotent, `--dry-run`).
2. A `metric_filters` config JSON (or YAML) listing the 5xx error filter
   pattern.
3. A `pytest` suite (≥ 5 moto tests) covering:
   - The 5xx metric filter is created with the right pattern.
   - The dashboard is created with the right body.
   - Both fast-burn and slow-burn alarms exist with the right thresholds.
   - The composite alarm references both.
   - The script is idempotent (run twice, no duplicates).
4. A 1-page `report.md` showing the burn-rate formulas you used and a
   screenshot / description of the rendered dashboard.

## Burn-rate math (use these numbers in your alarms)

Given SLO = 99.9% and window = 30d:

- `error_budget = (1 - 0.999) × 30 × 24 × 60 = 43.2 minutes`
- `fast_burn_threshold = 14.4 × error_budget / 1h`  → consumes entire
  monthly budget in 2 days if it stays at this rate
- `slow_burn_threshold = 6 × error_budget / 6h`    → consumes entire
  monthly budget in 5 days if it stays at this rate

## Suggested file layout

```
slo_dashboard/
├── README.md
├── build.py
├── config.yaml
├── test_build.py
└── report.md
```

## Grading rubric

| Area | Weight |
|---|---|
| Correct burn-rate math | 25% |
| Dashboard JSON valid + visualised | 25% |
| Idempotent `boto3` code with `--dry-run` | 20% |
| 5+ passing moto tests | 20% |
| `report.md` clarity | 10% |

## Stretch goals (optional)

- Add an **anomaly detection** band on the SLI line for additional signal.
- Add a **second SLO** (latency: p99 < 500 ms) to the same dashboard.
- Wire the composite alarm to an **SNS topic** whose email subscription
  is confirmed.

## Reference

- The Google SRE workbook, chapter 5: *Alerting on SLOs*.
- The course lecture `07_real_world/lecture_scripts/L30_slo_sli.md`.
