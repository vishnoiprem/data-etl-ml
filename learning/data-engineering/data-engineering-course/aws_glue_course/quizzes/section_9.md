# Section 9 Quiz — Glue Data Quality

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** In AWS Glue Data Quality, what is the relationship between a *rule* and a *ruleset*?

- A. They are synonyms — a rule and a ruleset both refer to a single atomic check
- B. A rule is a single atomic check (e.g. `IsComplete "user_id"`); a ruleset is a named, versioned collection of rules
- C. A ruleset is a single check; a rule is a group of checks bundled together
- D. A rule is a CloudWatch metric; a ruleset is the CloudWatch alarm attached to it

---

**Q2.** The DeeQu built-in rule `IsUnique "user_id"` is applied to a column containing 1,000,000 rows where 3 duplicate `user_id` values exist. What does the rule report?

- A. PASS — `IsUnique` only checks that the column is non-null
- B. FAIL — because the column contains duplicate `user_id` values
- C. PASS — duplicates under 1% of total rows are tolerated
- D. ERROR — `IsUnique` is not a valid DeeQu rule

---

**Q3.** You want to run data quality checks on a DynamicFrame inside a Glue Job. Which transform and Job argument pair correctly wires this up?

- A. `ApplyMapping` transform with `--data-quality-ruleset` in `AdditionalOptions`
- B. `EvaluateDataQuality` transform with `--data-quality-ruleset` in `AdditionalOptions`
- C. `EvaluateDataQuality` transform with `--dq-ruleset` as the Job name argument
- D. A standalone Python Shell job that calls the `boto3` Glue Data Quality API

---

**Q4.** By default, when a rule in the ruleset fails, what happens to the Glue Job, and which flag changes that behavior?

- A. The Job continues silently; use `--data-quality-ruleset-failure-behavior=warn` to fail the Job
- B. The Job fails immediately; use `--data-quality-ruleset-failure-behavior=skip` to warn and continue
- C. The Job retries 3 times; use `--data-quality-ruleset-retry-count=0` to disable
- D. The Job is cancelled; use `--data-quality-ruleset-failure-behavior=continue` to resume

---

**Q5.** You configure a CloudWatch alarm on the metric `glue.dataset.metrics.RuleEvaluationStatus` to fan out to an SNS topic. A rule in your ruleset fails. What value does the metric emit, and what does the alarm do?

- A. The metric emits `0`; the alarm transitions to `ALARM` and publishes to SNS
- B. The metric emits `1`; the alarm transitions to `ALARM` and publishes to SNS
- C. The metric emits `100`; the alarm treats this as a percentage breach
- D. The metric emits no value; CloudWatch derives it from Glue Job Run logs

---

# Answer Key

1. **B** — A rule is a single atomic check (e.g. `IsComplete "user_id"`, `IsUnique "user_id"`, `RowCount between 100 and 1_000_000`); a ruleset is a named, versioned collection of rules that is attached to a Glue Job or crawler. Rules are the building blocks; rulesets are the deployable unit.
2. **B** — FAIL. `IsUnique` asserts that the column has no duplicate values. Any duplicate — even a single row — fails the rule. (Compare with `IsComplete`, which asserts non-null; `IsPrimaryKey` is the stricter combination of `IsComplete` + `IsUnique`.)
3. **B** — The `EvaluateDataQuality` transform is the Glue-native integration point for DQ. It is added to the Job's `Transforms` list, and the ruleset is passed via `AdditionalOptions` as `--data-quality-ruleset <ruleset-name>`. There is no `--dq-ruleset` argument, and DQ does not run as a standalone Python Shell job in this pattern.
4. **B** — The Job fails. By default, any failed rule in the ruleset fails the Glue Job. Setting `--data-quality-ruleset-failure-behavior=skip` switches the Job to a warn-and-continue mode (the failure is logged and metrics are still emitted, but the Job Run status stays `SUCCEEDED`).
5. **A** — The `glue.dataset.metrics.RuleEvaluationStatus` metric emits `1` for a passing rule and `0` for a failing rule (one data point per rule). The CloudWatch alarm is configured to fire when the metric equals `0` (or `Average <= 0` over the evaluation window), transitions to the `ALARM` state, and publishes to the SNS topic.
