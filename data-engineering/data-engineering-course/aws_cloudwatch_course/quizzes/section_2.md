# Section 2 Quiz — Metrics

> 10 questions, multi-choice, single answer.

---

**Q1.** Which three things uniquely identify a CloudWatch metric time-series?

- A. Region, account, ARN
- B. Namespace, metric name, dimensions
- C. Tag, label, value
- D. Period, statistic, unit

<details><summary>Show answer</summary>

**B — Namespace, metric name, dimensions.** Any change in any of these three creates a different time-series. Tags and labels are not part of the identity.

</details>

---

**Q2.** What's the default storage resolution of `put_metric_data`?

- A. 1 second
- B. 10 seconds
- C. 60 seconds
- D. 300 seconds

<details><summary>Show answer</summary>

**C — 60 seconds.** Standard resolution. Set `StorageResolution=1` to opt in to high-resolution (1 sec), which costs 3× as much per datapoint.

</details>

---

**Q3.** How much does high-resolution metric data cost vs. standard?

- A. Same cost
- B. 1.5×
- C. 3×
- D. 10×

<details><summary>Show answer</summary>

**C — 3×.** Standard is $0.01 / 1,000 datapoints; high-res is $0.03 / 1,000 datapoints.

</details>

---

**Q4.** Which statistic is *most* appropriate for an "API is fast" SLI?

- A. `Average`
- B. `Sum`
- C. `SampleCount`
- D. `p99`

<details><summary>Show answer</summary>

**D — p99.** Average hides slow-tail effects; p99 (the 99th percentile latency) is the canonical "worst-case most users see" statistic. Sum is right for *counts* (requests, errors), not latency.

</details>

---

**Q5.** Which statistic is right for an "any 5xx in last 5 min" alarm?

- A. `Average`
- B. `Sum`
- C. `Maximum`
- D. `p99`

<details><summary>Show answer</summary>

**B — Sum.** You want the total count of error events in the window, not the average or the worst single datapoint. With `Sum`, one bad request is enough to fire.

</details>

---

**Q6.** Does CloudWatch metric math add a billable custom metric?

- A. Yes, always
- B. Yes, if you use the math expression in an alarm
- C. No, math is computed in-flight and not stored
- D. Only if you call `get_metric_data`

<details><summary>Show answer</summary>

**C — No.** Metric math is computed in-flight by the query engine. The result is not stored as a custom metric and is not billable as one. This makes math the right tool for derived signals like error rate and burn rate.

</details>

---

**Q7.** What's the max number of datapoints per `put_metric_data` call?

- A. 100
- B. 500
- C. 1,000
- D. 10,000

<details><summary>Show answer</summary>

**C — 1,000.** Batch accordingly; the SDK will raise `ValidationError` if you exceed it. The same call can mix different metric names.

</details>

---

**Q8.** How long are metrics kept at full 1-min resolution?

- A. 3 days
- B. 7 days
- C. 15 days
- D. 365 days

<details><summary>Show answer</summary>

**C — 15 days.** After that, CloudWatch aggregates to 5-min for 63 days, then 1-hour for 455 days. You pay the *storage* only once.

</details>

---

**Q9.** What is `StatisticValues` used for in `put_metric_data`?

- A. Selecting the statistic in a query
- B. Publishing min/max/sum/sample-count for a period
- C. Filtering by unit
- D. Anomaly detection

<details><summary>Show answer</summary>

**B — Publishing min/max/sum/sample-count for a period.** You can push a single statistic set instead of a single value, letting CloudWatch aggregate server-side. This is the right way to push batch-aggregated metrics.

</details>

---

**Q10.** Which API should you reach for first to query metrics?

- A. `get_metric_statistics`
- B. `get_metric_data`
- C. `list_metrics`
- D. CloudShell

<details><summary>Show answer</summary>

**B — `get_metric_data`.** The modern (post-2018) API; supports metric math and returns timestamped values. `get_metric_statistics` is older and only returns aggregated rows.

</details>
