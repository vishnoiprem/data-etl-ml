# Lesson 8 — Quiz: AI for Pipeline Development

> **Type:** Quiz · Module 3 · AI for Pipeline Development
> Self-check on the eight lessons. Answers at the bottom.

---

## Section A — Conceptual

**Q1.** Which is the highest-leverage setup activity for AI-assisted pipeline development?
- A) A model fine-tuned on your codebase
- B) A canonical `templates/dag_template.py` that AI extends
- C) Switching from Cursor to Claude Code
- D) Buying a vector DB

**Q2.** AI defaults to generating which kind of pipeline code?
- A) Defensive code that handles every edge case
- B) Happy-path-only code
- C) Over-engineered code with unnecessary abstractions
- D) Code that mirrors your style perfectly

**Q3.** The single most important instruction in a pipeline-generation prompt is:
- A) "Use the team's template"
- B) "DO NOT generate happy-path-only code; handle 429, 5xx, partial pages, ..."
- C) "Use type hints"
- D) "Be concise"

**Q4.** In PySpark, the safest pattern for a driver that might OOM is:
- A) `.collect()` after filtering
- B) `.toPandas()` for inspection
- C) `.count()` and `.take(N)`
- D) `.show()` repeatedly

**Q5.** The dbt file most useful for AI context is:
- A) `dbt_project.yml`
- B) `packages.yml`
- C) `target/manifest.json`
- D) `profiles.yml`

**Q6.** Which is **not** part of the four-layer self-healing architecture?
- A) Auto-retry on transient errors
- B) Severity-based alert routing
- C) LLM hypothesis generation
- D) Autonomous code refactor across multiple DAGs

**Q7.** According to Deloitte's 2025 State of AI in the Enterprise, what % of organisations have fully autonomous pipeline agents in production?
- A) ~50%
- B) ~25%
- C) ~10–15%
- D) Small single-digit %

---

## Section B — Scenario

**Q8.** A teammate says: *"I'll just have AI generate the whole pipeline in one prompt. It'll be faster."* What do you say, and why?

**Q9.** Your team wants to ship a self-healing pipeline feature in the next sprint. The CEO expects "AI runs the platform at 3 a.m." What do you actually ship, and how do you reset expectations?

---

## Section C — Practical

**Q10.** Write the most-important sentence in the **CONSTRAINTS** block of a pipeline-generation prompt for a Stripe payments ingestion pipeline.

**Q11.** List 5 silent Spark bugs that AI code commonly produces, and one verification step for each.

**Q12.** Generate the `CLAUDE.md` excerpt (3–6 lines) that tells AI about your dbt conventions.

**Q13.** You have 1 week to take a dbt project from 20% documentation coverage to 80%. Write the plan.

---

## Section D — Open

**Q14.** Pick a recent pipeline failure. Reconstruct the failure as if you were the AI investigator. What would you have proposed as the top hypothesis? What would you have done as the suggested next action?

---

## Answer Key

<details>
<summary>A1</summary>

**B** — A canonical template compounds across every DAG you generate. It's the highest leverage per minute spent.

</details>

<details>
<summary>A2</summary>

**B** — Happy-path-only code. AI generates beautiful code that handles the API-returning-clean-data case. Real failures live in the cases you didn't ask for.

</details>

<details>
<summary>A3</summary>

**B** — The negative-constraint instruction that names the edge cases. Without it, the AI skips them.

</details>

<details>
<summary>A4</summary>

**C** — `.count()` returns a scalar, `.take(N)` returns N rows. `.collect()` pulls everything to the driver.

</details>

<details>
<summary>A5</summary>

**C** — `manifest.json` after `dbt parse` contains every model, column, test, and relationship. With it indexed in the IDE, AI writes correct refs and uses real column names.

</details>

<details>
<summary>A6</summary>

**D** — Autonomous cross-DAG refactor is not part of any production self-healing pattern. It's overhyped.

</details>

<details>
<summary>A7</summary>

**D** — Small single-digit %. Most orgs pilot but don't deploy.

</details>

<details>
<summary>A8</summary>

A model answer:

