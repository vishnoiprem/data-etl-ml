# Practice Guide — AI Engineer Mastery (Tech Developer / Architect Track)

> **The hands-on lab manual for the AI Engineer Mastery course.**
> Every lesson in [`outlines/ai-engineer-mastery.md`](./outlines/ai-engineer-mastery.md) has a corresponding practice lab here. Every project in [`180-day-ai/`](./180-day-ai/) has starter code. Every capstone has a runnable starter. Every codebook snippet has a paired exercise.

---

## Why this guide exists

Reading a course outline doesn't make you an AI engineer. **Building does.**

This folder is the bridge between "I watched the video" and "I shipped a system to production." Every file in `course/practice/`, `course/capstone-starters/`, and `course/workbooks/exercises/` is a structured, hands-on lab — not a video transcript.

---

## How the practice is organized

### Three pillars of practice

| Pillar | Location | What it is | Time per item |
|---|---|---|---|
| **Per-lesson labs** | [`practice/`](./practice/) | One lab per lesson in the Mastery outline. Spec + starter + solution + architect notes. | 30-90 min |
| **180-day projects** | [`180-day-ai/`](./180-day-ai/) | 30 projects × 6 months. Each project is a complete working system. | 30-90 min/day |
| **Capstone starters** | [`capstone-starters/`](./capstone-starters/) | Runnable starter code for each of the 5 capstone templates. | Multi-day |
| **Codebook exercises** | [`workbooks/exercises/`](./workbooks/exercises/) | Challenges that turn the codebook reference into active practice. | 15-45 min |

### Pick your architect level

Every lab is annotated with a 4-level depth grid. Pick your level, complete that checklist, move on.

| Level | Years | What you focus on | Time per lab |
|---|---|---|---|
| 🟢 **Junior** | 1-2 | Implement and run. Get something working end-to-end. | 30-45 min |
| 🟡 **Mid** | 3-5 | Extend with observability, retries, basic error handling. | 45-60 min |
| 🟠 **Senior** | 6-10 | Add multi-tenancy, cost guardrails, SLO design. | 60-90 min |
| 🔴 **Staff** | 10+ | Design ADRs, capacity model at 100× scale, on-call runbook. | 90+ min |

The Markdown spec is the same for all levels. The **architect notes** at the bottom of each lab contain all four levels' content — you self-select.

---

## Learning paths (pick one)

### Path A: "I learn by reading then doing" (8-12 weeks)
1. Read a lesson in [`outlines/ai-engineer-mastery.md`](./outlines/ai-engineer-mastery.md)
2. Watch the video (if available)
3. Open the matching lab in [`practice/`](./practice/) — same lesson number
4. Read the **🧠 Concept** section
5. Code the **🛠️ Build It** section in the matching `.py` or `.ipynb` file
6. Read the **🏛️ Architect Notes** for your level
7. Answer the **🌙 Reflect** questions

### Path B: "I learn by shipping every day" (6 months)
1. Start with [`180-day-ai/`](./180-day-ai/) on **Day 1**
2. Each day: 30-90 min hands-on project with full starter code
3. End of each month: build the month project
4. Day 180: ship your own AI SaaS
5. Cross-reference the matching lab in `practice/` when you want deeper architect notes

### Path C: "I want to ship one product" (8 weeks)
1. Read [`projects/ai-engineer-capstone-guide.md`](./projects/ai-engineer-capstone-guide.md)
2. Pick one of 5 templates
3. Use the matching starter in [`capstone-starters/`](./capstone-starters/) — it's a runnable skeleton
4. Use the **labs in `practice/`** as you implement each technique (RAG, agents, deployment, etc.)
5. Use the **exercises in `workbooks/exercises/`** to fill specific skill gaps
6. Launch in 8 weeks

### Path D: "I have specific skill gaps" (ad-hoc)
- Browse [`workbooks/exercises/`](./workbooks/exercises/) — each exercise says which codebook section it pairs with
- Jump to the relevant section in [`workbooks/ai-engineer-codebook.md`](./workbooks/ai-engineer-codebook.md)
- Do the exercises in order
- Cross-check the relevant lab in `practice/` for architect context

---

## Practice content index

### [`practice/`](./practice/) — Per-lesson labs (one per Mastery lesson)

| Level | Lessons | Folder |
|---|---|---|
| Level 1: Foundations | 1.1 → 1.6 | [`practice/level-1-foundations/`](./practice/level-1-foundations/) |
| Level 2: Prompt Engineering | 2.1 → 2.10 | [`practice/level-2-prompt-engineering/`](./practice/level-2-prompt-engineering/) |
| Level 3: Building with APIs | 3.1 → 3.14 | [`practice/level-3-building-with-apis/`](./practice/level-3-building-with-apis/) |
| Level 4: RAG | 4.1 → 4.14 | [`practice/level-4-rag/`](./practice/level-4-rag/) |
| Level 5: Agents | 5.1 → 5.12 | [`practice/level-5-agents/`](./practice/level-5-agents/) |
| Level 6: Production | 6.1 → 6.16 | [`practice/level-6-production/`](./practice/level-6-production/) |
| Capstone | C.1 → C.8 | [`practice/capstone/`](./practice/capstone/) |

