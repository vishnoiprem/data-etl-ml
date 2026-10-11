# 86. Spotify (ML / Recsys)

- **Role:** ML Engineer (Personalization, Search, Content, Audio)
- **Tech stack:** Python, Java, Scala, PyTorch, TensorFlow, BigQuery, Cassandra, Kafka, Flink, Kubernetes, TensorFlow Extended (TFX)
- **Comp band:** $200K-$500K total comp (L4-L6); Staff $400K-$1M total comp; Director $700K-$1.4M total comp (Levels.fyi 2026, Stockholm premium ~20% lower) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1-2%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a Discover Weekly playlist with audio-embedding waveform and a bandit-arm diagram). Color: Spotify green (#1DB954). Headline: "Spotify / AI ML Engineer / 2026".

> **TL;DR:** Spotify's loop is recsys-heavy — collaborative filtering, contextual bandits, audio embeddings, and cold start for new artists are all in play, and the design round will absolutely push you on long-tail and popularity-bias. The winning candidate is fluent in bandits, has shipped real-time personalization, and treats user joy as a first-class metric.

```
┌──────────────────────────────────────────────────────────────────┐
│                       SPOTIFY HIRING FUNNEL                       │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (50%) ──► Tech Phone (35%) ──► Onsite       │
│                                                                  │
│  Onsite ──► Coding / Design / ML / Values ──► Bandit-Culture     │
│          (25%)                                  Review (60%)    │
│                                                                  │
│  Committee ──► Offer (L6 vs L7 split) ──► Stockholm/NYC match    │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, fit, location | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML | 60 min | ~35% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral + values | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Cross-org review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, level, team match | 1 week | — |

Spotify's ML org is one of the most respected in industry for recommender systems (their "Discover Weekly", "Release Radar", and now "AI DJ" are classics). The loop tests both recsys fundamentals (cold start, exploration, multi-armed bandits) and engineering quality. Stockholm and NYC are the main sites.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your recsys work"
**Answer:** "I built [X] for [Y], increasing [metric] by Z%. Most interestingly, I had to handle [specific challenge: cold start / diversity / long-tail]."
**Tip:** Spotify values long-tail / diversity thinking. Reference the cold-start problem explicitly.

### Q1.2: "Why Spotify?"
**Answer:** "Three reasons. First, the recsys problem here is legendary — Discover Weekly is the gold standard. Second, AI DJ and AI Playlist show real ML product investment. Third, I want to work at a company where ML directly serves user joy, not just ad revenue. That mission alignment matters to me."
**Tip:** Reference Spotify's 2026 AI features: AI DJ, AI Playlist, voice translation for podcasts.

### Q1.3: "Location + remote"
**Answer:** Stockholm, NYC, Boston, SF are core sites. Remote is limited but they have a "Flex" policy for partial remote. Be clear on willingness to relocate to Stockholm for senior roles.

Spotify's recruiter screen rewards candidates who speak diversity and long-tail. The phone screen is where they confirm you can actually build a recsys — collaborative filtering, audio embeddings, and bandit-based cold start are the moves they're listening for.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Two Sum + variants"
**Answer:**
```python
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
```
**Tip:** Spotify's phone screen is medium LeetCode. They've started including "code review" style questions.

### Q2.2: ML — "How would you build a 'Discover Weekly'-like playlist?"
**Answer:** "Three parts. (1) Candidate generation: collaborative filtering (matrix factorization or two-tower) on user-track listen matrix, plus content-based (audio embeddings from CNN, text embeddings from track metadata). (2) Ranking: gradient-boosted model on (user-track, context, listening history, time of day, device). (3) Slate optimization: optimize the 30-track sequence for session length + save rate + diversity. Cold start: use audio embeddings + nearest neighbors to bootstrap; explore via multi-armed bandits."
**Tip:** Mention audio embeddings specifically — Spotify uses CNNs on raw audio (VGGish, then transformer audio models).

### Q2.3: System design — "Design a real-time 'now playing' recommendation update"
**Answer:** "Stream listen events to Kafka. Flink job maintains per-user state (recent listens, mood inference). On every listen event, query a candidate generator (Redis cache + backend model) for next-track candidates. Rank by context model. Return <200ms. Learn from next-listen feedback (did user skip or complete?)."
**Tip:** Spotify loves real-time personalization. Show Flink/stateful-streaming fluency.

## Stage 3: Onsite (4 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "Merge intervals" (classic Spotify).
**Q3.1.2:** "Design a hit counter with 1-min, 5-min, hourly buckets."
**Q3.1.3:** "Serialize/deserialize a binary search tree." Practice, they ask.

### Round 3.2: System design
**Q3.2.1:** "Design Spotify's search system." Query understanding (artist vs song vs album vs playlist), BM25 + embedding ANN, ranking, autocomplete via prefix trie + ML. Discuss cold queries (new songs).
**Q3.2.2:** "Design a podcast recommendation system." Different from music — long-form, contextual, audience overlap with music, episode-level recsys.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through your favorite recsys you've shipped." Be specific about features, model, online gains.
**Q3.3.2:** "How do you handle the cold-start problem for new artists?"
**Answer:** "Content-based seeding (audio embeddings + text metadata + label similarity). Exploration: assign a fraction of impressions to new artists via bandit policy. Active learning: surface new artists to high-engagement users for fast signal. Use 'openness to discovery' as a user feature."

### Round 3.4: Behavioral + Values
**Q3.4.1:** "Spotify's values are 'Innovative, Passionate, Collaborative, Sincere, Playful.' Tell me a story for one." Pick a real one.
**Q3.4.2:** "Time you had to choose between user joy and business metric." STAR.

The onsite is where the recsys depth gets tested in conversation. The ML deep-dive is almost always Discover Weekly, cold start, or a bandit policy — prepare to defend your exploration rate and decay function. The values round tests whether "user joy" is something you actually optimize for.

## Stage 4: Hiring committee
Spotify's committee is a multi-level review with a strong values component (they take "bandit" culture seriously). Senior (L6) requires independent ML project ownership; Staff (L7) requires cross-team influence on the recsys platform. The bar is comparable to FAANG for L6+.

## Stage 5: Offer
Spotify comp is good but below FAANG for senior roles, especially in Stockholm. RSUs vest over 4 years. They are willing to negotiate on relocation packages. Team match is usually pre-onsite or within 2 weeks of offer.

## Tips for the Spotify loop
1. **Know recommender systems deeply** — collaborative filtering, content-based, hybrid, contextual bandits.
2. **Diversity / long-tail is a first-class concern** — popularity bias is the enemy.
3. **Audio understanding is a plus** — if you've worked with raw audio, mention it.
4. **Cold start is your friend** — Spotify asks this every loop, prepare 2-3 angles.
5. **Real-time personalization matters** — they love stateful streaming answers.
6. **AI DJ and AI Playlist are hot topics** — discuss voice/LLM product tradeoffs.
7. **Reference their engineering blog** — Discover Weekly, BaRT, audio CNN posts.

## Real candidate report
> "I interviewed for ML Engineer on Personalization. The ML deep-dive was on cold-start for new artists and they pushed hard on the bandit policy — I had to be specific about exploration rate, decay, and how to detect exploitation failures. Offer came back as L6 at $380K base + $650K RSU/4yr. Negotiation got me an extra $30K base. Stockholm was a real ask — they offered relocation." — Blind, 2025

## Sources
- [Spotify Research](https://research.atspotify.com/)
- [Spotify Engineering Blog](https://engineering.atspotify.com/)
- [Levels.fyi Spotify](https://www.levels.fyi/companies/spotify)
- [Glassdoor Spotify interviews](https://www.glassdoor.com/Interview/Spotify-Interview-Questions-E299551.htm)
- [LeetCode Spotify tagged](https://leetcode.com/company/spotify/)

---

## The 1 thing to remember

At Spotify, popularity bias is the enemy — the L6+ candidate is the one who designs for the long tail with audio embeddings and bandits, not just for tomorrow's hit.