# RRK Mock Set 3: One Full 60-Minute Interview

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Format:** a single timed interview, in the block order of `ROUND_1_RRK_RUNSHEET_AND_ARCH_DRILL.md`. Seven blocks, 60 minutes, with follow-ups the interviewer is likely to use.
**Why a third set:** Sets 1 and 2 are question banks. This set is a rehearsal, and it covers what the earlier sets leave thin: CDC with deletes and erasure, schema evolution, Beam triggers, a SQL `MERGE` review, Dataflow observability, utilisation and margin arithmetic, and when not to bid.
**How to use:** start a 60-minute timer. Read each question aloud, answer aloud within the block time, then compare. Score each block with the rubric at the end. Model answers are written at spoken length (about 2 minutes, 250 to 300 words); the follow-ups are where the interviewer decides.

> **Public repo.** No employer names, customer names or real figures here. Fill behavioural slots privately. Product facts change; verify prices and limits before quoting.

| Min | Block | Type | Topic |
|---|---|---|---|
| 0-3 | 0 | Opening | 90-second background and "why this role" |
| 3-13 | 1 | Behavioural | A migration cutover you led |
| 13-25 | 2 | Technical | CDC with deletes, erasure, schema drift |
| 25-40 | 3 | Practical | SQL `MERGE` review, then live design of a fraud-feature platform |
| 40-50 | 4 | Consulting | Customer standardised on another cloud; GSI partner in the room |
| 50-56 | 5 | Practice | Utilisation and margin, with the arithmetic |
| 56-60 | 6 | Close | Your two questions |

---

## Block 0 (0-3 min): Opening

**Q:** "Give me 90 seconds on your background, then tell me why a lead role in Google Cloud Consulting rather than staying as a head of data."

**Model answer**
> "Fifteen years in data, the last eight leading platforms: a VP role at a large e-commerce group building a real-time logistics data platform, then head of data engineering at a multi-country retail group, where I own the data, analytics and AI strategy and a thirty-person organisation across four domain squads. The outcome I'm proudest of there: month-end financial close went from five days to two hours, measured by the finance team's sign-off time, because we rebuilt the ledger pipelines on a lakehouse with reconciliation built in rather than bolted on.
>
> Why this role: I've been the customer in three large platform programmes. I know where consulting engagements fail, which is after the architecture is right and before the operating model exists. I want to do that work across many enterprises instead of one, and I want to do it on a stack where the serverless and AI layers are the strongest I've evaluated. I'm honest that my production depth is on other clouds; I've been closing that gap deliberately and I'd expect to certify in my first quarter."

**Why it passes:** one number with its method, a reason for Google that an interviewer can't hear from every candidate, and the gap stated before it's asked.

**Follow-up:** "Which part of that was you, rather than your team?"
> "The decision to put reconciliation in the pipeline rather than in a month-end spreadsheet, and the decision to make finance the owner of the metric definitions. My team built it; I made the two calls that made it stick."

---

## Block 1 (3-13 min): Behavioural, a migration cutover

**Q:** "Tell me about a migration you led where the cutover was reversible. What did you do, and what went wrong?"

**STAR skeleton (fill privately; every number needs a baseline and a method)**
> **S:** "[Legacy warehouse or platform], about [X] TB, [N] downstream reports, [cost or pain]. The business constraint was [a month-end, a regulator, a contract end]."
> **T:** "I owned [architecture and cutover plan]. Non-negotiable: no reporting outage across a month-end."
> **A:** "Four moves. One, inventory first; we retired about [Y]% of pipelines nobody used, which shortened everything. Two, dual-run for [N] weeks including one month-end, reconciling counts, sums and per-column checksums daily, not just row counts. Three, cutover behind a view switch per domain, so rollback was one statement and the old platform stayed read-only for [N] days. Four, decommission as a funded deliverable with a named owner, otherwise it never happens."
> **R:** "[X] TB moved, [runtime A to B], [cost A to B by mechanism], zero Sev-1 discrepancies at cutover. **What went wrong:** [one real miss, e.g. a timezone defect in one domain that dual-run caught in week two, or a consumer we didn't know existed]. **What I'd change:** [one real thing]."

**Follow-ups the interviewer will use**
1. "How did you know the reconciliation was good enough?" → tolerances agreed with finance in advance; every difference explained, not just within tolerance.
2. "What did you decommission, and who signed it off?" → if you can't name it, the interviewer assumes it's still running.
3. "What did the dual-run cost, and who paid?" → have the number and the trade-off.

**Rules:** under two minutes, "I" not "we", one honest miss, stop talking.

---

## Block 2 (13-25 min): Technical, CDC with deletes and erasure

