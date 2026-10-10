# Section 10: AI agents — the canonical use case, demonstrated on trading workflows

> **Section 10 in one line:** AI agents in 2026 are best understood through the workflows they own, not the decisions they replace. Trading is the cleanest demonstration because every workflow is a tight **read → score → write** loop. The 1 lecture in this section (L10.1) covers the 5 workflows (research, journal, sizing, EOD, compliance) + the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) + the 30-day build plan + the 12-workflow extension beyond trading. The FDE who can name the 5 workflows, name the 5 guardrails, recite the 1,150 hours/year saved, and articulate the 12-workflow pattern is the FDE who can land the AI-agent engagement.

## In 60 seconds

The 5 workflows + 5 guardrails + 7 ingredients + 4 use case criteria + 12 application workflows you must recite for the AI-agent interview:

1. **What an AI agent is in 2026:** LLM + tools + loop, with 5 guardrails. Not magic, not AGI, not a decision-maker. A junior assistant with infinite patience and zero judgment.
2. **4 use case criteria:** repetitive, language-heavy, tool-using, measurable. If a workflow doesn't hit all 4, don't automate it.
3. **5 workflows (trading):** pre-market research, trade journal analysis, position-sizing calculator, EOD recap + plan, compliance summary. Each saves 1-3 hours/week. Total: 1,150 hours/year.
4. **5 guardrails:** loop detector, schema validator, cost ceiling, idempotency, audit log. The same 5 from Section 6.5, applied to agents. Without them, the agent loops or runs up a $2K API bill.
5. **7 ingredients:** model (gpt-5-mini for research, gpt-5 for journal), tools (news API, CSV, calendar), memory (watchlist + risk rules), cost ceiling ($20/month), system prompt (5 versions), parser (Pydantic schema), loop driver (cron + retry).
6. **30-day build plan:** day 1-3 research, day 4-6 journal, day 7-9 sizing, day 10-12 EOD, day 13-15 compliance, day 16-30 iterate + add guardrails.
7. **12 workflows beyond trading:** customer support, sales call review, contract review, candidate screening, code review, content moderation, lead enrichment, tax categorization, meeting notes, news monitoring, inventory reorder, onboarding. Same shape, same guardrails, same 30-day build per workflow.
8. **The pitch:** the agent doesn't make the decision. The agent does the boring work around the decision. The operator reads the brief, decides, and clicks. $20/month + 30 hours setup = 1,150 hours/year back.

**The wrong choice is to automate the decision.** The right choice is the 5 workflows + 5 guardrails + 30-day plan + 12-workflow extension. The 60-second interview script for the AI-agent round lives in L10.1.

## The 1 lecture in this section

| # | Lecture | Topic | Read time | Interview signal |
|---|---------|-------|-----------|-------------------|
| 1 | `L10-1-ai-agents-for-trading-workflows.md` | What an AI agent is in 2026 + the 5 trading workflows + 5 guardrails + 30-day build + 12-workflow extension. The 50-line TradingAgent class. | 22 min | "Where do AI agents work best in 2026?" |

**Total: ~22 minutes of reading + 30 days of building.**

## Why this section exists

Sections 1-9 built the agent from first principles: the 7 ingredients, the 5 guardrails, the 4 testing layers, the 4 infrastructure pillars, the n8n platform, the use case rubric, the ROI formula. The agent is a working piece of software. **But software doesn't have value until it solves a real problem.** Section 10 is the application section — the use case that proves the FDE pattern, with trading as the canonical demonstration.

The 1 lecture answers the question every customer in 2026 asks:

1. **"Where do AI agents work best?"** — The boring, repetitive, language-heavy, tool-using, measurable work. Trading is the canonical demonstration: 5 workflows save 1,150 hours/year. The 5 guardrails make the workflows production-safe. The 30-day build plan ships the system. The same pattern unlocks 12 more workflows across the back office.

The lecture is short on purpose. The AI-agent round is a 60-second pitch + a 30-day build. The FDE who can name the 5 workflows + 5 guardrails + 4 use case criteria + 12 application workflows is the FDE who can land the engagement.

**Section 10 is a growing section.** Today: 1 lecture (L10.1). Tomorrow: L10-2 (options + derivatives workflows), L10-3 (multi-strategy portfolio workflows), L10-4 (compliance + reporting at scale), L10-5 (the prop-firm-specific challenges). The 5-workflow + 12-workflow pattern is the seed; the user (or future FDEs) can grow it.

## The case study that runs through this section

**Customer:** A solo operator running their own book. The operator currently works 60 hours/week: 5am research, intraday decisions, evening journaling, Sunday compliance.

**Goal:** automate the 5 boring workflows so the operator can work 25 hours/week instead of 60. The 5 workflows save 1,150 hours/year. The operator keeps the actual decision; the agent does the work around the decision.

**The build:** L10.1 walks through the 50-line TradingAgent class, the 5 workflow definitions, the 5 guardrails in code, and the 30-day build plan. By day 30, the operator has 5 agents running every day.

**Why this case study:** it's a real use case for the FDE pattern. The operator is the customer; the 5 workflows are the deliverable; the $20/month LLM API is the cost; the 1,150 hours saved is the value. The ROI is 28,500% in year 1. **The FDE proves the pattern on a use case the customer already has.** Then the same pattern extends to the other 12 workflows on the operator's (and the customer's) plate.

## How to use this section

1. **Read L10.1 once** — what an AI agent is in 2026 + the 5 workflows + 5 guardrails + 30-day plan + 12-workflow extension. This is the synthesis.
2. **Read L10.1 again** — this time, open your own inputs and run the prompts in ChatGPT. See what comes out.
3. **Build the 5 workflows** — 1 hour/day for 30 days. By day 30, the 5 agents run for you.
4. **Add the 5 guardrails** — day 16-30 of the build plan. The guardrails are what make the agents safe.
5. **Iterate weekly** — review the audit log every Sunday. Tune the prompts. Extend to the next workflow on the 12-workflow list.

**Hands-on:** the lecture ends with a 30-day build plan. Day 1: build workflow 1 (pre-market research). Day 30: all 5 workflows run. The 30 days are the lecture's homework.

## Read next

`L10-1-ai-agents-for-trading-workflows.md` — what an AI agent is in 2026 + the 5 trading workflows + 5 guardrails + 30-day build plan + 12-workflow extension. The 50-line TradingAgent class. The 8-section template (FDE framing → In 60 seconds → 3 things → Concept → Pattern → Code → Production → Cross-references → 3 questions → Read next).

For the Substack-friendly version of this lecture, see `marketing/content/articles/2026-10-ai-agents-for-trading-workflows.md`. The blog post is the same content in operator voice (~3,000 words); the lecture is the same content in FDE-study voice (~3,900 words).
