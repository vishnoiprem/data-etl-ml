# Techcombank — Director, Data Engineering (40000058)
## Technical Round: Question & Answer Prep
**Interview: Tue 1 Sep 2026 · Prem Vishnoi**

> Built from the actual job profile (SAP SuccessFactors export, 4 pages) + your track record at CP Axtra/Makro, Lazada, Standard Chartered, DBS.
> **How to use this:** read Sections 0–3 twice (positioning + numbers). Rehearse the ⭐ answers OUT LOUD. Skim the rest for vocabulary so nothing sounds unfamiliar.

---

## Section 0 — Decode the role before you answer anything

| JD signal | What it actually means | Your move |
|---|---|---|
| Reports to **Head of Data Engineering & Delivery** | You are *not* the top of the function. One layer below. | Do NOT posture as the CDO. Position as the person who *lands delivery* for the Head. |
| Direct reports: **Data Engineer, Senior Data Engineer** | Squad-level leadership (likely 8–20), still expected to be hands-on | Emphasise you still read PRs, design reviews, debug prod. Kill any "I only do strategy" impression. |
| "wore the **architect hat** in the past or worked with one extensively" | They want architect + manager in one head | Every answer: business problem → architecture → delivery → measured outcome. |
| Hadoop, Spark, **Flink**, Kafka, **Arrow**, Tableau | Legacy Hadoop estate + modern streaming ambition | Show you can run *both* and have a migration opinion. |
| Python, R, Scala, Java, **Rust, Kotlin** — "preference towards functional/trait oriented" | Someone in the panel is a real engineer with strong opinions | Be honest about depth (Python/Scala/SQL strong). Don't bluff Rust. |
| "recommenders delivering to **tens of millions of users**" | They have a personalisation/NBO ambition | Your Lazada + Makro personalisation work is the closest match — lead with it. |
| Competencies at **Level 4**: Data governance, Data management, Metadata management | Framework-level, auditable governance. This is a **bank**. | Bring BCBS 239, data contracts, lineage, stewardship model. This is where most candidates are thin. |
| Agile / Scrum "mastered and mentored" | Techcombank runs a **tribe/squad** model (JD says "Business Tribe, Enabling Tribe") | Speak tribe/squad/chapter language, not "my team". |
| Internal stakeholders listed up to **CEO, CIO, CDO, Chairman** | You will present to the very top | Have 2 stories of executive-level influence. |

**The one-line thesis you're selling:** *"I've built the governed data foundation for an $8bn multi-country business at Makro, and I built regulated banking data platforms at Standard Chartered and DBS. I can do both halves of this job — the architecture and the delivery — and I've done it in Vietnam-adjacent ASEAN markets."*

---

## Section 1 — Your opening (90 seconds, memorise the shape not the words) ⭐

> "I'm a data and AI leader with about 15 years across Southeast Asia, and my career actually started in banking — I built AML and compliance data platforms at Standard Chartered covering 15+ countries, and worked at DBS before that.
>
> Today I'm Head of Data Engineering at Makro, part of CP Group, where I own the data, analytics and AI platform for an $8 billion omnichannel retail business across three countries — about 30 people and a $3 million budget. The centrepiece is a Databricks lakehouse processing 10 billion-plus rows a day on a medallion architecture, serving BI, ML and GenAI off one governed copy of the data.
>
> Between those two I was VP of Data Engineering at Lazada, Alibaba's e-commerce arm — that's where I learned to run data platforms at consumer internet scale and latency.
>
> Why Techcombank: this role sits exactly on the intersection I've spent my career on — regulated financial data, done at consumer-internet scale. Vietnam is the most interesting banking market in ASEAN right now, and I want to be hands-on again in the engine room of a bank that is genuinely trying to be data-led, not just say it."

**Then immediately hand them the wheel:** *"Happy to go as deep as you want — architecture, modelling, streaming, or how I run a squad."*

**Pre-empt the two objections they're silently holding:**
1. *"He's a Head, this is a Director — will he be bored / too senior?"* → "I'm deliberately looking for a role where I'm closer to the build. At Makro my span grew faster than my hands-on time, and I miss it."
2. *"Retail, not banking, recently."* → "Banking is where I started and it's the discipline I still carry — my retail platforms are run to financial-controls standard because they feed the statutory close."

---

## Section 2 — Numbers you must have on the tip of your tongue

Never give a technical answer without landing one of these.

| Metric | Number |
|---|---|
| Years / years leading | ~15 / ~7+ |
| Current org size / budget | ~30 people / ~$3M |
| Business scale owned | $8bn revenue, 3 countries, ~200 stores, 5 DCs |
| Daily data volume | 10bn+ rows/day |
| Month-end close | 5 days → 2 hours |
| Executive dashboards delivered | 50+ |
| ML forecasting coverage | 1,000+ vendors |
| SCB AML platform footprint | 15+ countries |
| GenAI | Text-to-SQL platform in production |

**Have ready but don't volunteer:** pipeline SLA attainment %, cost per TB processed, % reduction in cloud spend, incident MTTR, number of squads/chapters you've run, attrition/retention in your team.

---

## Section 3 — Block A: Data Architecture ⭐ (highest-probability block)

### A1. "Design the target data architecture for a bank like ours."
Answer in **five layers**, and say the layers out loud as you draw:

