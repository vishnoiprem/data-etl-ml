# RRK Mock Set 5: Production Discipline and Delivery Commercials, 60 Minutes

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Format:** one timed interview. The interviewer this time is a delivery-minded practice lead who cares about what happens after go-live and what happens to the margin.
**Why a fifth set:** the brief names these and Sets 1 to 4 leave them thin: coaching a senior consultant through an over-budget engagement, testing strategy and safe rollout for data pipelines, a wrong number reaching executives, an orchestration (Composer) code review, migrating a Hadoop and Spark estate, scope creep on fixed price, and making the practice's customers self-sufficient without losing the practice.
**How to use:** 60-minute timer, answer aloud within each block, compare, score with the rubric. Delivery marks follow `ROUND_1_RRK_SPOKEN_DELIVERY.md`.

> **Public repo.** No employer or customer names, no real figures beyond the public resume. Behavioural slots are skeletons; fill privately.

| Min | Block | Type | Topic |
|---|---|---|---|
| 0-3 | 0 | Opening | The mistake enterprises keep making |
| 3-12 | 1 | Behavioural | Coaching a senior consultant through an over-budget engagement |
| 12-24 | 2 | Technical | A wrong number reached the board; testing, rollout and rollback for pipelines |
| 24-39 | 3 | Practical | Composer DAG review, then live design of a Hadoop and Spark estate migration |
| 39-48 | 4 | Consulting | Scope creep on fixed price, partner pointing at you |
| 48-55 | 5 | Practice | "Make yourselves redundant"; three bids land in one week |
| 55-60 | 6 | Close | A time you were wrong; your questions |

---

## Block 0 (0-3 min): Opening

**Q:** "What's the biggest mistake you see enterprises make with data platforms?"

**Model answer**
> "Building the platform before anyone has agreed what decision it's for. `///` I've seen it three times at scale: eighteen months of ingestion, a beautiful lakehouse, and on day one the finance team still closes the month in a spreadsheet because nobody made them the owner of the numbers. The platform was right. The operating model didn't exist. `///` The second mistake follows from the first: treating decommissioning as something that happens by itself. It never does. The old system runs for three more years, you pay for both, and the new one never becomes the source of truth. `///` So the two things I insist on in any programme: a named business owner for every data product before we build it, and retirement of the old thing funded as a deliverable, not a hope."

**Follow-up:** "Have you made that mistake yourself?" → "Yes. [One sentence, real, private.] It's why I insist on it now."

---

## Block 1 (3-12 min): Behavioural, coaching a senior consultant

**Q:** "A senior consultant you manage is leading an engagement that's 30% over budget at the halfway point. Tell me about a time you coached someone through that, and what you did."

**STAR skeleton (fill privately)**
> **S:** "[A senior engineer or lead] was running [a programme: scope, size]. At the midpoint, [effort or cost] was about [30]% over plan, and they hadn't raised it. I found out from [the finance report, a stakeholder]."
> **T:** "Recover the engagement, and keep the person. Both."
> **A:** "First conversation within a day, and not 'why didn't you tell me'. 'What's the picture, what do you need, what do you think happened?' Three causes came out: [scope absorbed without a change request; a dependency that slipped; an estimate that assumed clean data]. We did three things together. One: I sat with them to build the recovery options, cut scope, add capacity, move the date, each costed, but **they** presented them to the sponsor, with me in the room. Two: a weekly thirty-minute review of burn against plan, which I'd run with every lead from then on, not only this one. Three: the coaching itself: the skill they were missing wasn't technical, it was saying 'that's a change' to a customer they liked. We rehearsed it."
> **R:** "[Re-baselined by week N; final variance X%; the customer renewed or didn't.] They led the next engagement and came in under budget. **The miss:** I'd set up the weekly burn review for the whole practice only after this. The signal had been in the finance report for six weeks; nobody was reading it, including me."

**Follow-ups the interviewer will use**
1. "Why hadn't they told you?" → the honest answer is usually about your own signals: did you make bad news safe to bring?
2. "What would you have done if they'd hidden it deliberately?" → different conversation; integrity, not capability.
3. "What's your rule now?" → "Any variance over 10% is raised the week it's seen. Raising it is never the problem. Hiding it is."

---

## Block 2 (12-24 min): Technical, a wrong number reached the board

**Q:** "Last quarter, a revenue figure on the board deck was wrong by 4%. It came from a pipeline your team owns. Walk me through what you do, and how you make sure it doesn't happen again."

