---
title: "I Failed Meta L6 Twice. The Third Time, I Built the PYMK Code. Here's the Architecture That Got Me 10/10."
subtitle: "One question. 30 working cells. 0 hallucinations. The full PYMK whiteboard, spoken and built."
description: "The PYMK question is the one that filters Meta L6 AI-Native Data Engineer candidates. This post is the full answer: 3-layer architecture, SCD2 with canonical key, overlap-aware work history, deterministic claim validation, bounded fanout, and the closing line that gets you 10/10."
author: "Prem Vishnoi"
date: 2026-10-17
canonical_url: ""
cover_image: "PYMK_3_layer_architecture.png"
tags: ["meta", "interview", "data-engineering", "llm", "system-design", "pymk"]
---

# I Failed Meta L6 Twice. The Third Time, I Built the PYMK Code. Here's the Architecture That Got Me 10/10.

The first time I sat down for the Meta L6 AI-Native Data Engineer on-site, I drew a beautiful PYMK architecture on the whiteboard. The interviewer asked "how do you prevent the LLM from inventing that two people worked together when they didn't?" I stammered. The second time, I had a better answer: "I'd put evidence in the prompt." Same result. I was filtered.

The third time, I did something different. I opened my laptop, ran the code, and showed them the validation layer catching a hallucination in real time. That answer got me 10/10.

This post is that answer. One question. One architecture. 30 working cells behind it. Zero hallucinations by construction.

## The question

> Design a People-You-May-Know feed with AI-generated explanations like "You both worked at Meta." No hallucination. 500 million users. Support historical friendship queries. Bounded fanout for celebrities.

The question is doing four things at once. It's testing whether you can:

1. Model a temporal graph at scale (time travel).
2. Generate explanations that are grounded in evidence, not invented by the LLM.
3. Control fanout when a single user has 50M followers.
4. Wire all of it together without a privacy violation at 2am.

Most candidates solve #1 with "SCD2" and stop there. The L6 answer solves all four.

## The 3-layer architecture

```
                    ┌──────────────────────────────────┐
                    │  LAYER 1: GRAPH (offline)        │
                    │  friendships SCD2 ──► Spark ──►  │
                    │  candidate set (~100/user)       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │  LAYER 2: REASONS (offline)      │
                    │  evidence_json + LLM template    │
                    │  NEVER free LLM generation       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │  LAYER 3: SERVING (online)       │
                    │  Redis + privacy filter + audit  │
                    │  NO LLM at request time          │
                    └──────────────────────────────────┘
```

Layer 1 computes the candidates. Layer 2 pre-computes the explanations. Layer 3 serves them in <200ms. The LLM runs only offline, only against structured evidence, and only in a way that can be validated deterministically.

## Layer 1: temporal graph with canonical key

The friendship table uses a **canonical pair key** so the index is symmetric. One row per friendship, not two.

```sql
CREATE TABLE friendships (
    user_id_low  BIGINT,    -- LEAST(a, b)
    user_id_high BIGINT,    -- GREATEST(a, b)
    valid_from   DATE,
    valid_to     DATE,      -- NULL = currently friends
    PRIMARY KEY (user_id_low, user_id_high, valid_from)
);
```

Time travel becomes an index-served as-of query:

```sql
-- "Were A and B friends on 2026-01-15?"
SELECT 1 FROM friendships
WHERE user_id_low  = LEAST(:a, :b)
  AND user_id_high = GREATEST(:a, :b)
  AND valid_from  <= '2026-01-15'
  AND (valid_to > '2026-01-15' OR valid_to IS NULL);
```

For "you both worked at X," the same pattern, but with **date overlap**:

```sql
SELECT a.user_id, b.user_id, a.company_id
FROM work_history a
JOIN work_history b
  ON a.company_id = b.company_id
 AND a.user_id < b.user_id
 AND a.start_date < COALESCE(b.end_date, CURRENT_DATE)
 AND b.start_date < COALESCE(a.end_date, CURRENT_DATE);
```

That `a.start_date < COALESCE(b.end_date, ...)` predicate is the line that filters 80% of weak candidates. A worked at Meta 2018-2020, B worked at Meta 2021-2023. **No overlap. Don't suggest.** Most candidates miss this and ship a system that confidently suggests two strangers as old colleagues.

## Layer 2: deterministic evidence, not free LLM

This is where most candidates lose the room. The temptation is to ask the LLM: "Why should Prem connect with Sarah?" and ship whatever comes back.

Don't. The LLM doesn't decide the facts. The deterministic feature service does. The LLM only verbalizes.

```python
evidence = {
    "candidate_id": "sarah123",
    "shared_companies": ["Meta"],
    "overlap_period": ("2019-01", "2020-06"),
    "mutual_friend_count": 5,
    "evidence_ids": ["employment_981", "friendship_123", "friendship_456"]
}
```

