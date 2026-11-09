# RRK: Practice Commercial and Competitive Positioning

**Question:** Five customers want your team and you have capacity for three. Sales wants you to say yes to all five. How do you run the practice, and how do you position Google against Snowflake, Databricks, AWS and Azure?
**Follow-up:** How do you estimate?
**Time:** about 5 minutes, then 1 minute for the follow-up.
**Pass signal:** margin, utilisation, capacity and repeatability, plus honest competitor positioning.

> Competitor capabilities change quickly. Before the interview, re-check each vendor's current product pages and your own hands-on notes. Do not state a competitor weakness you can't defend.

---

## 1. Short answer (the version that was supplied, kept for reference)

Prioritise by strategic value, readiness and revenue. Staff three fully; cover two with advisory and partner-led delivery. Watch utilisation, margin and customer satisfaction together; 100% utilisation burns the team and kills enablement; over-delivery eats margin. Positioning: Snowflake strong for warehouse SQL, less native Vertex AI; Databricks strong for Spark and lakehouse, higher ops cost, less serverless; AWS and Azure strong if the customer is already there, but dual-cloud ops cost; Google's advantage is serverless BigQuery and Dataflow, Vertex AI with BigQuery vector search, and Dataplex governance. Build assets (migration playbook, Dataform templates). Estimate by workload, add 20% for data-quality surprises, write assumptions in the SOW, use change orders.

Good skeleton. Fixes needed:
- **"Databricks: less serverless, higher ops cost" is risky.** Databricks offers serverless compute and SQL warehouses. If you overstate a weakness, a knowledgeable interviewer will correct you and your credibility drops. State where each competitor genuinely wins.
- **"Add 20%" needs a reason.** Say it comes from a risk register and past variance, and show it as a range with assumptions.
- **"Yes to three" needs a visible method** (a scorecard) and a way to tell sales and the two declined customers.

---

## 2. Improved answer: running the practice

**Restate (10 s):** "Five customers want us, capacity covers three, sales wants five. I'll decide with a scorecard, protect delivery quality, keep every customer's relationship alive, and make the practice more scalable afterwards."

### 2.1 Decide with a scorecard (and share it)
| Criterion | What I look at |
|---|---|
| **Strategic value** | Reference value, expansion potential, industry or account priority |
| **Win certainty** | Executive sponsor, funded budget, signed or near-signed, competitive position |
| **Delivery readiness** | Clear scope, data access, customer team ready, realistic timeline |
| **Commercial quality** | Margin, payment terms, change-control discipline, fixed-price risk |
| **Fit with our skills** | Reusable assets, skills we have, skills we can staff |
| **Risk** | Regulatory, dependency, reputational |

Score the five, rank, and show the ranking to sales. It converts "no" into "here is the reasoning", and it is easier to defend.

### 2.2 The three and the two
- **Three get full teams,** with a named lead, a senior architect, and the right mix of grades.
- **The other two are not "no".** Offer, in order: a **later start date** with a firm slot; an **advisory-led engagement** (architecture and assurance from us, delivery by a partner); a **partner-led delivery under our design authority and quality gates**; a **paid discovery** that keeps them warm. Be honest about what each means for timing and risk.
- **Tell sales early,** with the scorecard and a plan for each customer. Do not let sales over-promise to the customer.

### 2.3 Run it with four numbers together
- **Utilisation** (healthy band, not maximum): 100% sustained leaves no time for enablement, reviews, pre-sales or leave, and drives burnout and attrition.
- **Delivery margin:** protect it from over-delivery with a firm SOW, weekly effort-versus-budget tracking and change requests. Sometimes over-delivery is a conscious investment to land and expand; then it's approved, capped and tracked, not silent.
- **Customer satisfaction and outcomes:** a leading indicator of repeat work.
- **Forward capacity:** a rolling 3-month view of probability-weighted pipeline against supply by skill and grade, with triggers to hire, use partners or decline.

### 2.4 Repeatability
- Reusable assets: migration assessment and playbook, validation and reconciliation framework, Dataform templates, governance checklist, FinOps health-check, runbooks.
- Enablement time protected in the plan, so assets get built and used.
- Measure reuse: how many engagements used an asset, and effort saved per engagement.
- Partners: scorecards, shared methods, defined quality gates.

