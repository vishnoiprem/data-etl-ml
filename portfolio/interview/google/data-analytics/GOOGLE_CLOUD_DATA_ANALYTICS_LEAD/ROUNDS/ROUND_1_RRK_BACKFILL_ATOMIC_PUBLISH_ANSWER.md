# RRK: Backfill, Atomic Publish and Rollback

**Scenario:** You must backfill 2 years of data and republish a dashboard that the business uses live.
**Question:** How do you do it safely?
**Follow-up:** The backfill fails at day 400.
**Time:** about 4 minutes, then 1 minute for the follow-up.
**Pass signal:** staging, validation, atomic publish, rollback, idempotency and checkpointing, and care for live consumers, not just "rerun it".
**Runnable companion:** `ROUND_1_RRK_MOCK_LAB.ipynb`, section 3 (write-audit-publish) and the idempotent sink in section 1.

---

## 1. Short answer (the version that was supplied, kept for reference)

Write to a staging table; validate row counts, checksums and data quality; then swap atomically via partition swap or `CREATE OR REPLACE`; keep v1 for 7 days with a config-flag rollback; make the backfill idempotent, by day, checkpointed; announce a maintenance window; clear decision rights. Follow-up: resume from the checkpoint, don't restart from day 1.

Good skeleton. Fixes needed:
- **"Atomic swap via partition swap" doesn't exist as a single operation in BigQuery.** A copy or load into one partition decorator is atomic **per partition**, but swapping 730 partitions is not one atomic step. For a true single-step publish, **repoint a view** (`CREATE OR REPLACE VIEW`) from `orders_v1` to `orders_v2`, or use a multi-statement transaction for bounded changes. Know which one you mean.
- **"Maintenance window" is usually unnecessary** if you build v2 in shadow and publish by repointing a view. That is zero-downtime, and also makes the rollback a one-line repoint.
- **A backfill will change numbers the business already saw.** You need a v1 versus v2 **difference report** with explanations before you publish, and a communication to consumers.
- **New data keeps arriving** during a long backfill. The plan needs a cut-off and a delta catch-up.
- **The follow-up needs more than "resume".** Say what you do with the failed day itself, and why it failed.

---

## 2. Improved answer

**Restate (10 s):** "Two years of history to rebuild and republish, with a dashboard in live use. The bar is: no consumer ever sees a half-built or wrong dataset, numbers are explained before they change, and I can roll back in minutes."

### Step 1. Clarify (and state assumptions)
- Why are we backfilling (logic fix, new field, correction, migration)? Will historic numbers **change**? Who's affected and who has to approve?
- Volume and cost: partitions per day, size, how long, and what is the compute budget?
- Is the dashboard on a table or a view? Are there downstream consumers (extracts, models, finance)?
- Is there a regulatory or audit sensitivity to restating history?

### Step 2. Build v2 in shadow (nothing live changes)
- Write to a **separate v2 dataset or tables**, never in place.
- Process **by day (partition)**, each day **idempotent**: the day's output is written with a replace (for example a load or copy to that partition with truncate), so reruns give identical results.
- A **control table** records each day's status (pending, running, done, validated), row counts and checksums. This is the checkpoint.
- **Run it in an isolated reservation or project and throttle parallelism,** so a 2-year rebuild cannot starve the live workload.
- Freeze a **cut-off date** (for example T minus 2 days). The live pipeline keeps handling recent data; the backfill covers history up to the cut-off, and a short **delta catch-up** closes the gap just before publish.

### Step 3. Audit (before anyone sees it)
- Row counts and per-column checksums against the source or an independent control total.
- Data-quality gates: nulls, uniqueness on the key, ranges, referential integrity, distribution checks.
- **v1 versus v2 difference report** by day and metric, with each material difference explained (the fix, the new rule) and signed off by the metric owner and finance where relevant.
- A rehearsal: run the swap and the rollback in a test environment.

### Step 4. Publish atomically
- The dashboard reads from a **view** (or a stable alias). Publish = `CREATE OR REPLACE VIEW` pointing to v2, in one statement. Consumers see v1 until the instant it switches, then v2. No half-state, no downtime.
- If you must replace a table's contents, build the full new table and replace it in one `CREATE OR REPLACE TABLE`, or use a multi-statement transaction for a bounded change. Avoid replacing hundreds of partitions one by one on a live table.
- Caches and BI extracts: refresh or invalidate them, and tell the dashboard owner.

### Step 5. Roll back and retire
- **Rollback = repoint the view to v1** (a minute). Keep v1 for a defined window (for example 7 days, longer across a month-end), then drop it with an owner sign-off. A 7-day figure is an example; set it with the business.
- Monitor the first days: freshness, error rates, and consumer questions. A named person watches.

### Step 6. Communicate and decide
- Decision rights: the metric owner approves the new numbers, the platform owner approves the publish, finance approves restated figures.
- Message to consumers: what's changing, from when, why the numbers moved, and where to ask. For restated figures, publish the difference report.
- No surprise, even if no maintenance window is needed.

### Measures
Zero partial states seen by consumers; v1 versus v2 differences all explained; backfill cost within budget; rollback tested; no consumer incident in the first week.

---

## 3. Follow-up: "The backfill fails at day 400."

**Answer:** "Because every day is idempotent and tracked in the control table, I resume from the **first day that isn't marked validated**, not from day 1. Day 400 itself is **re-run**, since it may be partially written; a replace-by-partition write makes that safe. Then I look at **why** it failed before resuming. If it was transient (a quota, a timeout), I resume with backoff. If it was bad data or a logic defect, I check whether days 1 to 399 were produced with the same logic, because they might need rework too. The audit step would catch it before publish, and nothing is live from v2 until it passes, so a failure costs time, not correctness. I'd tell the stakeholders the new estimate and the cause."

---

## 4. Pass checklist

- [ ] Shadow build in a separate v2, never in place
- [ ] Idempotent per day, control-table checkpoints
- [ ] Isolated compute and throttling so live users aren't hurt
- [ ] Cut-off date and delta catch-up for data arriving during the run
- [ ] Audit: counts, checksums, quality gates, **v1 versus v2 difference report**
- [ ] Atomic publish by repointing a view (and why partition-by-partition isn't atomic)
- [ ] Rollback by repoint, with a retention window for v1
- [ ] Communication and decision rights
- [ ] Follow-up: resume from the first unvalidated day, re-run day 400, find the cause first

## 5. Likely probes

| Probe | One-line answer |
|---|---|
| "Why not just overwrite the table?" | An in-place rewrite shows consumers a half-built table and makes rollback hard. Shadow plus a repoint is safer and reversible. |
| "How do you know v2 is right?" | Counts, checksums, quality gates and a reconciled difference report signed off by the owners. |
| "What if numbers change and the CFO objects?" | I show the explained differences before publish, and agree who approves restated figures. |
| "What if new data arrives during the run?" | A cut-off date, the live pipeline for recent data, and a delta catch-up before publish. |
| "What does this cost?" | Estimate bytes per partition times partitions, run in a dedicated reservation, and report spend as it progresses. |
