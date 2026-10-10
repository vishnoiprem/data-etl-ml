# 83. Reddit (ML / Search)

- **Role:** ML Engineer (Search, Ranking, Ads)
- **Tech stack:** Python, Go, Scala, PyTorch, TensorFlow, Cassandra, Postgres, Kafka, Flink, Spark, Kubernetes, BERT, LLama fine-tunes
- **Comp band:** $200K-$500K (L3-L5); Staff $400K-$900K; L6 Director $700K-$1.4M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, comp, fit | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML | 60 min | ~35% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Bar raiser review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Reddit's ML org is split between Search (post/comment ranking), Feeds (home feed), Ads (ad ranking), and Trust & Safety (spam, ban evasion, NSFW). Since the IPO in 2024, hiring bar rose significantly. Most loops for senior roles are 4 rounds in 1 day.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I spent 4 years at [Company] building recsys for [X], shipping a two-tower model that improved engagement by 12%. I owned the offline-to-online eval pipeline and the feature store. Most recently I've been doing LLM fine-tuning for [Y use case]."
**Tip:** Reddit is community-obsessed. Reference the human element of recommendations.

### Q1.2: "Why Reddit?"
**Answer:** "Three things. First, Reddit's data is uniquely rich — long-form text, votes, community structure, all publicly available, which makes the ML problem fundamentally different from short-form social. Second, Reddit Answers and the AI search launch signal real ML investment from leadership. Third, I want to work on ranking where the cost of a bad recommendation is a community you destroy — that responsibility appeals to me."
**Tip:** Reference Reddit's 2026 AI products (Reddit Answers, AI-powered search, community summaries).

### Q1.3: "Comp + remote"
**Answer:** Reddit is mostly SF/NYC onsite (3 days/week) for senior roles. Fully-remote is rare. Be clear on your floor and target.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Word break (LeetCode 139)"
**Answer:**
```python
def wordBreak(s, wordDict):
    word_set = set(wordDict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]
```
**Tip:** Reddit's phone screen is medium LeetCode. Practice DP and graph problems.

### Q2.2: ML — "How would you rank posts in r/programming?"
**Answer:** "Multi-stage: (1) Candidate generation — last 1000 posts in subreddit, eligible (not removed, not nsfw, age < 24h). (2) Light ranker — gradient-boosted on simple features (upvote rate, comment count, author karma, subreddit subscription). (3) Heavy ranker — fine-tuned LLM or two-tower model on user-post interaction history. (4) Diversity reranker — penalize multiple posts from same domain. Diversity matters a LOT on Reddit — the upvote ranking alone is a popularity trap."
**Tip:** Reddit explicitly tests for diversity / echo-chamber awareness.

### Q2.3: System design — "Design a comment ranking system"
**Answer:** "Sort by 'best' = Wilson score lower bound on upvote ratio * thread depth penalty * author credibility. Recursive structure — comments ranked independently within their parent. Use materialized paths for fast lookup. Anti-gaming: detect coordinated upvoting via cluster analysis on user-vote graph."
**Tip:** Wilson score is the canonical Reddit answer. They love it when you know it.

## Stage 3: Onsite (4 rounds, 1 day)

### Round 3.1: Coding
**Q3.1.1:** "Top K frequent elements" (LeetCode 347) — heap or quickselect.
**Q3.1.2:** "Design a data structure for a vote counter with O(1) getTopK()."
**Q3.1.3:** "Serialize/deserialize a tree of comments" — preorder + null markers.

### Round 3.2: System design
**Q3.2.1:** "Design Reddit's home feed." Multi-stage retrieval → ranking → re-ranking → diversity → pagination. Discuss cold start, recency vs relevance, per-user interest modeling.
**Q3.2.2:** "Design subreddit search." Query understanding, subreddit retrieval (BM25 + embedding), post retrieval within subreddit, ranking. Handle typos, abbreviations ("aita" → "Am I the A**hole").

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through how you'd detect ban evasion."
**Answer:** Graph features (IPs, device fingerprints, writing style embeddings), supervised model on confirmed evaders, threshold tuning to balance false positives vs negatives, human review queue.
**Q3.3.2:** "How do you A/B test a ranking change on Reddit?"
**Answer:** "Hashed user bucketing, primary metric (time-on-site, comments/post), guardrails (unsubscribe rate, mod actions), interleaving for ranking quality. Counterfactual eval via replay. Run for 2+ weeks to capture day-of-week effects."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you had to ship without consensus." STAR.
**Q3.4.2:** "Time you made a model more fair / less biased." STAR.
**Q3.4.3:** "What subreddit would you build an ML feature for?" — fun question, be specific.

## Stage 4: Hiring committee
Reddit's committee is a 4-5 person panel that includes a bar-raiser and the hiring manager. They score on a rubric (1-4) per round; the bar for senior is "3+" on all rounds. L5 (Senior) vs L4 (Mid) is decided here based on scope of past work.

## Stage 5: Offer
Reddit's offers are competitive with the Bay Area market. RSU refresher is annual with performance multiplier. Signing bonus is negotiable. Team match happens after offer.

## Tips for the Reddit loop
1. **Read the Reddit engineering blog** — especially "How Reddit ranks" and search posts.
2. **Wilson score confidence interval** — classic ranking interview answer, learn it.
3. **Diversity in ranking is a first-class concern** — mention it unprompted.
4. **Community-aware metrics** — don't just say "engagement", talk about healthy communities.
5. **Coding is medium LeetCode, not hard** — focus on clean, readable code.
6. **Mention interest in AI search / Reddit Answers** — shows you've kept up.
7. **Have an opinion on a Reddit ML problem** — "I'd rank controversial posts lower by default to reduce pile-ons" shows depth.

## Real candidate report
> "I interviewed for Search ML. The system design was Reddit's home feed and they pushed hard on the diversity reranker — I initially proposed pure engagement ranking and they asked 'but what about the echo chamber problem?' which I should have preempted. Offer came back as L4 at $290K + $400K RSU/4yr. They were firm on level. Negotiation moved base by $20K but not level." — Reddit r/MachineLearning, 2025

## Sources
- [Reddit Engineering Blog](https://www.reddit.com/r/RedditEng/)
- [Wilson score on Reddit (downrank early votes)](https://www.reddit.com/r/woahdude/comments/1ampd6/the_new_sorting_algorithm_explained/)
- [Levels.fyi Reddit](https://www.levels.fyi/companies/reddit)
- [Glassdoor Reddit interviews](https://www.glassdoor.com/Interview/Reddit-Interview-Questions-E229616.htm)
- [LeetCode Reddit tagged](https://leetcode.com/company/reddit/)
