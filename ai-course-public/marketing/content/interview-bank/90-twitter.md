# 90. Twitter / X (ML / Recsys)

- **Role:** ML Engineer (Timeline Ranking, Search, Ads, T&S)
- **Tech stack:** Scala, Java, Python, C++, PyTorch, TensorFlow, Flink, Kafka, Manhattan (custom KV), Cassandra
- **Comp band:** $250K-$700K total comp (L4-L6); Staff (L6) $500K-$1.2M total comp; Director (L7) $800K-$1.6M total comp (Levels.fyi 2026) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1-2%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a For You feed with adversarial content filter overlays and a Grok LLM badge). Color: X black with #1DA1F2 blue accent. Headline: "Twitter/X / AI ML Engineer / 2026".

> **TL;DR:** X's loop is real-time, adversarial, and civic-stakes — they care about timeline ranking on a bipartite graph, coordinated inauthentic behavior, and the integration of Grok into a live social surface. The winning candidate speaks in impressions-per-day, treats every metric as both engagement and civic, and has a "For You" design ready to defend.

```
┌──────────────────────────────────────────────────────────────────┐
│                       X / TWITTER HIRING FUNNEL                  │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (40%) ──► Coding Screen (30%) ──► Onsite    │
│                                                                  │
│  Onsite ──► Coding ×2 / Design / ML / Values ──► Tech Bar       │
│          (25%)                                  Review (55%)    │
│                                                                  │
│  Committee ──► Offer (L5 vs L6 split) ──► SF team match          │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, level | 30 min | ~40% advance |
| 2. **Coding screen** | 2 LeetCode mediums/hards (sometimes via HackerRank OA) | 60-90 min | ~30% advance |
| 3. **Onsite (4-5 rounds)** | 2 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Bar raiser + cross-team | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Twitter/X's loop is one of the most rigorous in consumer ML. Since the 2022 acquisition, the team has shrunk but the bar remained high, and the "rapid iteration under chaos" culture is unique. The ML surface spans timeline ranking (the "For You" feed), search, ads, and a significant T&S surface. Grok integration is the 2026 frontier.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I built [X] for [Y], working on [recsys / search / ads]. Most recently I shipped [Z] which moved [metric]."
**Tip:** Be specific about scale — Twitter does billions of impressions per day.

### Q1.2: "Why Twitter/X?"
**Answer:** "Three reasons. First, the timeline ML is the textbook problem — real-time engagement prediction on a bipartite graph with adversarial content. Second, Grok is a unique chance to integrate LLM reasoning into a live social product. Third, I want to work on a platform where the cost of bad ML is civic — viral misinformation, election integrity. That's a responsibility I want."
**Tip:** Reference Grok, the "For You" feed, and X's real-time data advantage.

### Q1.3: "Location + comp"
**Answer:** SF primary. Some remote for senior. Be clear on willingness to relocate. Comp is high to retain talent post-acquisition.

## Stage 2: Coding screen (60-90 min, sometimes HackerRank OA)

### Q2.1: "Trapping rain water" or "Word ladder"
### Q2.2: "Design a hit counter for tweets" — sliding window, segment tree, or rolling buckets.

**Tip:** Twitter's screen is medium-hard. Practice graph + DP.

The coding screen is where most candidates fall off — X's bar is real, and a 60-90 min HackerRank or virtual whiteboard will absolutely include a hard LeetCode. From there, every onsite round is a recsys + adversarial-ML exam; the design round will land on For You timeline, the ML deep-dive on coordinated inauthentic behavior.

## Stage 3: Onsite (4-5 rounds, 1-2 days)

### Round 3.1: Coding (2 rounds)
**Q3.1.1:** "Median of two sorted arrays" or "Serialize/deserialize a tree."
**Q3.1.2:** "Design a real-time trending hashtags system." Count-min sketch, sliding window top-K, distributed across regions.
**Q3.1.3:** "Rate limiter" or "LRU cache" — Twitter classics.

### Round 3.2: System design
**Q3.2.1:** "Design the 'For You' timeline." Multi-stage retrieval (in-network, out-of-network, embedding ANN), heavy ranker (engagement prediction), re-ranking (diversity, freshness, anti-bad-content), pagination. Discuss real-time feedback (every impression is training data).
**Q3.2.2:** "Design Twitter/X search." Query understanding, candidate generation (BM25 + embeddings), ranking, recency boost, real-time indexing of new tweets.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through your favorite production ML system." End-to-end.
**Q3.3.2:** "How would you detect a coordinated inauthentic behavior network on X?"
**Answer:** "Graph features: account age, follower graph, posting time correlation, content similarity (text + image embeddings), IP/network signals. Cluster detection (community detection, embeddings + HDBSCAN). Anomaly detection on volume and timing. Human review for confirmation. Model: gradient-boosted + GNN on the follower graph."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you shipped a feature that failed." STAR — Twitter loves postmortem culture.
**Q3.4.2:** "Time you had to defend a technical decision." STAR.
**Q3.4.3:** "How would you improve the X timeline for journalists / creators?" — be specific.

The onsite is dense and the design round is the centerpiece — every interviewer will eventually probe your For You design. Expect the ML deep-dive to land on adversarial content (coordinated inauthentic behavior, bot detection, prompt injection). The behavioral round is a postmortem culture test, not a values vibe check.

## Stage 4: Hiring committee
Twitter's committee includes the hiring manager, a senior IC, and a "tech bar" representative. The bar for L5 (Senior) is "ship a 2-quarter ML project independently with good metrics." L6 (Staff) requires cross-team influence. L7 (Director) is rare. Post-acquisition, levels map to E5-E7 in SpaceX.

## Stage 5: Offer
Twitter/X comp is at or above FAANG. RSU refresher is performance-based. Negotiation is real — they will move on base and equity. Relocation to SF is well-funded. Team match is usually pre-onsite for some roles.

## Tips for the Twitter/X loop
1. **Real-time ML is a core competency** — every impression is data.
2. **Grok integration is a 2026 theme** — know what it is and the technical challenges.
3. **Civic / misinformation ML is part of the surface** — be ready to discuss.
4. **Coding is medium-hard** — graph BFS, DP, sliding windows.
5. **Adversarial thinking matters** — bots, coordinated behavior, prompt injection.
6. **Reference 2026 X products** — Communities, audio/video, payments.
7. **Be ready to defend metrics choices** — engagement is not the only one; civic health matters.

## Real candidate report
> "Loop was 5 rounds. The For You feed system design was the core — they wanted me to talk about in-network vs out-of-network candidate generation, embedding retrieval, and how you balance engagement with anti-echo-chamber signals. The ML deep-dive was on coordinated inauthentic behavior detection. Got an L5 offer at $380K base + $1M RSU/4yr. They negotiated up by $80K when I had a Meta offer." — Blind, 2025

## Sources
- [X Engineering Blog](https://blog.x.com/engineering/)
- [X Research](https://x.ai/)
- [Levels.fyi Twitter](https://www.levels.fyi/companies/twitter)
- [Glassdoor Twitter interviews](https://www.glassdoor.com/Interview/Twitter-Interview-Questions-E100569.htm)
- [LeetCode Twitter tagged](https://leetcode.com/company/twitter/)

---

## The 1 thing to remember

At X, every impression is both engagement and civic signal — the L5+ candidate is the one who designs the For You feed as if a journalist and a foreign influence op are both reading it.
