# The Amazon Applied Scientist Interview in 2026: The Bar Raiser, the 16 Leadership Principles, and the 5 Answers That Get You Hired

*Article 11 of 11 in the "Top 100 AI/ML Interview Questions" series. This one is Amazon. Previous: Netflix. The mega-guide is next.*

---

Amazon's loop is the one where the Bar Raiser can veto your offer.

Where Netflix tests ownership and Stripe tests payments domain, **Amazon tests whether you can pass the most rigorous behavioral bar in big tech.** The 2026 Amazon loop has 3 signature elements: (1) the **Bar Raiser** — a specially trained interviewer outside the hiring team who assesses the candidate's overall quality and can veto an offer even when other interviewers favor it, (2) the **16 Leadership Principles** — every interviewer is assigned 2-3 LPs and grades the candidate's STAR-method answers against them, and (3) the **"2&5 Promise"** — 2 days after phone screens, 5 days after panel interviews. The candidate who treats Amazon like a generic Big Tech loop loses to the candidate who has 5 STAR stories ready, one per LP.

The 60-second pitch: **Amazon is hiring applied scientists who can ship ML at AWS / Alexa / Rufus / Shopping scale, defend their work against a Bar Raiser, and demonstrate the 16 Leadership Principles through specific STAR stories. The candidate who only has the technical depth loses. The right choice is to spend 6 hours on STAR stories + 4 hours on the Bar Raiser round before the loop.**

---

## The process map (5 stages, 3-6 weeks)

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Resume screen** | Recruiter reviews experience match. | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen (1-2 rounds, 60 min each)** | 1-2 coding problems (LeetCode medium) + 1 ML fundamentals. | 1-2 weeks | ~40% advance |
| 3. **Virtual onsite (5-6 rounds, 45-60 min each)** | 2 coding → 1 system design → 1 ML deep-dive → 1-2 behavioral (LPs) → 1 Bar Raiser. | 1-2 days | ~30% advance |
| 4. **Debrief + offer** | Interviewers + Bar Raiser hold a debrief meeting. 2&5 Promise applies. | 1 week | — |
| 5. **Offer** | Comp negotiation. | 1-2 weeks | — |

**Cumulative pass rate: ~2-3%.** Amazon's loop is the most structured of the 11 — the 2&5 Promise means the timeline is predictable, but the LP grading is the strictest.

**Comp (US, levels.fyi, Oct 2026):**

| Level | Title | Total comp |
|-------|-------|------------|
| L4 | SWE I | $180K-$245K |
| L5 | SWE II | $245K-$350K |
| L6 | SWE III (Senior) | $350K-$500K |
| L7 | Principal | $500K-$800K |
| L8 | Senior Principal | $800K-$1.2M+ |

**Note:** Amazon Applied Scientist levels mirror the SWE levels. L5 is the entry-level for AS (requires 2&5 Promise + 1-2 years of post-PhD or equivalent experience). L6 is the senior level (requires demonstrated ownership of a production ML system).

---

## Voices from the table (what real Amazon interviewers and candidates said)

### What a real Amazon Applied Scientist guide reports (IGotAnOffer, 2026)

