# 91. LinkedIn (ML / Feed)

- **Role:** ML Engineer (Feed, Search, Ads, Hiring, Recsys)
- **Tech stack:** Java, Scala, Python, C++, PyTorch, TensorFlow, Kafka, Pinot, Voldemort (custom KV), Espresso, Spark
- **Comp band:** $200K-$550K (IC3-IC5); Staff (IC6) $400K-$1M; Director (IC7) $700K-$1.4M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML | 60 min | ~35% advance |
| 3. **Onsite (4-5 rounds)** | 1-2 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Cross-org review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level | 1 week | — |

LinkedIn's ML org is large and well-organized. The unique surface is professional — feed posts, recruiter search, job recommendations, premium subscriptions, ads. The bar is FAANG-equivalent but the loop is slightly more structured and predictable. Sunnyvale and SF are the main sites.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I built [X] for [Y]. Most recently I shipped [Z] which moved [metric]."
**Tip:** Be specific about business impact — LinkedIn is metric-driven.

### Q1.2: "Why LinkedIn?"
**Answer:** "Three reasons. First, the professional graph is the most interesting ML substrate I know of — every interaction has economic intent (job, hire, sell, learn). Second, LinkedIn's investment in AI (Premium AI, Recruiter AI, AI-assisted profiles) is real and growing. Third, I want my ML to help people get hired or grow careers. That's mission-aligned work for me."
**Tip:** Reference 2026 LinkedIn AI: Premium AI, Recruiter AI, AI-assisted profiles, collaborative articles.

### Q1.3: "Location + comp"
**Answer:** Sunnyvale, SF primary. Some remote-US. Be clear on willingness to relocate. Comp is solid for Bay Area.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Merge intervals + scheduling"
**Answer:**
```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])
    res = []
    for s, e in intervals:
        if res and s <= res[-1][1]:
            res[-1][1] = max(res[-1][1], e)
        else:
            res.append([s, e])
    return res
```
**Tip:** LinkedIn's phone screen is medium LeetCode. They focus on clean code.

### Q2.2: ML — "How would you build a job recommendation system?"
**Answer:** "Two-sided: candidate side (skills, experience, location, salary) and job side (requirements, company, role). Retrieval: collaborative filtering on user-job interaction matrix + content-based (job embeddings from description, candidate embeddings from profile). Ranking: gradient-boosted on (user-job fit, location distance, recency, application likelihood). Cold start: content features + popularity priors. Diversity: don't show 5 backend roles in a row — mix seniority and function."
**Tip:** Two-sided matching is the LinkedIn way. Show you understand both sides.

### Q2.3: System design — "Design LinkedIn feed ranking"
**Answer:** "Multi-stage: candidate generation (network, followed, content-based) → light ranker (engagement prediction) → heavy ranker (deep model, cross-features) → re-ranking (diversity, freshness, professional-relevance). On-platform feedback (likes, comments, shares, dwells). Anti-spam: classifier on text + image. Time-decay: recent posts get a boost. For You + Following toggle (different ranking per surface)."

## Stage 3: Onsite (4-5 rounds, 1-2 days)

### Round 3.1: Coding (1-2 rounds)
**Q3.1.1:** "LRU cache" or "LFU cache."
**Q3.1.2:** "Find K-th largest in a stream." Min-heap of size K.
**Q3.1.3:** "Design a connection degree calculator in a graph." BFS.

### Round 3.2: System design
**Q3.2.1:** "Design LinkedIn Recruiter search." Query understanding (skills, location, experience), candidate generation (boolean + embedding ANN), ranking (match score, response likelihood), pagination, recruiter behavior feedback.
**Q3.2.2:** "Design LinkedIn Ads targeting." Audience selection, ML-based bid optimization, real-time CTR/CVR prediction, budget pacing, A/B testing.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through your favorite end-to-end ML system." Be specific.
**Q3.3.2:** "How would you detect professional spam / scams on LinkedIn?"
**Answer:** "Text classifier (job scam patterns, 'make $X from home'), behavior features (new account, high message volume, profile incompleteness), image classifier (stock photos, stolen profile pics), network features (cluster of accounts that DM each other only). Combined score, threshold for takedown, human review queue."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you had to convince a stakeholder with data." STAR.
**Q3.4.2:** "Time you improved a system by 10%+ in 2 months." STAR.
**Q3.4.3:** "How do you balance 'engagement' with 'professional value'?" — LinkedIn is explicit about this tradeoff.

## Stage 4: Hiring committee
LinkedIn's committee is structured and multi-level. The bar for IC5 (Senior) is "ship a 2-3 quarter ML project with measurable business impact." IC6 (Staff) requires influence on the ML platform or org-wide direction. LinkedIn is more methodical than FAANG — expect 1-2 weeks for committee.

## Stage 5: Offer
LinkedIn comp is competitive with Bay Area but slightly below top FAANG. RSU is 4-year vest with annual refresh. They negotiate on equity, less so on base. Relocation is well-funded. Team match is usually post-onsite.

## Tips for the LinkedIn loop
1. **Two-sided marketplace thinking** — candidate vs job, recruiter vs candidate, author vs reader.
2. **Economic intent is the differentiator** — every interaction has a job/hire/sell angle.
3. **AI-assisted features are 2026 hot** — Premium AI, Recruiter AI, AI profiles.
4. **Coding is medium LeetCode** — focus on clean, readable code.
5. **Business metrics matter** — Premium subscriptions, recruiter seats, ad revenue.
6. **Reference LinkedIn engineering blog** — they publish heavily on AI, search, recommendations.
7. **Have a LinkedIn opinion** — what's broken about job recommendations? Show product depth.

## Real candidate report
> "I interviewed for ML on the Feed team. The system design was on feed ranking and they pushed on 'engagement vs professional value' — I had to defend why showing a controversial post might hurt long-term user trust. The ML deep-dive was on cold-start for new users. Got an IC5 offer at $340K base + $700K RSU/4yr. They moved base by $20K and equity by $100K on negotiation." — Blind, 2025

## Sources
- [LinkedIn Engineering Blog](https://engineering.linkedin.com/blog)
- [LinkedIn AI Blog](https://www.linkedin.com/blog/topic/ai)
- [Levels.fyi LinkedIn](https://www.levels.fyi/companies/linkedin)
- [Glassdoor LinkedIn interviews](https://www.glassdoor.com/Interview/LinkedIn-Interview-Questions-E34865.htm)
- [LeetCode LinkedIn tagged](https://leetcode.com/company/linkedin/)
