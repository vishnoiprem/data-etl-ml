# Mock 2: CTO / Architect

> **Week 8 · Mock 2 · 60 min**
> **Goal:** The CTO is testing peer-level technical judgment. This is the technical round.

## The setup

The CTO is your peer (or your peer-adjacent). They want to know:

1. **Can you make technology decisions I can defend to my board?**
2. **Can you hold your own in a build-vs-buy debate?**
3. **Can you defer when I'm right, and defend when you're right?**
4. **Can you keep up with the pace of change in AI?**

This is the round where "depth" beats "breadth." Lead with the headline, defend in the follow-up.

## The structure (60 min)

| Section | Time | What to expect |
|---|---|---|
| Opener | 5 min | "Walk me through your current architecture" / "What's your stack today?" |
| Architecture | 20 min | Deep dive on 1-2 layers; the trade-offs; the rejected alternatives |
| Build-vs-buy | 15 min | 2-3 specific decisions; the framework; the cost |
| AI / forward-looking | 15 min | "How are you using AI?" / "What's your AI strategy?" / "What about agents?" |
| Closer | 5 min | "How do you keep up?" / "What do you want from me as a peer?" |

## The questions you'll get

1. **Opener:** "Walk me through your current architecture. What are the 5 layers? Why?"
2. **Architecture — storage:** "Lakehouse vs. warehouse — which, why, and what would change your mind?"
3. **Architecture — AI:** "How are you doing RAG in production? What about agents? What's your eval?"
4. **Build-vs-buy:** "Why did you build your feature store in-house rather than buy Tecton or Feast-managed?"
5. **Build-vs-buy:** "You use Snowflake. Why not BigQuery? Why not Databricks? Why not all-Postgres?"
6. **AI strategy:** "What's your AI portfolio? How do you pick use cases? How do you measure ROI?"
7. **AI / agents:** "How do you feel about agentic AI? When would you ship one to production? When would you not?"
8. **Forward-looking:** "What's the most overrated trend in data and AI right now? What's underrated?"
9. **Pace of change:** "How do you keep up with the pace of change in AI? What's your learning practice?"
10. **Closer:** "What do you want from me as a peer? What's the joint decision you need from us?"

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Technical judgment and architecture | 50% | The architecture is detailed; the trade-offs are named; the rejected alternatives are explicit |
| Strategic and business thinking | 20% | The architecture serves the strategy |
| Communication and structure | 15% | The answers are crisp; the diagrams are clear |
| Leadership and executive influence | 10% | The peer posture is right — defend, defer, find the joint |
| Commercial and financial understanding | 5% | The cost / build-vs-buy math is sound |

A score below 90 means the loop is not ready. Re-mock.

## What the CTO is really testing

| What they say | What they mean |
|---|---|
| "Lakehouse vs. warehouse — which and why?" | "Do you have a real opinion, or are you following the herd?" |
| "Why did you build your feature store in-house?" | "Do you understand the build-vs-buy math, or are you building for the sake of building?" |
| "What's your eval harness?" | "Are you shipping AI you can measure, or AI you can demo?" |
| "What about agents?" | "Are you current, or are you still living in 2023?" |
| "What's overrated?" | "Do you have the courage to call out hype?" |
| "What do you want from me as a peer?" | "Will you be a peer, or a competitor for my role?" |

## How to prepare

1. **Rehearse the architecture defense** (use Day 38 + Case Study 4)
2. **Pick 3 architecture stories** that cover: storage decision, AI platform decision, build-vs-buy decision
3. **Have a real opinion on agents** — what's the use case, what's the risk, what's the eval
4. **Have a real opinion on overrated / underrated** — be specific
5. **Prepare the "what do you want from me" answer** — the joint decision, the deferral

## How to run the mock

- 60 min, recorded, with a peer or coach playing the CTO
- Use the question list above
- After 60 min, score using the rubric
- Identify the 2 weakest answers
- Rewrite + re-mock

## The "what do you want from me" answer

The CDO who wants a peer relationship says:

"Three things. One, alignment on the architecture direction — lakehouse + dbt + Looker + multi-model LLM. If we don't agree, we escalate with a joint memo to the CEO. Two, your input on the build-vs-buy for the feature store — I'll defend my recommendation, I want your peer review. Three, clarity on the security posture — what's the joint decision on the AI Act?"

The CDO who wants a competitor relationship says: "I want you to back my play." That's the wrong answer.

## Re-record until you score ≥ 90

A score below 90 here is a no-offer. The CTO is the technical bar. Re-mock, rewrite, re-mock.

---

**Next:** Mock 3 — CEO / CFO.