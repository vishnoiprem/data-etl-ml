# Lesson 2 — Daily Workflow Changes

> **Type:** Article · **Length:** 6 min read · **Level:** Beginner
> **Author:** Gorijala Kiran · **76 completed** · **4.7 (3)**
> **Source:** [Data Vidhya — AI for Data Engineering](https://datavidhya.com/learn/ai-for-data-engineering/)

---

## Concrete before-and-after walkthroughs

How AI tools change SQL, pipelines, debugging, documentation, and data modeling for working data engineers.

A year ago, writing a Spark job took me 2 hours. Today it takes 20 minutes. I did not get 6× better at Spark in a year. I learned to use AI tools as a **thinking partner** instead of a code generator, and that shift changed how every part of my day looks.

This article is not theory. It is a task-by-task walkthrough of what changed: the SQL I write, the pipelines I ship, the bugs I chase, the docs I no longer dread. For each task, I will show you the manual workflow, the AI-assisted version, the specific time saved, and **at least one failure pattern I have personally hit**. Because here is the thing nobody wants to admit: AI tools fail silently. Not loudly. Silently. And if you do not know where they fail, you will ship the bugs.

By the end you will know exactly where AI shines, where it is dangerous, and what your day looks like once you have built the right habits.

---

## The shift in one sentence

> AI did not make me a faster typist. It made me spend less time on the parts of my job that were **never** the interesting part: boilerplate, first drafts, documentation, log parsing. The interesting parts (modeling decisions, business context, root-cause judgment) still take the same time. They should.

---

```
   +────────────────────────────────────────────────────────────────+
   |    AI SHINES vs AI FAILS — 2×2 for Data Engineering Work       |
   +────────────────────────────────────────────────────────────────+
   |                              STRUCTURAL                        |
   |                          (knowable by AI)                      |
   | AI SHINES (LOCAL + STRUCTURAL)                                |
   | • boilerplate • first drafts • syntax/nesting • log pattern   |
   |                          ┌──────────────┐                     |
   |                          │              │                     |
   |                          │   PARTIAL    │                     |
   |                          │ cross-system │                     |
   | LOCAL                    │ tracing,     │          LOCAL     |
   | (knowable by AI)         │ lineage      │          (tacit)   |
   |                          │              │          (org lore) |
   |                          │   PARTIAL    │                     |
   |                          │ team naming, │                     |
   |                          │ in-house     │                     |
   |                          │ patterns     │                     |
   |                          └──────────────┘                     |
   |                          AI FAILS (DISTRIBUTED + TACIT)       |
   |                          • business context • org politics    |
   |                          • 6-month history • conformed dims   |
   +────────────────────────────────────────────────────────────────+
                          DISTRIBUTED (across time / teams)
```

---

## SQL Development — Before vs After

SQL is where AI delivers the most immediate, most measurable productivity gain in data engineering. It is also where it fails most subtly.

### The before workflow
You get a request: *"Show me the top 3 products by revenue per category for users in the second-purchase cohort, last 90 days."* You open your editor, stare at the schema for a few minutes, sketch the CTE structure on paper, start writing. You forget which window function you want, Google it, get distracted, come back. You run the query. The numbers look weird. You add a `COUNT(*)` to check for fan-out. You spot a duplicate join. You fix it. **30–45 minutes later** you have a query that works.

### The after workflow
You describe the intent to your AI assistant with three things attached: the **schema**, the **dialect**, and an **example row**. You get a draft in 10 seconds. You read it. You check the joins. You run it on a sample. **8–12 minutes later** you have a query that works.

Here is the kind of draft I get back for a cohort-style window-function query, the sort I used to spend 30 minutes on:

```sql
WITH cohort AS (
  SELECT user_id, MIN(order_date) AS first_order_date
  FROM orders
  GROUP BY user_id
),
ranked AS (
  SELECT
    p.category,
    p.product_id,
    SUM(oi.revenue) AS revenue,
    ROW_NUMBER() OVER (
      PARTITION BY p.category
      ORDER BY SUM(oi.revenue) DESC
    ) AS rn
  FROM order_items oi
  JOIN orders o   ON o.order_id = oi.order_id
  JOIN products p ON p.product_id = oi.product_id
  JOIN cohort c   ON c.user_id = o.user_id
  WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY p.category, p.product_id
)
SELECT category, product_id, revenue
FROM ranked
WHERE rn <= 3;
```

That structure is correct 95% of the time. The skeleton is fine. **What is not fine is the joints.**

**Productivity gain: 3–5× for complex queries.** For me, a query that used to take 30 minutes now takes 8–10. Multiply that across the 6–8 SQL tasks I do in a typical day and that is two hours back.

> **AI-generated SQL looks right more often than it IS right.**
>
> I have caught all of these in AI output in the last six months:
>
> - **Silent fan-out joins.** AI used `JOIN` where the relationship was one-to-many, producing 3× expected rows. The aggregate looked plausible because the inflation was uniform.
> - **NULL exclusion in negation.** AI wrote `WHERE region != 'APAC'` to get non-APAC rows. 8% of rows had `NULL region` and were silently dropped. Nobody noticed for six weeks.
> - **Wrong window frame.** AI used `LAST_VALUE` without specifying `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`. Default frame returned the current row, not the actual last value.
> - **Timezone drift.** AI generated date filters in UTC for a report business users read in IST. Off by one day at the boundaries, off by a lot during DST.
>
> The AI saved me the first draft. It did not save me from verifying every line.

```
   AI-generated SQL splits into:
   ─────────────────────────────────────────────────────────────
   SKELETON (AI great)         JOINTS (you must verify)
   • CTE structure             • JOIN type fan-out
   • JOIN order                • WHERE != with NULLs
   • window function pick      • window frame clauses
   • syntax                    • timezone in date filters
   • subquery nesting          • NULL in aggregates
   ─────────────────────────────────────────────────────────────
```

**The rule I follow: trust AI for the skeleton, verify the joints.** Skeleton is structure (which CTE, which join order, which window function). Joints are the subtle logic (join type, NULL handling, frame clauses, timezone). The first AI is great at. The second is still on you.

---

## Pipeline Development — Before vs After

Pipelines are **80% boilerplate and 20% the part where you actually have to think.** AI handles the 80% almost perfectly. That is the entire pitch.

### The before workflow
A new ingestion pipeline used to take me **2–3 days**. Define source connection, write the extraction loop, add retries with backoff, write the schema validation, set up logging, write the loader, write unit tests, write the DAG, document it. Most of that is muscle memory you grind through. Half of it is copy-pasted from a previous pipeline and modified.

### The after workflow
I describe the pipeline: *"Pull from this API, paginated, with these auth requirements, write to a Snowflake staging table partitioned by ingest_date, schedule daily in Airflow, retry 3 times with exponential backoff, alert on failure."* I get a working skeleton in five minutes: the operator config, the extraction function with retries, the schema validation hooks, the test scaffolding, the DAG. I spend the rest of the day on the parts that actually need thought: the **business validation rules, the idempotency strategy, the edge cases specific to this source**.

**Productivity gain: 2–3× for standard pipelines.** A pipeline that used to take 2.5 days takes 6–8 hours of focused work. For novel or genuinely complex pipelines (stateful streaming, custom CDC) the gain shrinks to maybe 1.3× because the boilerplate is a smaller fraction of the total work.

### The happy path trap
AI loves the happy path. It generates beautiful extraction code that handles the case where the API returns clean data on the first try. Then you have to ask, explicitly:
- What happens when the API returns a 429?
- What about partial pages?
- What if the schema includes a new field tomorrow?
- What if a record arrives twice?

If you do not ask, AI will not write that code. And the failure mode in production is exactly the failure mode you did not specify.

**The habit I formed:** I never let AI generate a full pipeline in one shot. I break it into components (source, extractor, validator, loader, orchestrator) and generate each one separately, with explicit edge cases stated upfront. The output quality jumps. So does my ability to actually understand what it produced.

```
One-shot pipeline generation                          Component-by-component
──────────────────────────                          ────────────────────────
"Generate the whole pipeline"                        "Generate the source connector"
            │                                                   │
            ▼                                                   ▼
Happy-path-only code                                     with explicit edge cases
Silent failures in prod                                (errors, retries, duplicates,
                                                           schema drift)
```

---

## Debugging and Root Cause Analysis — Before vs After

Debugging is where AI quietly punches above its weight. Most data engineers do not realize this yet.

### The before workflow
The 3 a.m. Airflow alert. You log in, open the failed task, scroll through **4,000 lines of Spark executor logs** looking for the actual exception. You find a stack trace. You form a hypothesis. You test it. Wrong. You form another hypothesis. You test it. Wrong. **An hour later** you find the actual problem: a data-skew issue in the join key that the logs hinted at on line 2,847.

### The after workflow
You paste the failing query, the EXPLAIN plan, and the relevant log section into your AI assistant. You ask: *"Here is a Spark job that is failing with this stack trace. Here is the query plan. What are the most likely root causes ranked by probability?"* You get back three or four ranked hypotheses with the reasoning for each. You test them in parallel instead of sequentially. The actual answer is usually in the top two.

```
   BEFORE (sequential hypothesis test)          AFTER (parallel AI-ranked)
   ───────────────────────────────────          ────────────────────────
   test memory hypothesis → fail (15 min)       paste logs + EXPLAIN
   test timeout hypothesis → fail (15 min)      AI returns 3 ranked hypotheses
   ...                                          (largest gain: parallel testing)
   finally find data skew (30 min)              answer lands in top 2 (20 min)
   ───────────────────────────────────         ────────────────────────
   TOTAL: 60 min                                TOTAL: 20 min
```

**The reason this works:** debugging is pattern matching. AI has seen a million Spark stack traces. You have seen maybe a thousand. It is going to recognize the pattern faster than you will, especially at 3 a.m. when your brain is half asleep.

**Productivity gain: 2–4× on log-heavy debugging.** A debug session that used to take an hour takes 15–25 minutes. The gain is largest for unfamiliar systems (you just inherited a pipeline you did not write) and smallest for systems you know cold.

**Where AI falls down hard: cross-system debugging.** If the issue spans 5 services (Kafka producer, Kafka topic, Flink job, Iceberg table, downstream dbt model) and the smoking gun is in service 3 but the symptom is in service 5, AI cannot follow that thread because no single context contains the whole picture. That is still on you and the team.

---

## Documentation — Before vs After

This is the part of the job where AI has the **highest ROI**, because the honest before workflow is: **nobody does it.**

### The before workflow
You ship the pipeline. You promise yourself you will document it next sprint. Next sprint you ship another pipeline. Six months later someone asks *"what does this transformation do?"* and you have to read your own code to remember. Your data catalog has a tiny fraction of column-level documentation coverage, and on every team I have worked with that has been accepted as normal.

### The after workflow
AI reads the code. AI generates the docstring, the column descriptions, the model-level documentation, the lineage notes. You spend **three minutes reviewing** what would have taken **thirty minutes to write**. The 85% it generates is correct. The 15% that needs business context (why this column exists, what edge case this transformation handles, who depends on this) you fill in yourself in another five minutes.

For dbt projects specifically, this is transformative. Generating `schema.yml` files by hand is the kind of work nobody enjoys and everyone postpones. AI generates the entire file from the model SQL. You review, refine the tests, ship. **Documentation coverage on the dbt projects I have rebuilt this way went from roughly 15% to north of 85%** in the same time it used to take to document one model manually.

**Productivity gain: roughly 10× on documentation**, which is why I call out the ROI separately. The real win is not the time per document. **The real win is that documentation actually gets written at all.** The asymmetry between *"85% coverage that is mostly correct"* and *"5% coverage that is perfect"* is not even close, because future-you needs the 85%.

> **How a 12-person data team I advised uses this:** [link in source article]

**The thing that surprised me:** the act of asking AI to document the code often **surfaced bugs**. The model would describe what the code *"did"* and I would notice that description did not match what the code was *supposed to* do. Documentation as a debugging tool, indirectly.

---

## Data Modeling — Before vs After

Modeling is the most interesting case because AI is great at the standard patterns and bad at the parts that actually matter.

### The before workflow
You sit with a stakeholder. You whiteboard the entities. You sketch a star schema. You debate grain. You ask about historical changes. You go back to your desk and write the DDL. You iterate with the team. **Maybe two or three days** from *"we need a new mart"* to *"first version of the model is ready for review."*

### The after workflow
You describe the requirements to AI: *"We have orders, order items, customers, products. We need a fact table at order-line grain, dimensions for customers (Type 2 SCD on address), products, and dates. Use Kimball conventions, Snowflake dialect, surrogate keys, late-arriving fact handling."* You get a complete schema in under five minutes: DDL for the fact, all dimensions, the surrogate-key generation, the late-arriving record handling, the slowly-changing-dimension implementation. You review it. You correct the business logic. You ship.

**Productivity gain: ~80% reduction on standard dimensional models.** Going from 2 days to half a day on the mechanical part of modeling. But this number lies a little. The mechanical part was never the hard part.

### Where AI cannot help with modeling
The decisions that actually matter in a data model are not the mechanical ones:

- **Grain.** Does each row represent an order, an order line, a shipment line, or a fulfillment event? AI will guess wrong unless you specify. And if you do not understand grain well enough to specify it, AI cannot teach you.
- **SCD strategy.** Type 1, Type 2, Type 6, hybrid? Depends on whether the business needs historical reporting on this attribute. AI does not know your business.
- **Late-arriving facts.** AI defaults to "drop or reject." Your business may need "accept and reprocess." That decision needs context AI does not have.
- **Conformed dimensions.** AI does not know that your `customer_id` in the orders system is actually `cust_id_v2` in marketing and `account_number` in finance. That mapping is org knowledge.

I use AI for the first draft of any data model. It handles standard dimensional patterns perfectly. But I still validate business logic, choose the SCD strategy, and decide on grain. **AI proposes, you decide.**

> **The opinionated default I have settled on:** AI draws the schema, **I draw the boundaries**. The schema is a structural decision (which tables, which keys, which types). The boundaries are a business decision (what is a "customer," what counts as "active," which version of a product is canonical). Those still take a real conversation with a real human.

---

## What AI Cannot Do Yet

After two years of using these tools daily, the line between "AI helps here" and "AI cannot help here" is sharp and important to internalize. Roughly four categories sit firmly in the second bucket.

1. **Deep business context.** AI does not know that your `status = 3` means cancelled. It does not know that the finance team rebuilt revenue-recognition logic last quarter. It does not know that the marketing attribution model uses a 7-day window for organic and 28 days for paid. Every time it lacks this context, the output is plausible and wrong, which is the worst combination.

2. **Architectural decisions tied to org structure.** *"Should this data live in the analytics team's warehouse or the ML team's feature store?"* is not a technical question. It is a question about who owns what, who is on-call for what, and who pays for what. AI has no insight into any of that.

3. **Cross-system integration debugging.** When the bug is in service 3 but the symptom shows up in service 5 and the connecting thread is buried in a Kafka topic's retention policy from 8 months ago, the only thing that can solve it is a human who has been around long enough to know that history.

4. **Politics and consensus.** *"We need to deprecate this dataset"* is a 6-month conversation involving 15 stakeholders. AI cannot run that meeting. (Mercifully, neither do I want it to.)

**The pattern across all four:** AI is excellent at things that are *local* and *structural*. It is bad at things that are *distributed in time, across teams, or in private knowledge.*

---

## A Day in the AI-Assisted DE Workflow

To make this concrete, here is roughly what a productive day looks like for me now versus two years ago, for the same set of tasks.

| Task | Before (pure manual) | After (AI-assisted) | Time saved |
|---|---:|---:|---:|
| Triage morning pipeline alerts | 45 min | 15 min | 30 min |
| Write a new analytics SQL query | 30 min | 10 min | 20 min |
| Build a new ingestion pipeline | 2.5 days | 6–8 hours | 1.5 days |
| Debug a failed Spark job | 1 hour | 20 min | 40 min |
| Document a dbt model | 30 min (or skipped) | 5 min | 25 min |
| First draft of a dimensional model | 2 days | 4 hours | 1.5 days |

Over a typical week, this is somewhere between **8 and 12 hours of reclaimed time**, which is the number I quote when people ask. I do not spend that time on more tickets. I spend it on the parts of the job that actually need a senior engineer's attention: reviewing other people's modeling decisions, talking to stakeholders, thinking about platform-level problems, and yes, writing things like this article.

### The 60/40 rule

For any AI-assisted task, I aim to spend roughly **60% of the time on generation** (prompting, getting drafts, iterating) **and 40% on verification** (reading the output, testing edge cases, running sample data). Engineers who flip that ratio to **90/10 ship bugs**. Engineers who flip it to **20/80 may as well have written the code themselves**.

```
       20/80                60/40                 90/10
   (slow + safe)       (sweet spot)         (fast + bugs)
       ┌──┐                 ┌──┐                  ┌──┐
   AI   │██│                 │████│                │██████████│  AI
       │████│                │████│                │██│
   You │██████│              │████│                │  │  You
       └─────               └─────                └─────
   "may as well code       PRODUCTION           "ship the silent
    it yourself"           default              bugs"
```

---

## In an Interview

When this comes up, the framing matters more than the specifics.

**Junior and mid-level:** Demonstrate that you use AI tools productively and that you verify the output. *"I use Cursor to draft queries, then I verify with EXPLAIN plans and sample data"* is a far better answer than *"I'm interested in learning AI tools"* or worse, *"I don't trust AI for code."* Both extremes signal immaturity.

**Senior:** Show that you know where AI fails. Be specific. *"I use AI for boilerplate and first drafts, but I always verify join logic, NULL handling, and performance manually. The last time I caught a silent fan-out bug from AI output, it would have inflated reported revenue by 15%."* **A concrete failure story is the most senior-sounding answer you can give.**

**Staff and above:** Talk about workflow design and team-level adoption. Where in your pipeline-development lifecycle does AI live? What are the verification habits you have built into PR templates? How do you onboard new engineers to use these tools responsibly? The conversation is no longer about whether AI helps. It is about how to make AI help reliably across a team of 15 engineers without anyone shipping the silent bugs.

### The answer that lands

> *"AI didn't change what I work on. It changed what I spend my time on within each task. I spend less time on boilerplate and first drafts, more time on verification and the decisions that actually need a human. The productivity gain is real, around 30–40% on my measurable output, but the bigger shift is that I now ship documentation, write more tests, and catch more bugs in review because the AI handles the parts of those tasks that used to make them feel expensive."*

---

## Key Takeaway

> AI does not replace data engineering skill. It accelerates the parts of the job that were **never** the interesting part (boilerplate, first drafts, log parsing, documentation) and leaves the parts that matter (modeling decisions, business context, cross-system judgment) exactly where they were. The data engineers who get the most from AI are the ones who already write good SQL, build clean pipelines, and verify their output. AI makes strong engineers measurably faster. **It makes weak engineers measurably more dangerous.** Build the fundamentals first, then add the leverage.

---

## What Comes Next

> You know what changes when AI enters the daily workflow. The next article walks through **how to actually set up your environment** so AI tools generate useful output instead of generic garbage: IDE configuration, schema context files, project conventions, and the specific habits that turn *"I tried Copilot and it was meh"* into *"AI doubled my output."*

---

*Written by **Gorijala Kiran** · Source: [datavidhya.com](https://datavidhya.com/learn/ai-for-data-engineering/)*
