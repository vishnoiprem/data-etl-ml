# Section 9 — Glue Data Quality (Lectures L71-L77)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 7 lecture scripts (L71-L77) for Section 9.

---

## L71 — Section Overview (1:01)

> "Section 9 is Glue Data Quality. The 3 things we'll do: 1) create a DQ ruleset with 3 rules, 2) attach the ruleset to the Glue Job, 3) configure CloudWatch metrics + an alarm. By the end, the Job will fail if the DQ rules fail, and you'll get an alert via SNS."

---

## L72 — Data Quality 101 (2:43)

> "Glue Data Quality is a rules-based DQ engine. You author a *ruleset* — a JSON document with one or more *rules*. Each rule is a single check: `IsComplete "user_id"`, `IsUnique "event_id"`, `RowCount > 0`, `ColumnLength "country" between 2 and 3`, `ColumnValues "country" in ["US", "UK", "FR", ...]`. The engine evaluates the ruleset against the data, returns a pass/fail per rule, and publishes metrics to CloudWatch. The ruleset can be authored visually (in the console) or as JSON. For this course, we'll author it as JSON."

Key bullets: ruleset = JSON; rule = single check; visual or JSON authoring.

---

## L73 — Setting Up Data Quality Rule Set (4:02)

> "Create the ruleset. Glue → Data Quality → Rulesets → Create ruleset. Name: `city-temperature-dq`. Visual or JSON tab. The ruleset has 3 rules: 1) `IsComplete "region"`, 2) `IsUnique "country, year, month, day, city"` (composite key), 3) `RowCount > 0`. Save. Now attach the ruleset to the Glue Job: in the Job's `Security configuration, script libraries, and job parameters` section, add `--dq-ruleset city-temperature-dq` and `--dq-action primary` (the default — fail the Job on DQ failure)."

Lab: create the ruleset, attach to the Job, run the Job, verify it succeeds.

---

## L74 — Glue Job With Data Quality Check (3:38)

> "Walkthrough of the Glue Job with DQ enabled. The Job's script is the same as before; the DQ check is added by Glue automatically based on the `--dq-ruleset` argument. The DQ check runs *after* the Job's main script completes successfully. If the DQ check fails, the Job is marked FAILED. The DQ result is in the Job run history, under the 'Data quality' tab."

---

## L75 — Running the Glue Job (2:56)

> "Run the Job. The Job succeeds, the Parquet output is written, and the DQ check passes (all 3 rules). Now introduce a DQ failure: edit the ruleset to be too strict — change `IsUnique "country, year, month, day, city"` to `IsUnique "country"` (every country must appear exactly once, which is false). Re-run the Job. The Job's main script succeeds, but the DQ check fails, and the Job is marked FAILED. The Parquet output is *not* written (because the Job is marked FAILED, the post-DQ commit step is skipped)."

Lab: introduce a DQ failure, watch the Job fail, fix the ruleset.

---

## L76 — Setting Up Glue Data Quality CloudWatch Metrics (4:08)

> "Glue Data Quality publishes metrics to CloudWatch automatically. The metrics are in the `glue.dataset.metrics` namespace: `RuleEvaluationStatus` (0 = passed, 1 = failed) and `RuleEvaluationDuration` (how long the DQ check took). To set up a CloudWatch alarm: CloudWatch → Alarms → Create alarm. Select metric → `glue.dataset.metrics` namespace → `RuleEvaluationStatus` metric → `Average` statistic. Condition: `>= 1` for `1 minute`. Configure actions: send to a new SNS topic."

Lab: create the CloudWatch alarm; verify it's `OK` after a successful run; verify it's `In alarm` after a failed DQ run.

---

## L77 — Receiving Alerts for Data Quality Issues (1:49)

> "Subscribe your email to the SNS topic. SNS → Topics → `glue-dq-alerts` → Create subscription → Protocol: Email → Endpoint: your email. Confirm the subscription via the email. Now when the DQ check fails, the alarm fires, the SNS topic publishes, and you get an email. The email has a link to the CloudWatch console where you can see the alarm's state and the metric that triggered it."

Lab: trigger a DQ failure; verify the email arrives within 2-3 minutes.

---

## Section 9 Quiz

5 questions, see `quizzes/section_9.md`.
