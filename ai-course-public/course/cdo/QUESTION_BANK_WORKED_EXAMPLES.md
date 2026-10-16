# Question Bank — Worked Examples (Full Spoken Answers)

> **Use this every Tuesday.** Pick one example, speak the 60s version out loud, then the 2min version. Record. Compare to the written answer. Rewrite the parts where you drifted.
> **Coverage:** One worked example per group (5), plus the 3 highest-stakes questions (Q41, Q45, Q50) — 8 total.
> **How to read:** The 60s version is what you actually say in the first 30 seconds of the answer. The 2min STAR is the full 2 minutes. The "Why this works" line is the scoring signal. The "Counter-arguments" section is what the interviewer pushes back with.

---

## How to practice these

1. **Read the question out loud.** Then close the file.
2. **Speak the 60s version into a recorder.** Don't read; speak.
3. **Re-open. Compare to the written 60s.** Where did you drift?
4. **Speak the 2min STAR version.** Same protocol.
5. **Score yourself against the rubric** (Strategic 25 / Leadership 20 / Tech 20 / Commercial 15 / Comms 10 / Ownership 10).
6. **Rewrite the weakest 30 seconds.** Speak again.

If you can't say the 60s version in under 60 seconds without going over, you don't know the answer yet.

---

# Q1 — What is your data strategy?

**Tests:** Strategic thinking (25), Commercial (15)

## The 60-second answer (say this verbatim or close to it)

> "My data strategy starts with the business decisions you need to improve, not the technology. I work backwards from those decisions to the capabilities you need, then to the people who own them, then to the investment. At Makro, that meant three priorities: first, get the supply chain a single SKU master, because 40% of stores were over-ordering; second, build a customer 360 for the loyalty team, because churn was 18%; third, stand up a self-serve analytics layer for the category managers, because the central team was a bottleneck. The investment was $X over 18 months. The ROI was a 60% drop in data incidents, a 2-day to 2-hour month-end close, and $X in recovered margin. The strategy was '3 decisions, 3 capabilities, 3 owners, 1 platform underneath.' That's the shape."

**Word count:** ~140 words. **Time at 150 wpm:** ~56 seconds. ✅

## The 2-minute STAR version

**Situation (15 sec):** I joined Makro as Head of Data and Analytics. The company was a $8B retailer with five business units, each with its own data stack, its own SKU master, its own definition of "active customer." The central data team was 12 people; each BU had 6-8 embedded analysts. The data quality incidents were running 30+ per month. The CFO was asking why the company was spending $X on data when the month-end close took 5 days.

**Task (15 sec):** My mandate was to build a unified data platform that would (a) give the CFO a single source of truth, (b) unblock the BU analytics teams, and (c) enable the AI strategy the board had approved. The 3-year target was a 60% reduction in data incidents, a 2-hour month-end close, and 3 in-production ML use cases.

**Action (60 sec):**
1. I spent weeks 1-4 listening — 1:1s with every BU head, every analyst, the CFO, the CTO. I documented the decisions that needed data, not the data we had. The top three were: supply chain SKU master, customer 360 for loyalty, self-serve for category managers.
2. I named an owner for each. The supply chain owner was the COO. The customer 360 owner was the CMO. The self-serve owner was the CFO. I made the ownership visible in a steering committee I ran monthly.
3. I built a 3-year plan in three phases: Year 1 foundations (single SKU master, semantic layer, governance), Year 2 scale (customer 360, self-serve), Year 3 differentiation (ML use cases, external data products).
4. I cut three programs that didn't serve the three priorities — a real-time dashboard project, a marketing attribution tool, and a data lake that no one owned. The CTO hated the data lake cut; I traded it for a 2-week SLA on the semantic layer.
5. I hired 8 people — a data engineering lead, two ML engineers, a data product manager, a governance lead, two senior analysts, and a chief of staff. I left the existing 12 people in place.

**Result (30 sec):** Month-end close went from 5 days to 2 hours. Data incidents dropped 60%. The customer 360 launched in 14 months and was the substrate for the first ML use case (churn prediction). The category managers' self-serve hit 70% adoption in 6 months. The board re-upped the AI investment. The CFO called it the best technology investment of the year.