**Model answer**
> "**First 24 hours:** confirm the right number and get it to the CFO with the explanation, before anything else. Then find the cause, not the culprit. The likely classes: a definition change nobody propagated, a late-arriving partition that was read before it was complete, a duplicate from a retry, a join that fanned out, a currency or timezone boundary. I'd trace that one figure from the deck back to the source, one hop at a time, with the actual query at each hop.
>
> **The fix is a testing and release strategy, not a patch.** Four layers.
>
> **Unit tests on transformations:** given these ten rows, this is the output; run on every commit. **Contract tests at ingest:** schema, nullability, value ranges, row-count bounds; a drift fails the load before it lands. **Reconciliation tests on publish:** the curated total against the source-of-record total within a tolerance agreed with finance; a miss blocks publication. **Freshness and volume monitors in production:** a partition that's 20% smaller than the same weekday last month pages someone before the deck is built.
>
> **Safe rollout and rollback for pipelines** works like it does for services. Every change deploys to a shadow target first; we run it against yesterday's data and diff the output against the current pipeline's output. Zero unexplained differences, or it doesn't promote. Promotion is a view repoint, so rollback is one statement. Raw is immutable, so any day can be recomputed. Every change has a named owner and a change record.
>
> **The organisational half:** finance owns the definition of revenue, and it lives in one place, the semantic layer, not in six dashboards. The board number comes from certified content only.
>
> **Measure:** reconciliation defects caught before publish, time from defect to detection, and zero uncertified numbers in executive decks. **Prevent the quiet version:** a blameless post-mortem within a week, published to the whole team."

**Follow-up A:** "The CFO wants a guarantee it won't happen again." → "I'd say no guarantee is honest, and give them something better: the reconciliation gate means a wrong number can't be published; it can only be late. I'd ask them to choose late over wrong, and I'd put that in the SLO."

**Follow-up B:** "How do you test a streaming pipeline?" → "Same four layers, different mechanics. Unit tests on the transforms with a test stream. Replay a recorded day of events through the new version and the old in parallel, diff the sinks. Canary: route a percentage of keys through the new job before full cutover. Rollback: drain the new job, the old is still running. The invariant is that the sink is idempotent, so a replay after a rollback is safe."

**Follow-up C:** "What about data contracts, concretely?" → "A versioned schema and a set of guarantees the producer signs up to: fields, types, nullability, freshness, and a change process with notice. Enforced at ingest, not by goodwill. The consumer sees the version they coded against until they move. The contract is a file in a repo with an owner, reviewed like code."

---

## Block 3 (24-39 min): Practical

### 3a. Composer DAG review (6 min)

"This runs nightly in Cloud Composer. Review it."

```python
default_args = {"owner": "data", "retries": 3}

with DAG("daily_sales",
         start_date=datetime(2024, 1, 1),
         schedule_interval="0 2 * * *",
         default_args=default_args,
         catchup=True) as dag:

    def load(**ctx):
        today = datetime.now().strftime("%Y-%m-%d")
        df = pd.read_gbq(f"SELECT * FROM raw.sales WHERE DATE(ts) = '{today}'")
        df.to_gbq("mart.daily_sales", if_exists="append")

    PythonOperator(task_id="load", python_callable=load)
```

**Model review (order: correctness, idempotency, scale, semantics, security, maintainability)**
> "1. **Correctness: it processes the wrong day.** `datetime.now()` is wall-clock time at execution, not the run's logical date. A run at 02:00 loads 'today', which has two hours of data. A backfill of last March loads today's data into every one of those runs. Use the logical date from the context, `ds` or `data_interval_start`.
> 2. **Idempotency: `if_exists='append'` plus `retries=3`.** A task that fails after writing and retries appends the day again. Any rerun duplicates the day. Write to a partition decorator, `mart.daily_sales$YYYYMMDD`, with truncate semantics, or `MERGE` on a key. The run must be safe to execute twice.
> 3. **`catchup=True` with a 2024 start date.** First deployment schedules every missed day since January 2024, hundreds of runs at once, each loading 'today'. Either `catchup=False` or a start date you mean, and a pool or `max_active_runs` to bound concurrency.
> 4. **Scale and cost.** `SELECT *` through pandas pulls the whole day into a worker's memory and back out. This is a BigQuery-to-BigQuery transformation; it should be a single SQL statement run by a BigQuery operator, no data leaving BigQuery. `DATE(ts)` on an unpartitioned or wrongly partitioned column is a full scan each night; filter on the partition column.
> 5. **Semantics.** `DATE(ts)` is UTC; the schedule is 02:00 in the Composer timezone; the business day is probably local. Three different days. Define the business day once and use it.
> 6. **Reliability.** No data-quality check before the write, no row-count assertion, no SLA or alert. A silent zero-row day is 'success'.
> 7. **Maintainability and security.** SQL built by f-string, a generic owner, no tests, and the worker's identity needs both read on raw and write on mart; scope it to one service account per DAG.
>
> **Sentence to say:** 'This DAG is correct exactly once: the first run, if nothing fails. Every retry, rerun or backfill makes the mart wrong. Fix the date and the write mode first; they're both one-line changes with enormous blast radius.'"

