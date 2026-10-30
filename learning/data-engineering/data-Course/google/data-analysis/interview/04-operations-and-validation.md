# Module 4 — Operations, Validation & Reconciliation

> **14 questions · Module 4 · Operations, Validation & Reconciliation**

---

## The validation gate

### 1. What is a validation gate, and what does it protect?

**A gate is an automated set of checks that runs before a number is allowed to reach a dashboard.** It is the mechanism that converts "we trust the data" from a habit into an enforced property.

What it protects is not the data. It is **the promise a dashboard makes**. "Revenue is up 12% this quarter" is a promise that some number, computed some way, means something — and that promise breaks quietly:

- a fan-out join doubles a revenue number and nobody notices;
- a missing dimension value silently drops rows out of a total;
- a late-arriving fact means yesterday's number changes after yesterday's dashboard was read;
- a schema change removes a column and the metric goes to zero — which looks like a business event, not a bug.

**The failure story:** a company had a nightly job that wrote a "validated" flag, and the flag was set by a script that only checked the file existed and was non-empty. The job failed to run for four nights in a row — a scheduler quota — and the pipeline wrote an empty extract, which passed the check. The dashboard showed zero revenue for four days. Nobody looked, because zero revenue is a plausible number and the flag said the data was fine.

### 2. What are the four families of check, and what does each catch?

**Grain, referential integrity, completeness and freshness.**

- **Grain** — is the primary key actually unique? Catches the duplicated fact row that inflates every measure.
- **Referential integrity** — do the foreign keys resolve? Catches the blank label in a breakdown that leaves the total right.
- **Completeness** — are the required fields populated? Catches the null that quietly drops a segment.
- **Freshness** — is the data recent enough to be believed? Catches the extract that stopped running.

The ordering is not arbitrary. **Grain first** — because a duplicated primary key invalidates every measure over the table, so any other check that computes a number over it is computing a wrong number.

**The failure story:** a team checked completeness and freshness but not grain. The freshness check was green every day, the completeness check was green, and revenue was 4% too high for eleven months because one order line was being written twice by a retry in the ingestion code. Nothing else was wrong, so nothing else fired.

### 3. How do you decide whether a check should fail the build?

**ERROR only for things that make the number wrong or not current. WARNING for things worth a look. INFO for things that passed.**

And the rule that keeps a gate trusted: **never fail a build on a check that has fired before without a human deciding what to do.**

This is the whole governance question. A gate that fires on good data gets switched off within a week, and then it protects nothing. A gate that never fires protects nothing either. The design has to distinguish "this is broken" from "this is worth knowing about".

**The failure story:** a team added a check for "any row with a null product_id". Product IDs were legitimately null for gift-card orders, which were 3% of volume. The check failed the build every day. Within two weeks the team added `OR status = 'gift_card'`, and within a month someone added `OR 1=1` to the condition to stop the noise. The check was still in the file, still green, and protecting nothing — which was worse than not having it, because it created the *appearance* of a gate.

### 4. Why does freshness need a separate check, when the pipeline would fail anyway?

**Because "the pipeline ran" and "the data is current" are different claims.**

A pipeline that runs successfully against a source that stopped changing produces a perfectly valid extract of stale data. The extract is complete, the schema is correct, the grain is intact — and every number is wrong by the length of the outage.

Freshness is also the check that catches **partial** failures. A pipeline that ran and loaded three of four source files is *successful* by every structural check. Only a date comparison catches it.

**The failure story:** an extract job read from a source table whose ingestion had failed for six days. The extract succeeded daily, wrote a valid file, and the dashboard showed revenue frozen at a six-day-old level. The dashboard was read as "revenue has plateaued". It took a week to notice, because a flat line is a completely ordinary thing to see.

### 5. What is the difference between a stale extract and a genuine business event, and how do you tell them apart?

**A stale extract produces a flat line; a genuine event produces a change. The distinguishing signal is the freshness check, not the chart.**

The number that makes this concrete: if the newest row in the data is 126 days old, then *any* chart over the last 126 days is flat at the end, and the drop you are looking at is 126 days of missing data, not a business event.

The mechanism is that freshness is a property of the *whole table* — "when did this table last change?" — while the business event is a property of the *measure over time*. A table can be fresh and have a genuine drop; it can be stale and have no drop at all.