> One-shot pipeline generation is the fastest way to ship a happy-path-only pipeline. The production failure mode is the failure mode you didn't specify (429, 5xx, partial pages, schema drift, duplicates, malformed records).
>
> If you don't tell the AI about those edge cases, it won't write code for them. You'll ship a pipeline that fails in production on day one. We've seen this pattern destroy timelines.
>
> The fix is to break the pipeline into components (source, extractor, validator, loader, orchestrator) and prompt each one separately with the edge cases explicitly listed. The output is far better, and you actually understand what was generated.

</details>

<details>
<summary>A9</summary>

A model answer — ship these four layers, in this order, over multiple sprints:

1. **Layer 1 — Auto-retry on transient errors.** Highest leverage, lowest risk, ships in days.
2. **Layer 2 — Smart alert routing** (severity → page vs. slack). Eliminates alert fatigue.
3. **Layer 3 — LLM hypothesis + suggested fix in Slack.** Highest leverage for reducing MTTR; partial scope; human still approves.
4. **Layer 4 — Bounded auto-remediation** (1–2 narrow patterns). Pre-approved only.

Reset expectations: "Fully autonomous at 3 a.m. is not in production for most teams in 2026. What we ship is: auto-retry handles 8 out of 10 transient failures, smart routing ensures you sleep through the rest, and our LLM investigator puts a hypothesis in Slack within 60 seconds with a suggested fix. MTTR goes from 90 minutes to 20 minutes, on-call gets their nights back, but a human is still in the loop for any non-trivial action."

</details>

<details>
<summary>A10</summary>

A model answer:

> **DO NOT generate happy-path-only code.** You MUST explicitly handle: (1) 429 rate-limited response with exponential backoff + jitter, (2) 5xx server errors with retry up to 3 times, (3) partial-page responses (write what you got, log what was missing), (4) new fields appearing in the API response (log warning, accept, surface), (5) duplicate IDs in the same page (de-dupe before load), (6) malformed JSON (skip the row, log it, do not fail the whole extract), (7) secret rotation failure / 401 (fail loudly, alert, no silent fallback).

</details>

<details>
<summary>A11</summary>

A model answer:

| Silent bug | Verification |
|---|---|
| **Driver OOM from `.collect()`** | `grep` for `.collect(` in the diff |
| **Shuffle skew** | Look at Spark UI stage durations; max >> median = skew |
| **Cartesian product** | EXPLAIN shows no join condition |
| **Small files** | Count output files; >1000 small files = problem |
| **Python UDFs blocking Catalyst** | Job 10× slower than expected; rewrite with native functions |

</details>

<details>
<summary>A12</summary>

A model answer:

```markdown
## dbt conventions
- dbt-snowflake 1.8+. Models in models/staging, models/intermediate, models/marts.
- Staging views, intermediate views (or ephemeral), marts tables or incremental.
- All mart PKs: not_null + unique. Every model: description. Every column: description.
- Sources defined in models/staging/<source>/_sources.yml.
- Incremental: strategy merge, unique_key = PK, on_schema_change = append_new_columns.
- Follow @CLAUDE.md for full style.
```

</details>

<details>
<summary>A13</summary>

A model answer:

1. **Day 1–2:** Enable `target/manifest.json` indexing in your IDE.
2. **Day 3:** Write a prompt template that, given a model SQL, generates `_models.yml` with descriptions, tests, and column docs.
3. **Day 4–5:** Run the prompt on every model in `models/`. Review in batches.
4. **Day 6:** Add CI check: "if a column was added to the model, schema.yml must have changed."
5. **Day 7:** Spot-check 20% of generated descriptions for correctness. Ship.

Result: 80%+ coverage from 20% in one week.

</details>

<details>
<summary>A14</summary>

This is a personal reflection exercise. Walk through:

- What was the actual error in the log?
- What did the AI investigator likely output as the top 3 hypotheses?
- Which one would have been correct?
- What probe query would have confirmed it?
- What was the next action?

Compare your reconstruction against the actual postmortem. That's how you calibrate the AI investigator for your environment.

</details>

---

*End of Module 3. Move to [Module 4 — Vector Databases & Embeddings](../04-vector-databases-embeddings/README.md).*
