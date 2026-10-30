# Interview Question Bank — Semantic Layers, BI & Data Quality

> **The question bank for this course.** Module files build the understanding;
> [top-50.md](top-50.md) is the final-night revision.

---

## What this bank is

This is a working interview bank for semantic layers, BI tooling and data
quality — not a flashcard list, and not a set of definitions. Every question
was selected because the answer **changes what you build**, and every answer
is written the way a senior engineer who has actually run this in production
would say it out loud.

Each answer follows the same six-part structure:

1. **The direct answer**, in the first one or two sentences. No throat-clearing.
2. **The mechanism** — the internal concept that explains it: the grain, the
   additivity, the ratio, the join cardinality, the validity window, the
   spine, the null-safe comparison.
3. **When the alternative wins** — the trade-off and its boundary condition.
   "It depends" is never acceptable without saying what it depends on.
4. **A production failure story** — the actual symptom, and the fix.
5. **Code**, where it clarifies and nowhere else.
6. **Numbers** — row counts, percentages, pounds, days, milliseconds.

The failure story is the part interviewers probe. Anyone can recite that a
ratio must be `SUM(numerator) / SUM(denominator)`; a senior interviewer wants
to know whether you have *seen* it come out 3 points low on a £1.1M revenue
base, and what you did about it.

### How the bank is structured

| File | Questions | What it covers |
|---|---:|---|
| [01-foundations-and-the-semantic-layer.md](01-foundations-and-the-semantic-layer.md) | 14 | What a semantic layer is and what it buys you; the four objects; the grain as a contract; additivity; the ratio problem; `count` vs `count_distinct`; fan-out; grain mismatch; join cardinality; the date spine; date filter bounds; Looker Studio vs Looker vs dbt; the `{{ }}` build-time safety net; changing a measure additively |
| [02-measures-and-dimensions.md](02-measures-and-dimensions.md) | 14 | The three kinds of measure; why a ratio is sum-over-sum; the Looker Studio calculated-field trap; aggregation vs type; what a description must contain; `COUNT_DISTINCT` vs pre-aggregation; filtered measures; deprecation; dimension types; timeframes; the spine; conformed dimensions; dimension sets; dbt's entity model |
| [03-joins-and-grain.md](03-joins-and-grain.md) | 14 | Writing the grain down; the primary key as a function of the grain; grain mismatch; detecting fan-out; unresolved foreign keys; null foreign keys; SCD types 1/2/3; joining Type 2 with a validity window; surrogate keys; factless fact tables; degenerate dimensions; conformed-dimension joins; safe `many_to_many`; what belongs in a join description |
| [04-operations-and-validation.md](04-operations-and-validation.md) | 14 | What a validation gate protects; the four check families; ERROR vs WARNING vs INFO; why freshness is separate; stale extract vs business event; what a finding must contain; reconciliation; `IS DISTINCT FROM`; when to reconcile; the grain check; the fan-out check; freshness SLOs; the runbook; query cost; additive change; adoption |
| [top-50.md](top-50.md) | **50** | The highest-yield subset — read this the night before |

**Total: 106 questions.** The module files are arranged in the order the
course teaches the material; `top-50.md` is arranged by *interview theme*,
because that is how a conversation actually goes.

### How the bank maps to the chapters

| Module file | Primary chapters |
|---|---|
| `01-foundations-and-the-semantic-layer.md` | [01-what-is-a-semantic-layer](../chapters/01-what-is-a-semantic-layer.md), [05-looker-studio-and-looker](../chapters/05-looker-studio-and-looker.md) |
| `02-measures-and-dimensions.md` | [02-measures-and-dimensions](../chapters/02-measures-and-dimensions.md), [05-looker-studio-and-looker](../chapters/05-looker-studio-and-looker.md) |
| `03-joins-and-grain.md` | [03-joins-and-the-grain](../chapters/03-joins-and-the-grain.md) |
| `04-operations-and-validation.md` | [04-the-date-spine](../chapters/04-the-date-spine.md), [06-operations-and-validation](../chapters/06-operations-and-validation.md) |
| `top-50.md` | All of the above — selected for cross-layer coverage |