```
 SOURCES            INGEST                 STORE / PROCESS              SERVE                 GOVERN
 ─────────          ──────                 ───────────────              ─────               ─────────
 Core banking       CDC (Debezium/         BRONZE  raw, immutable,      Semantic layer      Catalog + glossary
 (T24-class)        GoldenGate) → Kafka    append-only, PII tagged      ↓                   Lineage (OpenLineage)
 Cards / payments   ─────────────────      ↓                           Tableau / BI         Data contracts
 Digital app        Streaming events       SILVER  conformed, DQ-       Feature store       DQ engine + SLOs
 CRM                (Kafka → Flink)        checked, SCD2, keys          (online/offline)    Access: RBAC+ABAC,
 Loan origination   ─────────────────      ↓                           API / microservices  masking, tokenisation
 Treasury/risk      Batch/file (SFTP,      GOLD    Kimball marts +      GenAI / Text-to-SQL  Audit trail
 Ext: bureau, KYC   vendor extracts)       aggregates, risk datamarts   Regulatory reports  Retention/purge
```

Then say the three things that make it a *banking* architecture rather than a generic one:

1. **Immutable bronze + full lineage** — because when the regulator or internal audit asks "where did this number in the SBV report come from", you must reproduce it as of the reporting date. Time travel on the table format is not a nice-to-have, it's the audit answer.
2. **PII handled at ingest, not at consumption** — classify and tokenise on the way in. Under Vietnam's Decree 13/2023 on personal data protection you need to know exactly which columns are personal data, who consented to what, and be able to honour deletion. Retrofitting that later is a multi-year cleanup.
3. **One governed copy, many engines** — open table format (Iceberg or Delta) on object storage so BI, ML and GenAI read the same certified data. The failure mode I've seen in every bank is three "single sources of truth": a warehouse, a lake, and a pile of Excel.

**Close with the delivery reality:** "And I wouldn't try to build all of that at once. I'd pick one high-pain, high-visibility domain — usually regulatory reporting or the month-end close — prove the pattern end-to-end in a quarter, and use that as the reference implementation everything else follows."

---

### A2. "Lakehouse vs data warehouse vs data lake — what would you pick and why?"

> "Lakehouse, and I'd be specific about why rather than just saying it's modern.
>
> A classic warehouse gives you great governance, great SQL performance and terrible economics and flexibility for semi-structured data and ML. A raw lake gives you cheap storage and flexibility and, in practice, no reliability — no ACID, no schema enforcement, so it silently becomes a swamp and the business stops trusting it.
>
> A lakehouse is object storage plus an open table format — Iceberg or Delta — which gives you ACID transactions, schema evolution, time travel and partition/file management *on top of* cheap storage. So you get warehouse guarantees at lake economics, and critically one copy of the data serving BI, ML and GenAI instead of copying between systems. Every copy is a governance gap and a reconciliation argument.
>
> At Makro that's exactly the architecture: Databricks lakehouse, medallion layering, ~10 billion rows a day, and the same curated layer feeds Tableau, the ML forecasting models and the Text-to-SQL GenAI interface.
>
> One caveat I'd give honestly: for very high-concurrency, low-latency operational serving — think a customer-facing balance API — a lakehouse is the wrong tool. That belongs in an operational store or a serving layer with a cache. I don't try to make the analytics platform do OLTP."

**If pushed on Iceberg vs Delta:** "Both give ACID, time travel, schema evolution. Iceberg's hidden partitioning and engine-neutral metadata make it the better bet if you want genuine multi-engine freedom — Spark, Flink, Trino, Snowflake all read it. Delta is tighter and more mature if you're standardising on Spark/Databricks. The decision is really 'how much do you value optionality vs a shorter path', and I'd let the existing estate decide it rather than have a religious position."

---

### A3. "We have a large on-prem Hadoop estate. What do you do with it?"
This is very likely a real question. Do **not** say "rip it out".

> "I'd resist the big-bang. I've never seen a Hadoop-to-cloud big bang land on time in a bank.
>
> First, I'd inventory by *workload*, not by cluster: what jobs run, who consumes the output, what's the SLA, what's the true cost, and — the one everybody skips — what's actually still used. In most estates 20–30% of jobs produce output nobody reads. Killing those is free progress and buys credibility.
>
> Then I'd bucket into four: **retire** (dead jobs), **rehost** (lift Spark jobs as-is, minimal change), **refactor** (Hive/MapReduce/Pig that needs rewriting to Spark SQL on an open table format), and **stay** (anything blocked by regulation, latency or a licence).
>
> Sequencing: start with a self-contained domain that has a clear business owner, run **dual-run and reconcile** — same inputs, both platforms, prove the numbers tie to the cent before you cut over. In banking the migration risk isn't technical, it's the moment someone's regulatory number moves by 0.3% and you can't explain why.
>
> On the technical patterns: HDFS → object storage with Iceberg/Delta; Hive Metastore → a real catalog with lineage; Oozie → Airflow or an orchestrator with proper dependency and backfill semantics; Sqoop → CDC via Debezium/Kafka, which is a genuine upgrade because you go from nightly full loads to near-real-time change capture; Kerberos/Ranger → cloud-native RBAC/ABAC and I'd map every existing Ranger policy explicitly rather than reinvent it.
>
> And I'd be blunt with the exec sponsor about the shape of the cost curve — during dual-run you pay for both. Budget for it or the programme gets killed at month six for looking expensive."

---

### A4. "How do you decide build vs buy?"
> "Four tests. **Is it differentiating?** — nobody wins by building their own scheduler; you might win by building your own feature engineering for fraud. **What's the true TCO** including the two engineers who own it forever, not just licence vs zero. **What's the exit cost** — can I get my data out in an open format? **What's the time-to-value** against the business window.
>
> My default: buy the plumbing, build the differentiation, and never build anything whose failure mode is 'the one person who understood it left'."

