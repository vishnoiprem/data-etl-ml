# PYMK Objection Handling + Candidate Metrics Matrix

Companion to the spoken answer. Practice these in mock interviews.

---

## OBJECTION HANDLING (the 5 follow-ups you'll get)

### Objection 1: "How do you answer 'were A and B friends on Jan 15' if the event arrived late on Jan 17?"

**Answer (spoken, 30s):**
> "Late-arriving events are the classic time-travel bug. The first line of defense is that Kafka preserves the original event timestamp, not the processing timestamp. So Flink reads `event_time`, not `processing_time`. The second defense is a watermark — I allow up to 7 days of lateness for friendship events. After the watermark closes, late events still get applied but they go to a reconciliation job that updates the historical store, not the live one. The third defense is to never expose the as-of query directly to a user — every time-travel call goes through a snapshot table that's rebuilt nightly. That way, even a missed late event only shows up after the next snapshot. The cardinal sin would be using `processing_time` and thinking your time travel is correct when it's actually drifting forward by however long the consumer lag is."

**SQL proof:**
```sql
-- Answer "were A and B friends on 2026-01-15?"
SELECT 1 FROM friendships
WHERE user_id_low = LEAST(:a, :b)
  AND user_id_high = GREATEST(:a, :b)
  AND valid_from <= '2026-01-15'
  AND (valid_to > '2026-01-15' OR valid_to IS NULL);

-- Late event arrived on Jan 17 for an event_time of Jan 14:
-- The query above still returns TRUE because valid_from = Jan 14 <= Jan 15.
-- The watermark guarantees we backfill valid_from, not valid_to.
```

### Objection 2: "What if employment doesn't overlap? A worked at Meta 2018-2020, B worked at Meta 2021-2023. Don't recommend."

**Answer (spoken, 30s):**
> "This is the most-missed requirement. Same company is not enough — I need real overlap. The SQL is a self-join on `work_history` with a date-overlap condition: `start_a < end_b AND start_b < end_a`, with `COALESCE(end_date, CURRENT_DATE)` for the current job. Test case in the eval set: A at Meta 2018-2020, B at Meta 2021-2023 — zero overlap, must NOT suggest. Most candidates just check `company_id = X` and ship a wrong explanation. The L6 line: 'I treat overlap as a first-class predicate. Without it, the explanation 'you both worked at Meta' is technically true but semantically false, and the user will lose trust in the system after one bad suggestion.'"

**SQL proof:**
```sql
SELECT a.user_id, b.user_id, a.company_id
FROM work_history a
JOIN work_history b
  ON a.company_id = b.company_id
 AND a.user_id < b.user_id
 AND a.start_date < COALESCE(b.end_date, CURRENT_DATE)
 AND b.start_date < COALESCE(a.end_date, CURRENT_DATE);
```

### Objection 3: "What if the LLM says 'You both worked at FakeCorp' but evidence says Meta?"

**Answer (spoken, 30s):**
> "Two defenses. First, the prompt explicitly says: 'Use ONLY the values present in evidence_json. If a value is not present, output the literal string unknown.' Second, and more important: a deterministic claim validator runs AFTER generation. Every factual claim — company, school, city, mutual count — is regex-matched against the evidence. If a claim is not in the evidence, the whole explanation is rejected and we fall back to a template like 'You have N mutual connections.' The validator runs in <1ms. The audit log records every rejected claim for offline analysis. The cardinal sin would be trusting the LLM's output and only catching hallucination via user reports."

**Code proof:**
```python
def validate_claim(claim: str, evidence: dict) -> bool:
    if "worked at" in claim.lower():
        # Extract company from claim
        for company in evidence.get("shared_companies", []):
            if company.lower() in claim.lower():
                return True
        return False  # Hallucinated company
    if "mutual" in claim.lower():
        # Extract number and check it matches
        import re
        nums = re.findall(r'\d+', claim)
        return nums and int(nums[0]) == evidence.get("mutual_friend_count", 0)
    return True  # Non-factual claims pass
```

