# Behavioral (Ownership) Round — Story Bank

Five STAR-format story scaffolds for the Meta DE Ownership round. Each story is paced to **under 5 minutes**, leads with the situation, walks through your specific actions ("I", not "we"), and closes with a measurable outcome.

> The 5-minute cap matters. Going over costs you question volume. **Rehearse aloud with a timer** until each story lands at 3:00–4:30.

---

## Story 1 — Led a project end-to-end

**Prompt:** Tell me about a time you led a project end-to-end.

**Use when:** Asked about ownership, end-to-end delivery, or "what's the project you're most proud of."

### Scaffold

- **Situation (≤30s)** — Set context: what was the business problem, why did it matter, who were the stakeholders?
- **Task (≤30s)** — Your specific responsibility: scope, timeline, what "done" meant.
- **Action (≤2m)** — What *you* did: defining milestones, unblocking the team, making the key technical trade-off, communicating status. Be specific. "I designed the ingestion schema," not "we worked on it."
- **Result (≤30s)** — Measurable impact + a thing you'd change.

### Sample (data-quality theme)

> **S:** Our analytics dashboards were showing a 12% gap between the orders pipeline and the source-of-truth OLTP DB, and finance was losing trust in the numbers. I was the lead data engineer on the reconciliation project over a 4-month span.
>
> **T:** I owned defining the daily reconciliation job end-to-end — schema design, the diff logic, the alerting policy, and the rollout plan across the 3 product teams that depended on the tables.
>
> **A:** I designed a row-hash-based comparison instead of full-table diffs, which kept the job under 10 min even on our largest 2B-row table. I wrote the alert routing rules so on-call got paged only when the gap crossed 0.5%, not on every transient blip. I drove the rollout: ran the job in shadow mode for two weeks, presented the gap report to finance weekly, and got sign-off before turning off the old report.
>
> **R:** Gap dropped from 12% to under 0.3%, finance regained trust, and we retired the old report 60 days later. **One thing I'd change:** I would've pushed back on the original 2-week shadow-mode timeline — we had two near-misses where the shadow run would've caught the bug a sprint earlier.

**What this story proves:** scoped + owned + drove cross-functional adoption + quantified outcome + reflective.

---

## Story 2 — Disagreed with a manager / team lead

**Prompt:** Tell me about a time you disagreed with your manager or team lead and how you resolved it.

**Use when:** Asked about friction, conflict resolution, "tell me about a time you pushed back," or any technical-disagreement scenario (especially around big migrations, rewrites, or architecture changes).

### Scaffold

- **Situation (≤30s)** — What was the disagreement about? Frame it as a real engineering trade-off, not a personality clash.
- **Task (≤30s)** — Your stake in the decision and what you'd lose if the other path was taken.
- **Action (≤2m)** — How you raised it: data, prototype, or written doc. Show that you didn't just complain — you did the homework. End with how the decision actually landed (your way, their way, or a third path).
- **Result (≤30s)** — Outcome and what you learned about disagreeing well.

### Sample (Redshift → Snowflake: pushed back on a hard-deadline big-bang cutover)

> **S:** Our org was migrating the analytics warehouse from Redshift to Snowflake, and my manager wanted to do it as a single big-bang cutover before the end of the quarter. The hard deadline was real — we had a contract commitment and a downstream consumer integration that went live on the new warehouse on a fixed date. I thought a big-bang was the wrong call. We had ~150 production tables, dozens of dbt models, and dozens of BI dashboards that all pointed at the old warehouse. If even one of those broke under the cutover, finance, exec dashboards, and customer-facing analytics all went dark at the same time — and we'd have no way to roll back quickly.
>
> **T:** I was the data engineer who would own the actual cutover, including the data validation, the dbt port, and the dashboard rewiring. If big-bang went wrong, I was the one on the hook for the rollback at 2am with the whole company watching.
>
> **A:** I didn't say "no." I put together a one-pager the same week. It had three things: a list of the 12 highest-risk tables and why each was risky, an honest estimate of the cutover window (single big-bang needed an 8-hour full-team freeze, phased could be done in 3-hour windows over a month), and a strangler-fig migration plan I sketched out myself. The phased plan ran both warehouses in parallel, with our ingestion layer writing to both, our dbt models dual-materialized, and dashboards reading from the new warehouse one team at a time — starting with the lowest-stakes internal tools, ending with finance and exec. I booked a 30-min meeting with my manager and her skip-level, walked through the doc, and acknowledged the deadline constraint up front. I proposed the phased plan *with* a hard cap: every table migrated within 6 weeks, the old warehouse decommissioned the day after the deadline no matter what, and a rollback plan for each wave in case something broke. The skip-level agreed; the manager agreed once the deadline cap was in.
>
> **R:** We migrated the full warehouse in 5 weeks, 3 waves, with zero downtime. The first 2 waves surfaced 4 query-performance and 2 schema-edge-case issues that would have been a single catastrophic incident under big-bang. We hit the contract deadline with a week to spare. **What I'd change:** I would have raised the concern the day the cutover plan was first proposed, not the week before kickoff. I lost a week of lead time because I was nervous about pushing back, and we ended up doing the first migration wave in a rush that didn't need to be a rush.

