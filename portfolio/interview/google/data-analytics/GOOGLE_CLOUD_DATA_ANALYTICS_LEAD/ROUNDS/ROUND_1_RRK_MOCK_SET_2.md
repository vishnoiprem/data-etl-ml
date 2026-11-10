# RRK Mock Set 2: Ten New Questions With Model Answers

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Why a second set:** `ROUND_1_RRK_MOCK_10.md` covers background, late data, code review, migration, off-track programme, executive challenge, practice P&L, pre-sales, underperformer and GenAI. This set covers the topics it does not: cost spike, data mesh, MLOps, batch versus streaming, disaster recovery, data trust, build versus buy, a Python review, hiring, and a failure story.
**How to use:** cover the answer, speak yours aloud for the time shown, compare, then score with the rubric at the end.
**Public repo:** behavioural answers use `[YOUR ...]` placeholders. Fill them privately. Competitor and product facts change; verify before quoting.

| # | Type | Topic | Time |
|---|---|---|---|
| 1 | Hypothetical | BigQuery bill jumped 10x | 5 min |
| 2 | Architecture | Data mesh versus central platform | 6 min |
| 3 | Technical | MLOps on Vertex AI: model degrades in production | 5 min |
| 4 | Technical | Batch or streaming? | 4 min |
| 5 | Architecture | RPO, RTO and disaster recovery | 5 min |
| 6 | Hypothetical | "I don't trust the dashboard" | 5 min |
| 7 | Consulting | Build, buy or partner | 4 min |
| 8 | Code review | Python transformation | 6 min |
| 9 | People | Build a hiring plan and bar | 5 min |
| 10 | Behavioural | A failure you learned from | 4 min |

---

## 1. BigQuery bill jumped 10x

**Q:** A customer's BigQuery spend went from $5K to $50K a month. Diagnose and fix.

**Answer**
> "**Clarify:** on-demand or reservations? When did it start (a date points to a change)? Any new workload, dashboard or team? Is the growth in compute or storage?
>
> **Diagnose with evidence, in this order:**
> 1. **Billing export and `INFORMATION_SCHEMA.JOBS`:** cost by project, user, service account, label, and query hash. Usually a handful of queries or one dashboard account for most of it.
> 2. **Pattern:** repeated full scans, a dashboard refreshing every minute with `SELECT *`, an unpartitioned table, a scheduled query nobody reads, a cross-join, or a BI tool with no cache.
> 3. **Storage:** active versus long-term, time travel and fail-safe on churned tables, forgotten copies.
> 4. **Ingestion:** streaming inserts versus free batch loads, and a pipeline writing far more rows than before.
> 5. **Split the bill first:** query (bytes scanned), slots (reservation or autoscaling), storage, and ingestion. Each has a different fix.
>
> **Contain this week:** `maximum_bytes_billed` on risky jobs, `require_partition_filter` on big tables, kill or throttle the worst offenders, pause unused schedules.
> **Fix:** partition and cluster on the filter keys, materialised views or BI Engine for repeated aggregates, rewrite the top 10 queries, set table expiry, and move steady workloads to reservations sized from slot-usage history (separate ETL, BI and ad hoc).
> **Stick:** budgets and alerts, showback by team, a cost lint in CI that rejects unpartitioned tables, and a monthly review with owners.
> **Measure:** bytes billed per query, cost per dashboard user, and spend versus budget. I'd model any saving before promising a percentage."

**Why it passes:** evidence first, contain, fix, make it stick, no invented saving.

**Follow-up A:** "One query scans 50 TB every hour. The business owner says it's critical and refuses to stop it."
> "I don't ask them to stop it; 'critical' and 'must scan 50 TB hourly' are different claims. First, **put a number on it**: 50 TB an hour is about 36,000 TB a month, which at an on-demand rate of roughly $6 per TB (verify current pricing) is on the order of $200K a month. Then understand the need: what decision, how fresh, full history or only new data? Then offer ways to keep it running for a fraction of the cost: **incremental processing** (only new or changed partitions), a **materialised view or pre-aggregation**, partition and cluster so filters prune, a schedule that matches the real need, and **isolation** in its own project or capped reservation so its cost is predictable. I'd avoid a hard `maximum_bytes_billed` on this job without agreement, because it would make the critical query fail. If they still refuse, I escalate as a **decision, not a veto**: show the sponsor and finance the numbers, ask the owner to accept the cost formally, and set a budget and alert meanwhile. **I protect the outcome, not the query.**"

