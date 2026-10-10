# Intro to AI Agents and Agentic AI — 54-lecture FDE synthesis

> **In 2026, the centerpiece round at most AI-native companies is a 60-minute live-build of a guarded multi-agent system with a cost ceiling, a runbook, and an eval set.** This course is the 54-lecture study path that takes the FDE candidate from *"I know LLMs"* to *"I can ship that system on Monday."* Read it once before the interview. Re-read L2-7 (the synthesis) the morning of.

## In 60 seconds

The course covers, in order: **definition** (S1) → **7 ingredients + 5 guardrails** (S2) → **6 agent types** (S3) → **prompting + teaching** (S4) → **5 architecture patterns** (S5) → **10-step implementation guide** (S6) → **8-lecture n8n platform** (S7) → **6-lecture agent infrastructure** (S8) → **3-lecture commercial toolkit** (S9) → **1-lecture trading-workflow application** (S10, growing). Five named taxonomies a candidate must recite: **7 ingredients, 5 guardrails, 3-tier cost ceiling, 4 RAGAS metrics, 4 error categories.** The synthesis lecture of the whole course is **L2-7** — it wraps the 7 ingredients + 5 guardrails in one 200-line shipping agent. If you only read two lectures, read L2-7 and L9-1.

> **This is a 54-lecture FDE-study synthesis of the source course "Intro to AI Agents and Agentic AI" (9 sections, 54 lectures, 2h 11m).** Each lecture is a written study guide: same topic, same scope, same depth as a 1-3 min video, but expanded to ~3K words of transcript-equivalent prose so the FDE candidate can read it as a study document rather than watch a video. **The source-course lecture titles are not in this repository;** the lecture filenames here are descriptive and the content is synthesized from the section-level summaries in `../intro-to-ai-agents.md` plus the Phase 1-5 FDE patterns. **Replace the lecture titles with the source's exact titles when you have them.**

---

## Why this directory exists

The 296-line `../intro-to-ai-agents.md` is a *cross-reference cheat sheet* — it tells the FDE candidate "Section 5 in the source maps to Phase 4 multi-agent dispatcher." It is not the 2h 11m course itself. **This directory is the read-it-as-a-doc expansion of that cheat sheet.** Every section in the source has a subdirectory here; every lecture in the source has a 3K-word file here. Read it as a 2-hour self-paced study guide.

## How the 54 lectures map to the 9 sections

| Section | Lectures | Time | Directory | "If you only read one" |
|---|---|---|---|---|
| 1. Understanding AI agents | 3 | 9 min | `s01-understanding-ai-agents/` | **L1-1** — sets the voice |
| 2. Essential ingredients for building AI agents | 7 | 16 min | `s02-essential-ingredients/` | **L2-7** — the synthesis (200-line shipping agent) |
| 3. Types of AI agents: from simple to complex structures | 8 | 15 min | `s03-types-of-ai-agents/` | **L3-4** — hierarchical + per-agent circuit breaker |
| 4. Guiding and teaching AI agents | 3 | 8 min | `s04-guiding-and-teaching/` | **L4-1** — the 6 prompting patterns |
| 5. AI agent architecture patterns | 6 | 16 min | `s05-architecture-patterns/` | **L5-3** — orchestrator pattern |
| 6. Implementing AI agents in practice | 10 | 24 min | `s06-implementing-agents/` | **L6-5** — the 5 guardrails |
| 7. Practical example — Build an agentic automation with n8n | 8 | 21 min | `s07-n8n-practical/` | **L7-7** — the 6-node complete automation |
| 8. AI agent infrastructure | 6 | 12 min | `s08-agent-infrastructure/` | **L8-4** — observability + 3am dashboard |
| 9. AI agents in business | 3 | 10 min | `s09-ai-agents-in-business/` | **L9-1** — the ROI formula + CFO pitch |
| 10. AI agents for trading workflows | 1 (growing) | 22 min | `s10-ai-in-trading/` | **L10-1** — the 5 workflows + 5 guardrails |
| **Total** | **55** | **153 min** | — | The 10 above = 80/20 of the course |

## Lecture file naming

```
L{section}-{lecture}-{slug}.md
```

Example: `L1-1-what-is-an-agent.md`, `L7-4-n8n-first-workflow.md`. Each file is ~3K words (a 2-3 min read at spoken-pace), structured as:

1. **Title** + 1-line FDE framing
2. **The 3 things you'll learn**
3. **Concept** — the section topic, written in FDE voice
4. **The pattern** — the abstraction, named and bounded
5. **Code or example** — minimal, stdlib-only
6. **Production addendum** — the FDE layer (cost ceiling, eval set, circuit breaker, handoff)
7. **Cross-references** — to the Phase 1-5 modules and the hardcode reference implementations
8. **The 3 questions this lecture preps you for** — interview signal