---

## Section 4 — Block B: Data Modelling (they said "dimensional data models" explicitly) ⭐

### B1. "Model the core banking data for analytics."
This is the question where you can visibly out-class other candidates. Be concrete.

> "I'd use a layered approach: a **Data Vault-style raw integration layer** and **Kimball dimensional marts** on top for consumption.
>
> Why both: Data Vault — hubs for business keys, links for relationships, satellites for descriptive history — is genuinely good at absorbing a bank's messy multi-source reality without remodelling every time a source system changes, and it's fully auditable by design. But it's hostile to business users and BI tools. So Vault for integration and history, Kimball star schemas for the marts people actually query.
>
> On the dimensional side, the important part is choosing the right **fact grain and fact type**:
>
> - **Transaction fact** — one row per posting. Grain: transaction line. Additive measures: amount, fee. Degenerate dimension: transaction reference.
> - **Periodic snapshot fact** — one row per account per day for **balances**. This is the one people get wrong: balances are semi-additive — you can sum across accounts on a given day, you cannot sum across days. You average or take end-of-period.
> - **Accumulating snapshot fact** — for **loan origination** or dispute lifecycle, one row per application updated as it moves through milestones: applied, credit-decisioned, approved, disbursed. That's how you answer 'what's our time-to-disbursement by channel' without gymnastics.
>
> Dimensions: Customer as **SCD Type 2** — mandatory, because when a customer's risk segment or KYC status changed matters for both analytics and regulatory answers. Account, Product, Branch/Channel, Date, plus a junk dimension for the pile of low-cardinality transaction flags.
>
> Two banking-specific modelling traps I'd flag: **joint accounts and account-to-customer many-to-many** need a bridge table with a weighting factor, otherwise every 'balance by customer' report double-counts. And **currency** — every monetary fact stores transaction currency amount, the rate used, and the base-currency amount, with the rate persisted on the fact. Never re-derive historical FX at query time; the number won't reproduce."

### B2. "How do you implement SCD Type 2 at scale?"
> "On a lakehouse: `MERGE` on the natural key. Close the current row — set `valid_to` and `is_current = false` — and insert the new version, in one atomic transaction so a failure can't leave the dimension with two current rows or none.
>
> Practical details that matter: hash the tracked attributes into a `row_hash` so you only version on real change, not on a source system rewriting the same values. Keep `valid_from`/`valid_to`/`is_current` plus a surrogate key that facts join to. Handle late-arriving and out-of-order source data explicitly — decide up front whether you're versioning on event time or load time, because in a bank the answer has to be defensible.
>
> At scale the killer is that `MERGE` rewrites files. So partition or cluster the dimension so the merge touches few files, use liquid clustering or Z-ordering on the join key, and compact regularly. I've seen a 'slow SCD2' turn out to be a small-files problem, not a logic problem."

### B3. "Normalised or denormalised? Star or one big table?"
> "Depends on the consumer, and I'd refuse to have one answer. Star schema for BI, because it's what the semantic layer and Tableau are built for and it keeps conformed dimensions genuinely conformed. One-big-table is legitimate for ML feature sets and for a specific hot dashboard where join elimination buys real latency. What I don't allow is OBTs proliferating as shadow marts with their own business logic — that's how you get five definitions of 'active customer'. If an OBT exists, it's *derived* from the star, in the platform, with lineage."

---

## Section 5 — Block C: Pipelines, Spark, Kafka, Flink ⭐

### C1. "A Spark job that used to take 20 minutes now takes 3 hours. Walk me through it."
Show a **method**, not a list of tricks.

> "I'd work outside-in. First: did the *data* change or did the *code* change? Row counts, file counts and input size by partition versus last week, and the git log. Nine times out of ten it's data.
>
> Then Spark UI, and I look at the stage timeline for the classic four:
>
> **Skew.** One task running 100× longer than the median. In banking this is nearly always a business reality — one mega-corporate customer, or a null/default key soaking up everything. Fixes: enable AQE skew join handling, salt the hot key, or split the job — broadcast-join the hot keys separately and union.
>
> **Shuffle.** Wrong partition count, or a join that should be a broadcast and isn't because statistics are stale. AQE fixes a lot of this dynamically; if it can't, I look at whether the join key cardinality changed.
>
> **Small files.** Thousands of tiny files from a streaming or CDC writer means task overhead dominates. Compaction / OPTIMIZE, and fix the writer.
>
> **Spill.** Executors spilling to disk means memory pressure — often from a wide aggregation or an exploded array. Repartition, or raise memory per executor rather than adding executors.
>
> Then the ones people forget: an accidental **cartesian or fan-out join** from a duplicate key upstream — count before and after the join; a **UDF** blocking predicate pushdown and vectorisation; **cache** that was helping and got evicted; and **partition pruning lost** because someone wrapped the partition column in a function in the WHERE clause.
>
> And after I fix it: the postmortem question is why it took a human noticing. That job should have had a duration SLO with an alert at p95 drift, and an input-volume check. I'd add both."