## Why this works

- **Opens with the business problem, not the technology.** "Decisions, not technology" is the right answer.
- **Names three concrete priorities with three concrete owners.** Specificity = credibility.
- **Names a cut.** Cutting three programs is the credibility move — anyone can add; few can subtract.
- **Ends with measurable outcomes.** Numbers are non-negotiable.
- **Total time: ~2:00.** Tight.

## Counter-arguments to be ready for

- **"How did you measure ROI?"** Three layers: adoption (% of BUs on platform), operational (incident rate, month-end close time), business (recovered margin, churn reduction).
- **"Who owned delivery?"** The BU heads. The platform team set the contract; the BUs owned the data products.
- **"What did you stop doing?"** Three programs: real-time dashboard, marketing attribution, data lake.
- **"What if a BU refused to standardize?"** I escalated to the CFO. The CFO made it non-negotiable. The contract is the platform mandate.
- **"What was your biggest mistake?"** I underestimated the change management on the SKU master. We had to do 3 months of training, not 3 weeks. The lesson: a contract without adoption is a contract on paper.

---

# Q11 — Design a modern enterprise data platform.

**Tests:** Technical (20), Strategic (25)

## The 60-second answer

> "The shape is five layers. First, ingestion — CDC and streaming, Kafka or a managed equivalent. Second, storage — a lakehouse on object storage with Iceberg or Delta, not a warehouse, because at 50 billion events a day the TCO is two to three times lower. Third, transformation — dbt for SQL, Spark or Flink for heavy lifting, with semantic-layer models. Fourth, serving — a feature store for ML, a query engine for BI, a vector store for RAG. Fifth, consumption — domain-owned data products, not central reports. Cross-cutting: lineage, observability, IAM, FinOps, contracts. The non-obvious answer: build the feature store in-house at 10 million-plus customers; the features are the IP. Build the lakehouse in-house too. Buy everything else."

**Word count:** ~140 words. **Time:** ~56 seconds. ✅

## The 2-minute STAR version

**Situation:** The company is a $5B retailer with 20 million customers, 50 billion events a day, five BUs, and a data team of 50. The current state: a Snowflake warehouse, three feature stores, two ETL tools, no lineage, no contracts, no observability. The incident rate is 25 per month. The ML team's biggest complaint is feature inconsistency — the same customer has three different lifetime values in three different models.

**Task:** Design a platform that (a) drops incident rate to under 5 per month, (b) gives every ML model a single feature source, (c) gives every BU a single metric source, (d) costs less than the current state at the 18-month mark.

**Action:**
1. **Ingestion:** Kafka for streaming, Fivetran or Airbyte for SaaS sources, Debezium for CDC. The ingestion layer is mostly off-the-shelf.
2. **Storage:** Migrate from Snowflake to an Iceberg-on-object-storage lakehouse. The reason: at 50 billion events a day, the Snowflake bill was $X. The Iceberg-on-S3 bill at the same workload was $0.4X. The migration takes 12 months; we do it workload by workload, not big-bang.
3. **Transformation:** dbt for SQL transformations; Spark for heavy ML feature engineering. The semantic layer is dbt's metrics layer or Cube. The metric definitions live in the semantic layer, not in Looker or Tableau.
4. **Serving:** Build a feature store in-house. The reason: the features are the IP. A vendor feature store sees the schema. A vector store — Pinecone or Weaviate — for RAG use cases. A query engine — the same Iceberg tables, queried by Trino or Athena.
5. **Consumption:** Domain-owned data products. Each BU owns its metrics, its features, its models. The central team owns the contract, the lineage, the FinOps dashboard, the IAM.
6. **Cross-cutting:** Lineage (OpenLineage or DataHub), observability (Monte Carlo or Bigeye), FinOps dashboard per BU, data contracts per source system.

**Result:** Incident rate drops from 25 to 4 per month. ML feature consistency goes from 3 sources to 1. The 18-month TCO is 30% lower than the legacy state. The first domain-owned data product (the customer 360) ships in month 14. The vector store is in production for the customer-support RAG by month 18.

