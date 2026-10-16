# Lesson 2: Executive Communication

> **Week 1 · Day 2 · 90 min**
> **Deliverable:** A 3-minute CEO-level pitch of a complex technology topic.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The most common failure mode in CDO interviews is **jargon dump**: explaining technology in the language of technology. The CEO does not need to know you used Kafka + Flink + Delta Lake. The CEO needs to know what changed for the business.

The conversion is:

| Technology says | Executive says |
|---|---|
| "We used Kafka + Flink + Delta Lake on Databricks." | "We built a real-time data platform that powers every customer-facing decision in under 200 milliseconds." |
| "We had 4 P1 incidents per month." | "Our most important business reporting was wrong 4 times a month." |
| "We cut cloud spend 40%." | "We saved the business $X million a year on infrastructure." |
| "We built an ML feature store." | "We gave our data scientists the ability to ship models in weeks, not quarters." |

The structure for any executive answer is **Problem → Decision → Action → Impact**:

- **Problem** — the business problem, framed in dollars or risk.
- **Decision** — the strategic choice, with the alternative that was rejected.
- **Action** — what you did, framed as a sequence of moves.
- **Impact** — the measurable outcome, with the number.

This is the same shape as a STAR story, but the language is different: STAR is for behavioral questions ("tell me about a time..."), PDCA is for technical or strategic questions ("how would you..." or "explain...").

## 🛠️ Build It

**Spec:** Take one technical topic from your work and convert it into a 3-minute CEO-level pitch.

**Acceptance:**
- 3 minutes (175-190 seconds), no overrun.
- 0 acronyms in the opening 30 seconds.
- The Problem is framed in dollars or risk.
- The Decision names the alternative that was rejected.
- The Action has 3-5 distinct moves.
- The Impact is a number you can substantiate.

**Starter:** Pick from your strongest stories:
- Story 1 (Unified Data Platform transformation, Makro)
- Story 3 (Multi-cloud migration)
- Story 7 (Cloud and Databricks cost optimization)
- Story 9 (GenAI / RAG document intelligence)

**Solution (3min, Story 1):**
> *"Three years ago we had a problem you can probably relate to. The board asked for month-end close on day five of the new month. Finance was still re-keying numbers. The retail business couldn't make decisions until week two. We had five business units, three cloud regions, twelve source systems, and four different ways to ingest data. Every report answered a different question, and nobody trusted any of them.*
>
> *I made two decisions. First, we were not going to refactor everything. That would have taken three years and we'd have lost the room. We were going to replatform in waves — start with the highest-value business unit, get a win, and use that to fund the next wave. Second, we were not going to build a data lake. We'd been burned by a data lake before. We built a lakehouse — Delta Lake on Databricks — so we could run our existing BI workloads while we migrated the new workloads in parallel.*
>
> *Three things made the difference. Data contracts with the top five source systems — that's what stopped the reconciliation wars. A single semantic layer with one definition per metric — that's what stopped the board asking which number was right. And a FinOps practice that cut our cloud and Databricks bill forty percent — that's what paid for the migration.*
>
> *The result: month-end close went from five days to two hours. P1 incidents went from four a month to one or two. Five business units now report from the same source. And we did it in `[CONFIRM: N months]` instead of three years, and we did it for less money than the legacy platform was costing us."*

## 🏛️ Architect Notes

- **Trade-off:** Tell the technology story vs. the business story. Tell the business story. The technology is on the resume.
- **Capacity / cost:** A 3-minute pitch is 450-500 words. The opening 30 seconds carries the most weight — that's when the listener decides whether to lean in.
- **When NOT to use:** Don't use this for a CTO or principal engineer interview. They want the technology story. Save the executive version for the CEO, the board, the CFO, and the recruiter screen.
- **Production checklist:**
  - [ ] First sentence names the business problem
  - [ ] The Decision names the rejected alternative
  - [ ] The Action has 3-5 moves
  - [ ] The Impact is one number, not a list
  - [ ] Zero acronyms in opening 30 seconds
  - [ ] Total time under 3:10

## 🌙 Reflect

- Which move in the Action is the one that mattered most? Could you remove the others?
- If the CEO interrupted at 30 seconds, what would you cut?
- Write the one sentence that replaces the rejected alternative.

---

**Next:** Day 3 — Leadership Storytelling (STAR).
