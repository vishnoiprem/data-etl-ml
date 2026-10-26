# Section 5 Quiz — EventBridge Scheduler

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** Which boto3 client should you use to create an EventBridge
Scheduler schedule?

- A. `boto3.client("events")`
- B. `boto3.client("scheduler")`
- C. `boto3.client("eventbridge")`
- D. `boto3.client("cloudwatch-events")`

<details><summary>Show answer</summary>

**B — `boto3.client("scheduler")`.** EventBridge Scheduler is a
distinct AWS service with its own service prefix (`scheduler`),
separate from the legacy CloudWatch Events `events` client. The
`events` client still works for the *old* `ScheduleExpression` rules,
but new code should use `scheduler`.

</details>

---

**Q2.** Which cron expression fires at exactly 8:00 AM on weekdays
(Monday–Friday) in **UTC**?

- A. `cron(0 8 * * MON-FRI)`
- B. `cron(0 8 * * ? *)` (5-field, missing year)
- C. `cron(0 8 ? * MON-FRI *)`
- D. `cron(8 0 ? * MON-FRI *)`

<details><summary>Show answer</summary>

**C — `cron(0 8 ? * MON-FRI *)`.** AWS cron expressions require
**six** fields (minute hour day-of-month month day-of-week year),
and one of `day-of-month` or `day-of-week` must be `?`. Option A
is missing the year. Option B has 5 fields. Option D swaps the
hour and minute, so it would fire at 8 minutes after midnight, not
8 AM.

</details>

---

**Q3.** Which rate expression is **invalid**?

- A. `rate(5 minutes)`
- B. `rate(1 hour)`
- C. `rate(1 hours)`
- D. `rate(7 days)`

<details><summary>Show answer</summary>

**C — `rate(1 hours)`.** Rate expressions require singular/plural
agreement: `1 hour` is correct, but `1 hours` is a validation
error. `5 minutes`, `1 hour`, and `7 days` are all valid.

</details>

---

**Q4.** You want a schedule that fires **exactly once** on
2026-12-31 at 23:59 UTC. Which expression is correct?

- A. `cron(59 23 31 12 ? 2026)`
- B. `at(2026-12-31T23:59:00)`
- C. `rate(1 day)` with `EventStartTime=2026-12-31T23:59:00`
- D. `once(2026-12-31T23:59:00)`

<details><summary>Show answer</summary>

**B — `at(2026-12-31T23:59:00)`.** At-expressions fire exactly
once at the named instant. `cron(...)` would fire on the same
date every year (or never, depending on the year field). `rate`
is recurring. `once(...)` is not a valid Scheduler expression.

</details>

---

**Q5.** Which `FlexibleTimeWindow` value tells the scheduler to
fire **exactly on the wall-clock minute**, with no spreading?

- A. `{"Mode": "OFF"}`
- B. `{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 0}`
- C. `{"Mode": "STRICT"}`
- D. `{"Mode": "EXACT"}`

<details><summary>Show answer</summary>

**A — `{"Mode": "OFF"}`.** The default. `FLEXIBLE` requires a
positive `MaximumWindowInMinutes`. `STRICT` and `EXACT` are not
valid modes.

</details>

---

**Q6.** You want a 9 AM Eastern (US East coast) cron. Which is the
right combination?

- A. `cron(0 9 * * ? *)` (UTC, no timezone)
- B. `cron(0 9 * * ? *)` with `ScheduleExpressionTimezone="America/New_York"`
- C. `cron(0 13 * * ? *)` with no timezone field
- D. Both B and C work, but B is the cleaner pattern

<details><summary>Show answer</summary>

**D — Both B and C work, but B is the cleaner pattern.** You can
either set `ScheduleExpressionTimezone` and write the local time
in the cron, or compute the UTC offset yourself and write the UTC
time. B is preferred because it survives DST changes — the
scheduler applies the IANA tz to the cron at every invocation.
C works in May but would be wrong in November (Eastern switches
between EST and EDT).

</details>

---

**Q7.** What happens on the spring-forward day for a
`cron(0 2 * * ? *)` with
`ScheduleExpressionTimezone="America/Los_Angeles"`?

- A. It fires at 2 AM as normal
- B. It fires at 3 AM (the new 2 AM equivalent)
- C. It does **not** fire (2 AM does not exist that day)
- D. It fires twice

<details><summary>Show answer</summary>

**C — It does not fire.** On the spring-forward day, the local
clock jumps from 1:59 AM to 3:00 AM. 2 AM does not exist, so the
cron has no valid instant to fire. The scheduler does not retry
the missed fire. If this matters, pick a different hour (3 AM or
later) or accept the gap.

</details>

---

**Q8.** Which service quota is most likely to bite you if you
create 100,000 schedules all firing at 2 AM?

- A. 1 million active schedules per region
- B. 1 invocation per second per account
- C. 14 million invocations per month free tier
- D. 5 archives per bus

<details><summary>Show answer</summary>

**B — 1 invocation per second per account.** If all 100k
schedules fire in the same 60-second window, the scheduler
service will buffer and may fail-fast. The fix is a
`FlexibleTimeWindow` with `MaximumWindowInMinutes=15` to spread
the invocations.

</details>

---

**Q9.** Which IAM permission does the **role passed to
Scheduler** (via `Target.RoleArn`) need at minimum?

- A. `iam:PassRole` only
- B. Permission to invoke the target service (e.g.
  `lambda:InvokeFunction`)
- C. Both A and B
- D. No IAM — the role is optional

<details><summary>Show answer</summary>

**C — Both A and B.** The Scheduler service must be allowed to
`iam:PassRole` to the target (otherwise the API call fails), and
the role's permission policy must allow the actual target
invocation (`lambda:InvokeFunction`, `sqs:SendMessage`, etc.).

</details>

---

**Q10.** Why is the `?` wildcard required in AWS cron expressions?

- A. It is just a Linux cron legacy
- B. AWS cron forbids having **both** day-of-month and
  day-of-week as `*`; one of them must be `?`
- C. It means "ignore this field"
- D. It is only valid in the year field

<details><summary>Show answer</summary>

**B — AWS cron forbids having both day-of-month and day-of-week
as `*`; one of them must be `?`.** This is the AWS-specific quirk
that catches Linux cron users. AWS requires an explicit
"day-of-month OR day-of-week" choice to disambiguate the
intent.

</details>