**What this story proves:** disagreed with evidence and a concrete alternative plan, didn't go over the manager's head, respected the hard constraint instead of ignoring it, proposed a path that honored the deadline, and reflected on the cost of waiting too long.

### Talking points if they probe deeper

- **"What made you think big-bang was risky?"** — I counted the blast radius. ~150 tables, ~40 dbt models, ~30 dashboards, all pointing at the same warehouse. Under big-bang, one bad query rewrite or one schema edge case would have taken down every consumer at once, with no easy rollback.
- **"How did you get the data to back up your pushback?"** — I profiled the 12 highest-risk tables myself — the ones with the most complex dbt models, the largest row counts, and the most dashboard consumers. Those were the ones most likely to break under a cutover, and they were the easiest to migrate first under a phased plan.
- **"What if the deadline had been non-negotiable?"** — I would have asked which deadline mattered more: the contract date, or the cutover date. Those were two different things. The contract was about being *on* Snowflake, not about *decommissioning* Redshift on the same day. A phased plan could still hit the contract date by migrating one team at a time.
- **"What was the rollback plan?"** — Each wave had a documented rollback: flip the dashboard or model back to Redshift, which was still receiving writes the whole time. The blast radius of any single wave was tiny, so rollback was a config change, not a fire drill.
- **"How did your manager take the pushback?"** — She pushed back on the timeline at first. Once I added the hard cap (6 weeks, no extensions) and the per-wave rollback, she was on board. The framing mattered — I wasn't saying "we can't do this," I was saying "we can do this with less risk and still hit the date."
- **"What did you learn about disagreeing well?"** — Bring the homework, not just the opinion. And raise it early. The same pushback a week earlier saves a week of rushed work.

---

## Story 3 — Improved a process with measurable business impact

**Prompt:** Tell me about a process you improved that had a measurable business impact.

**Use when:** Asked about impact, continuous improvement, "how do you make the team better?", or anything about platform/framework work that other teams adopted.

### Scaffold

- **Situation (≤30s)** — What process was broken? What was the cost (time, money, errors, on-call burden)?
- **Task (≤30s)** — Your role in identifying and owning the fix.
- **Action (≤2m)** — Diagnosis → root cause → fix → rollout. Quantify at each step.
- **Result (≤30s)** — Before/after metrics + adoption.

### Sample (built a reusable config-driven ingestion framework)

> **S:** Every team in our org was building their own ingestion pipeline from scratch — pull from an API or DB, land in S3, validate, load into the warehouse, hand off to dbt. We had ~30 of these one-off pipelines, and every new source took roughly 2 weeks: a custom Airflow DAG, custom schema-evolution logic, custom Great Expectations tests, and a custom retry/alerting setup. Quality was inconsistent — half of them had no tests, and a third of them silently dropped rows on schema drift. On-call spent hours every week chasing failures that should never have reached prod.
>
> **T:** I owned building a single, reusable ingestion framework that any team could point at a new source and have it running in days, not weeks. I was the only engineer on the framework; the downstream teams were my users.
>
> **A:** First I catalogued the 3 most common source patterns — REST API, relational DB, and SFTP/file drop — and built one config-driven abstraction for each. An engineer now writes a YAML config: source type, endpoint/table, schedule, schema contract, and warehouse target. The framework handles the rest: idempotent landing in S3 with partitioned Parquet, schema-drift detection, Great Expectations data-quality tests, dbt model scaffolding, retries with exponential backoff, and PagerDuty alerts wired to the right Slack channels. I built it on top of Airflow + dbt + our existing warehouse, so teams didn't have to learn anything new — they just wrote config. Then I dogfooded it: I personally migrated the two highest-traffic pipelines (our orders and our customers feeds) onto the framework myself, end-to-end, before asking anyone else to use it. That gave me two things — a proof point with real numbers, and a list of every rough edge before other teams hit it. I wrote a one-page README, a worked example, and ran a 30-min lunch-and-learn once the migration numbers were in. The other teams started asking to onboard within a week.
>
> **R:** Time to add a new source dropped from ~2 weeks to ~2 days. Within 3 months, 8 of our 30 one-off pipelines had been migrated, on-call pages for ingestion-related failures dropped ~70%, and the framework caught 3 schema-drift incidents automatically that would previously have been silent data loss. **What I'd change:** I would have instrumented the framework with row-count and freshness metrics from day one — I added them in month two, and there were two quiet incidents in the gap where the framework succeeded but the data was stale, and we didn't know until a dashboard broke.

