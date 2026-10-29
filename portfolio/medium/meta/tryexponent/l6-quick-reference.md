# Meta L6 Data Engineer — Quick-Reference Interview Playbook

> One-page map of the Meta DE L6 interview loop + L6 leveling cues, story-to-round index, and last-minute checklist. Use this alongside `behavioral-stories.md` (the 8 STAR stories) and `meta-data-engineer-interview-guide.md` (the round-by-round format guide).

---

## 1. The L6 Data Engineer Loop at Meta

A typical Meta DE L6 loop runs ~5 hours over 1–2 days. Standard rounds:

| # | Round | Format | Duration | Who runs it | What they're scoring |
|---|---|---|---|---|---|
| 1 | **Coding** | SQL + Python (sometimes Spark/Scala), live in shared editor | 45–60 min | DE hiring manager or senior DE | Data manipulation fluency, query optimization, code quality |
| 2 | **Data System Design** | Whiteboard / doc: design a data pipeline, warehouse, or analytics platform | 45–60 min | Senior DE / EM | System design for data: ingestion → transform → serve, scale, reliability, trade-offs |
| 3 | **Coding (harder)** | SQL window functions + Python data structures, often a real dataset | 45–60 min | Another DE | Depth, edge cases, clarity under pressure |
| 4 | **Behavioral (Ownership)** | 4–5 STAR questions, ~30 min total | 30 min | DE manager or EM | Leadership signals at L6: scope, autonomy, cross-functional impact, reflection |
| 5 | **Bar Raiser** | Behavioral + general engineering judgment | 45 min | Bar-raiser (outside the team) | Calibrates you against Meta's *level expectations*, not the team's needs |

> The bar-raiser round is the one that decides if you go up or down a level. More on this below.

---

## 2. The L6 Bar — What Meta Expects at L6

L6 at Meta = **Senior Engineer / Tech Lead** (industry-equivalent: Senior, Staff-track IC, or Tech Lead). Compared to L5 (SWE) and L7 (Staff):

| Signal | L5 (SWE) | **L6 (Senior / Tech Lead)** | L7 (Staff) |
|---|---|---|---|
| **Scope** | Single project, one team | **Cross-team project, multiple stakeholders** | Org-wide or multi-org |
| **Autonomy** | Given clear specs, executes | **Defines the spec, drives alignment, then executes** | Sets direction with little guidance |
| **Cross-functional** | Works within team | **Drives alignment across PM, Eng, Ops, Data Science** | Influences cross-org |
| **Technical depth** | Solid, can own a system | **Strong; makes hard trade-offs and defends them** | Org-recognized expert |
| **Mentorship** | Helps juniors informally | **Formal mentor; raises the team's bar** | Multi-team mentor; writes org-wide standards |
| **Failure mode to avoid** | "I executed what I was told" | "I solved a single team's problem" | "I went heads-down and didn't scale my impact" |

### The 3 L6 ownership signals the bar-raiser is listening for

1. **You defined the problem, not just solved it.** Your stories should show you noticing a problem, framing the trade-off, and getting alignment — not just being handed a ticket.
2. **You moved multiple stakeholders.** L6 stories almost always involve 2+ groups (PM, Eng, Ops, Data Science, Finance, etc.). One-team stories read as L5.
3. **You made a hard call before you had full buy-in.** L6 = RFC + soft buy-in, not unanimous agreement. L7 = writing the standard. L5 = waiting for direction.

> If your story has all three, it's L6. If it has only one, it's L5 even if the technical content is great.

---

## 3. Story-to-Round Index (the 8 STAR stories, mapped)

| Story | Use for round | Why it works at L6 |
|---|---|---|
| **Story 1** — Data-quality reconciliation (leadership) | Ownership Q: "Tell me about a time you led a project" | Shows scoped ownership, quantified impact, reflection. Use as a **safer fallback** if Story 6 feels too big for the question. |
| **Story 2** — Airflow vs homegrown orchestrator (disagreement) | Ownership Q: "Tell me about a disagreement" | Cost-vs-build trade-off, no hard deadline. Use when the interviewer wants a *philosophical* disagreement, not a deadline-driven one. |
| **Story 3** — Pipeline SLA fix (process win) | Ownership Q: "Tell me about a process you improved" | Single-pipeline diagnostic story. Use as a **safer fallback** for a focused improvement question. |
| **Story 4** — dbt + Snowflake from scratch (ramp-up) | Ownership Q: "Tell me about learning agility" | Classic ramp-up story. Safe, clean, but reads as L5 if not framed up. |
| **Story 5** — Go + Databricks rewrite (new tool) | Ownership Q: "Tell me about learning a new tool" | **Strong L6 signal** — picked up a new language, delivered cost + latency wins, built an API other teams adopted. |
| **Story 6** — **Lazada unified data platform** | **Best Ownership Q: "Tell me about a time you led end-to-end"** | **The L6 showpiece.** Platform-lead, 10+ engineers, 4 stakeholders, hard governance trade-off, phased rollout. Use this for "what's the project you're most proud of." |
| **Story 7** — **Redshift → Snowflake (pushed phased)** | **Best Ownership Q: "Tell me about a disagreement"** | **The L6 disagreement story.** Hard deadline, hard cap, skip-level in the room, zero downtime. The "did you go over her head?" talking point is gold. |
| **Story 8** — **Reusable ingestion framework (8 teams)** | **Best Ownership Q: "Tell me about a process you improved"** | **The L6 impact story.** Cross-team framework, dogfooded first, 8 teams adopted, schema-drift auto-caught. The "framework without observability" lesson is memorable. |

