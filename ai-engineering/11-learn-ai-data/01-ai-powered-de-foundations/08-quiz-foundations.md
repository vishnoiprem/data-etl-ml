# Lesson 8 — Quiz: AI-Powered DE Foundations

> **Type:** Quiz · Module 1 · AI-Powered DE Foundations
> Self-check on the eight lessons of Module 1. Answers at the bottom — no peeking.

---

## Section A — Conceptual (multiple choice)

**Q1.** Which of the following best characterises the "two lanes" framing of AI in data engineering?
- A) Lane 1: replace DEs with AI. Lane 2: train AI models.
- B) Lane 1: AI as a copilot on existing DE work. Lane 2: build infrastructure that AI products run on.
- C) Lane 1: vendor tools. Lane 2: open-source tools.
- D) Lane 1: prompt engineering. Lane 2: fine-tuning.

**Q2.** On the BIRD benchmark (messier, more realistic schemas than Spider), modern frontier models report roughly what execution accuracy?
- A) ~93%
- B) ~85–90%
- C) ~52%
- D) ~99%

**Q3.** Which verification habit is the single highest-leverage for catching AI-generated SQL bugs?
- A) EXPLAIN
- B) Row count + sample
- C) Code review
- D) Style lint

**Q4.** In a six-part prompt (role, context, task, constraints, format, verification), which part is most often forgotten?
- A) Role
- B) Constraints
- C) Format
- D) Verification

**Q5.** Which is a valid concern when pasting your warehouse schema into an AI tool?
- A) The vendor may train on it
- B) The AI may invent columns that don't exist
- C) PII may leak via prompts
- D) All of the above

---

## Section B — Scenario

**Q6.** A teammate says: *"I'll just have ChatGPT write all our dbt models and we won't need to review them — it gets it right 90% of the time on the Spider benchmark."*

What are the three most important things you would say back, and why?

**Q7.** You're building a customer-support auto-routing system. An LLM will decide which queue each ticket lands in. List five things from the ethics checklist that apply here.

---

## Section C — Practical

**Q8.** Write a six-part prompt that asks the AI to produce a dbt staging model `stg_subscriptions` from `raw.subscriptions_v3`, with columns `subscription_id`, `user_id`, `plan`, `status`, `started_at`, `cancelled_at`. Use your real warehouse's conventions.

**Q9.** Name the three categories of AI tool that are production-ready for DEs today, and give one example of each.

**Q10.** A failure has been reported: yesterday's AI-generated revenue dashboard shows a number 12% lower than it should be. Walk through your debugging steps in order.

---

## Section D — Open

**Q11.** Where on your team today could you safely apply AI for a 2–5× speedup with low risk? Where would you **not** apply AI yet, and why?

---

## Answer Key

<details>
<summary>A1</summary>

**B** — Lane 1 is AI as a copilot on existing DE work (productivity). Lane 2 is building the infrastructure (vector DBs, RAG, feature stores) that AI products depend on. Both share the same DE fundamentals foundation.

</details>

<details>
<summary>A2</summary>

