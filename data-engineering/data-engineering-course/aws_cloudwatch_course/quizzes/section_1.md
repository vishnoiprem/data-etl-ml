# Section 1 Quiz — Foundations

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** How many sections and lectures does the AWS CloudWatch Crash Course have?

- A. 5 sections, 25 lectures
- B. 7 sections, 35 lectures
- C. 10 sections, 50 lectures
- D. 12 sections, 60 lectures

<details><summary>Show answer</summary>

**B — 7 sections, 35 lectures.** The course is structured as Foundations (L01–L04), Metrics (L05–L09), Logs (L10–L14), Alarms (L15–L19), Dashboards (L20–L24), Logs Insights + Subscriptions (L25–L29), and Real-World Patterns (L30–L35).

</details>

---

**Q2.** Which AWS SDK is used in every `boto3` demo in the course?

- A. boto2
- B. boto3
- C. AWS CDK
- D. Terraform

<details><summary>Show answer</summary>

**B — boto3.** Every demo and every test in this course drives CloudWatch via `boto3` (the AWS SDK for Python). We use `moto` to mock the API in tests.

</details>

---

**Q3.** Which library is used to mock AWS APIs in the local test suite?

- A. unittest.mock
- B. responses
- C. moto
- D. vcr

<details><summary>Show answer</summary>

**C — moto.** The course's 5 demos are covered by 23+ moto tests. No real AWS credentials are required to run the test suite.

</details>

---

**Q4.** What are the three pillars of observability?

- A. Metrics, Logs, Traces
- B. CPU, Memory, Disk
- C. RPS, Latency, Errors
- D. Dev, Test, Prod

<details><summary>Show answer</summary>

**A — Metrics, Logs, Traces.** The pillars were coined by Peter Bourgeois in 2017. CloudWatch covers metrics and logs natively and integrates with X-Ray for traces.

</details>

---

**Q5.** Which two pillars does CloudWatch cover natively?

- A. Metrics and Logs
- B. Logs and Traces
- C. Traces and Metrics
- D. All three

<details><summary>Show answer</summary>

**A — Metrics and Logs.** CloudWatch has metrics, logs, alarms, dashboards, Events (EventBridge), Insights, Synthetics, and RUM. **Traces** are handled by the separate **X-Ray** service (integrated via ServiceLens).

</details>

---

**Q6.** Which AWS service covers traces and integrates with CloudWatch?

- A. CloudTrail
- B. AWS Config
- C. AWS X-Ray
- D. AWS Step Functions

<details><summary>Show answer</summary>

**C — AWS X-Ray.** X-Ray is a separate service. The CloudWatch console (specifically **ServiceLens**) shows X-Ray traces alongside metrics and logs.

</details>

---

**Q7.** Roughly how many CloudWatch metrics does the perpetual free tier cover per month?

- A. 100
- B. 1,000
- C. 10,000
- D. 1,000,000

<details><summary>Show answer</summary>

**C — 10,000.** Plus 1,000,000 metric data points and 1,000,000 API requests / month, 10 metric alarms, 3 dashboards (50 metrics each), and 5 GB log ingestion.

</details>

---

**Q8.** How long is the default log retention in CloudWatch Logs?

- A. 7 days
- B. 30 days
- C. 365 days
- D. Never expire

<details><summary>Show answer</summary>

**D — Never expire.** This is the most common cost surprise. Always set retention deliberately; 30 days is a sensible default for production debugging.

</details>

---

**Q9.** Which metric dimension pattern is the **least** likely to cause a cost surprise?

- A. `FunctionName`
- B. `Stage`
- C. `RequestId` (UUID)
- D. `Region`

<details><summary>Show answer</summary>

**C — `RequestId`.** Putting a per-request UUID as a dimension creates a new time-series per request. At 1,000 RPS that's 86 million series / day, each billable as a custom metric. Always keep dimensions bounded (function, region, status code) and put per-request data in logs instead.

</details>

---

**Q10.** Which is a *poor* choice for storing high-cardinality per-request data?

- A. A log event (structured JSON)
- B. A metric dimension
- C. An X-Ray annotation
- D. A CloudWatch tag

<details><summary>Show answer</summary>

**B — A metric dimension.** High cardinality in metric dimensions is the #1 way to blow up your CloudWatch bill. Logs and X-Ray annotations are designed for high cardinality.

</details>