### C2. "Kafka: how do you guarantee ordering and no data loss for financial events?"
> "Ordering is only guaranteed **within a partition**, so ordering is a partitioning-key decision, not a Kafka setting. For account-level events I key by account ID — all events for one account land in one partition and stay ordered. That also means one hot account can hot-spot a partition, which you have to watch.
>
> Durability: `acks=all`, `min.insync.replicas=2` with replication factor 3, and `enable.idempotence=true` on the producer so retries don't duplicate. Turn off unclean leader election — in a bank, losing committed data to gain availability is the wrong trade.
>
> End-to-end exactly-once needs the whole chain: idempotent producer, transactional writes for read-process-write, and — the part people skip — an **idempotent consumer**. I design the sink to be idempotent on a business key regardless, because 'exactly once' across system boundaries is a promise I don't want to depend on. Effectively-once with idempotent sinks is more honest and survives replay.
>
> Schema: Schema Registry with Avro or Protobuf and enforced backward compatibility. A producer team shipping a breaking schema change on a Friday is a much more common outage than a broker failure.
>
> For CDC off core banking I'd use Debezium reading the transaction log — not query-based polling, which misses deletes and intermediate states — and where the source team owns the events, the **outbox pattern** so the event and the state change commit in the same database transaction."

### C3. "Flink or Spark Structured Streaming?" (JD names Flink — expect this)
> "Both are good; they optimise for different things and I'd pick per workload.
>
> **Spark Structured Streaming** is micro-batch. Latency lands in the seconds. Its advantage is that it's the same engine, same code, same skills as your batch estate — so operationally it's nearly free if you're already on Spark. For the large majority of analytical streaming — near-real-time marts, CDC into the lakehouse, minute-level dashboards — it's the right answer precisely because it's boring.
>
> **Flink** is a true event-at-a-time streaming engine with much richer state handling. I'd choose Flink where I genuinely need sub-second latency, complex event-time processing with out-of-order data and watermarks, large keyed state with proper state TTL, or CEP-style pattern detection across a stream. In a bank the archetype is **real-time fraud and transaction monitoring** — 'three card-not-present transactions in different geographies inside 90 seconds' is a Flink pattern, not a micro-batch pattern.
>
> The concepts I'd expect to be tested on either way: **event time vs processing time** and why you almost always want event time; **watermarks** as your explicit statement of how much lateness you tolerate, and the trade-off that a generous watermark buys completeness and costs latency; **checkpointing** with RocksDB state backend for large state, and exactly-once via two-phase commit into the sink; and side outputs for late data so you never silently drop a transaction.
>
> My honest position: I've run Spark Structured Streaming in production at scale. Flink I know architecturally and have evaluated, but I'd be overstating it to claim I've operated a large Flink estate. If that's core here, that's something I'd ramp on fast and I'd hire or grow the depth in the team rather than pretend."

> ⚠️ **Say that last paragraph.** A Director who bluffs an engine gets found out in week three. Honesty here reads as senior, not weak.

### C4. "What is Apache Arrow and why is it in our JD?"
> "Arrow is a language-independent **columnar in-memory** format. Two things make it matter. First, it's zero-copy — engines and languages can share the same memory buffers without serialising and deserialising, which is where a shocking amount of pipeline CPU goes; pandas UDFs in Spark got dramatically faster because they moved to Arrow. Second, it's the interop substrate: Spark, Polars, DuckDB, Parquet readers, ADBC drivers, Flight for data transport all speak Arrow. So it's the reason a modern stack can be multi-engine without paying a conversion tax at every hop.
>
> The reason it's in a JD like this is usually that someone on the platform team is thinking seriously about performance and about not being locked into one engine. I'd read it as a signal about the engineering culture."

### C5. "Batch or streaming — how do you decide?"
> "By the **decision latency of the business**, never by fashion. If a human looks at the number once a day, streaming is cost and complexity for nothing. If the decision is automated and happens inside a customer interaction — fraud decline, limit check, next-best-offer in-app — it has to be streaming.
>
> My rule of thumb: default to batch, escalate to micro-batch when the business genuinely needs minutes, and reserve true streaming for sub-second automated decisions. And I'd rather run one well-operated streaming pipeline for fraud than fifteen mediocre ones because streaming became the standard."

### C6. "Orchestration and dependency management?"
> "Airflow or an equivalent, with a few non-negotiables: pipelines are **declarative and version-controlled**, tasks are **idempotent and re-runnable** so a backfill is safe, dependencies are on **data availability** not on wall-clock time — waiting for 3am and hoping is how you get silent partial loads — and every pipeline has an owner, an SLO and a runbook. Backfill is a first-class feature, not a heroic manual script, because in a bank you will be asked to restate a period."

---

## Section 6 — Block D: Governance, Metadata, Security (your differentiator — Level 4 competencies)

### D1. "How do you do data governance so it actually works?" ⭐
> "The reason governance fails in banks isn't tooling, it's that it's run as a documentation exercise by a central team with no authority. Four things I insist on:
>
> **Ownership with teeth.** Every domain has a named business **data owner** — accountable for definitions and access decisions — and a **data steward** who does the day-to-day. Not IT. If the owner of 'customer' is the data team, nobody owns customer.
>
> **Data contracts at the boundary.** A producing system commits to a schema, semantics, freshness and quality thresholds, and the contract is enforced in CI and at ingest — a breaking change fails the build, it doesn't fail my 6am pipeline. This is the single highest-leverage thing I've implemented; it moves quality upstream where it's cheap.
>
> **Quality measured and published.** Six dimensions — completeness, validity, accuracy, consistency, timeliness, uniqueness — with tests as code, thresholds per dataset, and a visible scorecard. Nothing changes behaviour like a dashboard your peers can see.
>
> **Governance in the flow of work.** Certification badges in the catalog so users can see what's trustworthy; access requests through a workflow, not a favour; lineage available so impact analysis takes minutes.
>
> And for a bank I'd anchor the whole thing to **BCBS 239** — the principles for effective risk data aggregation. It gives you a regulator-recognised frame for accuracy, completeness, timeliness, adaptability and lineage, which means governance stops being 'the data team's hobby' and becomes a supervisory expectation with executive attention. That's how you get funding."

