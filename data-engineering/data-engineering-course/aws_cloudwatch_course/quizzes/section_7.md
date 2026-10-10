# Section 7 Quiz — Real-World Patterns

> 8 questions, multi-choice, single answer.

---

**Q1.** For a 99.9% SLO over 30 days, what's the error budget?

- A. 4.32 minutes
- B. 43.2 minutes
- C. 4.32 hours
- D. 43.2 hours

<details><summary>Show answer</summary>

**B — 43.2 minutes.** `(1 - 0.999) × 30 × 24 × 60 = 43.2 minutes` of allowed failure per month.

</details>

---

**Q2.** What does a 14.4× burn rate over 1 hour imply for a 30-day budget?

- A. Budget lasts 2 days
- B. Budget lasts 5 days
- C. Budget lasts 2 weeks
- D. Budget lasts forever

<details><summary>Show answer</summary>

**A — 2 days.** That's why the canonical "fast-burn" alert uses 14.4× over 1h — it's the Google SRE workbook threshold for a *fast* outage that warrants paging.

</details>

---

**Q3.** Which is the *biggest* single CloudWatch cost lever?

- A. Custom metrics
- B. Detailed EC2 monitoring
- C. Log retention
- D. Alarm evaluation period

<details><summary>Show answer</summary>

**C — Log retention.** Default "Never expire" is the most common cost surprise. Set retention deliberately; 30 days is plenty for production debugging.

</details>

---

**Q4.** What is the canonical alarm name format?

- A. `<service>-<metric>-<threshold>`
- B. `<severity>-<service>-<signal>-<condition>`
- C. `<timestamp>-<team>-<metric>`
- D. `alarm-<n>`

<details><summary>Show answer</summary>

**B.** Severity prefix lets you filter (`p1-`, `p2-`, `p3-`); service identifies the owner; signal is the symptom; condition is "high" / "low" / "fast-burn".

</details>

---

**Q5.** In a multi-account org, where should the on-call SNS topic live?

- A. In every workload account
- B. In the monitoring / observability account
- C. In a region with the lowest latency
- D. In the dev account

<details><summary>Show answer</summary>

**B — In the monitoring account.** Centralises paging, decouples it from any single workload's blast radius.

</details>

---

**Q6.** Which Lambda metric indicates concurrency saturation?

- A. `Invocations`
- B. `Errors`
- C. `ConcurrentExecutions`
- D. `Throttles`

<details><summary>Show answer</summary>

**C — `ConcurrentExecutions` (Maximum).** When this approaches your reserved concurrency, you'll see throttling shortly after. `Throttles` is the lagging indicator.

</details>

---

**Q7.** Which ECS log driver is the standard for CloudWatch Logs?

- A. `splunk`
- B. `awslogs`
- C. `fluentd`
- D. `json-file`

<details><summary>Show answer</summary>

**B — `awslogs`.** Streams directly to a CloudWatch Logs group; per-container streams by default.

</details>

---

**Q8.** Which is the standard AWS-distro collector for traces in containers?

- A. CloudWatch agent
- B. ADOT (AWS Distro for OpenTelemetry)
- C. Datadog agent
- D. X-Ray daemon

<details><summary>Show answer</summary>

**B — ADOT.** The AWS-supported OpenTelemetry distribution. Ships traces, metrics, and logs to CloudWatch (and other backends).

</details>
