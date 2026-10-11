# 64. Copy.ai

- **Role:** AI Engineer (Workflow agents)
- **Tech stack:** Python, TypeScript, LangGraph, OpenAI/Anthropic, Postgres, Temporal, AWS
- **Comp band:** $160K-$320K total comp (L4-L6: AI Engineer → Staff) | Base + RSUs
- **Cumulative pass rate:** ~5-6%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: a LangGraph agent DAG with CRM → enrichment → LLM → send nodes, one branch labeled "human-in-the-loop". Color: Copy.ai indigo (#5B5FED). Headline: "Copy.ai / Workflow Agents / 2026".

> **TL;DR:** Copy.ai hires engineers who can ship GTM agents end-to-end, not just prompt an LLM. The signature round is the agent system design — candidates design a multi-tenant Temporal workflow with cost dashboards. The winning candidate has talked to a real SDR and can defend cost-per-execution.

```
Recruiter → Phone → Onsite (3 rounds) → Founder/CTO chat → Offer
```

The founder round is non-trivial. Paul Yacoubian cares about GTM empathy and shipping speed — vague "I'd build an agent" answers get cut.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Mission fit, remote setup | 30 min | ~60% |
| 2. Technical phone | Coding + agent design | 60 min | ~40% |
| 3. Onsite (3 rounds) | Coding, agent system design, behavioral | 3 hrs | ~30% |
| 4. Founder/CTO chat | Mission alignment | 30 min | ~70% |
| 5. Offer | Comp, equity | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Copy.ai now?"
**Answer:** "You've moved from copy generation to full go-to-market workflows. That's the right bet — most GTM tools are point solutions, and the orchestration layer is wide open. I want to build agents that connect SDR, marketing ops, and RevOps in one graph."
**Tip:** Show you understand the pivot from "AI copy tool" to "GTM OS."

### Q1.2: "Remote experience?"
**Answer:** "5+ years fully remote, led distributed teams, document everything in Notion, and my SF overlap is 4 hours. I treat writing as a forcing function for clarity."
**Tip:** They're remote-first. Don't undersell async fluency.

## Stage 2: Technical phone screen

### Q2.1: Implement a rate limiter.
**Answer:** Token-bucket with Redis Lua script for atomicity; per-tenant + per-user keys.
**Tip:** They use this pattern in production; show you can ship it.

### Q2.2: How would you design an agent that writes personalized cold emails given a CRM?
**Answer:** Workflow: pull contact from CRM → enrich with Clearbit → research company with RAG over 10-K → draft with LLM, structured JSON → A/B variant → compliance check (CAN-SPAM unsubscribe) → send via API. Add a human-in-the-loop approval step.
**Tip:** This is literally their product; bring product intuition.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Merge k sorted lists.
**Answer:** Heap-based; O(N log k).

### Round 3.2: System design
**Q:** Design a multi-tenant agent execution platform.
**Answer:** Per-tenant Temporal workflows, model router (cheap for easy tasks, frontier for hard), shared evaluation harness, prompt + tool registry, per-tenant cost dashboard.

### Round 3.3: ML / agent deep-dive
**Q:** How would you evaluate a GTM agent?
**Answer:** Offline eval on historical CRM data, online A/B on reply rate, human spot-checks, regression suite for tool failures.

### Round 3.4: Behavioral
**Q:** Tell me about an agent that broke in production.
**Answer:** STAR: own the failure, explain detection, mitigation, postmortem.

## Stage 4: Founder chat
Paul Yacoubian (CEO) often joins. He cares about GTM empathy and shipping speed.

## Stage 5: Offer
Equity vests 4 years 1-year cliff. They pay below market but RSUs have upside.

## Tips for the Copy.ai loop
- Read the Copy.ai blog and the GTM agent space.
- Use their product before the interview; bring specific feedback.
- Practice Temporal / LangGraph agent patterns.
- Show GTM intuition — talk to a real SDR.
- Know CAN-SPAM and email deliverability basics.
- Be ready to defend cost-per-execution of an agent.

## Real candidate report
> "Took 2 weeks. Coding was LeetCode medium, system design was their actual product. Got a fair offer. The team is small so I interviewed with the founders." — Glassdoor, AI Engineer, 2025

## Sources
- [Copy.ai careers](https://www.copy.ai/careers)
- [Copy.ai engineering blog](https://www.copy.ai/blog)
- [Levels.fyi — Copy.ai](https://www.levels.fyi/companies/copy-ai)
- [Glassdoor — Copy.ai](https://www.glassdoor.com/Interview/Copy-AI-Interview-Questions.htm)
- [Reddit r/MachineLearning](https://reddit.com/r/MachineLearning)

---

## The 1 thing to remember

Copy.ai rewards GTM empathy and shipping speed — if you can't defend cost-per-execution of an agent and haven't talked to a real SDR, the founder round will cut you.
