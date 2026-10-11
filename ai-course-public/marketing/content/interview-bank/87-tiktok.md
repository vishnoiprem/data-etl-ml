# 87. TikTok (ML / Recsys)

- **Role:** ML Engineer (Recommendation, Ranking, Search, T&S)
- **Tech stack:** Python, C++, Go, PyTorch, TensorFlow, Flink, Kafka, ClickHouse, Kubernetes, Monolith (TikTok's ML serving), ByteDance's Volcano
- **Comp band:** $250K-$700K total comp (L3-L6); L7 (Staff) $500K-$1.2M total comp; L8 Director $800K-$1.8M total comp (Levels.fyi 2026) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~0.8-1.5%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a For You feed with multi-modal embeddings — video frames, audio waveform, hashtag vectors — fanning into a ranking tower). Color: TikTok pink/cyan/black. Headline: "TikTok / AI ML Engineer / 2026".

> **TL;DR:** TikTok's loop is the most demanding recsys + LeetCode-hard combination in consumer — they expect DIN/DIEN fluency, multi-modal embedding knowledge, and the ability to derive contrastive losses on a whiteboard. The winning candidate quantifies everything in QPS, treats online learning as default, and ships a TikTok-feature critique unprompted.

```
┌──────────────────────────────────────────────────────────────────┐
│                       TIKTOK HIRING FUNNEL                        │
├──────────────────────────────────────────────────────────────────┤
│  Apply ──► Recruiter (40%) ──► Online Assessment (40%) ──► Phone │
│                                                                  │
│  Phone ──► Onsite (4-5 rounds) ──► Bar Raiser Committee         │
│         (30%)                              (50%, can veto)      │
│                                                                  │
│  Committee ──► Offer (L6 vs L7 split) ──► Team match (30 days)  │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, level | 30 min | ~40% advance |
| 2. **Online assessment (OA)** | 2-3 coding problems | 90 min | ~40% advance |
| 3. **Technical phone screen** | 1 coding + 1 ML | 60 min | ~30% advance |
| 4. **Onsite (4-5 rounds)** | 2 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1-2 days | ~20% advance |
| 5. **Hiring committee** | Bar raiser + cross-team | 1-2 weeks | ~50% advance |
| 6. **Offer** | Comp + level | 1 week | — |

TikTok/ByteDance has the most demanding ML interview loop of any consumer company. The bar is genuinely FAANG-tier plus recsys depth, plus a coding bar that often reaches LeetCode hard. The flip side: comp is among the highest in industry, especially for senior+.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** Lead with scale and recsys depth. "I built a real-time recsys at [Company] handling 50M QPS, with a two-tower model and online learning from engagement signals."
**Tip:** TikTok is obsessed with scale. Quantify.

### Q1.2: "Why TikTok?"
**Answer:** "Three reasons. First, the For You Page is the state-of-the-art in recsys — the engineering here is unmatched. Second, I want to work on real-time multi-modal recommendation across video, audio, text, and interactions. Third, ByteDance's investment in generative AI (Doubao / Seed) means frontier models are first-class."
**Tip:** Reference specific 2026 work: multi-modal embeddings, generative search, video understanding, AI effects.

### Q1.3: "Location, visa, comp"
**Answer:** TikTok has major offices in Mountain View, San Jose, Seattle, NYC, and Singapore. Remote is rare for ML. Be clear on visa needs.

## Stage 2: Online Assessment (90 min, on HackerRank/CodeSignal)

### Q2.1: "Valid parentheses + DP variant" — 30 min
### Q2.2: "Tree traversal + path sum" — 30 min
### Q2.3: "Math/greedy/array problem" — 30 min

**Tip:** Practice LeetCode mediums in 30-min windows. The OA is the first filter — many candidates don't make it past.

The online assessment is where most candidates fall off — TikTok's bar is real, and the phone screen confirms you can survive a LeetCode hard under time pressure. From there, every conversation is a recsys depth test: DIN, DIEN, multi-modal embeddings, online learning.

## Stage 3: Technical phone screen (60 min)

### Q3.1: Coding — "LRU cache" (LeetCode 146)
**Answer:**
```python
from collections import OrderedDict
class LRUCache(OrderedDict):
    def __init__(self, capacity):
        self.capacity = capacity
    def get(self, key):
        if key not in self: return -1
        self.move_to_end(key)
        return self[key]
    def put(self, key, value):
        if key in self: self.move_to_end(key)
        self[key] = value
        if len(self) > self.capacity:
            self.popitem(last=False)