**Q:** "A retailer wants its operational order database replicated into BigQuery. Updates and deletes must be reflected, the schema changes monthly, and legal says personal data must be erasable within 30 days of a request. Design it and recommend."

**Model answer**
> "**Restate:** trustworthy analytics on operational data, with deletes and updates correct, schema drift survived, and a provable erasure path. Two questions: what freshness, and is there a residency rule? If unanswered I'll assume minutes-level freshness and in-country storage.
>
> **Options.** A, nightly extract and reload: simple, but it misses hard deletes unless you diff, and freshness is a day. B, log-based CDC with Datastream into BigQuery: inserts, updates and deletes from the write-ahead log, no load on the source tables, managed. C, Debezium to Pub/Sub to Dataflow: most control, but we become the operators of connectors, ordering and schema handling. **I recommend B** for a team with no platform headcount, moving to C only if we need in-flight transformation or an unsupported source.
>
> **Correctness.** An append-only raw change log, then a curated current-state table, so replay and audit are always possible. Changes applied by primary key in source-log order, not arrival order, so retries and restarts are safe. Deletes carried as delete events, with a soft-delete flag in curated so consumers choose. Backfill is a consistent snapshot then CDC from that log position: no gap, no overlap.
>
> **Schema drift.** Additive columns flow through. Type changes and drops hit a contract check that alerts the owner instead of breaking dashboards silently.
>
> **Erasure.** A subject-to-key index; delete in raw, curated and every downstream copy; and one subtlety: BigQuery time travel keeps deleted rows recoverable for up to seven days, so I'd set the window to the minimum our recovery policy allows and document it in the legal position. Then the 30-day clock is met provably, not hopefully.
>
> **Security and cost.** A service account scoped to the replication path, a VPC Service Controls perimeter, policy tags on personal columns, a regional dataset, partitioning by change date with partition filters required.
>
> **Measure.** Replication lag under the freshness SLO, daily source-to-target reconciliation with zero unexplained differences, and an end-to-end erasure test that passes."

**Follow-up A:** "Datastream fails halfway through the initial snapshot. Now what?"
> "Nothing is published yet, so no consumer sees partial data: the snapshot lands in raw, and curated is only built once the snapshot is complete and reconciled. I restart the backfill from the last committed table or chunk, verify counts and checksums per table against the source, and only then start CDC from the recorded log position. The restartable unit is the table, not the whole snapshot."

**Follow-up B:** "Two tables reconcile perfectly but a revenue dashboard is wrong. Where do you look first?"
> "Not in the pipeline. If the data reconciles, the defect is in a definition or a join: a metric defined two ways, a filter nobody knows about, a timezone or currency boundary, or a many-to-one join duplicating amounts. I trace that one number from the dashboard back to the curated table and compare the semantic-layer definition with finance's. Then one definition, one owner."

**Follow-up C:** "How do deletes and late updates behave if you build this on Dataflow instead?"
> "Three things to get right. Event-time windows with allowed lateness set from the measured p99 of arrival delay. Accumulation mode: if the sink is an upsert keyed on the business key, I want accumulating panes so each firing carries the full current value; discarding panes only work for additive sinks. And data arriving after allowed lateness is dropped by the window by default, so a dead-letter path needs an explicit lateness check before the window, plus a counter I alert on and reconcile daily."

---

## Block 3 (25-40 min): Practical, code review then live design

### 3a. SQL review (6 min)

"This runs hourly to keep a current-orders table up to date. Review it."

```sql
MERGE `analytics.orders_current` T
USING (
  SELECT * FROM `raw.orders_changes`
  WHERE ingest_ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
) S
ON T.order_id = S.order_id
WHEN MATCHED THEN
  UPDATE SET status = S.status, amount = S.amount, updated_at = S.updated_at
WHEN NOT MATCHED THEN
  INSERT (order_id, status, amount, updated_at)
  VALUES (S.order_id, S.status, S.amount, S.updated_at)
WHEN NOT MATCHED BY SOURCE THEN
  DELETE;
```

