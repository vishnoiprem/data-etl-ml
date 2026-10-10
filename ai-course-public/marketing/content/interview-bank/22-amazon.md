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
**Answer:** "I'm an applied scientist with 5 years building LLM-backed systems. Most recently I led the retrieval model for [X], improving recall 14%. I want to come to Amazon because Rufus and Bedrock are the most concrete deployments of LLMs at scale, and I want to learn from teams that ship to hundreds of millions of users."
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

### Round 3.1: Coding (60 min, 2 questions)
- **Q:** LRU cache → O(1) get/put with doubly linked list.
- **Q:** Top-K most frequent k-mers in a sentence → Counter + heapq.nlargest or sort.
- (Optional 3rd): Graph problem, e.g., "Course schedule" (topological sort).

### Round 3.2: System design (60 min)
- **Q: "Design Rufus — Amazon's shopping assistant"** — Multi-turn dialog, retrieval-augmented generation, action execution (Add to Cart, search, recommend), guardrails, evaluation, A/B.
- **Q: "Design a feature store on AWS"** — S3 offline + DynamoDB online, EMR/SageMaker for batch, Lambda for streaming, point-in-time correctness.

### Round 3.3: ML deep-dive (60 min)
- **Q: "How would you fine-tune an LLM to be a shopping assistant with citation?"** — SFT data from click logs, RLHF or DPO with factual reward, retrieval grounding, hallucination eval.
- **Q: "Design the cold-start strategy for a new product with no reviews"** — Content features, LLM-generated pseudo-reviews for retrieval, popularity prior, exploration.

### Round 3.4: Behavioral (LP loop, 60 min)
- **Q:** "Tell me about a time you FAILED." (Learn & Be Curious + Bias for Action)
- **Q:** "Disagreement with a peer engineer — what did you do?" (Have Backbone; Disagree & Commit)
- **Q:** "A project you're most proud of — what was your specific contribution?" (Ownership)

### Round 3.5 (sometimes): Bar raiser round
The bar raiser is from a *different org* and is the only one with veto power. They probe both technical depth and the LPs. Be ready for "Why should we hire someone who is average for the role?" — they want to know you'll raise the bar.

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
> "The ML rounds for Rufus were very applied — they asked me to design retrieval, ranking, and the citation system. The bar raiser was from a totally unrelated org (Logistics). I bombed my first LP story with 'we' and got cut off — switched to 'I' and they bumped me. 5 weeks from screen to offer, ~$580K total comp at L6." — Blind, 2025-08

## Sources
- [Amazon.jobs Applied Science](https://www.amazon.jobs/en/teams/applied-science)
- [Levels.fyi Amazon salaries](https://www.levels.fyi/companies/amazon/salaries)
- [Amazon Leadership Principles](https://www.amazon.jobs/en/principles)
- [Glassdoor Amazon Applied Scientist interviews](https://www.glassdoor.com/Interview/Amazon-Applied-Scientist-Interview-Questions-EI_IE6036.0,6_KO7,24.htm)
- [r/MachineLearning Amazon thread](https://www.reddit.com/r/MachineLearning/)