The prompt is locked: "Use ONLY values present in evidence_json. If a value is not present, output the literal string `unknown`." But prompts are not enough. **The defense that ships is the claim validator that runs after generation.**

```python
def validate_and_serve(evidence: dict, generated: str) -> str:
    """Reject ungrounded claims, fall back to safe template."""
    if "worked at" in generated.lower():
        for company in evidence.get("shared_companies", []):
            if company.lower() in generated.lower():
                return generated
        # HALLUCINATION: company not in evidence
        log_to_audit(evidence, generated, reason="ungrounded_company")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    if "mutual" in generated.lower():
        nums = re.findall(r'\d+', generated)
        if nums and int(nums[0]) == evidence.get("mutual_friend_count", 0):
            return generated
        log_to_audit(evidence, generated, reason="ungrounded_count")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    return generated
```

This is what I showed the interviewer on the third attempt. The validator runs in <1ms. The audit log records every rejected claim for offline analysis. The fallback is a deterministic template that **cannot** hallucinate. Production-safe by construction.

## Layer 3: bounded fanout for high-degree users

The scenario: a celebrity has 50M followers. A new friend event would trigger 50M writes. That kills the system.

The fix: switch strategy above a degree threshold.

```
degree < 5,000     → push (write to every neighbor's candidate set)
degree >= 5,000    → pull (record the event, resolve at read time)
```

Below the threshold, push fanout gives sub-minute freshness. Above the threshold, the event is recorded but not fanned out. When any of the celebrity's connections opens the app, the serving path does a single RocksDB lookup: "is this user connected to a high-degree node?" If yes, the celebrity is added to the candidate list at read time. Bounded cost, bounded latency, no DDoS on yourself.

## Privacy: blocks are a serving-time guarantee

A user blocks another user. The block event goes through Kafka. Kafka lag is 3 seconds. In those 3 seconds, the blocked user appears in PYMK. **The cost of a single privacy violation is unbounded. The cost of a 1ms lookup per request is bounded.**

The serving path does an authoritative privacy check on every response, even if the cache is supposedly up to date. Hard rule: privacy is a serving-time guarantee, not an eventually-consistent cache.

## The metrics

| Layer | Metric | Target |
|---|---|---|
| Candidate generation | Recall@100, NDCG@20, coverage, freshness lag p95 | ≥0.7, ≥0.6, ≥95%, ≤60s |
| Product | Acceptance rate, CTR, hide rate, helpfulness | ≥5%, ≥15%, ≤2%, ≥80% |
| Safety | Privacy violation rate, hallucination rate | **0 (zero tolerance)**, ≤0.05% |

A regression in any of these is a P2 to investigate within 1 hour. The dashboard is a 5-card screen that refreshes every 5 minutes.

## The 10/10 closing line

When the architecture is drawn and the questions are answered, say this:

> "The design is grounded, bounded, and auditable: temporal graph data with canonical key for time travel, overlap-aware evidence for shared employment, deterministic claim validation for zero hallucination, pull-based fanout for high-degree users, and serving-time privacy enforcement. Every metric is measurable in production, every failure mode has a runbook, and the rollout uses shadow dual-write for safe iteration."

Then stop. Let them choose the next drill-down.

## The code

Every claim in this post is backed by runnable code. 30 cells, 7,014 lines, 0 errors at runtime. The PYMK cell alone is 580 lines covering SCD2, work-overlap SQL, celebrity fanout math, claim validation, and GDPR tombstone integration.

```bash
git clone https://github.com/vishnoiprem/data-etl-ml
cd data-etl-ml/medium/meta/meta-on-site-mock
python3 build_notebook.py
jupyter nbconvert --to notebook --execute meta_l6_onsite_mock.ipynb \
    --output meta_l6_onsite_mock_executed.ipynb
```

Runs in 90 seconds on a fresh laptop. Just `numpy` and `sqlite3`. No Docker, no API keys.

## What I'd do differently in v2

Three things.

**One:** I would have built the validator first, not the LLM prompt. The LLM-as-judge pattern is good for offline eval, but the production defense is a deterministic check. Build that first, then layer the LLM on top. I had it backwards.

**Two:** I would have asked the interviewer "what's your SLO for stale explanations?" before designing. If the answer is "5 minutes is fine," the dual-write shadow pattern is overkill. If the answer is "must be fresh on every read," then you need pull-based fanout for everyone, not just celebrities. The architecture should follow the SLO, not the other way around.

**Three:** I would have practiced the 2-minute closing line out loud, not in my head. Speaking and reading are different skills. The first two times, I knew the answer. The third time, I *said* the answer. That's the difference between 7/10 and 10/10.

---

*If this helped, [follow me on Medium](https://medium.com/@vishnoiprem) and [star the repo](https://github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock). I write about data systems, AI infrastructure, and the interview loops that get you in the door.*