**Model review (order: correctness, idempotency, scale, semantics, security, maintainability)**
> "1. **The `NOT MATCHED BY SOURCE ... DELETE` is the critical defect.** The source is only the last hour of changes, so every order that didn't change in the last hour gets deleted from the current table. Each run wipes most of the table. Deletes must come from explicit delete events (an `op = 'D'` flag), never from absence in an incremental source.
> 2. **No dedup in the source.** If one order has three changes in the hour, `MERGE` fails with a duplicate-source-row error, or if the key is non-unique in a different way, it applies them in undefined order. Fix: `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, log_position DESC) = 1`.
> 3. **Not idempotent or restart-safe.** The window is relative to `CURRENT_TIMESTAMP()`, so a run delayed by 90 minutes skips 30 minutes of changes, and a rerun picks up a different set. Use a high-water mark stored in a control table, inclusive of the last processed `ingest_ts` or log position.
> 4. **Out-of-order updates.** `WHEN MATCHED` overwrites unconditionally. An older change arriving late regresses the row. Add `AND S.updated_at > T.updated_at` to the match clause.
> 5. **Cost.** No partition filter on the target. If `orders_current` is partitioned, prune with the keys in the source; if it isn't, this is a full-table scan and rewrite every hour. Also `SELECT *` pulls columns that aren't used.
> 6. **Semantics.** `amount` type and currency aren't shown; if `amount` is `FLOAT64`, money is wrong by construction. `NUMERIC`.
> 7. **Maintainability.** No assertion that the source has no nulls on the key, no row-count check before and after, no dry-run cost guard.
>
> **Sentence to say:** 'This statement is correct only if every order changes every hour, arrives once and in order. None of those is true. I'd fix the delete clause first because it destroys data; everything else is about correctness under retry.'"

**Follow-up:** "The engineer says the delete clause is fine because they run a full reload nightly." → "Then for 23 hours a day the current table is wrong, and the nightly reload hides the defect rather than fixing it. The cost of a full daily reload is also the cost that makes this the top line on the bill."

### 3b. Live design (9 min)

**Q:** "A payments company wants real-time fraud scoring. The model needs features computed from the last 10 minutes of activity and from 90 days of history. Draw the platform and defend it."

**Order of play:** outcome and users → quantify NFRs → draw → one failure path → security and cost → trade-offs.

**Model answer**
> "**Outcome:** a score on every transaction before authorisation completes. So the decision latency is the budget: say under 200 ms end to end, which leaves tens of milliseconds for feature lookup. **NFRs I'd confirm:** transactions per second at peak, false-positive tolerance, availability (this is in the payment path, so 99.99% or better), residency, and whether the model team needs the same features offline for training. Assume yes; that's the whole design problem.
>
> **Draw it.** Transactions published to Pub/Sub. One Dataflow streaming job computes the short-window features (counts, sums, velocity over sliding 10-minute windows, keyed by card and merchant) and writes them to a low-latency online store, Bigtable, keyed for single-row reads. The same job writes the raw events to BigQuery, append-only and partitioned. A batch job in BigQuery computes the 90-day features and publishes them to the same online store on a schedule, and to the offline feature table. The model is served on Vertex AI endpoints; the scoring service reads online features, scores, and writes the decision and the features used back to BigQuery for audit and training. Both feature paths share one feature definition registry, so online and offline are computed from the same logic.
>
> **Failure path, late and duplicate events.** A duplicate transaction event would double a velocity count and trigger false declines, so dedup on the transaction ID inside the window with a bounded state TTL. A late event moves a count after the decision was made; I accept that for scoring and correct it in the offline table, because the decision latency matters more than the count being perfect at the edge.
>
> **Observability.** On the Dataflow job: system lag, backlog age, data freshness and watermark lag, alerted against the freshness SLO; on the online store, p99 read latency; on the model, score distribution drift and decline rate by segment.
>
> **Security and cost.** The write path is a single service account per job, perimeter around BigQuery, Bigtable and the endpoint, tokenised card numbers before the data ever lands. Cost control: Bigtable sized for peak reads with autoscaling, BigQuery partition filters, and a feature TTL so the online store doesn't grow forever.
>
> **Trade-offs.** I rejected computing all features in BigQuery at request time: wrong tool for a 50 ms read. I rejected a single streaming job for 90-day features: state too large and a restart replays 90 days. The split is the design."

**Follow-up:** "The model team says their offline training accuracy doesn't reproduce in production." → "Training-serving skew. The fix is structural, not a retrain: one feature definition compiled to both the streaming and batch path, point-in-time correct joins in the training set, and logging the exact features used at scoring time so training uses what the model actually saw."

**Virtual-drawing note:** have a blank diagram tool open before the call (a shared whiteboard or a slide). Draw left to right, label the arrows with what flows, add governance as a vertical bar last. If drawing isn't possible, narrate the diagram in the same left-to-right order and say so.

---

## Block 4 (40-50 min): Consulting, another cloud and a partner in the room

**Q:** "A bank's CIO has standardised on a competitor cloud and its warehouse. The account team wants you to pitch a full migration to BigQuery. A global SI partner is already embedded there. What do you do?"

