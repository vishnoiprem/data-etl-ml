# 82. Uber (Marketplace SWE)

- **Role:** Senior Software Engineer (Marketplace / Rides)
- **Tech stack:** Go, Java, Python, Kotlin (Android), Swift (iOS), React, gRPC, Kafka, Flink, Cassandra, Schemaless, Hive, TensorFlow, PyTorch, Michelangelo
- **Comp band:** $180K-$550K (L3-L5a); Staff (L5b) $400K-$900K; L6 Director $700K-$1.5M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1.5-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, comp expectations | 30 min | ~50% advance |
| 2. **Coding phone screen** | 1 LeetCode medium-hard | 60 min | ~35% advance |
| 3. **Onsite (4-5 rounds)** | 2 coding, 1 system design, 1 ML/domain, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Bar raiser + cross-team review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, level, team match | 1 week | — |

Uber's loop is one of the most demanding in marketplace engineering. The bar is high on coding (real LeetCode hard), the system design is always marketplace-flavored (matching, dispatch, surge), and they test whether you understand real-time ML at scale (Flink, online learning).

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Walk me through your background"
**Answer:** Lead with scale and real-time. "I led the [X] team at [Company] handling 50M events/day, with sub-200ms p99 latency on a Flink pipeline. I shipped a [specific ML feature] that moved metric Y by Z%."
**Tip:** Uber cares deeply about scale and real-time. Quantify throughput and latency upfront.

### Q1.2: "Why Uber after [current FAANG]?"
**Answer:** "Uber is the only marketplace where supply and demand are both in motion, and the optimization runs per second. Real-time dispatch with stochastic demand is the problem I've been working toward. Michelangelo and the 2026 autonomous push tell me ML is first-class, not bolted on."
**Tip:** Reference specific Uber 2026 work (autonomous, AI customer support, Eats recsys).

### Q1.3: "Comp expectations and location"
**Answer:** Give a range with stock-heavy weighting; Uber RSU refresher is every 4 years. SF, Seattle, NYC, Sunnyvale are core; remote is limited.

## Stage 2: Coding phone screen (60 min)

### Q2.1: "Word search II (LeetCode 212)"
**Answer:**
```python
def findWords(board, words):
    trie = {}
    for w in words:
        node = trie
        for c in w:
            node = node.setdefault(c, {})
        node['$'] = w
    res, rows, cols = [], len(board), len(board[0])
    def dfs(r, c, node):
        c_char = board[r][c]
        if c_char not in node: return
        nxt = node[c_char]
        if '$' in nxt:
            res.append(nxt['$'])
            del nxt['$']  # dedupe
        board[r][c] = '#'
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] in nxt:
                dfs(nr, nc, nxt)
        board[r][c] = c_char
    for r in range(rows):
        for c in range(cols):
            if board[r][c] in trie:
                dfs(r, c, trie)
    return res
```
**Tip:** Uber does ask trie problems. Practice them.

### Q2.2: "LRU cache" or "Design a rate limiter" — both common.

### Q2.3: ML — "How would you predict ETAs more accurately?"
**Answer:** "Two components: (1) route-level base ETA from a graph neural network on the road graph with historical speeds. (2) Real-time adjustment layer: a gradient-boosted model on live features (traffic, weather, time of day, day of week) with online learning from actual trip durations. Loss: pinball loss for quantiles (p50/p80/p95) since the cost of being late is asymmetric."
**Tip:** Pinball loss + quantiles is the answer for any ETA/travel-time question. Mention online learning explicitly.

## Stage 3: Onsite (4-5 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "Merge k sorted lists" or "Median of two sorted arrays" (hard, real).
**Q3.1.2:** "Design a parking lot / elevator system" (OOD).
**Q3.1.3:** "Given a stream of driver locations, find the k nearest to a rider." Use a kd-tree or ball tree.

### Round 3.2: System design
**Q3.2.1:** "Design Uber's dispatch system." Cover: rider request → nearest driver search (H3 geo-index, ring search) → driver offer (real-time pub/sub) → acceptance → trip start. Discuss surge pricing as a feedback loop, supply/demand heatmaps, batching for airport pickups.
**Q3.2.2:** "Design Uber Eats restaurant ranking." Two-tower retrieval, ranking, promotion rules, A/B test infra, food ETA model.

### Round 3.3: ML / domain
**Q3.3.1:** "How do you detect fraud in real-time at Uber's scale?" Feature store (Cassandra + Redis), model on feature embeddings, <50ms inference, risk score → action (allow / review / block), feedback loop from chargebacks.
**Q3.3.2:** "Surge pricing — how do you avoid wild oscillations?" PID controller, smoothing, hysteresis, demand prediction (10-min ahead), caps and floors, fairness constraints.

### Round 3.4: Behavioral
**Q3.4.1:** "Tell me about a production incident you led." STAR — Uber does this every loop, postmortem culture.
**Q3.4.2:** "Disagreement with PM on scope." STAR.
**Q3.4.3:** "Why Uber over a smaller marketplace startup?"

## Stage 4: Hiring committee
Uber uses a "bar raiser" model inspired by Amazon. A senior engineer outside your target team reviews your packet and can veto below-bar hires. Level calibration is cross-org. L5a vs L5b is determined here — L5b staff requires system design that affects multiple teams.

## Stage 5: Offer
Base + RSU refresher every 4 years is the unique perk. RSUs vest annually after year 1. No-sign-on is common but relocation is strong. Team match is pre-onsite for some roles. Negotiation: know your level (L4 vs L5a is a $200K+ swing).

## Tips for the Uber loop
1. **Practice trie, segment tree, and graph problems** — they appear disproportionately.
2. **Real-time systems fluency is table stakes** — pub/sub, exactly-once, backpressure.
3. **Quantify scale in your stories** — "X million QPS", "Y ms p99".
4. **Know Flink and Kafka deeply** — they ask about state management, checkpoints, exactly-once.
5. **Surge / dispatch questions recur** — prepare the PID controller / hysteresis answer.
6. **Pinball loss for any quantile / ETA question** — instant credibility.
7. **Read Uber's engineering blog** — Michelangelo, H3 geo-index, and real-time trip pipeline.

## Real candidate report
> "I went through 4 rounds in one day. The dispatch design was the heart of it — they wanted me to talk about H3 hexagons, ring search, and how you'd handle 10M drivers with sub-second matching. I got L5a at $350K base + 60K RSUs/yr. They were clear about L5a vs L5b — they said L5b needs 'org-wide influence' which I didn't demonstrate." — Blind post, 2025

## Sources
- [Uber Engineering Blog](https://www.uber.com/blog/engineering/)
- [H3: Uber's Hexagonal Hierarchical Spatial Index](https://h3geo.org/)
- [Levels.fyi Uber](https://www.levels.fyi/companies/uber)
- [Glassdoor Uber interviews](https://www.glassdoor.com/Interview/Uber-Interview-Questions-E575263.htm)
- [LeetCode Uber tagged](https://leetcode.com/company/uber/)
