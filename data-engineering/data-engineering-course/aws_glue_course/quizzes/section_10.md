# Section 10 Quiz — Glue DataBrew

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** What is the difference between a Glue Data Quality *rule* and a *ruleset*?

- A. A rule is a single check; a ruleset is a named collection of rules
- B. A rule is for one column; a ruleset is for the whole table
- C. A rule is in Python; a ruleset is in SQL
- D. There is no difference

---

**Q2.** A Glue Data Quality rule `ColumnLength "country" between 2 and 3` fails. What is the most likely cause?

- A. The column has values longer than 3 characters (e.g., "USA", "UK")
- B. The column has null values
- C. The column is the wrong type
- D. The rule syntax is wrong

---

**Q3.** A Glue Data Quality rule fails and the Glue Job writes 0 records to the target. What is the default behavior?

- A. The job continues and writes 0 records
- B. The job fails entirely
- C. The job writes the records and flags the failure in CloudWatch
- D. The behavior depends on the `Action` parameter

---

**Q4.** You want to be alerted when a Glue Data Quality rule fails. What is the standard pattern?

- A. CloudWatch metric → CloudWatch alarm → SNS topic → email
- B. Lambda + SES
- C. EventBridge + Lambda
- D. Direct SNS publish from the Glue Job

---

**Q5.** A Glue Data Quality rule `IsComplete "user_id"` is set up. The rule fails. Which of the following is the most likely cause?

- A. The `user_id` column has null values
- B. The `user_id` column has duplicate values
- C. The `user_id` column has the wrong type
- D. The rule is misconfigured

---

# Answer Key

1. **A** — Rule = single check; ruleset = named collection. A ruleset is the artifact you attach to a Glue Job (e.g., `DQRuleset: "completeness-user-id"`).
2. **A** — Values longer than 3 characters. "USA" is 3 characters (passes), "UK" is 2 (passes), but "United States" is 13 (fails). The fix is to use the 2- or 3-letter country code (ISO 3166-1 alpha-2/alpha-3).
3. **D** — Depends on the `Action` parameter. The default is `"primary"` (fail the job). `"secondary"` lets the job continue and writes the records. `"publish"` writes to a separate metrics stream.
4. **A** — CloudWatch metric → alarm → SNS. Glue Data Quality publishes metrics to CloudWatch (`glue.dataset.metrics.RuleEvaluationStatus`); a CloudWatch alarm fires on `1` (failed); SNS delivers to email/Slack/PagerDuty.
5. **A** — Null values. `IsComplete` checks for non-null values. If the column has nulls, the rule fails.
