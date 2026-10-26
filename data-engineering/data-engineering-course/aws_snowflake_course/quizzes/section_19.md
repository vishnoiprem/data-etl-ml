# Section 19 Quiz — Data Sampling

> 6 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** Which is *not* a typical use case for data sampling?

- A. ML training
- B. Test/dev environments
- C. Exact total revenue for a financial close
- D. Ad-hoc data exploration

<details><summary>Show answer</summary>

**C — Exact total revenue for a financial close.** Sampling gives
estimates, not exact values. For exact totals, scan the full table.

</details>

---

**Q2.** Which statement returns a random 1% of rows?

- A. `SELECT * FROM t LIMIT 1 PERCENT;`
- B. `SELECT * FROM t SAMPLE (1);`
- C. `SELECT * FROM t WHERE rownum <= 1 PERCENT;`
- D. `SELECT TOP 1 PERCENT * FROM t;`

<details><summary>Show answer</summary>

**B — `SELECT * FROM t SAMPLE (1);`** The `SAMPLE` keyword takes
a percentage. By default it samples whole micro-partitions
(SYSTEM-style).

</details>

---

**Q3.** `SAMPLE BERNOULLI (10)` and `SAMPLE SYSTEM (10)` differ in:

- A. Output schema
- B. Randomness (per-row vs block-level) and performance
- C. Result row count
- D. They are identical

<details><summary>Show answer</summary>

**B — `BERNOULLI` is per-row (uniform but slower); `SYSTEM` is
block-level (faster but less uniform).**

</details>

---

**Q4.** `SAMPLE` runs before or after `WHERE`?

- A. Before
- B. After
- C. Depends on the optimizer
- D. They are fused

<details><summary>Show answer</summary>

**B — After.** The filter runs first, then sampling. This is the
right order for "sample the matching rows" semantics.

</details>

---

**Q5.** Which is the ANSI SQL equivalent of `SAMPLE SYSTEM`?

- A. `TABLESAMPLE SYSTEM`
- B. `SAMPLE TO ROWS`
- C. `LIMIT 10`
- D. `SAMPLE BLOCK`

<details><summary>Show answer</summary>

**A — `TABLESAMPLE SYSTEM`.** The ANSI form for portable SQL.

</details>

---

**Q6.** A 1% sample of a 1B-row table is approximately how many
rows?

- A. 1,000
- B. 100,000
- C. 1,000,000
- D. 10,000,000

<details><summary>Show answer</summary>

**D — 10,000,000.** 1% of 1B = 10M. Sample sizes scale
proportionally to the source table.

</details>