---

## 3. Improved answer: competitive positioning

**Principle:** "Position by customer need, not by loyalty. Say where each competitor wins, then where Google is a better fit." This is more credible and is how a consultant is trusted.

| Competitor | Where it genuinely wins | Where Google often fits better | Honest line |
|---|---|---|---|
| **Snowflake** | Simple operations, cross-cloud data sharing and marketplace, strong concurrency story | Serverless BigQuery with no sizing, tight link to Vertex AI and Gemini, native streaming, Looker semantic layer, open table formats | "If cross-cloud sharing is the priority, Snowflake is a fair choice. If analytics, AI and streaming on one governed platform matter, BigQuery." |
| **Databricks** | Spark and Delta lakehouse depth, data-science workflow and notebooks, strong open-source community | Serverless SQL warehouse, integrated BI and governance, lower operating burden for SQL-centred teams, open formats narrowing the gap | "They're often complementary: Databricks for heavy Spark and ML, BigQuery for serving. Let the workload decide." |
| **AWS** | Largest service catalogue and installed base, deep ecosystem | Serverless analytics with less capacity planning, global network, data and AI integration | "If the customer is committed to AWS, we reduce friction with open formats and BigQuery Omni, not force a move." |
| **Azure / Microsoft** | Power BI, Microsoft 365 and Entra integration, enterprise relationships | Large-scale analytics, openness, Looker | "Power BI can stay as the front end over BigQuery." |

**Where to be careful (verify before you say it):** Snowflake has its own AI features and Databricks has serverless offerings. Frame differences as *emphasis and operating model*, not "they can't".

**Multi-cloud cost point (valid):** running two clouds adds real cost: duplicated skills, networking, security and governance. Say it as a trade-off to quantify, not as an argument against.

**Google strengths to name accurately:** BigQuery serverless architecture, Dataflow for unified batch and streaming, Vertex AI with BigQuery ML and vector search, Dataplex governance and lineage, Looker's semantic layer, and open formats (Iceberg through BigLake).

---

## 4. Follow-up: "How do you estimate?"

**Answer:** "By **workload**, not by table count, because ten simple tables cost less than one complex pipeline with 400 lines of business logic.
1. **Inventory and classify** workloads by complexity (simple, medium, complex) using real usage data, and retire the unused first.
2. **Estimate per class** using past effort from similar work or an accelerator, giving a **range** (low, expected, high), not a single figure.
3. **Add explicit contingency from a risk register,** for data-quality surprises, access delays, SQL translation edge cases and partner productivity. A flat 20% is a starting point only if past projects support it; I'd justify it with variance from past engagements.
4. **Write the assumptions into the SOW** (data access date, volume, number of source systems, who tests, environments). If an assumption breaks, a **change request** follows.
5. **Phase it:** a paid assessment first, then fixed or capped delivery per wave, so the estimate improves as we learn.
6. **Review actual versus estimate** at the end and feed it back into the next estimate."

---

## 5. Pass checklist

- [ ] A scorecard to choose three of five, shared with sales
- [ ] A real path for the two declined (later start, advisory, partner-led, paid discovery)
- [ ] Utilisation as a band, not a maximum, with the reason
- [ ] Margin, over-delivery and change control
- [ ] Forward capacity planning with triggers
- [ ] Reusable assets and a reuse metric
- [ ] Competitors: each one's real strength first, then Google's fit
- [ ] Estimation by workload, ranges, a risk-based contingency, assumptions, change orders

## 6. Likely probes

| Probe | One-line answer |
|---|---|
| "Sales has a $3M deal that scores lowest. Do you still take it?" | Only if the gap is fixable (scope, access, price). Otherwise decline or reshape, and I tell leadership the reason. |
| "The customer insists on Snowflake. Now what?" | Respect the choice, make sure we're recommending the right design on their platform, and keep the relationship. We can still add value on governance and AI. |
| "How do you price?" | Phased: a fixed-price discovery, then delivery capped or time-and-materials with ranges and change control. |
| "What's your target utilisation?" | I'd use the practice's target band by grade, and watch the trend and the causes, not a single number. |
| "How do you know an asset is worth building?" | It has been used on at least two engagements and cut measurable effort. |