### D2. "Metadata management — what does good look like?" (JD: Level 4)
> "Three kinds of metadata, and most organisations only do the first.
>
> **Technical** — schemas, types, partitions, table stats. Harvested automatically; if a human maintains it, it's already wrong.
>
> **Business** — the glossary. What does 'active customer' mean, who approved that definition, which physical columns implement it. This is the hard one because it's a political negotiation, not a technical task.
>
> **Operational** — freshness, last successful run, row counts over time, query frequency, cost, who actually uses this table. Enormously underrated: it tells you what to deprecate and what to protect.
>
> Then **lineage**, column-level where you can get it — OpenLineage as the standard, or the catalog's native capture. Lineage earns its keep in three moments: impact analysis before a change, root cause during an incident, and the regulatory question 'how was this number derived'.
>
> The maturity step beyond a passive catalog is **active metadata** — metadata that drives behaviour rather than describing it. Classification tags automatically applying masking policies. Freshness SLOs generating alerts. Deprecation warnings appearing in the query interface. Unused tables flagged for retirement. That's the level I'd aim for, and it's also what makes GenAI-on-data viable — my Text-to-SQL work at Makro only works because the semantic metadata is good; the LLM is the easy part."

### D3. "Data security and privacy in a Vietnamese bank?"
> "Layered, and designed in rather than bolted on.
>
> **Classify at ingest** — public, internal, confidential, restricted/PII — as tags carried in the catalog, so policy attaches to the tag, not to individually-maintained grants on 4,000 tables.
>
> **Protect by technique matched to use case.** Tokenise or vault the direct identifiers so analysts work on tokens and only a narrow, audited service can detokenise. Dynamic masking for partial-visibility cases. Row-level and column-level security via ABAC — attributes like branch, role, purpose — because role-based grants alone don't scale past a few hundred people. Encryption at rest and in transit with proper key management as table stakes.
>
> **Minimise and expire.** Don't copy PII into the lake because it might be useful. Retention and purge policies enforced by the platform, with deletion demonstrable.
>
> **Audit everything** — who queried what, when, under which justification. In a bank you will be asked, and 'we don't log that' is not an acceptable sentence.
>
> On the Vietnam specifics I'd want to confirm the current position with your legal and compliance teams rather than assert it, but the frame I'd work to is **Decree 13/2023 on personal data protection** — lawful basis and consent, data subject rights, and impact assessment obligations including for cross-border transfers; the **Cybersecurity Law and Decree 53/2022** on localisation and storage; and **SBV's IT-security requirements for credit institutions**, which shape what you can put in public cloud and how. Practically that means the architecture needs to answer three questions cleanly from day one: where does personal data physically live, who can reach it, and can we prove both."

### D4. "How would you handle a data breach or a wrong number going to the regulator?"
> "Same discipline as any sev-1: contain, assess, notify, remediate, learn — in that order, and notification timelines in financial services are short so the clock matters more than the diagnosis.
>
> Contain: cut access, freeze the affected pipeline, preserve evidence and logs before anyone 'fixes' anything. Assess scope with lineage — which datasets, which fields, which downstream reports and consumers, which customers. Notify: legal, compliance, DPO, CISO, and the exec sponsor immediately; I don't decide the regulatory notification myself, but I make sure the people who do have accurate facts within the hour rather than a comfortable story by end of day.
>
> Then remediate and — the part that matters for a Director — a blameless postmortem with a written control change, and I present it to the risk committee myself. Owning the bad news is most of the credibility."

---

## Section 7 — Block E: ML & GenAI enablement (JD: "enable data scientists", "recommenders to tens of millions")

### E1. "How do you enable data scientists rather than block them?"
> "The complaint from every data science team I've inherited is the same: 80% of their time is finding and cleaning data. So my job is to remove that, not to gatekeep it.
>
> Concretely: **reusable, certified data assets** at the right grain so scientists don't each rebuild customer transaction history their own way. A **feature store** with an offline store for training and an online store for serving from *one* definition — that's the only reliable cure for training-serving skew, which is the most common silent killer of models in production. **Self-service with guardrails** — sandbox environments, real compute, cost visibility, and a clear promotion path from notebook to production rather than 'throw it at engineering'. And **point-in-time correct joins** available as a platform capability, because feature leakage from naive joins is subtle and it invalidates the model, and most scientists shouldn't have to hand-roll that.
>
> The relationship model I use: I sit in their planning, they sit in mine, and I hold one rule — if a model is going to production, engineering is involved from design, not at handover."