**Follow-up B (practise in your own words):** "You cut it from 50 TB to 2 TB an hour. Now the owner says the dashboard is 20 minutes staler than before and wants the old version back. What do you do?" Hint: restate the freshness requirement as a number, compare the cost of closing the gap against its business value, offer options (a faster incremental cadence, a hot-path for the latest hour, a documented freshness SLO), and never revert silently.

**Note on illustrative tables:** if you show a before and after cost table, make the totals match the scenario ($5K to $50K here). A table that doesn't reconcile costs credibility.

---

## 2. Data mesh versus a central platform

**Q:** A retail group with five business units asks whether to adopt data mesh. What do you recommend?

**Answer**
> "Data mesh is four ideas: domain ownership, data as a product, a self-serve platform, and federated governance. It is an **operating-model change**, not a tool.
>
> **Questions I'd ask:** do the domains have engineers who can own pipelines and quality? Is there executive appetite to fund domain teams? What is breaking today: a central team bottleneck, or poor data quality and unclear ownership?
>
> **Options:** (A) *Central platform and team*: simple, consistent, but a bottleneck as demand grows. (B) *Full mesh*: scales ownership, but fails without mature domains and strong platform tooling, and risks duplicated or inconsistent data. (C) *Hub and spoke*: a central platform team owns standards, storage, security and tooling; domains own their data products with a defined contract, owner and SLO.
>
> **Recommend C, as a path to mesh.** Start with two domains that have capable teams and a clear business case; build the platform capabilities they need (catalogue, quality, access, cost showback, templates); add domains as they meet a readiness checklist.
>
> **Governance:** federated policy as code (classification, access, retention) enforced by the platform (Dataplex, BigQuery, IAM), **data contracts** between producing and consuming domains, and a council for exceptions.
> **Risks:** domains without skills, inconsistent definitions, no one funding the platform. **Measure:** data products with named owners and SLOs, time to onboard a domain, consumer adoption, incidents by domain."

**Pass line:** "Mesh is an operating model; I'd earn it domain by domain."

---

## 3. A model degrades in production (MLOps)

**Q:** A churn model on Vertex AI was accurate at launch and is now performing badly. What do you do?

**Answer**
> "**First, confirm and size the problem:** compare current accuracy against the launch baseline on recent labelled data, by segment. Is the loss gradual (drift) or sudden (a pipeline or schema change)?
>
> **Diagnose:** (1) **data quality:** nulls, schema or unit changes, a broken feature pipeline. (2) **training-serving skew:** features computed differently online and offline. (3) **data drift:** input distributions shifted (new customers, season, pricing). (4) **concept drift:** the relationship changed (competitor, policy). (5) **label delay:** is the metric itself stale?
>
> (6) **Infrastructure:** endpoint latency, errors, autoscaling, and which model version is actually serving.
>
> **Contain:** if business impact is high, fall back to the previous model or a rule-based baseline, and flag the output. For a retrained candidate, use a **shadow deployment** (it scores live traffic without affecting users) before promotion.
> **Fix:** repair features or skew; retrain on recent data with the same pipeline; evaluate against a held-out recent set and against the incumbent before promoting; canary release with automatic rollback.
> **Prevent:** Vertex AI Model Monitoring for skew and drift, alerts on feature distribution and prediction distribution, a scheduled retraining or evaluation pipeline, a feature store for consistent features, versioned data, model and code, and an owner and runbook.
> **Measure:** performance by segment versus baseline, drift metrics, time to detect, time to roll back, and business KPI (retention)."

---

## 4. Batch or streaming?

**Q:** A customer says "we need real time". How do you decide?