**Follow-up:** "The engineer says they've never seen a duplicate." → "They've never had a retry at the wrong moment. The mechanism is there; the luck has held. I'd rather the design didn't depend on luck."

### 3b. Live design (9 min)

**Q:** "A telco runs 500 Spark and Hive jobs on an on-premises Hadoop cluster, 2 PB, licence renewal in 14 months, a team of 25 who know Spark and nothing else. Design the migration and defend it."

**Model answer**
> "**Outcome:** off the cluster before renewal, without losing 25 people's productivity or 500 jobs' correctness. **NFRs to confirm:** how many of the 500 run in a given month, how many are interactive versus scheduled, peak compute shape, data residency, and the team's appetite to learn SQL-first tooling. The team is the main constraint, so I'd design around it.
>
> **Options.** A: rewrite everything to BigQuery SQL. Best end state, but 500 jobs in 14 months with a Spark team is a rewrite project that misses the renewal. B: lift the whole estate to Dataproc as a persistent cluster. Fast, but recreates the on-prem cost model in the cloud. C: **lift to Dataproc, but ephemeral and serverless, with storage separated, then modernise by workload.** Recommend C.
>
> **Draw it.** Data moves first: HDFS to Cloud Storage, bulk transfer for the 2 PB then incremental sync until cutover. Hive metastore to Dataproc Metastore so every job finds its tables. Jobs run on Dataproc Serverless for Spark where they can, ephemeral clusters per workload where they need specific configuration, nothing permanent. Orchestration in Composer. Then, by workload: the reporting and aggregation jobs, usually most of them, move to BigQuery with BigLake over the same Cloud Storage files so nothing is copied; the true Spark workloads, feature engineering and ML, stay on Dataproc or move to Vertex AI. Governance from day one: Dataplex over Cloud Storage and BigQuery, IAM per domain, perimeter, CMEK.
>
> **Failure path.** The job that works on-prem and silently differs in the cloud: a different Spark version, a different timezone default, a Hive setting nobody documented. So: pin versions, run every job against the same input on both sides for one cycle, diff the outputs, and only then retire the on-prem job. A job isn't migrated until its diff is zero and its on-prem copy is off.
>
> **The people.** Twenty-five Spark engineers become the team that owns this. Dataproc first because it's their language; BigQuery second with structured enablement and the first ten jobs done in pairs. Certification targets as part of the plan, not an afterthought.
>
> **Cost.** Ephemeral compute means the bill tracks usage, not cluster size. Storage classes on Cloud Storage for the cold PB. The number I'd watch monthly: cost per job and cluster-hours with zero jobs running, which should be zero.
>
> **Plan.** Months 1-2: inventory, dead-job retirement, landing zone, metastore. 3-5: data moved, the first fifty jobs on Dataproc with diffs. 6-11: the rest in waves, BigQuery modernisation starting with reporting. 12-13: on-prem read-only, decommission. 14: renewal declined.
>
> **Trade-offs.** I rejected a persistent cluster because it's the same cost model with a different logo. I rejected rewrite-first because the team can't do it in 14 months and the renewal is the only hard date."

**Follow-up:** "Why not just put everything in BigQuery and retrain the team?" → "Because the date is fixed and the team isn't. The 14 months buys us the move; the modernisation continues after it, on a platform that doesn't have a renewal."

---

## Block 4 (39-48 min): Consulting, scope creep on fixed price

**Q:** "You're six weeks into a fixed-price engagement. The customer's programme manager has added eleven 'small' requests, the GSI partner delivering half the work says your team's delays are the reason their track is late, and the sponsor has asked for a status call tomorrow. What do you say on that call?"