**The fix is not the chart. It is the label.** A dashboard that says "data as of 2026-05-05" makes the staleness visible at the point of use. This is the cheapest control in the whole discipline and the one most often omitted.

**Failure story:** a subscription company's weekly dashboard showed a sudden 40% drop in signups. Nobody investigated it for two weeks, because a 40% drop is exactly the sort of thing you attribute to a marketing change. The tracking SDK had broken on a deployment eleven days earlier and the events were being dropped before they reached the warehouse. The extract was still running, the schema was still correct, and the freshness check — which was comparing against the pipeline's own last-run time rather than the newest row — was green every day. The number only moved because the *volume* changed; the *freshness* never did.

### 6. What should a validation finding contain?

**Severity, a machine-readable code, a human-readable message, and a count of affected rows.**

The code matters because it is what you alert on, suppress, and trend over. The message matters because a gate that says "check failed" gets muted; a gate that says "primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated" gets acted on.

The count matters because it separates "one bad row" from "the table is broken". A single null customer_id in a million-row table is a note; the same finding in a thousand-row table is an outage.

**The failure story:** a team's validation output was a boolean. `True` meant fine, `False` meant broken. When it broke, the on-call engineer had to write a query to find out what was wrong, and one Saturday that took two hours — for a check that could have said exactly what was wrong in one line. The gate was technically working and practically useless.

## Reconciliation

### 7. What is reconciliation, and what is it for?

**Comparing the number the dashboard shows against the number the source of truth says, at the level of individual values.**

The word doing the work is **values**. Most reconciliation attempts compare row counts, and row counts are a weak signal: two systems can have identical counts and entirely different contents.

The three outcomes are `MISSING` (in the source, not in the dashboard), `EXTRA` (in the dashboard, not in the source), and `VALUE_MISMATCH` (present in both, with different values). The third is the interesting one — it is the one that a count comparison cannot see.

**Failure story:** a team reconciled their dashboard against the warehouse every night for a year, and it always matched. It was matching because both were reading the same table — a tautology that would have caught a broken pipeline exactly zero times. The reconciliation only found the real problem when they added a genuine second source: the payment processor's settlement file. That comparison showed 2% of transactions being dropped, and the nightly dashboard-vs-warehouse check had been structurally incapable of ever finding it.

### 8. Why does the reconciliation query use `IS DISTINCT FROM` rather than `<>`?

**Because `NULL <> NULL` is `NULL`, not `TRUE`.** A `<>` comparison silently drops every row where either side is null, and a null is exactly where reconciliation problems hide.

`IS DISTINCT FROM` is null-safe: it returns `TRUE` when the two values differ *or* when exactly one of them is null, and `FALSE` only when they are genuinely equal. That means a null in one system and a value in the other is correctly reported as a mismatch.

**The failure story:** a reconciliation query used `<>` and reported zero differences for six months. The actual state was that 4% of rows had a null in the warehouse that had a value in the dashboard. The `<>` filtered them out, and the query reported "0 differences" — a clean bill of health for a pipeline that was losing data in one direction.

### 9. When should you reconcile, and at what level?

**Nightly, automatically, at the level of individual rows for the measures that matter** — and the level is the decision that determines whether it is useful.

Reconciling a single aggregate number tells you *that* something is wrong. Reconciling row by row tells you *which* rows, which is the difference between an investigation and a guessing game.

The practical compromise most teams land on: a nightly row-level reconciliation on the primary key, plus a per-measure aggregate check.

**The failure story:** a team reconciled daily revenue totals against the source. For a year they reconciled every night and it always matched. It was matching because the dashboard and the source were both reading the same table. The reconciliation was a tautology and would have caught a broken pipeline exactly zero times. It took a genuine second source — the payment processor's settlement file — to find that 2% of transactions were being dropped.

### 10. What is a "grain check" in reconciliation, and why is it separate?

**A check that the two systems agree on the *level of detail*, not just the values.** The same total can be produced by completely different row structures — one system with 450 rows of £2,509 average and another with 901 rows of £1,253 average agree perfectly on the total and disagree completely on the grain.