**Answer**
> "I'd **question the premise**. 'Real time' means different things: sub-second, seconds, minutes or hourly. I ask: what decision changes if the data is fresher, and by how much? What does the delay cost? Who acts on it, and how fast?
>
> **Decision test:** if a human looks at a dashboard daily, batch or micro-batch is enough. If an automated action depends on the event (fraud block, inventory alert, pricing), streaming earns its cost.
> **Trade-offs:** streaming adds state management, late-data handling, exactly-once concerns, higher operational complexity and often higher cost. Batch is simpler, cheaper and easier to reconcile.
> **Pattern:** often a **hybrid**: stream the few events that need it into an operational store or alert path, and batch the rest, with a periodic reconciliation. On Google Cloud: Pub/Sub plus Dataflow for streaming, BigQuery scheduled or incremental loads for batch.
> **Recommend** by freshness SLO per use case, not a blanket choice. **Measure:** freshness SLO met, cost per use case, and incidents."

---

## 5. RPO, RTO and disaster recovery

**Q:** A bank asks for a disaster-recovery design for its data platform. How do you approach it?

**Answer**
> "**Start with business tiers, not technology.** For each data product or service, agree an **RPO** (how much data loss is acceptable) and an **RTO** (how long it can be down) with the business, and a cost the business is willing to pay. Not everything is tier 1.
>
> **Options by tier:** (1) *Regional design with multi-zone resilience* and backups: low cost, longer RTO. (2) *Cross-region replication* for critical datasets (BigQuery dataset replication or managed disaster recovery, multi-region storage): lower RPO and RTO, higher cost. (3) *Active-active* for the most critical streaming path: highest cost and complexity.
> **Residency constraint:** where law requires data to stay in one country, cross-region copies may not be allowed. Singapore has a single Google Cloud region, so DR within the country relies on multi-zone and in-country backups unless the regulator and legal approve otherwise. Raise it as a decision.
> **Beyond data:** infrastructure as code so the platform can be rebuilt, tested restore procedures, runbooks, failover drills, and dependency mapping (identity, network, keys).
> **Measure:** RPO and RTO achieved in drills, restore success rate, drill frequency. An untested backup is not a backup."

---

## 6. "I don't trust the dashboard"

**Q:** Executives say they don't trust the numbers on the main dashboard. What do you do?

**Answer**
> "Trust is lost for a reason, so I'd **find it** before fixing anything. Collect the specific examples: which number, compared against what, by whom.
>
> **Likely causes:** two definitions of the same metric (revenue gross versus net), stale or late data, a duplicate or missing record, a timezone or currency issue, a filter nobody knew about, or an undocumented manual adjustment.
> **Approach:** (1) pick the top 3 disputed metrics and **trace lineage** from dashboard to source; (2) **reconcile** each to an authoritative source (finance ledger, source system) and explain every difference; (3) agree **one definition per metric** with a named owner, in a governed semantic layer (for example LookML); (4) show **freshness and quality status** on the dashboard itself; (5) add automated tests and a freshness SLO; (6) set a channel where suspect numbers are reported as defects.
> **Communicate:** tell the executives what was wrong, for how long, and what changed. Don't hide it.
> **Measure:** reconciliation to source within tolerance, fewer metric disputes, and weekly active users of the governed metrics. Trust returns when the number is explainable."

---

## 7. Build, buy or partner

**Q:** A customer wants a data-quality and observability capability. Build, buy or partner?

**Answer**
> "Decide on **differentiation, time, cost of ownership and skills**. Data quality isn't a competitive differentiator for most firms, so **default to buy or use platform-native features** unless a requirement can't be met.
> - **Platform-native** (Dataplex quality scans, Dataform assertions): fast, integrated, lowest overhead, good for common rules.
> - **Buy** a specialised tool: when the customer needs advanced anomaly detection, cross-platform coverage or a business-user workflow.
> - **Build:** only for requirements nothing meets, and with an owner who will maintain it for years.
> - **Partner:** when capacity or specialist skills are the constraint.
> **Criteria I'd score:** requirement fit, integration with their stack, total cost over three years including people, time to value, lock-in and exit, security and residency, vendor viability.
> **Recommend** starting platform-native on the most critical data products, measure the gaps, and buy only against a demonstrated need. **Measure:** coverage of critical products, incidents caught before users, and maintenance effort."

---

## 8. Python code review

**Snippet**
```python
def daily_revenue(orders, rates):
    totals = {}
    for o in orders:
        date = o["created_at"].split(" ")[0]
        amount = o["price"] * o["qty"] * rates[o["currency"]]
        totals[date] = totals.get(date, 0) + amount
    return totals
```