**Model answer**
> "Before the call, I want three facts: the eleven requests listed against the signed scope with an effort estimate each; our actual delivery against plan on our track, with dates; and the partner's dependency on us, with the dates they asked and the dates we delivered. Facts first, because tomorrow's call is about accountability and I need to know how much of it is mine.
>
> **On the call, three parts.** **Status first, honestly:** here's where we are against plan, here's what's late, including anything that's ours. If any of the partner's claim is true, I say so before they do. **Then scope:** these eleven items aren't in the statement of work. Here's the effort for each. Some are genuinely small and I'll absorb them as a goodwill decision I'm making openly, with a number attached. The rest are a change request, and here are two ways to fund them: a change order, or a trade against lower-priority scope. **Then the partner:** I don't litigate it on the sponsor's call. I say the dependency dates are documented, I'll review them with the partner lead this week, and we'll bring the sponsor one joint view of the critical path next week.
>
> **What I'm protecting:** the sponsor's trust, which comes from hearing bad news from me first, and the margin, which dies when 'small' requests are absorbed silently. **What I'm not doing:** blaming the programme manager for asking. Asking is their job. Saying 'that's a change' is mine.
>
> **Afterwards:** a weekly scope log the customer sees, every request logged on the day with an estimate, and a joint plan with the partner that has one critical path, not two. **Measure:** change requests signed versus absorbed, variance against plan, and whether the sponsor calls me or the partner first when something goes wrong."

**Follow-up:** "The programme manager says the eleven items were 'obviously implied' by the scope." → "Some may be, and I'll concede those on the spot. For the rest, the statement of work is what we both signed, and the way to keep the relationship is to be clear now, not resentful in month six."

---

## Block 5 (48-55 min): Practice

**Q1:** "A customer's CDO says: 'I want you to make yourselves redundant. Build our team so we don't need consultants.' How do you respond, and how does that square with running a practice?"

**Model answer**
> "I'd say yes, and mean it, because it's the best thing we can sell. A customer that becomes capable renews for the next hard problem; one that stays dependent churns the moment the budget is cut.
>
> **How I'd structure it:** every workstream has a customer lead paired with ours, with a date by which the customer lead runs it. Enablement is a deliverable with acceptance criteria: certifications, a design review they chair, an incident they handle. Our assets, the accelerators, the runbooks, the reference architectures, are handed over, not licensed. We measure our own ramp-down: our share of the hours falls quarter on quarter, and that's success, not leakage.
>
> **How that squares with the practice:** our revenue should come from the next problem, not the same one. A practice that depends on customers never learning is a practice with a ceiling. The ones that grow sell capability transfer and then get invited to the next transformation. And it changes the mix: fewer long T&M tails, more discovery and architecture, which is higher margin and higher value per hour.
>
> **What I'd watch:** the customer team's readiness honestly assessed, so we don't leave before they can carry it; and a clear end-state agreement so 'redundant' has a definition and a date."

**Q2:** "Three large bids land in the same week and you have capacity for one. How do you decide?"
> "Not by size. Four questions per bid: is there a sponsor for a business outcome, or a procurement exercise? Can we win it on merit, or are we the price check? Does it build an asset or a reference we can reuse? And can we staff it with the right people, not just enough people? I score them with the account teams in the room, pick one to lead, one to partner-led with us on architecture and quality, and one to decline well: a conversation with the customer about timing, not silence. The decline is a relationship investment. And I'd use the week as evidence for the capacity plan: three in a week isn't an anomaly if the pipeline said so a quarter ago."

---

## Block 6 (55-60 min): Close

**Q:** "Briefly: a time you were wrong about something important."
> "[Fill privately. Structure: what I believed, what evidence I ignored or didn't have, what it cost, what I do differently now, with a mechanism not a resolution.] The pass signal is a real cost and a real mechanism. 'I learned to listen more' fails."

**Your questions (pick two)**
1. "What does the practice do after an engagement ends to know whether the customer actually adopted what we built?"
2. "How does the practice handle a partner conflict when the customer is watching?"
3. "What's the engagement you'd most want to re-run with what the practice knows now?"

---

## Scoring (0 to 2 per line, 8 per block, 48 total for blocks 0 to 5)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| Structure | Jumped to a solution | Some clarifying | Restated, clarified, stated assumptions, then options |
| Judgement | Component list or "it depends" | Options, weak pick | 2 to 3 options, trade-offs, a clear recommendation |
| Evidence and numbers | Vague | Some figures | Defensible numbers with baseline, method and your role |
| Enterprise scope | Single project | Mentions operations | Ownership, adoption, rollback, decommission, cost |

**Targets:** 36 or more of 48 is ready. 27 to 35: repeat the weakest two blocks. Under 27: restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.

**Hard fails for this round:** blaming the consultant, the programme manager or the partner; a testing answer with no reconciliation gate; a DAG review that misses the `datetime.now()` defect; absorbing scope silently; a "time you were wrong" with no cost.