## Why this works

- **Five layers, named.** The interviewer can draw the boxes with you.
- **Cost number with the lakehouse.** "TCO is 2-3× lower" is the defensible answer.
- **In-house feature store, justified.** "Features are the IP" is the right reason.
- **Domain-owned data products.** Federation is the destination.
- **Cross-cutting named.** Lineage, observability, IAM, FinOps, contracts.

## Counter-arguments to be ready for

- **"Why not Snowflake?"** Snowflake is great for governed BI. At 50B+ events/day, the TCO is 2-3× higher. Most enterprises end up with both — Snowflake for finance/BI, Iceberg for ML/AI.
- **"Why not Databricks?"** Databricks is the right answer if you want a single vendor and you don't have the team to operate Iceberg yourself. The build-vs-buy call depends on team capacity.
- **"Why dbt?"** Industry standard. Hireable. The semantic layer is a feature, not a vendor.
- **"Why not Airflow?"** Dagster or Prefect are the modern alternatives. Airflow works; it's just not the new default.
- **"What's the migration risk?"** The biggest risk is the cutover. We migrate workload by workload, never big-bang. The first migration is the lowest-risk workload (the marketing campaign data); the last is the highest-risk (the financial close).

---

# Q21 — Tell me about a time you raised the bar.

**Tests:** Leadership (20), Ownership (10)

## The 60-second answer

> "When I joined Makro, the data team had 12 engineers and a 30-incident-per-month quality problem. I raised the bar three ways. First, I changed the on-call from a punishment to a rotation, with comp. Second, I made the SLA visible — every dashboard had a freshness and a reliability score, posted publicly. Third, I cut the three lowest-quality pipelines in the first 60 days, even though the BU leads pushed back. The result: incident rate dropped 60% in 12 months, the team was proud of the on-call, and the BU leads stopped asking me to 'just keep the lights on' and started asking me to ship ML. The lesson: bar-raising is subtraction, not addition."

**Word count:** ~120 words. **Time:** ~48 seconds. ✅

## The 2-minute STAR version

**Situation:** Makro's data team was 12 engineers. The incident rate was 30 per month. The on-call was a punishment — the same two senior engineers carried it, and they were burning out. The dashboards had no SLAs. Three pipelines were the source of 60% of the incidents, and they belonged to the highest-revenue BU.

**Task:** Drop incident rate to under 10 per month in 12 months. Fix the on-call. Make the SLAs visible. Keep the BUs happy.

**Action:**
1. **On-call:** I made on-call a rotation with comp. Every engineer did one week per quarter. I made the rotation fair (alphabetical, not political). I added a "follow-the-sun" handoff to reduce the wake-up pages. The senior engineers got their nights back.
2. **SLAs:** Every dashboard got a freshness score and a reliability score, posted on a public dashboard. The BUs could see which dashboards were unreliable. The unhealthy ones got a "do not use for decisions" banner. The pressure to fix the SLAs came from the BUs, not from me.
3. **The cut:** In the first 60 days, I cut the three lowest-quality pipelines. They were in the highest-revenue BU. The BU lead pushed back. I said: "These three pipelines are the reason your data is unreliable. Cut them; I'll re-platform the two that matter in 90 days." He agreed. The cut was the credibility move.
4. **The re-platform:** I re-platformed the two pipelines that mattered. The third was replaced by a manual report that the BU lead preferred anyway.
5. **The bar:** I made the bar visible in hiring. Every new data engineer had a take-home that included an on-call scenario. The interview scorecard included "would I put this person on-call?"

**Result:** Incident rate dropped from 30 to 12 per month in 12 months (target was under 10, missed by 2; revised to 8 in month 18). The on-call rotation was sustainable. The SLA dashboard was the most-viewed internal page. The BU leads stopped saying "fix the data" and started saying "ship the ML." The team was proud of the on-call, which is the only metric that matters.

## Why this works

- **Three concrete moves.** On-call rotation, visible SLAs, three pipeline cuts. Not a narrative; a playbook.
- **The cut is the credibility.** Anyone can add; few can subtract.
- **"Bar-raising is subtraction, not addition."** This is the line the interviewer remembers.
- **Names a missed target.** "Hit 12, not 10" is the credibility move — over-claiming kills trust.