**What this story proves:** saw a repeating pain across the org, built a single abstraction instead of more one-offs, dogfooded on the highest-stakes pipelines to de-risk it, drove adoption through proof rather than mandate, quantified before/after, and reflected on what to add sooner.

### Talking points if they probe deeper

- **"Why a framework and not just a template?"** — A template gets copied and then drifts. A framework with config-driven source types means every new pipeline inherits the same schema-drift detection, tests, and alerting. The wins compound.
- **"How did you pick the 3 source patterns?"** — I counted them. REST API, relational DB, and SFTP/file drop covered ~90% of our pipelines. I left the long tail (Kafka, event streams) for a v2.
- **"What was hardest about the migration?"** — Schema drift. The old one-off pipelines had quietly allowed columns to come and go; the new framework failed loud. I had to add a "known drift" whitelist and a 1-week grace period so teams weren't paged on the first legitimate schema change.
- **"How did you get buy-in?"** — I didn't pitch a framework. I migrated two real pipelines, showed the numbers, and let the other teams come to me. Adoption was pull, not push.
- **"What would you do differently?"** — Add row-count and freshness metrics from day one, and write a migration runbook *before* migrating the first pipeline, not after the second.
- **"Did anyone push back?"** — Yes. One senior engineer preferred his custom DAG. I offered to migrate his pipeline myself; once it was done, he became the framework's strongest advocate.

---

## Story 4 — Learned a new tool / system quickly and delivered

**Prompt:** Tell me about a time you had to learn a new tool or system quickly and deliver results.

**Use when:** Asked about learning agility, ramp-up speed, or "how do you approach new tech?"

### Scaffold

- **Situation (≤30s)** — What tool/system, what deadline, why you were the one doing it.
- **Task (≤30s)** — The deliverable and the constraint (time, stakeholders, scale).
- **Action (≤2m)** — How you ramped: docs, office hours, prototype first, pair-programming, scope cuts to ship faster. Be concrete about the time investment.
- **Result (≤30s)** — What shipped + what you learned about ramping.

### Sample (dbt + Snowflake from scratch)

> **S:** My team adopted dbt and Snowflake 6 weeks before a critical finance close project. I'd never used either tool. The deliverable was a reconciled revenue dataset that finance would sign off on for the quarter.
>
> **T:** I was the data engineer assigned to build the dbt models and the Snowflake ingestion for this dataset — basically the whole pipeline, with a hard deadline.
>
> **A:** I spent the first three days reading dbt's docs and rebuilding one of our existing pipelines end-to-end as a learning exercise. I booked daily office hours with our analytics engineer for the first two weeks. I scoped the project aggressively: 4 models for the close, not 10. I wrote tests on every model from day one because I didn't trust my own output. I paired with finance for an hour every other day to validate definitions rather than building in a vacuum.
>
> **R:** We delivered on time, finance signed off, and the models became the template for the next two pipelines on the team. **What I'd change:** I would've pushed for a shorter, sharper kickoff doc up front — I spent a day re-litigating definitions that a 30-min conversation at the start would've resolved.

**What this story proves:** ramp-up plan, deliberate practice, scope discipline, paired with stakeholders, reflected on what to change.

---

## Story 5 — Learned Go and reimplemented our Databricks integration (faster, cheaper, simpler API)

**Prompt:** Tell me about a time you had to learn a new tool or system quickly and deliver results.

**Use when:** Asked about learning agility, ramp-up speed, polyglot work, backend services, or "how do you approach new tech?" — and especially when the answer involves data infrastructure, cost reduction, or building an API/platform that other teams adopt.

### Scaffold

- **Situation (≤30s)** — What tool/system, what deadline, why you were the one doing it.
- **Task (≤30s)** — The deliverable and the constraint (time, stakeholders, scale).
- **Action (≤2m)** — How you ramped: docs, prototype first, pairing, scope cuts. Be concrete about time investment.
- **Result (≤30s)** — What shipped + what you learned about ramping.

### Sample (Go + Databricks connector rewrite)

