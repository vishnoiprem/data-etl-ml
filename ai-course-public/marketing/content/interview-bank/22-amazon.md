# 22. Amazon (Alexa / Rufus / AWS AI)

- **Role:** Applied Scientist (L5/L6) for Alexa AI, Rufus, or AWS Bedrock
- **Tech stack:** Python, PyTorch, JAX, TensorFlow, SageMaker, AWS (S3, EMR, Kinesis, DynamoDB), Java, Spark
- **Comp band:** $200K-$700K (L5-L7); L7+ crosses $1M+; sign-on and RSUs heavy
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Loop intro, comp alignment, basic fit | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding (45 min) + 1 ML (45 min) | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, ML design, leadership principles | 1-2 days | ~30% advance |
| 4. **Bar raiser + hiring committee** | Cross-org review, "Is this person a bar-raiser?" | 1-3 weeks | ~50% advance |
| 5. **Offer** | Comp, team match, sign-on negotiation | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Walk me through your background"
**Answer:** I'm an applied scientist with 5 years building LLM-backed systems. Most recently I led the retrieval model for [X], improving recall 14%. I want to come to Amazon because Rufus and Bedrock are the most concrete deployments of LLMs at scale, and I want to learn from teams that ship to hundreds of millions of users.
**Tip:** Mention "Working Backwards" once — write the PR/FAQ mentally. Recruiters love it.

### Q1.2: "Tell me about a time you used Customer Obsession"
**Answer:** Use STAR: situation (user pain), task (your mandate), action (anonymized customer interviews + a metric), result (shipped X with Y% lift). The leadership principle must be the *first* word of the answer.
**Tip:** The 16 LPs are scored. Have 2-3 stories per LP at the ready.

## Stage 2: Technical phone screens (90 min total)

### Q2.1: Coding — "Word search in a grid"
**Answer:** Backtracking with visited set. O(M·N·4^L) where L is the word length. Pruning via trie if many words.
**Tip:** Expect medium LeetCode. Don't waste time on micro-optimization.

### Q2.2: ML — "Design a product search ranking model"
**Answer:** Outline: (1) query understanding — spell correction, expansion via embeddings; (2) retrieval — BM25 + dense bi-encoder; (3) ranking — LTR with XGBoost or neural ranker; (4) features — text match, behavioral, freshness; (5) training — click models with position debiasing; (6) serving — sub-100ms with embedding cache; (7) offline metrics — NDCG@10, MRR; online — A/B on CTR and revenue. Discuss how you'd handle tail queries.
**Tip:** Be specific about *which* features, *which* loss, and *how* you handle cold start.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "LRU cache"
**Answer:** Doubly linked list + hashmap. O(1) get/put. On `get`, move to head; on `put` at capacity, evict tail.

### Q3.1.2: "Top-K most frequent k-mers in a sentence"
**Answer:** `Counter` over k-mers + `heapq.nlargest(k, counter.keys(), key=counter.get)`. O(N log K). For very long streams: Count-Min Sketch for approximate frequency.

### Round 3.2: System design (60 min)

### Q3.2.1: "Design Rufus — Amazon's shopping assistant"
**Answer:** Multi-turn dialog (state machine, slot filling) + RAG (Bedrock Knowledge Bases for product/catalog retrieval) + action execution (Add to Cart, search, recommend via the Amazon APIs) + guardrails (Bedrock Guardrails for content + jailbreak detection) + evaluation (LLM-as-judge on 1K conversations/week, A/B on conversion) + observability (per-turn latency, fallback rate). Latency budget: 800ms p99.
**Tip:** Draw the diagram; name every component, the trade-off, the threshold.

### Q3.2.2: "Design a feature store on AWS"
**Answer:** S3 offline + DynamoDB online. EMR/SageMaker for batch features; Lambda + Kinesis for streaming. Point-in-time correctness: feature timestamp joined with event timestamp; reject features newer than the event. Train/serve skew fix: shared Python module for feature definitions.
**Tip:** PIT correctness is the differentiator.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "How would you fine-tune an LLM to be a shopping assistant with citation?"
**Answer:** Three stages: (1) SFT data from click logs + human-written responses with citations, (2) RLHF or DPO with a factual-reward model (penalizes hallucination, rewards grounded claims), (3) retrieval grounding (RAG over product catalog before each generation). Eval: faithfulness rubric (does the citation support the claim?) on 500 held-out queries; human eval weekly.
**Tip:** SFT + factual RM + RAG is the citation pattern.