### E2. "Design a recommender for tens of millions of users." (JD calls this out)
> "Two-stage, because you can't score 10 million items per request.
>
> **Retrieval** — narrow millions of candidates to a few hundred in tens of milliseconds. Two-tower model: a user encoder and an item encoder trained so relevant pairs are close in embedding space. Item embeddings precomputed and indexed for approximate nearest neighbour search — HNSW-class index. User embedding computed from features at request time or refreshed on a short cycle.
>
> **Ranking** — a heavier model over those few hundred candidates with richer features: user history, real-time session context, item attributes, cross features. Gradient-boosted trees or a deep ranker depending on latency budget and feature richness.
>
> Then the parts that actually determine whether it works: a **latency budget written down and enforced** — say 100ms p99 end to end, which forces the design; **business rules and eligibility as a separate layer** — in a bank you must not recommend a product a customer isn't eligible for or hasn't consented to be marketed, and that logic belongs in a deterministic filter, not learned; **cold start** handled with popularity and content-based fallbacks and a graceful degradation path when the model service is unhealthy; **offline evaluation** on recall@k and NDCG to choose candidates, but **online A/B on the business metric** to decide, because offline and online disagree constantly; and a **feedback loop with position-bias correction**, otherwise the model just learns to recommend whatever it already recommended.
>
> Banking-specific: fairness and explainability. If a recommendation influences a credit-adjacent decision, you need to be able to explain it, and you need to test for proxy discrimination. I'd rather ship a slightly weaker model I can defend."

### E3. "GenAI on data — real or hype?"
> "Both, and the split is predictable. The failures are always data problems dressed as AI problems.
>
> The one I've actually shipped is **Text-to-SQL** at Makro — natural language to governed SQL over the lakehouse. What made it work wasn't the model, it was the semantic layer, the certified tables, the glossary and the row-level security. The LLM inherits your governance; if your metadata is bad, GenAI industrialises your inconsistency. And it must run *through* the access controls, not around them — the answer a user gets has to respect what that user is allowed to see.
>
> For a bank the near-term high-value cases I'd back are analyst productivity on documents and policies with RAG, code and pipeline assistance for the engineering team itself, and internal knowledge retrieval. Customer-facing generation in a regulated context, I'd move slowly and with a human in the loop.
>
> The unglamorous point I'd make to the exec team: the best GenAI investment a bank can make in year one is usually finishing its data foundation."

---

## Section 8 — Block F: Reliability & operations

### F1. "How do you monitor a data platform?" ⭐
> "I separate **system health** from **data health**, because a green Airflow DAG with wrong numbers in it is the failure mode that destroys trust.
>
> System: job success, duration against p95 baseline, resource saturation, queue depth, cost.
>
> Data: **freshness** — is it here when promised; **volume** — row counts against expected range, which catches partial loads that succeed technically; **schema** — unexpected drift; **distribution** — null rates, category cardinality, value ranges shifting, which catches the upstream 'we changed the default value' change nobody told you about; and **reconciliation** — control totals tied back to source, which in banking is non-negotiable.
>
> Every important dataset gets an explicit **SLO** — freshness, completeness, availability — published to consumers, with an error budget. That reframes the conversation from 'the pipeline is broken' to 'we've spent 60% of this quarter's error budget, here's the reliability work I'm prioritising'. It's also how you say no to feature work with evidence.
>
> On alerting discipline: alert on **symptoms the consumer feels**, page only on things a human must act on now, everything else goes to a queue. Alert fatigue is a real outage cause — if the team ignores the channel, you have no monitoring regardless of how many checks you wrote."

### F2. "Tell me about your worst production incident." (STAR — have this ready)
Structure it, using a real one:
- **S** — name the business impact first, in money or in who was blocked. Not the technology.
- **T** — what you owned.
- **A** — sequence: detect → contain → communicate (stakeholders got updates on a cadence) → diagnose → fix → verify by reconciliation.
- **R** — restored in X, and then: root cause, the *control* you added, and whether it's recurred.
- **Learning** — one sentence on what you changed about how the team works, not just the code.

> Pick one where **you were the reason it was caught late** if you can bear it — owning a monitoring gap you'd left open is far more convincing at Director level than a story where you were purely the hero.

---

## Section 9 — Block G: Agile delivery & project management (JD has a whole accountability on this)

### G1. "How do you run delivery?"
> "Techcombank runs a tribe and squad model, so I'd work with that grain rather than against it. My approach: **squads own outcomes, chapters own craft.** The squad has a business outcome and a product owner; the data engineering chapter owns standards, code review, architecture consistency and career growth, so we don't end up with eight squads inventing eight ingestion frameworks.
>
> Cadence: quarterly outcome-level planning with the tribe, two-week sprints, demo to actual business stakeholders — not to me. I keep a visible split of capacity between business features, platform/enabling work and a fixed slice for reliability and tech debt. If I don't reserve that slice explicitly, it becomes zero within two quarters and the platform decays.
>
> Where I'm pragmatic: Scrum ceremonies are a means, not a religion. Streaming and platform work often fits Kanban with flow metrics better than sprint commitment. I care about outcomes, cycle time, and whether the team can say 'no, not this sprint' with evidence."

### G2. "A key stakeholder demands a report by Friday and it's not possible. What do you do?"
> "I don't say no and I don't say yes-and-fail. I go back with the business question behind the request — usually the deadline is real but the scope isn't. Then I offer options with explicit trade-offs: 'Friday, we can give you these three numbers with a manual reconciliation and a known caveat; the governed automated version lands in three weeks.' Named trade-off, named risk, their choice.
>
> What I won't trade silently is controls. If Friday requires bypassing access control or shipping an unreconciled number into a regulatory pack, I escalate rather than absorb it — and I document it. That's the line, and being consistent about it is why stakeholders eventually trust the yeses."

### G3. "How do you handle conflicting priorities across tribes?"
> "Make the conflict visible and let the business resolve it, with data. I maintain a single capacity view and a scoring frame — business value, risk/regulatory obligation, effort, and dependency unblocking. Regulatory and risk work has a standing claim; everything else competes openly. Then I take the tie-breaks to a forum where the tribe leads are in the room together, rather than negotiating bilaterally and being the bottleneck. The failure mode is a data team that says yes to everyone and delivers to no one."