The grain check asks: does the row count, and the distinct primary key count, agree? A total-level reconciliation passes. The grain check fails. And the grain check is the one that catches a fan-out.

**The failure story:** a dashboard's revenue matched the warehouse exactly, every night, for eight months. The dashboard was summing an order-grain table and the warehouse was summing a line-grain table — the numbers matched because the underlying data was the same. The row counts were 450 and 901. Nobody checked, because the totals always agreed, and the totals are what everybody looks at.

### 11. What is a fan-out check, and how does it differ from the grain check?

**The grain check compares row counts. The fan-out check compares the *measure* before and after the join.**

They catch different things. The grain check catches a structural difference in row counts. The fan-out check catches a measure that changes — which is what actually matters, and which a row-count comparison can miss entirely (a join that fans out by exactly 1.0x, or one that changes the measure without changing the row count).

**The failure story:** a pipeline's row count matched the source exactly, every night, for a year. The grain check was green. But the pipeline had started filtering out refunds and adding them back at the aggregate level, so the count matched and every number was wrong. The count was never going to catch it; only a value-level check would.

### 12. What is a freshness SLO, and how do you set one?

**A stated maximum age for the newest row in a model, measured in hours, with an owner.** The number is not the important part — the *statement* is.

The mechanism: without an SLO, "is the data fresh?" is a judgement call made by whoever is looking, and the answer depends on how urgently they need it. With an SLO, it is a comparison.

The setting rule: **set it from the business's tolerance for being wrong, not from the pipeline's current performance.** If the daily report goes out at 8am, the SLO is something like 6am. If the pipeline currently delivers at 4am, the SLO is 6am — not 4am. A performance measurement is not a requirement.

**Failure story:** a team set their freshness threshold from their measured pipeline performance — 4am, because that was what the job currently achieved. Six months later a scheduled job's runtime crept to 4.5am, then 5am, then 5.5am, and the freshness alert fired every single day without anyone acting on it. Because the threshold had been set from a measurement rather than a requirement, there was no principled place to argue that 5.5am was still fine. Within two weeks the alert was muted. The threshold that would have survived was 6am — the time the report was actually due.

## Operations

### 13. What belongs in a runbook for a semantic layer?

**Five things, and the fifth is the one everybody omits:**

1. the grain of every table;
2. the fan-out risk of every join;
3. the freshness expectation for every model;
4. **the exact queries to run, in order, when a number is questioned**;
5. who to page, and who to ask.

Item 4 is what makes the runbook operational rather than descriptive. When someone says "revenue looks wrong", the runbook should say: run this, then this, then this. Without it, every investigation starts from scratch, and at 9am on a Monday that is the difference between ten minutes and two hours.

**The failure story:** a company had a 200-page wiki. When a metric was questioned, the on-call engineer read the wiki, found no runbook, searched Slack history for how the last investigation was done, and eventually rebuilt the query from scratch — forty minutes, for a question that had been answered in six the previous time.

### 14. What is the query-cost problem, and how do you detect it?

**A dashboard whose query scans far more bytes than the fact table does is fanning out, and the problem gets worse as the data grows.**

The check is a ratio: the bytes scanned by the dashboard's query, divided by the bytes of the fact table. A ratio near 1.0 means the query is about as expensive as reading the fact. A ratio of 100 means the joins are multiplying work by two orders of magnitude.

**Why it matters more than the runtime:** a dashboard that takes 30 seconds is annoying. A dashboard that scans 2 TB because of a fan-out is *expensive*, and the cost grows with the data while the useful information does not. It becomes unaffordable precisely as the company succeeds.

**The failure story:** a reporting dashboard cost £4,200 a month in BigQuery because it joined a 200-million-row fact table to a customer dimension that had duplicate rows. The dashboard took 12 seconds and nobody complained — it was "fast enough". The bill was 40x the cost of the actual data, and the fix was a `relationship:` declaration that made the tool rewrite the join.

---

## The operational summary

The validation gate, the reconciliation and the runbook are three views of the same idea: **a number that nobody has checked is a number nobody can defend.** The gate prevents unverified numbers from being published. The reconciliation finds the ones that got through. The runbook makes the response to a question fast enough that people actually ask instead of guessing. None of them is interesting on its own; together they are the difference between a semantic layer that is trusted and one that is merely present.