### Round-by-round story picks (recommended)

- **Q: "Tell me about a time you led a project end-to-end"** → Story 6 (Lazada). Fallback: Story 1.
- **Q: "Tell me about a time you disagreed with your manager"** → Story 7 (Redshift → Snowflake). Fallback: Story 2.
- **Q: "Tell me about a process you improved"** → Story 8 (ingestion framework). Fallback: Story 3.
- **Q: "Tell me about a time you learned something new quickly"** → Story 5 (Go + Databricks). Fallback: Story 4.
- **Q: "What's the project you're most proud of?"** → Story 6. Then *bridge* to Story 8 if they want a second one.
- **Q: "Tell me about a time you dealt with ambiguity"** → Story 6 (the schema contract RFC phase) or Story 7 (the cutover design).

> If you have time for only 3 stories, rehearse **6, 7, 8** in that order. They are your L6 showpieces.

---

## 4. How to Land Each Story at L6 (not L5)

After each story, ask yourself: does it show all 3 L6 ownership signals?

| L6 signal | Story 6 | Story 7 | Story 8 | Story 5 |
|---|---|---|---|---|
| 1. Defined the problem | ✅ (saw fragmentation, wrote RFC) | ✅ (saw blast radius, designed strangler-fig) | ✅ (saw repeating pain, built abstraction) | ✅ (saw cost + ownership gap) |
| 2. Moved multiple stakeholders | ✅ (marketing, ops, finance, data science) | ✅ (manager + skip-level, with both in room) | ✅ (8 teams adopted) | ✅ (3 teams adopted the API) |
| 3. Made the hard call before full buy-in | ✅ (schema contracts RFC) | ✅ (phased over big-bang) | ✅ (frame the right abstraction) | ✅ (rewrite in a new language) |

If a follow-up threatens to drop you to L5 ("why did you do that?" → "because my manager told me to"), **redirect to the trade-off you framed, not the directive you received.** That's the L6 move.

---

## 5. L6 Coding Round — What to Drill

| Topic | Time to spend | What "good" looks like at L6 |
|---|---|---|
| **SQL window functions** | 3–4 hrs | RANK, DENSE_RANK, ROW_NUMBER, LAG/LEAD, NTILE, running totals, sessionization — write them cold |
| **SQL optimization** (EXPLAIN, indexes, joins) | 2–3 hrs | Read a query plan; pick the right join (broadcast vs shuffle); know when a CTE helps vs hurts |
| **SQL: dedup, funnel, retention** | 2 hrs | Classic DE interview patterns — practice 5 of each |
| **Python: data structures** | 2 hrs | Dicts, sets, heaps, generators — for streaming/aggregation problems |
| **Python: pandas / PySpark** | 2 hrs | GroupBy, window, join optimization, UDF vs built-in |
| **One real dataset problem** (LC or Strata scratch) | 2 hrs | End-to-end: read CSV, clean, join, aggregate, output |

> L6 coding is *not* leetcode-hard. It's **fluent SQL + clean Python under time pressure**. If you can write a 5-table window-function query in 15 minutes without Googling syntax, you're in good shape.

**Top 5 patterns to drill cold:**
1. Top-N per group (window function + filter)
2. Sessionization (gap detection with LAG)
3. Funnel (conditional aggregation over ordered events)
4. Retention (self-join or window on cohort)
5. Slowly-changing-dim merge (full outer + COALESCE)

---

## 6. L6 Data System Design — What to Drill

A typical prompt: *"Design a data pipeline for X. Walk me through ingestion, transformation, serving, and how you'd handle scale and reliability."*

L6 expects: end-to-end design, named trade-offs, **scale numbers**, failure modes, and a clear *opinion* on the architecture (not a "depends on the use case" punt).

### Framework to use (memorize this)

```
1. Clarify the use case (latency? volume? consumers?) — 3 min
2. Sketch the high-level architecture:
     sources → ingestion → storage (raw) → transform → serving → consumers
3. Name the trade-offs (batch vs stream, push vs pull, pushdown vs ELT)
4. Quantify scale (rows/day, GB/day, queries/sec, freshness SLA)
5. Reliability: retries, idempotency, schema drift, backfills, data quality
6. Cost: where does the money go? how would you cut it 50%?
7. Wrap with: "what I'd watch in the first 30 days" — shows L6 ownership
```

### Top 5 system design prompts to practice

