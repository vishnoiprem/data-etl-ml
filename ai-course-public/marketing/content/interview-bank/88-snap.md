# 88. Snap (ML / Camera / AR)

- **Role:** ML Engineer (Camera, AR, Generative, Recsys, Ads)
- **Tech stack:** Python, C++, Objective-C/Swift, Java, PyTorch, TensorFlow, gRPC, Cassandra, Kafka, Kubernetes
- **Comp band:** $200K-$500K (L4-L5); L6 (Staff) $400K-$1M; L7 Director $700K-$1.4M (Levels.fyi 2026)
- **Cumulative pass rate:** ~1.5-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML | 60 min | ~35% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML deep-dive, 1 behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Cross-org review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level | 1 week | — |

Snap's ML org spans computer vision (Lenses, AR), generative AI (My AI, image generation), recsys (Stories, Spotlight), and ads ranking. The unique surface is camera-first ML — most of their ML models are run on-device or in real-time. The bar is FAANG-equivalent with a creative-product twist.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I built [X] for [Y], working on [specific surface — vision, recsys, ads]. Most recently I shipped [Z] which moved [metric]."
**Tip:** Be specific about your product surface. Snap cares about ML that ships to real users.

### Q1.2: "Why Snap?"
**Answer:** "Three reasons. First, camera-first ML is unique — most companies optimize feed scrolling, Snap optimizes what you see and create through the camera. Second, My AI and the 2026 generative AR features (Dress Up, Bitmoji generation) show real ML investment. Third, Snap is the right size — large enough for serious ML infra, small enough to have product impact."
**Tip:** Reference Snap's 2026 features: My AI, generative AR, AR mirrors, Lens Studio AI.

### Q1.3: "Location + comp"
**Answer:** Snap is primarily LA (Santa Monica) with offices in SF, Seattle, NYC, London. Relocation to LA is common. Remote is limited.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Valid anagram + frequency sort"
**Answer:**
```python
def groupAnagrams(strs):
    from collections import defaultdict
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```
**Tip:** Snap's phone screen is medium LeetCode. Strings, arrays, hash maps are common.

### Q2.2: ML — "How would you build a Lens recommendation system?"
**Answer:** "Three surfaces: (1) 'Try this Lens' push — based on user-Lens interaction history + content-based (image embeddings, Lens category, trending). (2) Lens search — BM25 + embedding ANN over Lens metadata. (3) In-context — if a friend used a Lens, suggest to you. ML model: gradient-boosted or two-tower on (user-Lens-context). Diversity budget to avoid Lens monoculture. Cold start: popularity priors + category exploration."
**Tip:** Mention mobile / on-device constraints. Snap pushes ML onto phones.

### Q2.3: System design — "Design a Snapstreak prediction system"
**Answer:** "Predict P(streak continues to day N) for each user-pair. Features: recent activity, time-zone alignment, message frequency, recency, app-open frequency. Model: gradient-boosted on these features. Output score → push notification if streak at risk. Goal: drive engagement without being annoying — send notification only if user is likely to act."
**Tip:** Snap loves notification-quality questions. Show you understand the cost of bad push.

## Stage 3: Onsite (4 rounds, 1 day)

### Round 3.1: Coding
**Q3.1.1:** "LRU cache" or "LFU cache" (Snap asks this).
**Q3.1.2:** "Top K frequent elements in a stream." Count-min sketch + heap.
**Q3.1.3:** "Design a Snap message queue." Priority queue, ack, retry, dead letter.

### Round 3.2: System design
**Q3.2.1:** "Design Snap's Stories ranking." Multi-stage: candidate generation (followed friends, content-based, collaborative), ranking (engagement prediction, recency), diversity, freshness. Discuss anti-bullying filters.
**Q3.2.2:** "Design an AR Lens ranking system." Lens metadata, user behavior, on-device constraints, real-time inference, network usage.

### Round 3.3: ML deep-dive
**Q3.3.1:** "Walk me through a real ML system you've shipped." Be specific.
**Q3.3.2:** "How would you detect NSFW / unsafe content on Snap?"
**Answer:** "Multi-modal: image classifier (CLIP fine-tuned), text classifier (DistilBERT), combined score, age-aware thresholds. Human review queue. Fast takedown for confirmed CSAM (NCMEC reporting). False positive cost high — graduation photo false-positive is a real risk."

### Round 3.4: Behavioral
**Q3.4.1:** "Tell me about a time you had to ship a feature in 1 week." STAR.
**Q3.4.2:** "Time you influenced product direction with data." STAR.
**Q3.4.3:** "What's your favorite Lens and why?" — be specific, shows product love.

## Stage 4: Hiring committee
Snap's committee includes the hiring manager, 2-3 cross-functional peers, and a senior leader. The bar for L5 (Senior) is "scope and ship a 2-quarter ML project independently." L6 (Staff) requires influence on the ML platform or org-wide direction. Snap takes 1-2 weeks for committee.

## Stage 5: Offer
Snap comp is solid for the Bay Area but slightly below FAANG. RSU is 4-year vest. They negotiate on equity, less so on base. Relocation to LA is well-funded. Team match is usually after the onsite.

## Tips for the Snap loop
1. **Camera-first thinking is a plus** — if you've worked on AR/CV, mention it.
2. **On-device ML is real** — model size, quantization, mobile inference.
3. **Generative AR is hot** — Stable Diffusion + ControlNet, inpainting, depth estimation.
4. **Multi-modal ML** — Snap is fundamentally text + image + video + audio.
5. **Coding is medium LeetCode** — focus on clean, fast code.
6. **Reference My AI and 2026 features** — shows you've used the product.
7. **Be specific about user behavior on Snap** — younger demographic, ephemeral, camera-first.

## Real candidate report
> "I interviewed for ML on the Camera team. The system design was on AR Lens ranking, and they pushed hard on on-device inference constraints (model size, latency, battery). The ML deep-dive was on multi-modal embeddings (image + text) for Lens retrieval. Got an L5 offer at $320K base + $550K RSU/4yr, LA. Negotiation moved base by $25K but they wouldn't budge on level." — Glassdoor, 2025

## Sources
- [Snap Engineering Blog](https://eng.snap.com/)
- [Snap Research](https://research.snap.com/)
- [Levels.fyi Snap](https://www.levels.fyi/companies/snap)
- [Glassdoor Snap interviews](https://www.glassdoor.com/Interview/Snap-Interview-Questions-E950299.htm)
- [LeetCode Snap tagged](https://leetcode.com/company/snap/)