**Model answer**
> "**First, separate the outcome from the solution preference.** A full migration is the account team's preferred solution. The question is what business outcome the bank has that its current platform can't meet. If there isn't one, we shouldn't bid for a migration, and I'd say so to the account team with reasons.
>
> **Where I'd look for the outcome:** workloads where our platform is materially better for them: AI on their data without data movement, serverless analytics on unpredictable workloads, streaming at scale, or a regulatory or cost pressure the current platform is failing. Also, what their data teams are struggling with in practice, from their engineers, not the CIO's slides.
>
> **Options.** A, full migration: highest value to us, highest risk to them, and against the CIO's stated direction, so low probability and a trust cost if we push it. B, a coexistence foothold: one workload where we win on merit, interoperating with the incumbent through open formats and federation, proving value in a quarter. C, no bid now; stay close, invest in the relationship, revisit at their next platform decision point.
>
> **I'd recommend B,** scoped as a paid discovery and a lighthouse, with the exit criteria written down. It respects the CIO's decision while giving them evidence.
>
> **The partner.** I treat the SI as a stakeholder with its own incentives, not an obstacle. Clear decision rights up front: who owns architecture, who owns delivery, who the customer calls when something breaks. If the partner's incentive is to protect the incumbent estate, I surface that to the sponsor as a governance point, not as an accusation.
>
> **When I would not bid:** no executive sponsor for an outcome, a regulator or residency rule we can't meet, or a margin that only works if the partner delivers for free. Walking away well is part of the job."

**Follow-up:** "The account team says you're leaving money on the table." → "I'm leaving a loss on the table. A migration sold against the CIO's direction is a troubled engagement in nine months, and we'd all be in the room for that too. Let's win the one workload and earn the second."

---

## Block 5 (50-56 min): Practice, the arithmetic

**Q:** "Your practice is at 78% utilisation but delivery margin is falling. Walk me through what's happening, with numbers."

**Model answer**
> "Utilisation up and margin down almost always means one of three things: over-delivery, wrong staffing mix, or rate erosion. Let me put numbers on it.
>
> Take a consultant with a fully loaded cost of $200K a year, about 1,800 available hours, so about $110 an hour. Billed at $250 an hour, at 78% utilisation that's 1,400 billable hours, $350K of revenue, and a margin of about 43% at the individual level, before practice overhead.
>
> Now the three leaks. **Over-delivery:** if that consultant works 1,600 hours on fixed-price engagements but we only recognise 1,400, utilisation reads fine and margin drops roughly eight points; the time is real, the revenue isn't. **Staffing mix:** if a senior architect at $160 an hour cost is doing work scoped for a $90 an hour engineer, margin on that work falls by about a third, and utilisation still looks healthy. **Rate erosion:** a discount from $250 to $220 to win a deal takes twelve points of revenue at the same cost.
>
> **Which matters most:** margin, because it is the outcome; utilisation is an input, and a 78% number can hide every one of those leaks. The target band I'd run is utilisation in the mid-seventies for seniors, higher for delivery staff, with the remaining time deliberately spent on assets, pre-sales and enablement, which is what makes the practice scale beyond the people in it.
>
> **What I'd do this quarter:** reconcile hours worked against hours recognised per engagement to size over-delivery; make any over-delivery a conscious, approved investment or a change request; review staffing mix against the scoped pyramid; and put a three-month forward capacity view against probability-weighted pipeline so hiring and partner leverage are planned, not reactive.
>
> **Honesty line:** I've owned a platform budget with real trade-offs, not a consulting P&L. The mechanics transfer; the rate card and margin model here I'd learn in my first thirty days."

**Follow-up:** "How much over-delivery is acceptable?" → "Any amount that was decided in advance for a reason: land-and-expand, a reference customer, protecting a renewal. Zero that was discovered after the fact."

---

## Block 6 (56-60 min): Close

Ask two. The interviewer scores whether your questions are about the practice, not about yourself.

1. "What separates the practice leads who thrive here in the first year from those who struggle?"
2. "Where is the practice tightest today: pre-sales capacity, delivery capacity, or reusable assets?"
3. "Which customer programme in the region would you most want the person in this role to have led?"

Close with one line: what you heard about the role, and that you want it.

---

## Scoring (0 to 2 per line, 8 per block, 48 total for blocks 0 to 5)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| Structure | Jumped to a solution | Some clarifying | Restated, clarified, stated assumptions, then options |
| Judgement | Component list or "it depends" | Options, weak pick | 2 to 3 options, trade-offs, a clear recommendation |
| Evidence and numbers | Vague | Some figures | Defensible numbers with baseline, method and your role |
| Enterprise scope | Single project | Mentions operations | Ownership, adoption, rollback, decommission, cost |

**Targets:** 36 or more of 48 is ready. 27 to 35: repeat the weakest two blocks. Under 27: restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.

**Hard fails:** a number you can't defend; blaming a team or a partner; no clarifying question before a design; a recommendation with no risk and no measure; running past the block time.

**Time check:** if you are still talking at two minutes on any single answer, stop and say "I'll pause there; happy to go deeper on any part."
