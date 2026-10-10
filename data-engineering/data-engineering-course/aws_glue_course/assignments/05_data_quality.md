# Assignment 05 — Glue Data Quality + CloudWatch

> **Section:** 9 (Glue Data Quality)
> **Due:** End of week 5
> **Deliverable:** A Glue Data Quality ruleset with 3 rules + a CloudWatch alarm that fires when any rule fails.

## Objective

Add a Glue Data Quality ruleset to the existing Glue Job from Assignment 02 (or to a new Job). The ruleset must contain 3 rules: completeness, uniqueness, and row-count match. The deliverable proves you can:
- Author a Glue Data Quality ruleset (in the visual editor or via JSON).
- Attach the ruleset to a Glue Job.
- Configure CloudWatch metrics + an SNS topic + an alarm.

## Steps

1. **Create a Glue Data Quality ruleset** named `city-temperature-dq` with 3 rules:
   - `IsComplete "user_id"` — wait, use `region` for this dataset. `IsComplete "region"`.
   - `IsUnique "city"` (across the table) — every city appears once per (year, month, day).
   - `RowCount "city_temperature" > 0` — the table has at least 1 row.
2. **Attach the ruleset to the Glue Job**:
   - In the Job's `Security configuration, script libraries, and job parameters` section, add:
     - `--dq-ruleset`: `city-temperature-dq`
     - `--dq-action`: `primary` (fail the job on DQ failure)
3. **Run the Job** — verify it succeeds and the Parquet output is correct.
4. **Introduce a DQ failure** — modify the ruleset to be too strict (e.g., `IsUnique "country"` — there are duplicates). Re-run the Job. Verify it fails.
5. **Configure CloudWatch**:
   - The Job automatically publishes the `glue.dataset.metrics.RuleEvaluationStatus` metric.
   - Create a CloudWatch alarm: when the metric is `1` (failed) for 1 minute, send to an SNS topic.
   - Subscribe your email to the SNS topic.
6. **Verify** — the alarm fires when you re-run the Job with the too-strict ruleset.

## Acceptance criteria

- Ruleset has 3 rules (1 completeness, 1 uniqueness, 1 row-count).
- Job fails when ruleset fails (default behavior with `--dq-action=primary`).
- CloudWatch metric `glue.dataset.metrics.RuleEvaluationStatus` shows `1` after the failed run.
- CloudWatch alarm transitions to `In alarm` state.
- You receive an email via the SNS topic.

## Stretch (optional, 1 hour)

- Add a 4th rule: `ColumnLength "country" between 2 and 3` (ISO 3166-1 alpha-3).
- Use `aws glue get-data-quality-rule-recommendation` to generate ruleset recommendations from the data, and compare the recommended rules to your hand-written ones.
- Add an EventBridge rule that triggers a Lambda function on DQ failure, which posts a message to a Slack channel via webhook.