```
**Tip:** LeetCode medium-hard. Know this cold.

### Q3.2: ML — "How does TikTok's For You Page work?"
**Answer:** "Multi-stage. (1) Candidate generation: collaborative filtering (item-to-item, two-tower) + content-based (multi-modal embeddings from video, audio, text, hashtags). (2) Light ranker: gradient-boosted on (user-video, context, historical engagement). (3) Heavy ranker: deep model with cross-features (DIN-style attention over user history). (4) Re-ranking: diversity, freshness, anti-echo-chamber. Online learning from every interaction. Bandits for exploration. Cold start: content features + small-batch seeding + trend signals."
**Tip:** Be very specific. TikTok expects DIN/DIEN knowledge, multi-modal embeddings, online learning, bandits.

## Stage 4: Onsite (4-5 rounds, 1-2 days)

### Round 4.1: Coding (2 rounds)
**Q4.1.1:** "Longest substring without repeating characters" or "Word break II" or graph BFS.
**Q4.1.2:** "Design a system to count top-K hashtags in a stream." Count-min sketch + heap.
**Q4.1.3:** "Order statistic tree / segment tree" — TikTok loves these.

### Round 4.2: System design
**Q4.2.1:** "Design TikTok's video upload + encoding pipeline." Cover transcoding (multiple bitrates), storage, CDN, ML-based thumbnail selection.
**Q4.2.2:** "Design TikTok Search." Multi-modal query understanding, candidate generation, ranking, autocomplete, trending.

### Round 4.3: ML deep-dive
**Q4.3.1:** "Walk me through a recsys you've built end-to-end." Be specific.
**Q4.3.2:** "How do you detect duplicate / near-duplicate videos?"
**Answer:** "Multi-stage: perceptual hash (pHash) for exact/near duplicates, video embedding (CNN or ViT) for visual similarity, audio fingerprinting for sound reuse, time-sync alignment. Combine scores; threshold for copyright/dupe flag."

### Round 4.4: Behavioral
**Q4.4.1:** "Time you had to ship fast under pressure." STAR.
**Q4.4.2:** "Time you disagreed with a senior engineer." STAR.
**Q4.4.3:** "What's your favorite TikTok feature and how would you improve it?" — be specific, shows product depth.

The onsite is 4-5 rounds across 1-2 days, and the ML deep-dive is where TikTok separates staff from senior. Be ready to derive loss functions on the whiteboard and defend an online-learning architecture. The behavioral round specifically rewards product critique — bring a "favorite feature I'd improve" answer.

## Stage 5: Hiring committee
TikTok has a serious bar-raiser process. The committee is cross-org, includes a senior leader outside the team, and is empowered to reject below-bar candidates. Level calibration is strict — L5 vs L6 is decided here, often after debate. Staff (L7) is rare and requires a separate committee.

## Stage 6: Offer
TikTok comp is top of market. Base is strong, RSU is generous. They will negotiate. Signing bonus is common. Relocation is well-funded. Team match is pre-onsite for some roles. Post-offer you can sometimes swap teams within 30 days.

## Tips for the TikTok loop
1. **Practice LeetCode hard, not just medium** — TikTok's coding bar is real.
2. **Know DIN, DIEN, multi-modal embeddings** — these are the recsys classics they test.
3. **Quantify scale in every story** — "I optimized a model serving at 10M QPS to 5M QPS with no quality loss."
4. **Multi-modal ML is a strength** — if you've worked with video/audio/text, mention it.
5. **Online learning and bandits** — show you understand real-time feedback.
6. **Reference 2026 TikTok products** — generative search, AI effects, Doubao.
7. **Practice the OA** — many strong candidates fail at this stage.

## Real candidate report
> "I went through the full loop. Two coding rounds (medium + hard), one system design on For You Page, one ML deep-dive on multi-modal embeddings, one behavioral. The ML deep-dive was the hardest — they asked me to derive the loss function for a contrastive multi-modal model on the whiteboard. Got an L6 offer at $420K base + $1.2M RSU/4yr. They negotiated up on equity when I had a competing FAANG offer." — Blind, 2025

## Sources
- [TikTok Engineering Blog](https://engineering.tiktok.com/)
- [ByteDance Research](https://www.bytedance.com/en/research)
- [Levels.fyi TikTok](https://www.levels.fyi/companies/tiktok)
- [Glassdoor TikTok interviews](https://www.glassdoor.com/Interview/TikTok-Interview-Questions-E2232956.htm)
- [LeetCode TikTok tagged](https://leetcode.com/company/tiktok/)

---

## The 1 thing to remember

At TikTok, online learning is the default and DIN/DIEN is the lingua franca — the L6+ candidate is the one who derives a contrastive loss on the whiteboard and quantifies scale in QPS, not millions of users.
