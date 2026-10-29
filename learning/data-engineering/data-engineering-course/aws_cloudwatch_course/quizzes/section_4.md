# Section 4 Quiz — Alarms

> 10 questions, multi-choice, single answer.

---

**Q1.** What are the three alarm states?

- A. GREEN / YELLOW / RED
- B. OK / ALARM / INSUFFICIENT_DATA
- C. HEALTHY / DEGRADED / DOWN
- D. UP / DOWN / UNKNOWN

<details><summary>Show answer</summary>

**B — OK / ALARM / INSUFFICIENT_DATA.** INSUFFICIENT_DATA means "not enough datapoints to evaluate" — not "fail-safe".

</details>

---

**Q2.** What does `TreatMissingData=breaching` do?

- A. Treats a missing datapoint as not-breaching (alarm stays OK)
- B. Treats a missing datapoint as a breach (alarm goes ALARM)
- C. Drops the alarm
- D. Pages on-call

<details><summary>Show answer</summary>

**B.** Useful when a stopped instance should page on-call (no metric = bad). `notBreaching` is the more common setting for transient data.

</details>

---

**Q3.** In a "3 of 5 datapoints" alarm with `Period=60`, how long is the lookback?

- A. 1 minute
- B. 3 minutes
- C. 5 minutes
- D. 15 minutes

<details><summary>Show answer</summary>

**C — 5 minutes.** `EvaluationPeriods * Period = 5 * 60 = 300 seconds = 5 minutes`. `DatapointsToAlarm` is how many of those 5 must breach.

</details>

---

**Q4.** Which comparison operator is right for an anomaly-detection alarm with two bands?

- A. `GreaterThanThreshold`
- B. `LessThanThreshold`
- C. `GreaterThanUpperThreshold`
- D. `LessThanLowerOrGreaterThanUpperThreshold`

<details><summary>Show answer</summary>

**D — `LessThanLowerOrGreaterThanUpperThreshold`.** Fires when the metric is outside *either* the lower or the upper band. Use `GreaterThanUpperThreshold` for upper-only and `LessThanLowerThreshold` for lower-only.

</details>

---

**Q5.** Which action types are *valid* for an alarm? (Pick the most complete list)

- A. SNS only
- B. SNS, ASG, Lambda, EC2
- C. SNS, SQS, S3
- D. Email only

<details><summary>Show answer</summary>

**B — SNS, ASG, Lambda, EC2 (Reboot / Stop / Terminate / Recover).** The EC2 actions use the `arn:aws:swf:...` format. SNS is the most common; Lambda is the most flexible (transforms to PagerDuty / Slack).

</details>

---

**Q6.** How many actions per state does CloudWatch support?

- A. 1
- B. 3
- C. 5
- D. Unlimited

<details><summary>Show answer</summary>

**C — 5.** Each state (ALARM / OK / INSUFFICIENT_DATA) can have up to 5 actions.

</details>

---

**Q7.** What does `ActionsEnabled=False` do?

- A. Deletes the alarm
- B. Master switch — alarms still transition but no actions fire
- C. Disables OK actions
- D. Sets the alarm to OK

<details><summary>Show answer</summary>

**B — Master switch.** Useful during planned maintenance. The alarm still transitions through OK / ALARM / INSUFFICIENT_DATA but no actions fire. Don't forget to re-enable it.

</details>

---

**Q8.** What is the syntax for an OR composite alarm?

- A. `a OR b`
- B. `ALARM(a) OR ALARM(b)`
- C. `a | b`
- D. `AlarmName=a, AlarmName=b`

<details><summary>Show answer</summary>

**B — `ALARM(a) OR ALARM(b)`.** The composite alarm expression language supports `ALARM(name)`, `OK(name)`, `INSUFFICIENT_DATA(name)`, `AND`, `OR`, `NOT`, and parentheses.

</details>

---

**Q9.** How long does anomaly detection take to train?

- A. 1 hour
- B. 1 day
- C. 1 week
- D. Up to 2 weeks

<details><summary>Show answer</summary>

**D — Up to 2 weeks.** Plan for this in any new service rollout; bands are not sensible for the first 14 days.

</details>

---

**Q10.** What's the canonical pattern for wiring an alarm to PagerDuty?

- A. Direct `pagerduty.com` API from the alarm
- B. SNS topic → Lambda → PagerDuty Events API
- C. Email subscription only
- D. Anomaly detection + Slack

<details><summary>Show answer</summary>

**B.** CloudWatch doesn't integrate with PagerDuty directly. The pattern is: alarm → SNS topic → Lambda (transforms to PagerDuty payload) → PagerDuty Events API. Lambda gives you transformation, deduplication, and routing control.

</details>