---

## Section 10 — Block H: People & leadership (Director-band questions)

Expect 3–5 of these. Answer with specifics from Makro/Lazada/SCB.

| Question | Your hook |
|---|---|
| "How do you structure a data engineering team?" | Platform/enabling team + domain-aligned engineers + chapter for craft. Platform team builds the paved road so domain teams go fast safely. Explicitly reject the pure-central model (bottleneck) and the pure-embedded model (chaos, eight frameworks). |
| "How do you hire data engineers in this market?" | Vietnam market is competitive — hire for fundamentals (SQL, distributed systems reasoning, debugging) over tool familiarity; tools are teachable in weeks. Take-home or pairing exercise on a realistic broken pipeline, not algorithm puzzles. Build the pipeline from graduates/analysts as well as buying senior. |
| "How do you develop your people?" | Capability matrix against the competency levels, individual development plans, deliberate rotation across domains, senior engineers own design reviews as a growth mechanism. Name someone you promoted and what you did specifically. |
| "How do you handle an underperformer?" | Diagnose first — capability, clarity, or context? Most "performance problems" are unclear expectations or a bad role fit. Then explicit expectations, written, with a timeline and support. If it doesn't move, act decisively and kindly, because the cost of not acting falls on the rest of the team. Have a real example. |
| "How do you retain people when a competitor pays more?" | Be honest: you can't win on cash alone. Win on interesting problems, modern stack, visible impact, and growth. Also: fight for the market adjustments you can get, and never let a good engineer discover their market value from a recruiter first. |
| "You'd be joining below your current title. Why?" | Straight answer, no defensiveness — closer to the build, bigger technical problem, banking is where you started, Vietnam's the most interesting market in ASEAN. Then flip it: "and my expectation of myself is to earn a bigger scope by delivering, not by negotiating a title." |

---

## Section 11 — Three whiteboard scenarios (rehearse drawing these)

### Scenario 1 — "Real-time fraud detection on card transactions"
```
Card switch / payment gateway
      │  (transaction event, must not block authorisation path)
      ▼
   Kafka  topic: txn.authorisation   key = card_id   (ordering per card)
      │
      ├──────────────► Flink  (streaming decision engine)
      │                  • keyed state per card, RocksDB backend, state TTL
      │                  • event time + watermark (tolerate ~seconds lateness)
      │                  • velocity/CEP rules: N txns / M seconds, geo-impossible pair
      │                  • feature lookup ← online feature store (p99 < 10ms)
      │                  • model score ← inference service
      │                  └─► decision topic ──► case management / step-up auth
      │                  └─► side output: late events (never dropped)
      │
      └──────────────► Bronze (raw, immutable) ──► Silver ──► Gold
                          └── same features computed in batch for TRAINING
                              (one definition, offline+online = no skew)
```
**Talking points:** latency budget as a hard design constraint; fail-open vs fail-closed is a *business* decision you escalate, not an engineering default; false-positive cost is customer friction so you tune with the fraud team, not alone; every decision is logged and explainable because declines get disputed; and rules plus model together — rules for the things you must guarantee, model for the pattern you can't enumerate.

### Scenario 2 — "Real-time single customer view / 360"
```
Core banking ──CDC(Debezium)──┐
Cards        ──CDC────────────┤
Digital app  ──events─────────┼──► Kafka ──► Stream processing
CRM          ──CDC────────────┤                 │  identity resolution
Loans        ──CDC────────────┘                 │  (deterministic keys first,
                                                │   probabilistic only with a
                                                │   human review queue)
                                                ▼
                         Bronze ──► Silver (conformed, SCD2 customer)
                                        │
                          ┌─────────────┼──────────────┐
                          ▼             ▼              ▼
                    Gold marts     Feature store   Serving API
                    (BI/Tableau)   (ML)            (low-latency store
                                                    + cache, for app/RM)
```
**Talking points:** the hard part is **identity resolution and golden record survivorship rules**, not the pipes — and those rules are a business decision that needs a data owner to sign them off. Consent and marketing permissions travel *with* the customer record. Don't serve the app from the analytics store — project into a serving store. And define "customer" once, in the glossary, before writing any code.

### Scenario 3 — "Regulatory / risk reporting you can defend"
```
Sources ──► BRONZE  immutable, as-of-received, retained per policy
                │        (this is your audit anchor — never mutate)
                ▼
            SILVER  conformed + DQ gates + reconciliation to source control totals
                │        └─ failed records quarantined, never silently dropped
                ▼
            GOLD    risk/reg datamarts, versioned business logic
                │
                ▼
        Report generation ──► sign-off workflow ──► submission
                │
                └── reproducibility: (a) table time travel to as-of date
                                     (b) code version pinned to the run
                                     (c) full column-level lineage
                                     (d) approval + adjustment audit trail
```
**Talking points:** BCBS 239 as the frame; manual adjustments are a fact of life so *model them* as an auditable adjustment table rather than pretending they don't happen; restatement must be a supported workflow; and the acceptance criterion isn't "the report ran", it's "we can reproduce this number in twelve months' time".

---

## Section 12 — Hard / gotcha questions and how to handle them

