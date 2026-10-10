# 35. Pinterest (ML / Visual Search / Ranking)

- **Role:** ML Engineer / Applied Scientist (Home Feed, Visual Search, Ads Ranking, Shop)
- **Tech stack:** Python, PyTorch, C++, MXNet, Flink, Kafka, HBase, Pinball (workflow), Manas (search)
- **Comp band:** $250K-$700K (L4-L6); senior crosses $900K+; RSUs vest 4-year
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Feed/Search/Ads/Shop), comp | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~55% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Pinterest for ML?"
**Answer:** "Pinterest's challenge is the hardest in visual search — 50B+ pins, mostly images, with semantic meaning that's hard to extract from raw pixels. The published work on visual embedding (PinSage, GraphSAGE) and the home feed ranking is some of the best applied ML in industry. I want to work on the system that inspires 500M+ users monthly."
**Tip:** Reference *PinSage*, *PinnerFormer*, *Home Feed ranking*, *Visual Search*, *Shop*, *Ads* — distinct surfaces.

### Q1.2: "Describe a ranking or visual search model you shipped"
**Answer:** STAR with focus on *graph features*, *multi-modal embeddings*, and *long-tail creator content*.
**Tip:** Pinterest is uniquely graph-structured — show you think about Pin → Board → Pinner relationships.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "Implement K-means clustering"
**Answer:** Lloyd's algorithm with random init + multiple restarts.
**Tip:** ML-flavored coding questions are common.

### Q2.2: ML — "Design Pinterest's visual search model"
**Answer:** (1) Visual encoder — ResNet/ViT pretrained + fine-tuned on Pin Board labels; (2) Embedding space optimized for cosine similarity + click-through co-engagement; (3) Two-tower: visual query tower + pin tower; (4) ANN retrieval with FAISS/ScaNN over billions of pins; (5) Re-rank with multi-task model (CTR, save, long-click); (6) Continuous embedding refresh via Flink streaming.
**Tip:** Pinterest publishes — reference *PinSage*, *PinnerFormer*, *Pixie*.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- **Q:** Word search II (Boggle) → Trie + DFS with pruning.
- **Q:** LRU cache + variants.
- (Optional 3rd): Graph — Pin-Board-Pinner traversal.

### Round 3.2: System design (60 min)
- **Q: "Design Pinterest's home feed ranking"** — Two-tower retrieval from Pinner action history → light ranker → heavy ranker with multi-task heads → diversity re-rank → serving at <100ms.
- **Q: "Design Pinterest's embedding serving at 100M+ QPS"** — Sharded ANN indices, embedding cache, versioned embeddings, continuous updates.

### Round 3.3: ML deep-dive (60 min)
- **Q: "How would you handle cold-start for new pins?"** — Visual features (CLIP), board context, creator prior, popularity priors with exploration.
- **Q: "How would you improve Ads relevance on Pinterest?"** — Multi-task (CTR, saves, conversion), position bias, diversity, advertiser quality score.

### Round 3.4: Behavioral (60 min)
- **Q:** "Tell me about a time you built a model with diverse content creators in mind." Pinterest is creator-positive.
- **Q:** "A time you shipped something imperfect to measure impact."
- **Q:** "Disagreement with a peer."

## Stage 4: Hiring committee
A panel of senior engineers + scientists reviews. They look for: (1) ML bar for the level, (2) Pinterest values (Put Pinners First, Act with Kindness, Be a Force for Good, Build Together), (3) creator-positive mindset, (4) impact at scale. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Pinterest is competitive but typically below FAANG top-of-band. Negotiation is moderate. Team match after loop. SF HQ is main hub; some roles in Toronto, Bangalore.

## Tips for the Pinterest loop
- Reference *PinSage*, *PinnerFormer*, *Pixie*, *Shop*, *Ads* — distinct surfaces.
- For ML rounds, emphasize *graph features* and *multi-modal embeddings* — Pinterest's strengths.
- For system design, embedding serving + retrieval is the bread-and-butter.
- Pinterest is *creator-positive* — show you think about content creators, not just consumers.
- For behavioral, "put pinners first" and "act with kindness" are real values.
- Quantify scale: "50B+ pins", "500M MAU", "100ms ranking latency".
- For visual search, expect ViT/CLIP-level depth.

## Real candidate report
> "Loop for Home Feed ML. 4 rounds in 1 day. The ML deep-dive was on two-tower retrieval with PinSage-style graph features — they wanted me to discuss random walk sampling and embedding staleness. The system design was embedding serving at 100M+ QPS. Behavioral was 'put pinners first' flavored. Offer at L5, ~$580K total. 4 weeks." — Blind, 2025-08

## Sources
- [Pinterest Careers](https://www.pinterestcareers.com/)
- [Levels.fyi Pinterest salaries](https://www.levels.fyi/companies/pinterest/salaries)
- [Pinterest Engineering blog](https://medium.com/pinterest-engineering)
- [Pinterest Research](https://research.pinterest.com/)
- [r/MachineLearning Pinterest thread](https://www.reddit.com/r/MachineLearning/)