## Counter-arguments to be ready for

- **"What did you cut?"** Three pipelines in the highest-revenue BU. Two were re-platformed; one was replaced by a manual report.
- **"How did the team react?"** The senior engineers were relieved. The junior engineers were scared of on-call at first; the rotation made it fair. The team eNPS went from neutral to +30.
- **"What if the BU lead refused?"** I escalated to the COO. The COO backed the cut because the data quality was affecting the month-end close. The cut was non-negotiable.
- **"What's the lesson?"** Bar-raising is subtraction, not addition. The cut is the credibility move.

---

# Q31 — How would you establish enterprise data governance?

**Tests:** Leadership (20), Technical (20)

## The 60-second answer

> "Three moves, in this order. First, I would establish a data council with the C-suite and the BU heads, chaired by the CDO, meeting monthly, with a published charter. The council owns the policies, the data domains, and the escalation path. Second, I would name a data owner for every domain — not a central team; a domain expert in the BU. The data owner is accountable for the quality, the documentation, and the access. Third, I would publish a data catalog with lineage, ownership, and a data contract per source. The contract is the leverage — without it, governance is a wiki. The non-obvious answer: governance is a product, not a compliance function. The user is the data scientist. The SLA is data access in under one hour, data quality score above 95%, and lineage for 100% of critical assets."

**Word count:** ~155 words. **Time:** ~62 seconds. (Slightly long; trim to 140 if needed.)

## The 2-minute STAR version

**Situation:** The company is a $5B financial services firm with 50+ source systems, 200+ dashboards, and no central data ownership. The CFO asks "what is our customer count?" and gets three different answers. The risk team asks "what is our exposure to X?" and the answer takes 2 weeks. The data team is 80 people, mostly embedded in BUs.

**Task:** Establish enterprise data governance that (a) gives the CFO a single source of truth, (b) gives the risk team a 1-day answer, (c) doesn't slow down the BU analytics teams, (d) costs less than $1M in new headcount.

**Action:**
1. **Data council:** Charter a data council with the CDO as chair, the CFO, the CRO, the BU heads, and the CISO. Monthly. The council owns: data policies, data domains, escalation path, and the data investment budget. The first 90 days are spent agreeing on the charter and the first three domains (customer, product, transaction).
2. **Data owners:** For each domain, name a data owner in the BU. Not a central team; a domain expert. The data owner is accountable for the quality (DQ score above 95%), the documentation (in the catalog), and the access (entitlement review quarterly). The data owner gets 20% of their time allocated; the rest is BU delivery.
3. **Data catalog:** Deploy a data catalog (DataHub, Atlan, or Collibra) with lineage (OpenLineage), ownership, and a data contract per source. The data contract is the lever: the producer of the data commits to schema, freshness, and quality; the consumer commits to usage. Without the contract, the catalog is a wiki.
4. **Product framing:** Treat governance as a product. The users are the data scientists and the analysts. The SLAs are: data access in under 1 hour (from request to grant), DQ score above 95% for critical assets, lineage for 100% of critical assets. The product team is 3 people in the central data team.
5. **Adoption:** The first 100 users in the catalog are the data council + the top 10 analysts in each BU. The adoption metric is weekly active users in the catalog. Target: 200 weekly active users in 6 months.

**Result:** After 12 months: 30 data owners named; 80% of critical assets have lineage; DQ score on critical assets is 96%; data access time is 4 hours (target was 1 hour, missed by 3 hours; revised to 1 hour in month 18). The CFO has a single customer count. The risk team has a 2-day answer. The BU analytics teams are faster, not slower.

## Why this works

- **Three moves, in order.** Council → owners → catalog + contracts. The sequence is the answer.
- **Data owner in the BU, not central.** Federation is the right shape.
- **Data contract is the lever.** The word "contract" is the right word.
- **Governance is a product.** The non-obvious answer.
- **Names a missed target.** "4 hours, not 1" — credibility.

## Counter-arguments to be ready for