**C** — ~52% for GPT-4 on BIRD, versus ~93% for human experts. (Spider's 85–90% is on cleaner 5–20-table schemas.)

</details>

<details>
<summary>A3</summary>

**B** — Row count + sample catches the most common and most silent class of AI bugs (plausible-but-wrong joins, filters, aggregations).

</details>

<details>
<summary>A4</summary>

**D** — Verification. Without it, the prompt produces output you can't trust.

</details>

<details>
<summary>A5</summary>

**D** — All three. Vendor training opt-in, hallucinated facts about your data, and PII leakage are all real risks.

</details>

<details>
<summary>A6</summary>

A model answer:

1. **Spider benchmark accuracy ≠ your warehouse accuracy.** Spider uses 5–20 well-documented tables. Your warehouse likely has 200+ with inconsistent naming, business logic in views, and undocumented columns. Published case studies put text-to-SQL on real warehouses in the single-to-low double digits.
2. **Even at 90% benchmark accuracy, that's 1 in 10 wrong.** At pipeline volume, that's dozens of broken queries a week. The blast radius is the data, not the SQL.
3. **You still own the output.** Whether AI or junior wrote the SQL, the senior reviewer is responsible. Skipping review because "AI wrote it" is the failure mode the auto-routing system at the retail team in Lesson 1 demonstrated.

</details>

<details>
<summary>A7</summary>

A model answer — five from the ethics checklist that apply:

1. **Vendor review** — what model, what data-retention policy, what training opt-out.
2. **Bias audit** — accuracy by language, by region, by user segment. Spanish-language tickets may be mis-routed if the model skews English.
3. **Appeal path** — customers must be able to dispute a wrong routing decision.
4. **Logging** — every routing call logged with prompt + response + model version, for incident review.
5. **Fallback** — what happens when the AI is down or returns low-confidence? Tickets can't disappear.

</details>

<details>
<summary>A8</summary>

A model answer — six-part prompt:

```
ROLE
You are a senior analytics engineer at [company].

CONTEXT
Snowflake warehouse. Schema documented in @schema.md.
dbt project, models in models/{staging,intermediate,marts}.
Style: lowercase keywords, explicit JOINs, CTEs over subqueries.
Timestamps are TIMESTAMP_NTZ in UTC.

TASK
Write a dbt staging model `stg_subscriptions` from `raw.subscriptions_v3`.
- Select: subscription_id, user_id, plan, status, started_at, cancelled_at
- Rename for consistency with rest of project
- Cast started_at and cancelled_at to TIMESTAMP_NTZ
- Filter out cancelled_at IS NULL AND status = 'cancelled' (data quality issue)
- Add surrogate subscription_pk (MD5 of subscription_id)

CONSTRAINTS
- Do not include any column not listed above
- Do not use dbt_utils.surrogate_key (use raw MD5)
- Do not generate tests (added separately)

FORMAT
Return:
1. SQL in a ```sql block
2. 2-line explanation of choices
3. 2 sample row-check queries for verification

VERIFICATION
After the SQL, list how to confirm correctness: expected row count,
null checks on PK, distinct value check on status.
```

</details>

<details>
<summary>A9</summary>

1. **AI coding assistants** — Cursor, Copilot, Claude Code, Codex, Q Developer.
2. **AI-powered data quality** — Monte Carlo, Anomalo, Datadog (Metaplane).
3. **AI-powered data catalogs** — Atlan, Alation, Collibra.

</details>

<details>
<summary>A10</summary>

A model debugging order:

1. **Re-run the AI-generated query by hand.** Confirm the 12% delta reproduces.
2. **Compare to yesterday's known-good result.** What changed?
3. **Check the AI's recent edits.** Was there a refactor, a rename, a join change? `git log`, `git diff`.
4. **EXPLAIN the query.** Look for new full scans, new shuffles, new broadcast skew.
5. **Sample 10 rows by hand.** Are the values what you expect?
6. **Check the upstream sources.** Did the source schema change? Did a null appear in a previously-populated column?
7. **Roll back the AI-generated change** if the issue is in the AI's commit. Don't try to "fix forward" without understanding the root cause.
8. **Postmortem.** Document what the AI missed, update your `.cursorrules` or `schema.md` to prevent recurrence, share with the team.

</details>

<details>
<summary>A11</summary>

This is personal to your context. A few prompts:

- "I could safely apply AI to: dbt model scaffolding, SQL first drafts from spec, doc generation from code, test scaffolding."
- "I would not yet apply AI to: production schema migrations, anything touching raw PII, anything customer-facing without a human in the loop, anything where the verification cost is higher than the typing cost."

The exercise is to make the boundary explicit on your team, then review it in 90 days.

</details>

---

*End of Module 1. Move to [Module 2 — AI for SQL & Analytics](../02-ai-for-sql-analytics/README.md).*