### Objection 4: "Celebrity with 50M followers. You process a friend-add. 50M writes?"

**Answer (spoken, 30s):**
> "Yes, that's the bug. Below 5000 connections, I use push fanout — when a friendship is created, I write to every neighbor's candidate set. Above 5000, I switch strategies. First, the friendship event is recorded but NOT fanned out. Second, when any of the celebrity's connections opens the app, the PYMK service does a real-time lookup: 'is this user connected to a high-degree node?' If yes, the celebrity is added to the candidate list at read time, with a bounded cost of one RocksDB lookup. Third, an async batch job precomputes PYMK for the top 1% of high-degree users' connections — only those who engage with the celebrity often. The math: 50M friends becomes 50M lookups at read time, which is fine if each lookup is 0.1ms and only 1% of them actually fire. The cardinal sin would be a uniform push-fanout for every user regardless of degree."

### Objection 5: "User A blocked user B. The block hasn't propagated. A sees B in PYMK. Now what?"

**Answer (spoken, 30s):**
> "Two layers. First, the block event goes through Kafka and updates the RocksDB blocklist within 5 seconds. Second — and this is the critical part — the serving path does an authoritative privacy check on EVERY response, even if the cache is supposedly up to date. The check is a single RocksDB point lookup at the head of the request, taking <1ms. If the candidate is blocked, it's filtered out before the response is built. The reason: the cost of a privacy violation is unbounded — it's a regulatory incident, a user trust violation, and a PR event. The cost of a 1ms lookup per request is bounded and small. The cardinal sin would be trusting the cache and getting a 2am page about a user seeing their stalker in PYMK."

---

## OBJECTIVE & CANDIDATE METRICS (the matrix you asked for)

### The objective (one sentence)

> "Recommend the most relevant people a user may know, with a trustworthy explanation, while respecting privacy and keeping recommendations fresh."

### Candidate-generation metrics (offline)

| Metric | What it measures | Target | How to compute |
|---|---|---|---|
| **Recall@K** | Did we include the truly good candidates in top K generated? | >= 0.7 at K=100 | On held-out set of users with known connections: did we generate them as a candidate? |
| **Precision@K** | Of K generated, how many are actually relevant? | >= 0.3 at K=100 | User labeled "would accept" / total generated |
| **NDCG@K** | Are the strongest candidates ranked near the top? | >= 0.6 at K=20 | Standard NDCG formula on graded relevance |
| **Candidate coverage** | What % of active users get enough quality candidates? | >= 95% of DAU have >= 20 candidates | Count users with `candidate_count >= 20` / total DAU |
| **Freshness lag** | How quickly new friendship/work changes affect candidates? | p95 < 60s | Time from event creation to candidate_set update |
| **Blocked/invalid candidate rate** | How many generated candidates are filtered out by privacy? | < 0.1% | Blocked / generated, per day |
| **Hallucination rate** | How many explanations fail validation? | < 0.05% | Claim validator rejections / total served |

### Final product / business metrics (online)

| Metric | What it measures | Target | How to compute |
|---|---|---|---|
| **Connection acceptance rate** | Did the user actually send a friend request? | >= 5% | Friend requests sent / PYMK impressions |
| **Recommendation CTR** | Did the user click a PYMK card? | >= 15% | Clicks / impressions |
| **Hide / dismiss rate** | Did the user explicitly hide a recommendation? | < 2% | Hides / impressions |
| **Explanation helpfulness** | Did the user find the explanation useful? (👍/👎) | >= 80% thumbs up | Thumbs up / total feedback |
| **Privacy violation rate** | Did a blocked user appear? | 0 (zero tolerance) | Hard alert on any occurrence |
| **P95 serving latency** | End-to-end PYMK fetch | < 200ms | Tracing + dashboard |

### The 5-card L6 dashboard (single screen, refreshes every 5 min)