- **"What if a BU refuses to name a data owner?"** I escalate to the data council. The council makes it non-negotiable. The CFO backs the council.
- **"What about regulatory compliance?"** The data council owns the regulatory reporting; the data owners are the first line; the central governance team is the second line. The model is the same as financial controls.
- **"What if the catalog becomes a wiki?"** The SLAs are the protection. If the data access SLA is missed 3 times in a quarter, the data owner is escalated. The contract has teeth.
- **"What's the cost?"** $800K in headcount (3 people) + $200K in tooling. The ROI is the avoided cost of the 2-week risk-team answer and the avoided regulatory fine.

---

# Q41 — Why should we hire you as Head of Data?

**Tests:** Comms (10), Strategic (25), Ownership (10)

## The 60-second answer

> "Three reasons. First, I have 15+ years of operating at scale — $8B businesses, 50+ billion events a day, 200-person data teams, and 99.99% uptime. Second, I have the rare combination of build, lead, and own. I have built data platforms from zero, led 200-person orgs through transformations, and owned the P&L for the data investment. Third, I have a track record of measurable business outcomes — not 'I shipped a data lake,' but 'I dropped data incidents 60%, cut month-end close from 5 days to 2 hours, and shipped 3 ML use cases that moved revenue.' The non-obvious reason: I am willing to say no to the CEO when the data says no. The role you are hiring for needs someone who can be the truth-teller in the room. That is what I am."

**Word count:** ~150 words. **Time:** ~60 seconds. ✅

## The 2-minute STAR version

**Situation:** You are interviewing me for Head of Data. You have a shortlist of 4-5 candidates. Most have strong technical backgrounds. A few have led teams. Almost none have done both at your scale.

**Task:** Convince you in 2 minutes that I am the right hire.

**Action — three reasons, with evidence:**

**Reason 1: I have operated at your scale.** I have led data + AI at $8B businesses, with 50+ billion events per day, 200-person data teams, and 99.99% uptime SLAs. I have done this in retail (Makro), e-commerce (Lazada), fintech (Xendit), and banking (SCB). The patterns are the same: the failure modes are the same; the solutions are the same. I am not learning on the job.

**Reason 2: I have the rare combination of build, lead, own.** Build: I have built data platforms from zero (Lazada Customer 360 was a greenfield build). Lead: I have grown data teams from 8 to 200 and transformed them through mergers, reorgs, and capability shifts. Own: I have owned the P&L for the data investment — $Xm annual budget, with a 30% TCO reduction target that I hit. Most candidates have one of these. Few have all three.

**Reason 3: I have measurable business outcomes.** Not "I shipped a data lake." The actual outcomes: data incidents dropped 60%; month-end close dropped from 5 days to 2 hours; 3 ML use cases shipped, each with a measurable revenue or cost impact. The CFO called the data platform investment the best technology investment of the year. The board re-upped the AI investment based on the data team's track record.

**The non-obvious reason: I am willing to say no to the CEO.** The role you are hiring for needs someone who can be the truth-teller in the room. I have said no to a CEO who wanted to ship an AI feature in 30 days. The 60-day plan shipped. The 30-day plan would have killed trust. I have Disagreed and Committed on a federated data strategy that I thought was wrong; the federation failed 18 months later, and the central platform was rebuilt. I am not a yes-person. I am a builder-operator who tells the truth.

**Result:** The hire. (Or, in the practice version: the next 90 days — see Q3.)

## Why this works

- **Three reasons, with evidence.** Not a narrative; a pitch.
- **Names the non-obvious reason.** "Willing to say no to the CEO" is the differentiator.
- **Specific numbers throughout.** "60%", "5 days to 2 hours", "3 ML use cases."
- **References real resume stories.** S1, S7, S15.
- **Total time: ~2:00.** Tight.

## Counter-arguments to be ready for

- **"What makes you different from the other candidates?"** The combination. Most candidates have built or led. Few have done both at scale, with measurable P&L outcomes. And the willingness to say no to the CEO.
- **"What's your biggest weakness?"** I am impatient with low-quality work. I have learned to coach rather than criticize, but the impatience is still there. I manage it by making the bar visible and the cuts visible — that way the team sees the standard, not just my frustration.
- **"Why are you leaving your current role?"** I have done what I came to do. The platform is in production. The team is in place. I am looking for a 10× problem, not a 2× problem.
- **"What would your first 90 days look like?"** See Q3.

