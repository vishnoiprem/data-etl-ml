# Section 10: AI agents for trading workflows — the solo-trader playbook

> **Section 10 in one line:** trading is the canonical use case for AI agents in 2026. The 1 lecture in this section (L10.1) covers the 5 workflows (research, journal, sizing, EOD, compliance) + the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) + the 30-day build plan. The FDE who can name the 5 workflows, name the 5 guardrails, and recite the 1,150 hours/year saved is the FDE who can land the prop-trader engagement.

## In 60 seconds

The 5 workflows + 5 guardrails + 7 ingredients you must recite for the trading-agent interview:

1. **5 workflows:** pre-market research, trade journal analysis, position-sizing calculator, EOD recap + plan, compliance summary. Each saves 1-3 hours/week. Total: 1,150 hours/year.
2. **5 guardrails:** loop detector, schema validator, cost ceiling, idempotency, audit log. The same 5 from Section 6.5, applied to trading. Without them, the agent loops or runs up a $2K API bill.
3. **7 ingredients:** model (gpt-5-mini for research, gpt-5 for journal), tools (news API, CSV, calendar), memory (watchlist + risk rules), cost ceiling ($20/month), system prompt (5 versions), parser (Pydantic schema), loop driver (cron + retry).
4. **30-day build plan:** day 1-3 research, day 4-6 journal, day 7-9 sizing, day 10-12 EOD, day 13-15 compliance, day 16-30 iterate + add guardrails.
5. **The pitch:** the agent doesn't make the trade. The agent does the boring work around the trade. The trader reads the brief, decides, and clicks. $20/month + 30 hours setup = 1,150 hours/year back.

**The wrong choice is to automate the trade decision.** The right choice is the 5 workflows + 5 guardrails + 30-day plan. The 60-second interview script for the trading-agent round lives in L10.1.

## The 1 lecture in this section

| # | Lecture | Topic | Read time | Interview signal |
|---|---------|-------|-----------|-------------------|
| 1 | `L10-1-ai-agents-for-trading-workflows.md` | The 5 trading workflows + 5 guardrails + 30-day build plan. The 50-line TradingAgent class. | 22 min | "Where do AI agents work best in 2026?" |

**Total: ~22 minutes of reading + 30 days of building.**

## Why this section exists

Sections 1-9 built the agent from first principles: the 7 ingredients, the 5 guardrails, the 4 testing layers, the 4 infrastructure pillars, the n8n platform, the use case rubric, the ROI formula. The agent is a working piece of software. **But software doesn't have value until it solves a real problem; trading is the canonical real problem in 2026.** Section 10 is the application section — the use case that proves the FDE pattern.

The 1 lecture answers the question every customer in 2026 asks:

1. **"Where do AI agents work best?"** — Trading is the answer. The 5 workflows save 1,150 hours/year. The 5 guardrails make the workflows production-safe. The 30-day build plan ships the system.

The lecture is short on purpose. The trading-agent round is a 60-second pitch + a 30-day build. The FDE who can name the 5 workflows + 5 guardrails + the 1,150 hours saved is the FDE who can land the engagement.

**Section 10 is a growing section.** Today: 1 lecture (L10.1). Tomorrow: L10-2 (options + derivatives workflows), L10-3 (multi-strategy portfolio workflows), L10-4 (compliance + reporting at scale), L10-5 (the prop-firm-specific challenges). The 5-workflow pattern is the seed; the user (or future FDEs) can grow it.

## The case study that runs through this section

**Customer:** A solo Singapore-based prop trader with a $50K account, working on the FTMO challenge (10% profit target, 5% daily max loss, 10% trailing drawdown). The trader currently works 60 hours/week: 5am research, intraday execution, evening journaling, Sunday compliance.

**Goal:** automate the 5 boring workflows so the trader can work 25 hours/week instead of 60. The 5 workflows save 1,150 hours/year. The trader keeps the actual trade decision; the agent does the work around the trade.

**The build:** L10.1 walks through the 50-line TradingAgent class, the 5 workflow definitions, the 5 guardrails in code, and the 30-day build plan. By day 30, the trader has 5 agents running every day.

**Why this case study:** it's a real use case for the FDE pattern. The trader is the customer; the 5 workflows are the deliverable; the $20/month LLM API is the cost; the 1,150 hours saved is the value. The ROI is 28,500% in year 1. **The FDE proves the pattern on a use case the customer already has.**

## How to use this section

1. **Read L10.1 once** — the 5 workflows + 5 guardrails + 30-day plan. This is the synthesis.
2. **Read L10.1 again** — this time, open your own broker CSV and run the prompts in ChatGPT. See what comes out.
3. **Build the 5 workflows** — 1 hour/day for 30 days. By day 30, the 5 agents run for you.
4. **Add the 5 guardrails** — day 16-30 of the build plan. The guardrails are what make the agents safe.
5. **Iterate weekly** — review the audit log every Sunday. Tune the prompts. Add new workflows.

**Hands-on:** the lecture ends with a 30-day build plan. Day 1: build workflow 1 (pre-market research). Day 30: all 5 workflows run. The 30 days are the lecture's homework.

## Read next

`L10-1-ai-agents-for-trading-workflows.md` — the 5 trading workflows + 5 guardrails + 30-day build plan. The 50-line TradingAgent class. The 8-section template (FDE framing → In 60 seconds → 3 things → Concept → Pattern → Code → Production → Cross-references → 3 questions → Read next).

For the Substack-friendly version of this lecture, see `marketing/content/articles/2026-10-ai-agents-for-trading-workflows.md`. The blog post is the same content in small-business-owner voice (~2,300 words); the lecture is the same content in FDE-study voice (~3,300 words).