1. **"Design a real-time campaign analytics platform"** — use your Lazada Story 6 work as the spine.
2. **"Design a data warehouse for a marketplace (orders, inventory, sellers)"** — Meta-relevant.
3. **"Design a CDC pipeline from OLTP to a warehouse"** — Debezium → Kafka → consumer.
4. **"Design a metrics platform for a product team"** — events → pipeline → aggregation → dashboard.
5. **"Design an experimentation data pipeline"** — Meta's bread and butter.

---

## 7. Bar-Raiser Playbook

The bar-raiser is a Meta engineer **outside the team**, calibrated on Meta's leveling rubric. They have one job: *make sure Meta doesn't hire below the bar.* They can uplevel you (rare) or downlevel you (common).

### What they listen for

- **L6 ownership signals** (the 3 in §2)
- **Reflection and growth** — every story needs a real "what I'd change"
- **Engineering judgment** — they ask *why*, not *what*. "Why this and not that?"
- **Meta values alignment** — Move Fast, Be Bold, Focus on Long-Term Impact, Be Open, Build Social Value

### Common bar-raiser questions

- "Tell me about a time you **influenced without authority**." → Story 6 or 8.
- "Tell me about a time you **failed**." → Have one ready (NOT in the 8 STAR stories — be honest, brief, and end with what you learned).
- "Tell me about a time you **disagreed with data**." → Story 7.
- "Tell me about the **most complex system** you've designed end-to-end." → Story 6.
- "Tell me about a time you **raised the bar** for the team." → Story 8.
- "Tell me about a time you **had to learn something quickly**." → Story 5.
- "What would your **last manager** say you should improve?" → Have one ready. Make it real, not humble-brag.

### 3 things that *fail* a bar-raiser round

1. **Heroes vs villains** — never badmouth a manager, even a bad one.
2. **No reflection** — every story ends with "what I'd change." If yours doesn't, it's L5 at best.
3. **"We did X" without "I did Y"** — vague team credit is a strong L5 signal.

---

## 8. L6 Pricing / Leveling — How to Position Yourself

This is the part most candidates skip, and it's where L6 packages differ from L5 by **$80K–$150K/year** in base+RSU.

### L6 Data Engineer base/TC bands (US, approximate, public ranges)

| Level | Base | RSU/yr | Total Comp |
|---|---|---|---|
| **L5 (SWE)** | $170–200K | $80–150K | **$250–350K** |
| **L6 (Senior / Tech Lead)** | $200–240K | $200–400K | **$400–640K** |
| **L7 (Staff)** | $240–290K | $400–800K | **$640K–1.1M** |

> These are approximate and move with market + location + stock price. Use Levels.fyi for live data. They are **level signals**, not guarantees.

### How to land at L6, not L5

| Signal | L5 risk | L6 fix |
|---|---|---|
| Scope | "I owned this pipeline" | "I led a cross-team platform with 10+ engineers and 4 stakeholder groups" |
| Decision | "My manager and I decided…" | "I made the call, got alignment through an RFC, and the team adopted it" |
| Impact | "We delivered on time" | "Latency dropped 24h → 60s, 5 stacks consolidated, 10+ engineers migrated in 4 months" |
| Reflection | "It went well" | "What I'd change: stand up the schema registry in shadow mode during design, not as Phase 1" |

### Negotiation prep

- Have **3 comparable offers** before the level is decided if possible.
- **Get the level written in the verbal offer** before negotiating base/RSU.
- L6 vs L5 changes the *job*, not just the comp — make sure you actually want the scope.
- For TC negotiations, ask: "What's the RSU refresh policy at this level?" (Meta refreshes annually, so the L6 grant is more than the L5 grant *over 4 years*.)

---

## 9. The Day-Before Checklist

- [ ] Rehearse **Stories 6, 7, 8** aloud, timed, under 4:30 each.
- [ ] Have **one failure story** ready (separate from the 8 STAR). 1–2 min, real, ends with what you learned.
- [ ] Drill **5 SQL patterns** (§5) cold, on a shared doc.
- [ ] Sketch **3 system design prompts** (§6) on paper — full architecture, scale numbers, failure modes.
- [ ] Read the **team's recent work** (blog posts, papers, public talks). Have 1 question per interviewer.
- [ ] **Sleep.** The bar-raiser round is the one where being tired loses you the level.
- [ ] Bring water, a notebook, a pen, your laptop charger, and a smile.

---

## 10. The 5-Minute Self-Pitch (have this ready)

When they ask "Tell me about yourself" (every round opens with this), here's the structure:

```
- 30s: who I am (1 line: "Senior data engineer, X years, focused on data platforms")
- 60s: my strongest story (Story 6 — Lazada platform) — situation + result only
- 30s: what I'm looking for next (1 line: "I want to scale this kind of platform work at Meta's scale")
```

**Do NOT recap your resume.** They have it. Tell them what they can't read.

---

*Last updated alongside `behavioral-stories.md`. Rehearse stories 6, 7, 8, then this playbook, then sleep.*