> *"Interviewers usually prefer that you structure your answers using the STAR method (Situation, Task, Action, Result). You'll be asked to walk through your past projects in detail, including the technical decisions you made, the trade-offs you considered, and the outcomes you delivered. The candidate who gives vague 'we did X' answers loses. The candidate who names the specific decision, the specific trade-off, and the specific metric wins."*
> — [IGotAnOffer — Amazon Applied Scientist Interview (process, questions, prep) (2026)](https://igotanoffer.com/en/advice/amazon-applied-scientist-interview)

### What a real Amazon AI Engineer guide reports (DataInterview, 2026)

> *"Behavioral questions focus on Amazon's Leadership Principles. Promotion to Applied Scientist II (L5) requires demonstrated ownership of a production ML system. Promotion to L6 requires demonstrated cross-team impact. The candidate who treats the behavioral round as a formality loses — Amazon is the only company where the behavioral round is weighted as heavily as the technical rounds."*
> — [DataInterview — Amazon AI Engineer Guide (2026)](https://www.datainterview.com/blog/amazon-ai-engineer-interview)

### What a real Amazon L6 guide reports (Hello Interview, 2026)

> *"You'll spend about 30 minutes on a phone or video call with a technical recruiter who just wants to verify you're a real candidate worth moving forward. The L6 loop is 5-6 rounds, with each interviewer assigned 2-3 Leadership Principles. The Bar Raiser is a specially trained interviewer outside the hiring team who can veto an offer even when other interviewers favor it. The Bar Raiser is the meta-rubric."*
> — [Hello Interview — Amazon L6 Interview Guides & Questions (2026)](https://www.hellointerview.com/guides/amazon/l6)

### What the official Amazon interview prep page says (Amazon, 2026)

> *"Applied science is highly experimental and needs to be supported through strong theoretical analysis and associated process innovations. Our applied scientists publish in top-tier venues, ship to production, and mentor junior scientists. The interview tests for: technical depth (ML fundamentals, system design, coding), scientific rigor (experiments, metrics, ablations), and Leadership Principles."*
> — [Amazon — Applied Scientist Interview Prep (Official)](https://amazon.jobs/content/en/how-we-hire/applied-scientist-interview-prep)

### What a real Amazon behavioral interview guide reports (TryExponent, 2026)

> *"Can you develop and articulate a bold vision? Prepare examples of times when you've thought outside the box and come up with solutions at a higher level. The 'Invent and Simplify' LP is tested with questions like 'tell me about a time you invented a solution to a problem that didn't have an obvious answer.' The 'Dive Deep' LP is tested with 'tell me about a time you found the root cause of a production issue.'"*
> — [TryExponent — Amazon Behavioral Interview Questions and Answers (2026 Guide)](https://www.tryexponent.com/blog/how-to-nail-amazons-behavioral-interview-questions)

### The 5 things every real Amazon report has in common

1. **The Bar Raiser is the meta-rubric.** A specially trained interviewer outside the hiring team can veto an offer. The Bar Raiser is graded on the overall candidate quality, not the specific role fit.
2. **All 16 Leadership Principles are tested.** Each interviewer is assigned 2-3 LPs. Prepare 5 STAR stories minimum.
3. **STAR method is the structure.** Situation, Task, Action, Result. Vague "we did X" answers lose. Specific decisions, specific trade-offs, specific metrics win.
4. **The "2&5 Promise" applies.** 2 days after phone screens, 5 days after panel interviews. The timeline is predictable.
5. **ML depth + system design + LPs.** The technical rounds test ML fundamentals (L1/L2, ensemble methods, transformers, U-Net), system design (always AWS / Alexa / Rufus / Shopping themed), and coding (LeetCode medium).

---

## The 15 most-asked questions at Amazon Applied Scientist (2026)

### Coding round (60 min, LeetCode medium)

1. **Two Sum. Extend to handle duplicates and return all unique pairs.** (~70%)
2. **Connected components in a graph. Implement Union-Find.** (~50%)
3. **Balanced parentheses. Extend to handle multiple bracket types.** (~50%)
4. **House Robber. Discuss DP vs. greedy.** (~40%)
5. **Merge k sorted lists. Use a heap.** (~40%)

### ML fundamentals round (60 min)

6. **L1 vs. L2 regularization. When do you pick which, and why?** (~70%)
7. **Ensemble methods: bagging vs. boosting. Explain the bias-variance trade-off.** (~70%)
8. **PCA and dimensionality reduction. Walk through the math.** (~50%)
9. **RNN vs. BiLSTM vs. GRU. When do you pick which?** (~50%)
10. **Attention mechanism. Walk through scaled dot-product attention. Compare to CNN.** (~60%)

### System design round (60 min, AWS / Alexa / Rufus / Shopping themed)

11. **Design a recommendation system for Amazon Shopping. Discuss collaborative filtering, content-based, the hybrid approach, the cold-start problem.** (~70%)
12. **Design the Alexa NLU pipeline. Discuss ASR, intent classification, slot filling, the dialog manager.** (~50%, if Alexa)
13. **Design Rufus (Amazon's shopping assistant). Discuss the retrieval pipeline, the LLM serving, the safety layer.** (~60%, if Rufus)
14. **Design a real-time fraud detection system for Amazon Pay. Discuss the feature store, the model, the <100ms latency budget.** (~50%)
15. **Design an A/B testing platform for Amazon. Discuss the experiment assignment, the metric pipeline, the statistical analysis, the CUPED variance reduction.** (~60%)

### Behavioral round (45 min, STAR + 16 LPs)

Plus the Amazon-specific questions (each tied to 1-2 LPs):
- *"Tell me about a time you had to make a decision with incomplete information. (Bias for Action)"* (~80%)
- *"Tell me about the most innovative project you contributed to. (Invent and Simplify)"* (~80%)
- *"Tell me about a time you had to dive deep into a production issue. (Dive Deep)"* (~80%)
- *"Tell me about a time you disagreed with a colleague. How did you resolve it? (Have Backbone; Disagree and Commit)"* (~80%)
- *"Tell me about a time you had to ship something under a tight deadline. What did you cut? (Deliver Results)"* (~80%)

### Bar Raiser round (60 min, the meta-rubric)

Plus the Bar Raiser-specific questions:
- *"Walk me through your career. Why each step? What would you do differently?"* (~100%)
- *"Why Amazon, specifically? What bet would you test?"* (~100%)
- *"What's the highest-impact decision you've made in the last 12 months? Why?"* (~100%)

---

## The 5 meta-answers (the patterns that work across all 15)

### Meta-answer 1: "L1 vs. L2, with the right pick"

The L1 vs. L2 question is asked in 70% of loops. The wrong answer: "L1 produces sparsity, L2 shrinks coefficients." The right answer: "L1 (Lasso) adds a penalty equal to the absolute value of the coefficients; L2 (Ridge) adds a penalty equal to the squared magnitude. L1 produces sparsity (some coefficients become exactly 0), which is good for feature selection. L2 shrinks all coefficients smoothly, which is good for handling multicollinearity. The right pick: L1 when you want interpretability or feature selection; L2 when you want to handle correlated features. The trade-off: L1 is not differentiable at 0, so it requires subgradient methods; L2 has a closed-form solution (ridge regression). For deep learning, L2 is the standard (weight decay). For linear models with many features, L1 is the standard." **Name the penalty, name the sparsity, name the right pick, name the trade-off, name the deep learning standard.**

### Meta-answer 2: "Bagging vs. boosting, with the bias-variance trade-off"

The ensemble question is asked in 70% of loops. The wrong answer: "Bagging trains models in parallel; boosting trains models sequentially." The right answer: "Bagging (e.g., Random Forest) trains N models in parallel on bootstrap samples, then averages their predictions. Bagging reduces variance without changing bias. Boosting (e.g., XGBoost, LightGBM) trains N models sequentially, where each model focuses on the errors of the previous one. Boosting reduces both bias and variance. The right pick: bagging when you have high-variance base learners (deep trees); boosting when you have high-bias base learners (shallow trees). For tabular data, gradient boosting is the standard (XGBoost, LightGBM, CatBoost). For images and text, deep learning is the standard." **Name the parallel vs. sequential, name the variance vs. bias, name the right pick, name the tabular standard.**

### Meta-answer 3: "Recommendation system, with the hybrid approach"

The recommendation system question is asked in 70% of loops. The wrong answer: "I'd use collaborative filtering." The right answer: "There are 3 main approaches: collaborative filtering (CF, uses user-item interactions), content-based (uses item features), and hybrid (combines both). CF is the most common but suffers from cold-start (new users / new items). Content-based handles cold-start but lacks diversity. The right pick: hybrid. The implementation: matrix factorization (e.g., SVD, ALS) for the CF component; a neural network over item features for the content-based component; a learned weighted combination. The trade-off: latency vs. quality. For a Shopping recommendation, the latency budget is <100ms; we precompute the candidate set (top-1000) and re-rank with a lightweight model in real-time. The cold-start fix: for new users, use the content-based path; for new items, use popularity + content features." **Name the 3 approaches, name the cold-start fix, name the hybrid, name the latency budget, name the precompute + re-rank.**

### Meta-answer 4: "STAR story, with the specific metric"

Every behavioral answer is graded on whether it has the 4 STAR components. The wrong answer: "I led a project that improved the model's accuracy." The right answer: "Situation: the search ranking model at my last job was missing 30% of relevant results. Task: I was assigned to lead the fix as the tech lead. Action: I dug into the failure cases, found that the model was treating query and document as the same embedding space (a known issue with cross-encoders), and proposed a bi-encoder architecture with hard-negative mining. I shipped the new model over 4 weeks with a 5% canary, monitoring NDCG@10 and click-through rate. Result: NDCG@10 improved from 0.62 to 0.71, click-through rate improved by 8%, and the new architecture was adopted as the standard for all search products." **Name the situation, name the task, name the action (with the technical decision), name the result (with the metric), name the team adoption.**

### Meta-answer 5: "Bar Raiser, with the bold vision"

The Bar Raiser round is graded on whether you have a clear, bold vision. The wrong answer: "I want to work on ML at Amazon." The right answer: "My bold vision: I think the future of e-commerce is conversational. The bet: by 2028, 30% of Amazon Shopping interactions will be through Rufus, not the search bar. The 1 thing I'd test: whether Rufus can match the conversion rate of the search bar for high-intent queries (e.g., 'best running shoes under $100'). The 1 thing I disagree with: I think Rufus is too conservative on the recommendation side — it should be allowed to suggest items the user didn't explicitly ask for, as long as it cites the source. The 1 thing I'd do differently in my career: I'd spend more time on the production side earlier — my PhD was heavy on research, but the highest-impact work I've done has been shipping ML to production." **Name the bold vision, name the bet, name the test, name the disagreement, name the career reflection.**

---

## The 30-day prep plan (1-2 hours/day)

**Week 1 — Coding + ML fundamentals (8-10 hours):**
- [ ] Do 30 LeetCode mediums. Focus on: arrays, strings, trees, graphs, BFS/DFS, sliding window, two pointers, hash tables.
- [ ] Re-read the L1/L2 / ensemble / PCA sections of a deep learning textbook. Be able to derive on a whiteboard.

**Week 2 — System design + AWS / Alexa / Rufus (8-10 hours):**
- [ ] Read the Amazon Science blog. Note the recent Rufus + Alexa + AWS AI bets.
- [ ] Practice 3 system designs out loud (60 min each): Shopping recommendation, Alexa NLU, Rufus architecture.
- [ ] For each, write the trade-off table: 3 options × 4 dimensions (latency, throughput, cost, quality).

**Week 3 — Behavioral + STAR stories (6-8 hours):**
- [ ] Write 5 STAR stories: Bias for Action, Invent and Simplify, Dive Deep, Have Backbone, Deliver Results.
- [ ] Each story must be: 2-3 min long, with a specific decision, a specific trade-off, and a specific metric.
- [ ] Practice each story out loud. Time yourself. Cut anything that doesn't add to the punchline.

**Week 4 — Bar Raiser + final reps (6-8 hours):**
- [ ] Write your Bar Raiser answers: career walkthrough, why Amazon, highest-impact decision.
- [ ] Write your bold vision. 1 bet, 1 test, 1 disagreement.
- [ ] Do 1 full mock loop (5-6 hours) with a friend. Debrief. Repeat 2-3 times.

**Total: ~30 hours over 30 days.**

---

## The 5 things to remember

1. **The Bar Raiser can veto your offer.** A specially trained interviewer outside the hiring team. The Bar Raiser is the meta-rubric.
2. **All 16 Leadership Principles are tested.** Each interviewer is assigned 2-3 LPs. 5 STAR stories minimum.
3. **STAR method is the structure.** Situation, Task, Action, Result. Specific decisions, specific trade-offs, specific metrics.
4. **The 2&5 Promise applies.** 2 days after phone screens, 5 days after panel interviews. Predictable timeline.
5. **ML depth + system design + LPs.** The technical rounds test ML fundamentals + system design (AWS / Alexa / Rufus / Shopping themed) + coding (LeetCode medium). The behavioral round is weighted as heavily as the technical rounds.

---

## What's next

**Article 12 (next week):** *Top 100 AI/ML Interview Questions — The Mega-Guide.* Aggregating all 100+ questions from the 11 company articles (OpenAI, Anthropic, DeepMind, Meta, Microsoft, NVIDIA, Apple, Databricks, Stripe, Netflix, Amazon) into a single searchable document organized by company, by round type, and by topic.

**The series wrap-up:** A reflection on the 11 loops — the 5 patterns that show up in every company, the 5 things that differ, and the 30-day plan that covers the most ground.

---

## What to do today (1 hour)

- [ ] **Write your 5 STAR stories** (30 min). One per LP. Each with a specific metric.
- [ ] **Practice the Bar Raiser "bold vision" answer** (20 min). 1 bet + 1 test + 1 disagreement.
- [ ] **Read 1 Amazon Science post from the last 30 days** (10 min). Note the 1 bet you'd test.

— Vishnoi

---

**Sources (with the human voices):**

- [IGotAnOffer — Amazon Applied Scientist Interview (process, questions, prep) (2026)](https://igotanoffer.com/en/advice/amazon-applied-scientist-interview) — the STAR method, the technical decision framework
- [DataInterview — Amazon AI Engineer Guide (2026)](https://www.datainterview.com/blog/amazon-ai-engineer-interview) — the L5/L6 promotion criteria, the LP weighting
- [Hello Interview — Amazon L6 Interview Guides & Questions (2026)](https://www.hellointerview.com/guides/amazon/l6) — the loop structure, the Bar Raiser role
- [Amazon — Applied Scientist Interview Prep (Official)](https://amazon.jobs/content/en/how-we-hire/applied-scientist-interview-prep) — the source for the applied science culture, the technical rigor rubric
- [TryExponent — Amazon Behavioral Interview Questions and Answers (2026 Guide)](https://www.tryexponent.com/blog/how-to-nail-amazons-behavioral-interview-questions) — the LP-specific question patterns
- [TechScreen — The Machine Learning Engineer Interview Guide (2026)](https://techscreen.app/articles/machine-learning-engineer-interview-guide-2026) — the cross-lab ML systems design framework
- [Levels.fyi — Amazon compensation](https://www.levels.fyi/companies/amazon/salaries/software-engineer) — the L4-L8 comp band
- [Amazon Science Blog](https://www.amazon.science/) — the source for the Rufus, Alexa, and AWS AI bets

*This is article 11 of 11 in the "Top 100 AI/ML Interview Questions" series. Articles 1-10 (OpenAI, Anthropic, DeepMind, Meta, Microsoft, NVIDIA, Apple, Databricks, Stripe, Netflix) are already live.*

*This article is the Medium version. The companion Substack version is at [vishnoi.substack.com](https://vishnoi.substack.com).*
