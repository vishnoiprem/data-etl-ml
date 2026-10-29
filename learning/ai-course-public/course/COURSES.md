# Course index — `ai-course-public/`

> **One paragraph per course, mapped to the same instructor's track.**

This directory started out as a flat repo of fragments. As more courses were
mirrored into it, the same instructor's content kept appearing in different
trees. The arrangement below is the deliberate one — three sibling director-
ies under data_llm_engineer/, plus the standalone courses that don't overlap.

---

## Ed Donner's AI Engineering trilogy

The three courses the instructor publishes as a series:

| # | Course | Where | Weeks | What it adds |
|---|---|---|---|---|
| 1 | **LLM Engineering: Core** | `data_llm_engineer/` | 8 | Brochure, Gradio airline agent, RAG, QLoRA fine-tune, pricer capstone, autonomous deal agent |
| 2 | **LLM Engineering: Production** | `data_llm_engineer/production_track/` | 4 | Vercel → AWS migration, Terraform, Bedrock/SageMaker, observability |
| 3 | **Agentic AI Engineering** | (covered by `agentic-ai/`) | 6 | OpenAI Agents SDK, CrewAI, LangGraph, AutoGen, MCP |

Course 3 is the same instructor's program but mostly overlaps with the 19
existing `agentic-ai/` projects. The framing is the 8-application arc, but the
weeks are largely re-implementations of what is already here. **If you want
MCP / multi-agent work, start in `agentic-ai/`**; come back to a course-3
scaffold only if you specifically need a particular framework (CrewAI / Agno /
Strands / Mastra) that isn't yet present.

---

## Standalone courses

These don't fit neatly into a track and live on their own:

| Course | Where | Why it's separate |
|---|---|---|
| **AI Builder in n8n** | `ai-builder-n8n/` | Vendored to n8n; doesn't share concepts with the Python courses |
| **AI Coder (Claude Code et al.)** | `ai-coder-coding-agents/` | About *driving* coding agents, not building LLM apps |
| **AI Leader** (executive briefing) | `ai-leader-genai-briefing/` | Frameworks and rubrics, no code. Different audience entirely |

---

## Other directories under `ai-course-public/`

These predate the index. Quick orientation:

| Directory | What it is |
|---|---|
| `180-day-ai/` | A separate learn-by-doing curriculum, not part of any published course |
| `AI-Engineer-Interview-loop/` | Interview preparation; not a course |
| `Full-Stack-Engineering/` | A complete fast-track program (largely independent) |
| `ai-agents/` | Older agent coursework |
| `ai-fde/` | AI Forward Deployed Engineer (PacificFreight drafter) |
| `ai-native-de/` | AI-native data engineering |
| `capstone-starters/` | Bootstraps for the various capstone projects |
| `hardcode/` | "Build everything from scratch" exercises |
| `outlines/` | Course outlines and metadata |
| `practice/` | Practice exercises |
| `projects/` | Project shells, not course-aligned |
| `scripts/` | Helper scripts |
| `usage.jsonl` | Telemetry from running course exercises |
| `workbooks/` | Notebooks and supporting files |
| `PRACTICE-GUIDE.md` | Practice-use guidance for the directory as a whole |

---

## How to read this index

If you're working through one of the courses above, **start in that
course's README** — they all follow the same shape (What you build / File
layout / How to use / What this is NOT / Source / provenance). Each README
also states honestly what is **authored from the lecture titles alone**
versus what matches verified existing code in the repo. The instructor's
name is left blank where I don't know it.

---

**Last updated:** 2026-10-21