Each lab has **3 files**: `lesson-X-Y-topic.md` (spec), `lesson-X-Y-topic.py` (runnable code), `lesson-X-Y-topic.ipynb` (notebook).

### [`180-day-ai/`](./180-day-ai/) — 180 hands-on projects

| Month | Theme | File |
|---|---|---|
| Month 1 | AI + PostgreSQL | [`month-1-projects.md`](./180-day-ai/month-1-projects.md) |
| Month 2 | AI + REST APIs | [`month-2-projects.md`](./180-day-ai/month-2-projects.md) |
| Month 3 | AI + Documents & Search | [`month-3-projects.md`](./180-day-ai/month-3-projects.md) |
| Month 4 | AI + Files & Media | [`month-4-projects.md`](./180-day-ai/month-4-projects.md) |
| Month 5 | AI + Real-Time Streams | [`month-5-projects.md`](./180-day-ai/month-5-projects.md) |
| Month 6 | AI + Vector Search at Scale | [`month-6-projects.md`](./180-day-ai/month-6-projects.md) |

### [`capstone-starters/`](./capstone-starters/) — 5 runnable products

| # | Product | Stack | Folder |
|---|---|---|---|
| 1 | AI Document Q&A | RAG + Pinecone + FastAPI + Stripe | [`01-ai-doc-qa/`](./capstone-starters/01-ai-doc-qa/) |
| 2 | AI Research Assistant | ReAct + Tavily + LangGraph | [`02-ai-research-assistant/`](./capstone-starters/02-ai-research-assistant/) |
| 3 | AI Sales Coach | Whisper + GPT-4o + function calling | [`03-ai-sales-coach/`](./capstone-starters/03-ai-sales-coach/) |
| 4 | AI Data Analyst | Code interpreter + Pandas + Plotly | [`04-ai-data-analyst/`](./capstone-starters/04-ai-data-analyst/) |
| 5 | AI Content Generator | GPT-4o + Tavily + RAG | [`05-ai-content-generator/`](./capstone-starters/05-ai-content-generator/) |

### [`workbooks/exercises/`](./workbooks/exercises/) — Codebook practice challenges

Paired 1:1 with the 10 sections in [`ai-engineer-codebook.md`](./workbooks/ai-engineer-codebook.md). Each section has 3-5 challenges that force you to modify, extend, and break the reference snippets.

---

## What "architect-grade" means here

Every lab includes — at the bottom, in **🏛️ Architect Notes** — five things a normal tutorial skips:

1. **Trade-off tables** — 3 options, pros/cons for each, when to pick which
2. **Capacity model** — RPS, p99 latency, storage at 1K / 10K / 100K users
3. **Cost model** — $/1K requests broken down by LLM, embedding, storage, compute
4. **Anti-patterns** — what goes wrong at scale, when NOT to use this pattern
5. **Production checklist** — what "done" looks like before you ship

This is the content that turns a working tutorial into a deployable system.

---

## How long does this take?

| Path | Time to ship | Time to "AI engineer ready" |
|---|---|---|
| Path A: Per-lesson labs (all 70+) | 8-12 weeks @ 1hr/day | 3 months |
| Path B: 180-day projects | 6 months @ 1hr/day | 6 months + 180 portfolio items |
| Path C: One capstone product | 8 weeks | 2 months + 1 shipped product |
| Path D: Skill-gap fill (per exercise) | varies | 1-2 weeks per gap |

You can mix paths. Most learners do **Path A + Path C in parallel**: do the per-lesson labs in order, but build their capstone alongside using the matching starter.

---

## Verification & quality bar

Every file in this practice track follows the standard lab template (see the bottom of this file). If you find a lab that doesn't, it's a bug — open an issue.

**Quality bar:**
- All Python code is runnable as-is (with a virtual env + API keys)
- All Notebooks open in Jupyter without errors
- All Markdown renders cleanly in GitHub preview
- All trade-off tables, capacity models, and cost models include numbers, not handwaving

---

## Lab standard template (used by every file)

```markdown
# Lesson X.Y: <Title>

## 🎯 Architect Level
- [ ] Junior  (1-2 yrs)
- [ ] Mid     (3-5 yrs)
- [ ] Senior  (6-10 yrs)
- [ ] Staff   (10+ yrs)

## 🧠 Concept (5 min)
## 🛠️ Build It (45 min)
### Spec
### Acceptance Criteria
### Starter Code
### Solution
## 🏛️ Architect Notes
### Trade-offs
### Capacity Model
### Cost Model
### When NOT to use this
### Production Checklist
## 🌙 Reflect (10 min)
```

Every lab. Every level. Every format.

---

**Last updated:** 2026-10-09
**Practice tracks:** 4 (per-lesson, 180-day, capstones, codebook)
**Total hands-on items:** 260+ (70+ labs × 3 formats + 180 daily projects + 5 capstones + 10 codebook exercise sets)
**Architect depth levels:** 4 (Junior, Mid, Senior, Staff)