### Q3.3.2: "Design the cold-start strategy for a new product with no reviews"
**Answer:** Content features (title, description, image embeddings from a multimodal model) + LLM-generated pseudo-reviews for retrieval (cheap, decent quality) + popularity prior (Bayesian shrinkage to category mean) + exploration boost (10% of impressions for 2 weeks). Eval: A/B on conversion after week 2; lift should match mature-product baseline.
**Tip:** Exploration budget + content features is the canonical answer.

### Round 3.4: Behavioral — LP loop (60 min)

### Q3.4.1: "Tell me about a time you FAILED." (Learn & Be Curious + Bias for Action)
**Answer:** Use STAR. The action must show what *I* did (not "we"). Pick a failure where you took a specific action to fix it. Result: 2-3 specific outcomes.
**Tip:** "I" not "we" is graded. 2-3 stories per LP.

### Q3.4.2: "Disagreement with a peer engineer" (Have Backbone; Disagree & Commit)
**Answer:** Use STAR. State the disagreement in 1 sentence. The action: I built a benchmark or analysis that resolved it. The result: we adopted X.
**Tip:** Data, not opinion, wins.

### Q3.4.3: "A project you're most proud of" (Ownership)
**Answer:** Pick your strongest end-to-end project. The action must show *your* specific contribution (1-2 sentences max on team support). Result: 1-2 quantified metrics.
**Tip:** End-to-end + quantified impact.

### Round 3.5 (sometimes): Bar raiser round

The bar raiser is from a *different org* and is the only one with veto power. They probe both technical depth and the LPs. Be ready for "Why should we hire someone who is average for the role?" — they want to know you'll raise the bar.
**Tip:** Treat the bar raiser as the hardest behavioral; rehearse 2-3 LP stories.

## Stage 4: Hiring committee + Bar raiser

Each interviewer writes a "narrative" and a level. The bar raiser writes a separate document. The hiring committee is a separate group of senior scientists/PMs. They look for: (1) technical bar at the level, (2) LPs demonstrated, (3) bar-raiser sign-off (no hire without it), (4) team fit (sometimes). Loop is "debanded" — feedback cannot be edited after submission.

## Stage 5: Offer

Base + sign-on + RSUs. Negotiation is real — bring competing offers. The comp team will match most of a competing base. Equity refreshers are annual. Team match is *after* loop pass but before formal offer.

## Tips for the Amazon loop

- Memorize all 16 Leadership Principles — Amazon scores on them explicitly.
- For coding rounds, speak through tradeoffs and time/space complexity at every step.
- For ML design, *draw the system* — boxes for retrieval, ranker, feature store, serving.
- Have 2-3 stories per LP. Use the format: Situation, Task, Action, Result, with "I" not "we."
- The bar raiser can sink you. Treat their round as the hardest behavioral.
- Reference Rufus, Bedrock, or specific orgs in your "why Amazon" — generic answers tank.
- Prepare for the "scope" question: "How do you decide what's a 1-pager vs a 6-pager?" (Working Backwards)

## Real candidate report

> "The ML rounds for Rufus were very applied — they asked me to design retrieval, ranking, and the citation system. The bar raiser was from a totally unrelated org (Logistics). I bombed my first LP story with 'we' and got cut off — switched to 'I' and they bumped me. 5 weeks from screen to offer, ~$580K total comp at L6."
> — Blind, 2025-08

## Sources

- [Amazon.jobs Applied Science](https://www.amazon.jobs/en/teams/applied-science)
- [Levels.fyi Amazon salaries](https://www.levels.fyi/companies/amazon/salaries)
- [Amazon Leadership Principles](https://www.amazon.jobs/en/principles)
- [Glassdoor Amazon Applied Scientist interviews](https://www.glassdoor.com/Interview/Amazon-Applied-Scientist-Interview-Questions-EI_IE6036.0,6_KO7,24.htm)
- [r/MachineLearning Amazon thread](https://www.reddit.com/r/MachineLearning/)