| They ask | Do this |
|---|---|
| **"Rust or Kotlin experience?"** (JD lists them) | "No production Rust or Kotlin. Python, SQL, Scala and Java are where I'm real. I read the JD's 'functional/trait-oriented' preference as a signal about engineering standards, which I'd support — but I'd be misleading you if I claimed Rust." Then pivot to a language-agnostic strength: type safety, testing discipline, code review standards. |
| **"Graph databases?"** | Be honest about depth, then show you know *when*: fraud rings, AML network analysis, beneficial ownership, entity resolution. "The pattern is multi-hop relationship traversal — where a SQL self-join at depth five stops being viable. In AML at Standard Chartered that's exactly the shape of the problem." |
| **"How much do you still code?"** | Do not say "I'm hands-off". "I don't own sprint tickets — that would be taking work from my team. I do read PRs, run design reviews, and I still go into the code when we're debugging something serious. I need to be able to check the answer I'm given." |
| **"Your recent experience is retail, not banking."** | Career *started* in banking (SCB AML across 15+ countries, DBS). Retail platforms feed the statutory close so they're run to financial-controls standard. Frame the retail years as an advantage: consumer-internet scale and speed, which is exactly what banks are trying to acquire. |
| **"Why leave Makro?"** | Forward-looking, never negative. Closer to the build, bigger regulated-data problem, Vietnam market. Do not criticise your current employer — it's the single fastest way to lose a panel. |
| **"What's your biggest weakness?"** | Real, with active mitigation. E.g. "I go too deep too fast on technical detail when the room needs the business framing — I now write the one-sentence business answer at the top of anything I present, and I've had my leads call it out when I do it." |
| **"Something you got wrong?"** | Have one prepared where the mistake was *judgment*, not bad luck. Underestimating change management / adoption is a great one — technically correct platform, insufficient adoption, and what you changed permanently in how you run programmes. |
| **"Salary expectations?"** | Don't anchor first if you can avoid it. "I'd rather understand the level and scope properly first — I'm sure you have a band for the role, and if you share it I can tell you quickly whether we're in the same range." |
| Question you genuinely can't answer | "I don't know" + how you'd find out + a related thing you do know. At Director level, calibrated confidence is being assessed as hard as knowledge. Bluffing is the only fatal answer. |

---

## Section 13 — Questions to ask them (pick 4; asking well is scored)

**Technical / role**
1. "What does the current estate actually look like — how much is on-prem Hadoop versus cloud, and where is the real pain today?"
2. "The JD mentions Flink and recommenders at tens-of-millions scale. Is that live today, or is it the ambition I'd be building toward?"
3. "How is the boundary drawn between this role and the Head of Data Engineering & Delivery — what decisions land with me?"
4. "What's the split between regulatory/mandatory work and discretionary business-value work for this team right now?"

**Organisational**
5. "In the tribe model, where does data engineering sit — central enabling tribe, embedded in business tribes, or hybrid? And how well is that working?"
6. "How does the bank handle cloud versus on-prem given SBV requirements and data localisation? What's the current position?"
7. "Who are my most demanding internal stakeholders, and what would they say about the data team today?"

**Success**
8. "If we're talking in twelve months and this has gone extremely well, what's true that isn't true today?"
9. "What happened to the last person in this seat — and what did the organisation learn?"

> Ask #8 no matter what. It gets you their real priorities, and you can use the answer in your closing.

---

## Section 14 — Night-before checklist

- [ ] Rehearse the opening (Section 1) out loud, 3×, timed under 100 seconds
- [ ] Rehearse **A1** (architecture), **B1** (banking data model), **D1** (governance), **F1** (monitoring) — these four carry the round
- [ ] Practise **drawing** all three Section 11 diagrams on paper from memory
- [ ] Say the Flink honesty line (C3) out loud until it sounds relaxed, not apologetic
- [ ] Have 4 STAR stories loaded: worst incident · exec influence · underperformer · a failure/misjudgment
- [ ] Numbers from Section 2 memorised cold
- [ ] Blank paper + pen on the desk; if it's virtual, test screen-share and have a whiteboard tool open
- [ ] Re-read the JD's competency list once — mirror their vocabulary back ("metadata management", "data governance", "computation modelling")
- [ ] Your 4 questions written down where you can see them

---

## Section 15 — The three sentences to close on

> "Two things I'd want you to remember about me. One, I've built the governed data foundation for an $8 billion business and I started my career building regulated banking data platforms across 15 countries — so I know both the scale and the controls. Two, I'm looking for this level deliberately, because I want to be in the engine room delivering, not one more layer away from it.
>
> What I'd want to do in the first ninety days is simple: understand the estate and the stakeholders properly, find the one domain where a governed end-to-end delivery would change how the business sees the data team, and ship it.
>
> Is there anything about my fit you're still unsure about? I'd rather address it now."

> That last question is the most valuable one in any interview. Ask it.

---

### Assumptions I made (flag anything wrong and I'll adjust)
- Round is technical + technical-leadership, panel likely includes the Head of Data Engineering & Delivery and an architect; conducted in English.
- Techcombank's estate: I've written answers that work whether they're Hadoop-heavy, cloud-forward, or hybrid — I did **not** assume a specific vendor stack. If you know which cloud/core-banking platform they run, tell me and I'll sharpen A1/A3.
- Vietnam regulatory references (Decree 13/2023, Decree 53/2022, Cybersecurity Law, SBV IT-security requirements) are given as the *frame you'd work to*, deliberately phrased as "I'd confirm the current position with legal and compliance." Do not assert specifics you haven't verified — with a bank panel, a confidently wrong regulatory claim costs more than a hedged correct one.