## What this is not

- **Not a transcript of the source course.** The source-course lecture titles, video timings, and slide content are not in this repository. The content here is *synthesized* from the section-level topic summaries in `../intro-to-ai-agents.md` and the Phase 1-5 patterns. If you have the source lecture list, replace the filenames and titles with the source's exact ones.
- **Not a substitute for hands-on.** Reading 54 lectures does not build the muscle memory. Pair each lecture with the matching code in `course/practice/level-5-agents/` and the matching project in `course/ai-fde/phase-4-capstone/projects/`.
- **Not vendor-specific.** No LangChain / AutoGen / CrewAI / n8n API keys are required. The code is stdlib-only Python; the n8n section is workflow-level description only.

## How to use this directory

1. **Pick a section.** Each section directory has a `README.md` that lists the 3-10 lectures in that section with a 1-line topic each. Read that first.
2. **Read the lecture.** Each `L{x}-{y}-{slug}.md` is a self-contained 3-4K-word study guide. Read it as you would watch the source video.
3. **Run the code.** Every lecture that has a code block also has a corresponding runnable file in `course/practice/level-5-agents/`. Run it. Tweak it. Break it. Read the failure mode.
4. **Cross-reference Phase 1-5.** Each lecture's "Cross-references" section names the Phase 1-5 module that deepens it. Open that module and read the matching lesson.
5. **Practice the interview questions.** The last section of each lecture lists 3 interview questions the lecture preps you for. Answer them out loud before checking the answers in `course/ai-fde/phase-6-interview-prep/`.

## The 5 things this synthesis adds beyond the source course

1. **The FDE voice.** Every lecture is written in the same declarative, property-naming voice the Phase 1-5 modules use. The source is a generic Udemy course; this is a study guide for FDE candidates.
2. **The cross-reference layer.** Every lecture points to the Phase 1-5 module + the practice code + the hardcode reference implementation that deepens it. The source doesn't have this scaffolding.
3. **The production addendum.** Every lecture has a "Production addendum" section naming the FDE guardrail (cost ceiling, circuit breaker, eval set, handoff) the topic touches. The source focuses on the prototype.
4. **The 3 interview questions.** Every lecture ends with 3 questions the FDE candidate should be able to answer out loud. The source has quizzes, not interview signal.
5. **The "next lecture" pointer.** Every lecture ends with a "Read next" pointer to the next lecture in the section. The source has a video player; this has a reading order.

## The thesis

**The 2h 11m source course teaches the agent vocabulary. This 54-lecture synthesis teaches the FDE study path through that vocabulary.** The candidate who reads all 54 lectures + runs all 12 practice code files + completes the 4 Phase 4 projects + answers the 3 questions per lecture out loud will be ready for the centerpiece round at any AI company that uses agents.

**Read the section README first. Then the lecture. Then the code. Then the question. Then the next lecture.** That's the FDE-study path.

---

## Build status

**Complete: 55 / 55 lectures written across 10 sections.** All 10 sections have a `README.md` and the full lecture set:

| Section | Lectures | Status |
|---|---|---|
| 1. Understanding AI agents | 3 (L1-1 to L1-3) | done |
| 2. Essential ingredients | 7 (L2-1 to L2-7) | done |
| 3. Types of AI agents | 8 (L3-1 to L3-8) | done |
| 4. Guiding and teaching | 3 (L4-1 to L4-3) | done |
| 5. Architecture patterns | 6 (L5-1 to L5-6) | done |
| 6. Implementing agents | 10 (L6-1 to L6-10) | done |
| 7. n8n practical | 8 (L7-1 to L7-8) | done |
| 8. Agent infrastructure | 6 (L8-1 to L8-6) | done |
| 9. AI agents in business | 3 (L9-1 to L9-3) | done |
| 10. AI agents for trading workflows | 1 (L10-1) — growing | seeded |
| **Total** | **55 lectures + 10 section READMEs = 65 .md files** | **complete (S1-9) + growing (S10)** |

Total: ~205K words across 65 files. Each lecture is 3-4K words, structured as: FDE framing → 3 things you'll learn → concept → pattern → code → production addendum → cross-references → 3 interview questions → read next.

**S1-9 are closed.** **S10 is a growing section** — start with L10-1 (the 5 trading workflows + 5 guardrails), then add L10-2 (options/derivatives workflows), L10-3 (multi-strategy portfolio workflows), etc. Use the directory as a self-paced FDE study guide. Replace the lecture titles with the source's exact titles when the source lecture list is available.