> **S:** Our data team was running a Python service that triggered Databricks jobs, polled for completion, and pulled results back into our pipeline. It worked, but it was slow, expensive on cloud bills, and the surface area had grown into a tangle of ad-hoc scripts. Nobody owned it. I had never written Go before — I'd done Python and Java, but never shipped a service in Go.
>
> **T:** I volunteered to rewrite the integration in Go as a small, focused service: one static binary, a clean REST API on top, and a thin Databricks SDK wrapper. The constraint was that it had to be production-ready in 4 weeks, replace the Python service without downtime, and cut our Databricks job-run costs.
>
> **A:** I spent week one doing a "Tour of Go" plus reading the Databricks REST API docs end-to-end. I didn't try to read everything — I picked the 4 endpoints we actually used (`jobs run-now`, `jobs get`, `jobs list`, `jobs cancel`) and built a tiny CLI that hit them by hand using `curl`. That gave me a working mental model before I wrote a line of service code. Week two I built the first end-to-end slice: submit job → poll → return result. I leaned on Go's `net/http` standard library instead of pulling in a heavy framework — fewer abstractions to learn, fewer surprises. I used `context.Context` everywhere for cancellation so a shutdown wouldn't leave jobs orphaned. For the Databricks SDK I wrote a minimal client wrapping just our endpoints, with retries, exponential backoff, and a single shared `http.Client` so we reused connections instead of paying TLS handshakes on every poll. I pair-programmed with a senior Go engineer for two 1-hour sessions to review concurrency patterns and error handling — that one decision saved me a week of debugging. I also scoped ruthlessly: no auth refactor, no multi-cloud, no streaming — just a drop-in replacement for the Python service, plus a small `/healthz` endpoint. In week three I added structured JSON logging and Prometheus metrics so we could see cost and latency. In week four I ran it shadow-mode behind the Python service for a week, then cut over.
>
> **R:** The Go service shipped on time, ran with 1/10th the memory of the Python service, and our average job-run cost dropped ~40% because we stopped spinning up new connections and could actually cancel zombie jobs we previously orphaned. The REST API became the default way other teams trigger Databricks — three teams adopted it in the first month without me asking. Latency p95 went from ~3s to ~300ms. **What I'd change:** I would have stood up the shadow-mode cutover earlier in week two instead of week four — the integration tests caught things the unit tests didn't, and I burned a weekend chasing a polling bug I would've caught on day three.

**What this story proves:** ramped a new language in 1 week, used docs + hands-on prototyping over passive learning, scoped the v1 to ship, used senior engineers strategically, instrumented from day one, and reflected honestly on what to improve.

### Talking points if they probe deeper

- **"Why Go?"** — single static binary, great stdlib for HTTP services, low memory, fast startup. Perfect fit for a small "control plane" service that orchestrates Databricks jobs.
- **"How did you learn Go so fast?"** — I didn't try to learn all of Go. I learned the 20% I'd actually use: structs, interfaces, goroutines, channels, `context`, and `net/http`. I built a CLI first, then a service.
- **"How did you cut cost?"** — connection reuse via a shared `http.Client`, proper cancellation via `context` so zombie jobs stopped running, retries with backoff instead of fail-fast loops, and metrics so we could see where the money was going.
- **"What was hardest?"** — the mental shift from Python's dynamic typing to Go's explicit error handling. The first week I wrote way too much defensive code. I learned to trust small interfaces and let errors bubble.
- **"How did you get buy-in to rewrite?"** — I didn't pitch a rewrite. I shipped a shadow-mode service that ran alongside the Python one, showed the cost and latency numbers, and let the team decide to cut over.
- **"What would you do differently next time?"** — Stand up shadow mode earlier, write the kickoff doc for myself on day one (endpoints, SLAs, failure modes), and borrow the senior Go engineer's review checklist from session one.

---

## Universal rules for every story

1. **Lead with "I", follow with specifics.** Avoid "we did X" without saying what *you* did.
2. **≤5 minutes.** Time it. Cut filler. The round has 4-5 questions in 30 min.
3. **Measurable outcome.** Numbers (%, $, hours, errors, latency) are required. If you can't quantify, say *how you'd measure it now*.
4. **End with what you'd change.** This signals self-awareness and growth — exactly what the Ownership round is testing.
5. **No heroes vs villains.** Frame conflicts as trade-offs and learning, not as personalities.
6. **Rehearse aloud.** Silent prep doesn't catch the places you mumble or overrun.

---

## Practice protocol

- Pick the five stories above; tailor each to your real history.
- Time each story out loud; aim for 3:00–4:30.
- Have a partner ask one drill-down per story: *"What would you have done if your manager had said no?"* — the follow-ups are where ownership is actually scored.
- Rehearse the "what I'd change" line so it sounds natural, not rehearsed.