---

# Q45 — How would you handle a CEO who demands unrealistic timelines?

**Tests:** Leadership (20), Communication (10)

## The 60-second answer

> "Three moves, in that order. First, reframe from deadline to outcome. Ask the CEO: 'What business outcome are you trying to hit by when?' Usually the answer is not 'ship the feature by Friday' — it is 'hit the Q4 number by Q4.' The deadline is a proxy for the outcome. Second, show the trade-off. 'We can ship in 30 days with 60% confidence, or in 60 days with 90% confidence. The 30-day plan has a 40% chance of a public failure. The 60-day plan has a 10% chance.' Make the trade-off explicit. Third, offer the smallest credible commitment. 'I will ship a 1-day demo in 7 days, a beta in 30 days, and a production version in 60 days. The 7-day demo is the smallest credible commitment that gets you to the Q4 outcome.' The CEO will usually take the 60-day plan. If they insist on 30, I will do it — but I will document the trade-off in writing. The CEO buys math, not narrative."

**Word count:** ~165 words. **Time:** ~66 seconds. (Slightly long; trim if needed.)

## The 2-minute STAR version

**Situation:** The CEO wants a new AI feature shipped in 30 days for a board demo. My engineering team says 60 days is realistic. The board demo is 45 days away. The CEO is pushing hard; the board is the audience.

**Task:** Ship something credible in 30 days without killing the team's trust or the feature's quality.

**Action:**
1. **Reframe (5 min):** I asked the CEO: "What business outcome are we trying to hit by the board demo?" The answer was: "Show the board we are an AI company." The deadline was a proxy for the outcome. The real outcome was the *narrative* for the board, not the feature itself.
2. **Trade-off (10 min):** I laid out three options:
   - **Option A:** Ship a demo in 7 days (a controlled environment, a curated input, a 95% success rate). 30 days of work: design, build, demo.
   - **Option B:** Ship a beta in 30 days (real users, real data, a 70% success rate, a known failure mode that we document). 60 days of work: design, build, beta, monitor.
   - **Option C:** Ship in production in 60 days (real users, real data, a 95% success rate, a monitored failure mode). 90 days of work: design, build, beta, production, monitor, iterate.
3. **The trade-off was explicit:** Option A risks the board thinking the feature is fake. Option B risks a public failure in the first 30 days. Option C is safe but misses the board demo. The CEO picked Option A + B: demo in 7 days, beta in 30 days, production in 60. The board got the demo. The beta was shipped 2 days late. The production version was shipped on time.
4. **The documentation:** I sent the CEO a one-pager: "Here is the trade-off. Here is what we are shipping. Here is what we are not shipping. Here is the failure mode I am worried about. Here is the mitigation." The one-pager is the protection. If the beta fails, the CEO cannot say "you didn't warn me." The one-pager is the Disagree-and-Commit artifact.
5. **The team:** I told the team the trade-off before I told the CEO. The team knew I had their back. The on-call was staffed for the 30-day beta. The team worked hard, but they were not surprised.

**Result:** The demo worked. The board was impressed. The beta shipped 2 days late. The production version shipped on time. The CEO later said: "That was the right call. Thank you for not just saying yes." The trust went up. The team's trust went up. The next time I had a trade-off to make, the CEO asked for the one-pager before the meeting.

## Why this works

- **Reframe from deadline to outcome.** The first move.
- **Three options with explicit trade-offs.** Not "yes" or "no"; "here are the three ways."
- **Smallest credible commitment.** Option A + B is the right answer.
- **Document the trade-off in writing.** The one-pager is the protection.
- **Tell the team first.** The team comes before the CEO.

## Counter-arguments to be ready for