```
┌──────────────────┬──────────────────┬──────────────────┐
│ Recall@100       │ Privacy Viol.    │ Freshness Lag    │
│   0.74 ✓         │   0 today ✓      │   28s p95 ✓      │
├──────────────────┼──────────────────┼──────────────────┤
│ P95 Latency      │ Hallucination    │ Acceptance Rate  │
│   180ms ✓        │   0.02% ✓        │   6.2% ✓         │
└──────────────────┴──────────────────┴──────────────────┘
```

A regression in ANY ONE is a P2 to investigate within 1 hour.

### The interview sentence (use this verbatim)

> "I measure at three layers. For candidate generation, Recall@K, Precision@K, NDCG@K, coverage, and freshness lag. For the product, acceptance rate, CTR, hide rate, and explanation helpfulness. For safety, privacy violation rate (zero tolerance) and hallucination rate (under 0.05%). The 5-card dashboard refreshes every five minutes; a regression in any card is a P2."

---

## WHAT TO SAY IF THEY ASK "WHY THESE METRICS, NOT OTHERS?"

**Answer (spoken, 30s):**
> "Three principles. First, every metric must be actionable — if it goes red, an engineer must know what to do. Second, every metric must be measurable in production, not just on a synthetic test set. Third, every metric must be cheap — the dashboard itself should cost less than the product it monitors. Recall@K and NDCG@K are the only retrieval metrics that survive contact with the real world. Acceptance rate is the only business metric that matters; CTR is a proxy that can be gamed. Privacy violation rate is zero-tolerance because the cost of a single incident dwarfs the cost of the dashboard. Hallucination rate is a leading indicator: it goes red before users notice, so you can fix it before the PR event."

---

## FULL PRACTICE SCRIPT (2 minutes, no notes)

> "First, I'll clarify the requirements. We have around 500 million users, we need explainable recommendations, no unsupported AI claims, sub-minute freshness, support for historical friendship checks, and bounded fanout for very high-degree users.
>
> I'll split the system into three parts: historical graph storage, candidate generation, and online serving with grounded explanations.
>
> For friendship history, I'll use a canonical pair key with `user_id_low` and `user_id_high`, plus `valid_from` and `valid_to`. That lets me answer questions like, 'Were A and B friends on January 15th?' using an as-of query. I'll use the same temporal approach for work history, because 'you both worked at Meta' should only be true if their employment periods actually overlapped.
>
> For candidate generation, I'll use an offline Spark pipeline over graph features like mutual friends and shared work history. It produces a bounded candidate set per active user, maybe top 100, rather than calculating the whole graph at request time. For freshness, new friendship events go through Kafka and Flink. Flink updates recent features incrementally. The online service merges precomputed candidates with fresh signals.
>
> For celebrity or high-degree users, I don't fan out millions of writes. Below a threshold I push updates; above the threshold I switch to a pull or lazy-compute model. That keeps work bounded.
>
> For the AI explanation, the LLM never decides the facts. A deterministic evidence service first produces structured evidence like shared company Meta and five mutual friends. The LLM only verbalizes that evidence. After generation, I validate every factual claim against the evidence. If validation fails, I fall back to a deterministic explanation such as 'You have mutual connections.' I also keep an audit record for traceability.
>
> For privacy, blocks and deletions are hard constraints. I can propagate them asynchronously through the stream for efficiency, but I still perform an authoritative serving-time privacy filter before returning recommendations.
>
> At scale, 500 million users times 100 candidates is up to 50 billion candidate records, so I would not treat everything as hot. I'd keep hot candidates for active users in cache, durable candidates in a sharded store, and expire or regenerate stale candidates.
>
> For metrics, I measure three layers. Retrieval: Recall@K, Precision@K, NDCG@K, candidate coverage, freshness lag. Product: acceptance rate, CTR, hide rate, explanation helpfulness. Safety: privacy violation rate (zero tolerance) and hallucination rate. The dashboard refreshes every five minutes; a regression in any metric is a P2.
>
> The design is grounded, bounded, and auditable: temporal graph data for time travel, overlap-aware evidence for shared employment, grounded explanations with validation, bounded fanout for high-degree users, and safe rollout with shadowing and rollback."

Then stop. Let them choose the next area.
