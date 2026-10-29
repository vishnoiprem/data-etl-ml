# Lesson 5 — Trust vs Verify

> **Type:** Article · Module 1 · AI-Powered DE Foundations
> The verification habits that turn AI from a risk into a 2–5× productivity lever.

---

## The core principle

> **Trust the speed. Verify every output.**

The whole point of AI is to move fast. The whole point of verification is to make that speed **safe**. These are not opposing forces. They are the same force in two directions.

```
     TRUST ←─────────────► VERIFY
     (AI as copilot)         (you as senior)
```

If you trust without verifying, you ship plausible-but-wrong SQL to prod. If you verify without trusting, you spend 3 hours reviewing what a junior could have validated in 15 minutes. The goal is **trust the speed, verify the output**.

---

## The five verification habits

### 1. Row count + sample
The single highest-value habit in DE.

```sql
-- after the AI writes a query:
SELECT COUNT(*) FROM <result>;

-- sample 10 rows:
SELECT * FROM <result> ORDER BY RANDOM() LIMIT 10;
```

If the row count is "close to but not exactly" what you expected, **stop**. Investigate before shipping. AI-generated SQL frequently produces wrong-but-plausible row counts (off by joins, off by filters, off by aggregations).

### 2. EXPLAIN / query plan
Especially for non-trivial queries.

```sql
EXPLAIN <query>;
```

Look for:
- Full table scans on large tables
- Cartesian products (AI loves accidentally duplicating rows)
- Shuffle / broadcast skew on joins

### 3. Tests
Every AI-generated artifact needs tests. dbt tests, pytest, whatever your stack uses.

```yaml
# schema.yml — write these even if AI didn't
models:
  - name: stg_orders
    columns:
      - name: user_id
        tests:
          - not_null
          - relationships: { to: ref('stg_users'), field: user_id }
      - name: gross_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### 4. Diff review (the code review you do to yourself)
Read the diff before commit, even if you wrote it via AI. Look for:
- A column you didn't expect
- A filter that shouldn't be there
- A type cast that loses precision
- A join that produces duplicates

### 5. Schema + sample-value sanity
After AI writes a model, run:

```sql
SELECT * FROM <model> LIMIT 5;
```

If a column looks weird (NULL when it shouldn't be, a different format, an unexpected value), investigate.

---

## Where AI is NOT allowed

Be explicit with your team. A "no AI for these" list removes ambiguity.

1. **PII / regulated data paths.** No AI on raw customer PII. Use masked or aggregated views.
2. **Production credentials.** Never paste a prod key into a prompt. Use warehouse MCP with scoped, read-only credentials.
3. **Drop / truncate statements.** AI writes the SELECT, you write the DELETE.
4. **Schema migrations on prod.** AI proposes, you review with a migration plan, peer-reviewed by a human.
5. **Anything that touches prod without a peer review.** This is just good engineering, but worth stating.
6. **Decision records / incident postmortems where you are the subject.** AI can draft; the human takes ownership.
7. **Anything legally binding.** Contracts, GDPR letters, compliance sign-offs.

---

## The cost of skipping verification

| Skip habit | Failure mode | Typical blast radius |
|---|---|---|
| Row count | Wrong revenue number on exec dashboard | One bad decision per quarter per team |
| EXPLAIN | Query times out, takes warehouse down | Hours of downtime |
| Tests | Null user_id propagates to 30 downstream models | Days of backfill + comms |
| Diff review | Filter silently dropped in refactor | Silent wrong numbers for weeks |
| Sample value | AI hallucinated a column that doesn't exist | Pipeline fails in prod, page at 3 a.m. |

---

## Building the habit

The verification habits don't appear by wishing. They appear by **installing them into your workflow**.

1. **Cursor rule (or equivalent):** force the AI to *include* a verification block with every SQL draft.
2. **PR template:** include a "How did I verify?" section. Even a one-liner counts.
3. **Team norm:** no PR merged without a verification note. Even from senior+ staff.
4. **Personal commitment:** if you shipped AI code without verifying, own the rollback. This builds the habit faster than any rule.

---

## The "where AI helps most" map (vs. where it doesn't)

| Task | AI helps? | Verify by |
|---|---|---|
| SQL first draft | ✅ Yes (5×) | Row count + sample |
| SQL debugging | ✅ Yes (3×) | EXPLAIN + run on small data |
| dbt model scaffold | ✅ Yes (5×) | Tests + diff review |
| dbt test writing | ✅ Yes (3×) | Intentionally break to confirm test fires |
| Pipeline scaffold (Airflow) | ✅ Yes (4×) | Dry-run + manual trigger |
| Pipeline logic / business rules | ⚠️ Partially | Heavy review, the logic is yours |
| Architecture decisions | ❌ No (summarise yes) | You + team |
| Incident response | ⚠️ Hypotheses only | You run the probes |
| Docs from code | ✅ Yes (10×) | Spot-check 10% by hand |
| PII / compliance review | ❌ No | You + legal |

---

## What Comes Next

> Lesson 6 — **AI-Augmented Workflow** — the end-to-end flow that ties prompt, draft, review, test, ship together. The shape of a typical day when every habit is in place.