- **"What if the CEO insists on 30 days anyway?"** I do it. But I document the trade-off in writing. The one-pager protects me and the team.
- **"What if the feature fails publicly?"** The one-pager is the protection. The CEO cannot say "you didn't warn me." The post-mortem is also a credibility move.
- **"What if the team can't deliver?"** I escalate. I tell the CEO: "I will not promise what the team cannot deliver. If you want 30 days, I need 2 more engineers. If you want 60 days, I will deliver 95%." The trade-off is the answer.
- **"What if the CEO is right and 30 days is feasible?"** I am wrong. I commit. I deliver. The lesson: "Bias for Action" does not mean "ship faster than the data supports." It means "make the call with the data you have."

---

# Q50 — What would your first-year scorecard look like?

**Tests:** Strategic (25), Ownership (10)

## The 60-second answer

> "Three layers. Foundational: 99.9% reliability on the top-20 dashboards, 100% lineage on critical assets, 95% data quality score, governance operating in every domain. Operational: 30% TCO reduction or 30% capacity reinvested, 70% BU adoption of the platform, 5 in-production ML use cases. Business: 3 measurable revenue or cost outcomes, 1 customer-visible data product, board re-up of the AI investment. The scorecard is 12 metrics across 3 layers. I would publish it on day 1 and report against it monthly to the CEO and quarterly to the board. The scorecard is the contract."

**Word count:** ~110 words. **Time:** ~44 seconds. ✅

## The 2-minute STAR version

**Situation:** I am 30 days into the Head of Data role. The CEO has asked for a first-year scorecard. The board has approved the data + AI investment. The BUs are waiting to see what the new CDO will do.

**Task:** Build a 12-metric scorecard across 3 layers that the CEO, the board, and the BU heads can all see.

**Action:**

| Layer | Metric | Y1 target | Why it matters |
|---|---|---|---|
| **Foundational** | Top-20 dashboard reliability | 99.9% | The BUs trust the data |
| | Critical-asset lineage | 100% | Regulatory + risk |
| | Critical-asset DQ score | 95% | The data is right |
| | Governance operating in every domain | Yes | The data has an owner |
| **Operational** | TCO reduction or capacity reinvested | 30% | The platform is efficient |
| | BU adoption of the platform | 70% | The BUs use the platform |
| | ML use cases in production | 5 | The AI is shipping |
| | Time-to-data-access | < 1 hour | The platform is fast |
| **Business** | Measurable revenue or cost outcomes | 3 | The data moves the P&L |
| | Customer-visible data product | 1 | The data is a product |
| | Board re-up of AI investment | Yes | The investment is sustained |
| | Team eNPS | +20 | The team is healthy |

**The scorecard is published on day 1, reported monthly to the CEO, quarterly to the board.** I commit to the targets in writing. I report misses as well as hits. The scorecard is the contract between me and the company.

**Result:** End of Y1. Foundational: 99.9% reliability (hit), 100% lineage (hit), 95% DQ (hit at 96%), governance in every domain (hit at 4 of 5). Operational: 28% TCO reduction (missed 30% by 2 pts; hit in Y2), 65% BU adoption (missed 70% by 5 pts; hit in Y2), 4 ML use cases (missed 5 by 1; hit in Y2). Business: 2 measurable outcomes (missed 3 by 1), 1 customer-visible data product (hit), board re-up (hit), team eNPS +25 (beat +20). Net: 8 of 12 hit, 4 missed. The misses are the credibility. The CEO trusts the scorecard because I report the misses.

## Why this works

- **Three layers, 12 metrics.** Specific.
- **Targets, not aspirations.** "99.9%" is the right format.
- **Published on day 1.** Commitment in writing.
- **Reports misses.** Credibility = reporting misses.
- **Names actual results.** "8 of 12 hit" is the credibility move.

## Counter-arguments to be ready for

- **"What if a metric is missed?"** I report it, I root-cause it, and I commit to the catch-up date. The misses are the credibility.
- **"What if the board changes the scorecard?"** I negotiate. The scorecard is a contract; both sides commit. If the board wants to change a target, I ask for the rationale and the trade-off.
- **"What if the BU heads don't accept the scorecard?"** I escalate to the CEO. The CEO backs the scorecard. The scorecard is the platform mandate.
- **"What if a metric is wrong?"** I change it. The scorecard is a living document. I commit to the changes in writing.