---

## The study plan

### If you have one hour

Read [top-50.md](top-50.md) questions 1–14. Those fourteen cover the grain,
additivity, the ratio problem, fan-out, grain mismatch and the date spine —
which is roughly 80% of what gets asked.

### If you have one afternoon

Read the whole of [top-50.md](top-50.md). Then re-read questions 4, 6, 14,
15, 24, 28, 33 and 37 — the eight with the highest failure-story density.

### If you have a full day

Read the four module files in order, then `top-50.md` as a consolidation pass.
For each question, answer it **out loud, in the six-part structure**, before
reading the answer. The point is not to read the answer; it is to find the
gap between what you would have said and what the answer says.

### How to practise

The course's semantic layer is pure Python, so you can *check* your answers
rather than trusting your memory:

```bash
cd data-engineering/data-Course/google/data-analysis
python project/local_bi.py describe
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region \
    --measures total_revenue,distinct_orders,gross_margin
python project/local_bi.py validate --input ./sample_data/orders.csv
```

Every number quoted in this bank is reproducible with those commands, and
the test suite asserts the ones that matter:

```bash
python -m pytest project/tests/ -q
```

---

## How to answer these questions

Three rules, and they are the difference between a good answer and a
recollection.

**Lead with the direct answer.** "A ratio must be `SUM(numerator) /
SUM(denominator)`" — not "well, it depends on the aggregation, and in Looker
the calculated fields are evaluated after...". The mechanism comes second.

**Always attach a number.** "That would inflate the revenue" is a shrug.
"That would inflate it by 77.6% — the regional distinct counts sum to 799
against a global 450" is an answer. A number is what makes the claim
checkable, and checkable claims are what a hiring manager remembers.

**Always bring the failure.** "I would use `IS DISTINCT FROM` because
`NULL <> NULL` is `NULL`, so `<>` silently drops the null rows — which is
where the reconciliation problems hide" is much stronger than the same
sentence without the last clause. The failure is what proves you have seen
the code in production rather than in a tutorial.

### The trap to avoid

The most common way to lose an interview on this material is to give a
**correct-but-generic** answer to a question with a specific answer. "You
should be careful about joins that cause fan-out" is correct, and it is what
every candidate says. "Fan-out happens when you traverse from the one side
to the many side, so `orders → customers` is safe and `customers → orders` is
not — I caught one last year where a customer-attributes table with two rows
per customer doubled revenue overnight, and I now run a measure-comparison
check in CI" is the answer that gets the offer.

---

## Where the numbers come from

Every figure in this bank comes from the course's deterministic dataset
(`SEED = 42`), so it is reproducible rather than illustrative:

| Figure | Value |
|---|---:|
| Order lines | 901 |
| Distinct orders | 450 |
| Distinct customers | 121 |
| Lines per order | 2.00 |
| Lines per customer | 7.45 |
| Total revenue | £1,128,941.37 |
| Average order value | £2,508.76 |
| Average line value | £1,252.99 |
| Revenue after duplicating the fact table | £2,257,882.74 |
| Regional `distinct_orders` sum | 799 (vs 450 global — 77.6% inflation) |
| Correct gross margin rate | 0.5125 |
| Margin rate via average-of-ratios | 0.4816 (3.1 points low) |
| Days with no orders in the spine | 9 of 177 |
| Age of the newest row in the sample data | 126 days |

Regenerate them yourself:

```bash
python resources/sample_data.py --output-dir ./sample_data
python project/local_bi.py validate --input ./sample_data/orders.csv
```

---

## Related material

- **[The chapters](../chapters/)** — where the material is taught.
- **[The notebooks](../notebooks/)** — the same material, executable.
- **[The project](../project/README.md)** — the semantic layer, the CLI and
  the test suite.
- **[The cheatsheet](../resources/CHEATSHEET.md)** — the one-page version of
  the whole course.