**Answer (reading order: correctness, idempotency, scale, semantics, security, maintainability)**
> "1. **Correctness:** `rates[o["currency"]]` raises `KeyError` for an unknown currency and fails the whole run. `price` and `qty` may be strings or `None`. **Floats for money** accumulate rounding error; use `Decimal` or integer minor units. Refunds and cancellations are not handled, so 'revenue' may be wrong. Does 'revenue' mean gross or net?
> 2. **Semantics:** `created_at.split(" ")[0]` takes a date from a string with an unknown timezone. An order at 23:30 in Singapore is a different UTC date. Use timezone-aware parsing and an agreed business timezone. Which exchange rate: at order time or at report time? One rate dictionary can't express that.
> 3. **Duplicates:** if `orders` contains the same order twice (retries, replays), revenue is double-counted. There's no order ID check or version.
> 4. **Idempotency and restart:** it returns a dict with no persistence, so it can't be safely re-run into a table without a defined overwrite for that date.
> 5. **Scale:** a Python loop over all orders in memory won't scale; push the aggregation into BigQuery or a streaming job with a deduplicated, partitioned source.
> 6. **Maintainability:** no types, no tests, no validation, no handling of bad rows.
> **Sentence to say:** 'The loop is probably correct for clean data. It's only correct if upstream guarantees unique, clean, timezone-consistent orders, and nothing here enforces that.'
> **Require before merge:** `Decimal`, a dead-letter path for bad rows, dedupe by order ID and version, timezone rules, and tests for refunds, duplicates and unknown currencies."

---

## 9. Hiring plan and bar

**Q:** You need to grow the practice from 10 to 20 senior engineers and architects in a year without lowering the bar. How?

**Answer**
> "**Define the bar first.** A written scorecard per role: technical depth, design judgement, customer influence, delivery ownership, coaching. Calibrated examples of 'strong' and 'not yet'.
> **Plan from demand:** a rolling forecast of pipeline by skill, so I hire for known needs (migration architects, GenAI engineers, delivery leads), with partners covering spikes.
> **Sourcing:** referrals, targeted communities and certified talent; diverse slates and structured outreach.
> **Process:** structured interviews with the same questions, a work sample (a design review), trained interviewers, a hiring committee, and a rule that a 'no' from the bar-raiser stands. Reference checks on the specific gap.
> **Ramp:** a 90-day plan, a buddy, early customer exposure, and certification targets, so new hires are productive in weeks.
> **Retention:** growth paths, interesting work, fair load.
> **Measure:** time to hire, offer acceptance, quality of hire (performance at 6 and 12 months), ramp time, diversity of slates and hires, attrition in the first year. I'd rather be short for a quarter than lower the bar, and I'd say so to leadership with the cost of the gap."

---

## 10. A failure you learned from

**Q:** Tell me about a time you failed.

**Answer structure (fill with a real story; do not use a strength disguised as a weakness)**
> **S:** [Real situation with real stakes.] **T:** [My responsibility, stated plainly.]
> **A (what I got wrong):** "I made a wrong call: **I** [assumed X without testing it / didn't escalate Y in time / chose speed over a control Z]." No blaming others.
> **R:** [The real cost: delay, wrong data, money, trust.]
> **What I changed:** [a concrete mechanism: a checklist, a contract test, an escalation rule, a review gate], and [evidence it worked since].
> **Reflection:** [the principle I now apply].

**Pass signal:** specific, owned, with a mechanism that changed afterwards.

---

## Scoring rubric (0 to 2 per line, 8 per answer, 80 total)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| Structure | Jumped to a solution | Some clarifying | Clarified, stated assumptions, then options |
| Judgement | Component list or "it depends" | Options, weak pick | 2 to 3 options, trade-offs, a clear recommendation |
| Evidence and numbers | Vague | Some figures | Defensible figures with baseline, method and your role |
| Enterprise scope | Single project | Mentions operations | Ownership, adoption, rollback, decommission, cost |

**Targets:** 60 of 80 or more is ready. 45 to 59: repeat your weakest three. Below 45: restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.
**Close each answer with one of:** what could go wrong and how I'd measure it; what I need from you by when; or what I'd do differently.