---

# Q36 — How would you respond to an AI hallucination incident?

**Tests:** Leadership (20), Communication (10)

## The 60-second answer

> "Five moves, in this order. First, acknowledge fast. The first 2 minutes are the most important. 'Thanks for the report. We're investigating. We'll publish a written response within 24 hours.' Do not defend. Do not deflect. Second, investigate. Pull the model decision log. Pull the eval harness results. Find the root cause — usually prompt injection, retrieval hallucination, eval harness gap, or model drift. Third, communicate. 'The correct response should have been X. The likely cause was Y. The model is within SLO / requires re-eval / requires rollback.' This is my accountability — the eval harness is the data team's responsibility. Fourth, remediate. 24h: public response, brief the CEO, pause the model. 1 week: fix the eval, add the scenario. 1 month: continuous eval in CI, model registry, quarterly transparency report. Fifth, defend. Every follow-up question gets a 30-second answer: 'How did this get through?' — CI/CD gap. 'Who is accountable?' — me. 'Is the model safe?' — affected capability isolated, rest within SLO."

**Word count:** ~165 words. **Time:** ~66 seconds. (Slightly long; trim if needed.)

## The 2-minute STAR version

Use the same five-move structure but expand with the actual incident. Reference the case-study files for the company-specific version:

- **Google:** Gemini eval public failure → `case-studies-by-company/google/cs-05-gemini-eval-public.md`
- **Meta:** Llama 4 eval public failure → `case-studies-by-company/meta/cs-05-llama-eval-public.md`
- **Stripe:** Radar false-decline incident → `case-studies-by-company/stripe/cs-05-radar-false-decline-crisis.md`
- **Shopify:** Sidekick hallucination → `case-studies-by-company/shopify/cs-05-sidekick-hallucination-crisis.md`
- **Amazon:** Q hallucination at re:Invent → `case-studies-by-company/amazon/cs-05-q-hallucination-reinvent.md`

The structure is the same. The numbers and the cast change. The pattern is universal.

## Why this works

- **Five moves, in order.** Acknowledge → Investigate → Communicate → Remediate → Defend.
- **"This is my accountability"** — the data team owns the eval harness.
- **24h / 1 week / 1 month / quarterly cadence.** Specific.
- **Every follow-up answered in 30 seconds.** The defender's discipline.

## Counter-arguments to be ready for

- **"How did this get through?"** The CI/CD had a gap. Fix: continuous eval in CI; merchant/customer feedback as a first-class signal; tool-use sandboxing.
- **"Who is accountable?"** Me. The eval harness and the feedback loop are the data team's responsibility.
- **"Is the model safe to ship?"** The affected capability is isolated; the rest is within SLO.
- **"What about the [tweet / customer / developer]?"** Direct, public, no-conditions outreach. Make them a customer of the next improvement.
- **"What about the [N retweets / N customers affected]?"** One high-quality response + one written post. The signal is the answer, not the volume.

---

# How to score yourself

For each answer, score against the rubric (max 100):

| Competency | Weight | What to look for |
|---|---|---|
| Strategic and business thinking | 25 | Did you name the business outcome first? Did you name the trade-offs? |
| Leadership and executive influence | 20 | Did you name the people moves? Did you name a cut? |
| Technical judgment and architecture | 20 | Did you name the specific technology choices? Did you justify the build-vs-buy? |
| Commercial and financial understanding | 15 | Did you name a number? Did you name the ROI? |
| Communication and structure | 10 | Did you open with the answer? Did you end on time? |
| Ownership and measurable impact | 10 | Did you say "I" not "we"? Did you name a missed target? |

**Target:** ≥90/100 per answer.

**If you score <80:** the answer is too long, too narrative, or missing numbers. Rewrite.

**If you score 80-89:** the answer is mostly there. Find the one number you didn't name. Add it.

**If you score ≥90:** the answer is ready. Record it. Move on.

---

**Source:** Built from the 50 questions in `QUESTION_BANK.md`, the 15 stories in `STORY_BANK.md`, and the 5 company case studies in `case-studies-by-company/`.
