# 84. Discord (ML / Trust & Safety)

- **Role:** ML Engineer (Search, Trust & Safety, Recommendations)
- **Tech stack:** Python, Rust, Elixir, PyTorch, ScyllaDB, Cassandra, Redis, Kafka, Flink, Kubernetes, Triton
- **Comp band:** $220K-$600K (IC3-IC5); Staff (IC6) $500K-$1.1M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit | 30 min | ~45% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML fundamentals | 60 min | ~30% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1 day | ~25% advance |
| 4. **Hiring committee** | Bar-raiser + IC review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Discord's ML org is unique: most of their user-generated content is text (chat), but the scale is massive (billions of messages/day). Trust & Safety is a top priority given their younger user base. Search and Discovery is the other major ML surface. Discord leans heavily on Elixir for real-time services, which is rare and a sign of how they think about stateful realtime.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML work"
**Answer:** "I built [X] for [Y] — production ML serving at [scale]. Most recently I worked on [specific T&S or recsys problem]."
**Tip:** Be specific about scale. Discord handles billions of messages, so "I worked on a model" without scale context lands flat.

### Q1.2: "Why Discord?"
**Answer:** "Three reasons. First, it's real-time — most ML is async, but Discord is 'what to show this user in the next 200ms.' Second, T&S stakes are unusually high because the user base skews young. Third, Discord's investment in AI features (Clyde, AI companions, server summaries) signals real leadership commitment. I want my ML to directly protect people, not just optimize ad clicks."
**Tip:** Reference Clyde, AI server summaries, voice/avatar generation from 2025-2026.

### Q1.3: "Location + remote"
**Answer:** Discord is SF/remote-US. Remote is genuine and well-supported. International is harder.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Design a rate limiter (token bucket)"
**Answer:**
```python
import time
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.time()
    def allow(self):
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```
**Tip:** Discord asks this directly because they rate-limit everything.

### Q2.2: ML — "How would you detect grooming / predatory behavior in DMs?"
**Answer:** "Multi-signal: (1) Message classifier on text — fine-tuned classifier for grooming patterns (solicitation, age-inappropriate content, isolation tactics). (2) Graph features — new account, low friend count, DM pattern across many servers. (3) Behavioral anomalies — late-night messaging, rapid escalation. Score per DM thread, escalate high-risk threads to a human moderation queue. Important: false positive cost is high (cutting off legitimate teen friendships), so use high precision and human-in-the-loop."
**Tip:** Show you understand the asymmetry of T&S errors. Precision-first with human review.

### Q2.3: System design — "How would you build server discovery search?"
**Answer:** "Indexing: ingest server metadata + recent message embeddings (sentence-transformers) into Elasticsearch + a vector index (FAISS or ScaNN). Query: user query → BM25 + embedding ANN → blend. Ranking: gradient-boosted on (text relevance, server size, member overlap with user, recency, server health metrics). A/B test ranking changes via interleaving."
**Tip:** Mention server health / moderation history as a feature — it shows T&S thinking.

## Stage 3: Onsite (4 rounds, 1 day)

### Round 3.1: Coding
**Q3.1.1:** "Implement an LRU cache" — classic.
**Q3.1.2:** "Given a stream of message events, find the median at any time." Two heaps.
**Q3.1.3:** "Build a trie with autocomplete." Standard.

### Round 3.2: System design
**Q3.2.1:** "Design Discord's notification system." Real-time push (mobile + desktop), per-user prefs, quiet hours, batching, ML-driven prioritization (which notifications are most likely to be opened).
**Q3.2.2:** "Design NSFW image detection at scale." Image classifier (CLIP or EfficientNet variant), optimized inference, multi-tier escalation, false positive review, model updates with feedback loop.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through your favorite end-to-end ML system you've shipped."
**Answer:** Pick a real one. Cover data, features, training, serving, eval, monitoring, iteration.
**Q3.3.2:** "How do you detect spam/invite-spam in servers?"
**Answer:** "Graph features (account age, mutual connections, message velocity), text classifier (URL classifier, similar-spam cosine), community-feedback signals (reports, mutes). Real-time score per message. Threshold tuning, fast feedback loop from human mods."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you made a high-stakes decision with incomplete info." STAR.
**Q3.4.2:** "How do you balance user privacy with safety?" — philosophical but real at Discord. Reference end-to-end encryption, data minimization, on-device processing where possible.
**Q3.4.3:** "Why trust & safety vs ads/recsys?" — be genuine.

## Stage 4: Hiring committee
Discord uses IC-level calibration. The bar is high for IC5 (senior) — they want someone who can scope a multi-quarter ML project independently. IC6 (staff) is a separate bar. The committee includes a "values fit" check, which is heavier at Discord than at most companies (they have a strong culture of empathy for users).

## Stage 5: Offer
Discord is fully remote-US with strong base salary. Equity is competitive (vested over 4 years, 1-year cliff). Negotiation: they don't move much on base but will move on equity for strong candidates.

## Tips for the Discord loop
1. **Real-time systems fluency is mandatory** — WebSockets, presence, pub/sub.
2. **T&S asymmetry** — they test whether you understand precision/recall tradeoffs in moderation.
3. **Don't be precious about false positives** — show you've thought about the cost of removing a real friendship.
4. **Mention user safety unprompted** — "how does this affect vulnerable users?"
5. **Rust and Elixir are differentiators** — if you know them, mention it.
6. **Coding is moderate LeetCode, not hard** — focus on edge cases and clean code.
7. **AI features are happening fast** — Clyde, AI server summaries, voice generation. Be ready to discuss.

## Real candidate report
> "I interviewed for Trust & Safety ML. The T&S round asked me to design a grooming detector and they pushed back hard — 'what if two 17-year-olds are flirting, is that grooming?' I had to be specific about thresholds, human review, and the difference between suspicious patterns and normal teen behavior. They were very thoughtful about the social cost of false positives. Offer: IC5 at $400K base + $700K RSU/4yr, fully remote." — Blind, 2025

## Sources
- [Discord Engineering Blog](https://discord.com/blog/engineering)
- [Discord Trust & Safety](https://discord.com/safety)
- [Levels.fyi Discord](https://www.levels.fyi/companies/discord)
- [Glassdoor Discord interviews](https://www.glassdoor.com/Interview/Discord-Interview-Questions-E950851.htm)
- [LeetCode Discord tagged](https://leetcode.com/company/discord/)
