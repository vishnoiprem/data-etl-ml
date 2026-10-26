# The Top 100 AI / ML Interview Questions at the 10 Companies Hiring AI Engineers in 2026

*Series landing page — one article per company, 11 articles in total, ~150,000 words of interview prep grounded in real human voices from tech leads and recruiters.*

---

## The series (11 articles)

This is the **Top 100 AI/ML Interview Questions** series: one article per company, each with the most-asked questions, the meta-answers that work across all of them, the 30-day prep plan, and the 5 things to remember. Every article is grounded in **real human voices** — direct quotes from tech leads, recruiters, and candidates sourced from public interview guides, official company prep pages, Reddit AMAs, and Glassdoor reports.

| # | Company | Role | Loop stages | Pass rate | One-line hook |
|---|---------|------|-------------|-----------|---------------|
| 1 | [OpenAI](./01-openai.md) | AI Engineer | 5 | ~1-2% | The "small system you'd actually build on the job" round |
| 2 | [Anthropic](./02-anthropic.md) | AI Engineer (Safety) | 6 | ~1% | Dedicated safety round + Constitutional AI |
| 3 | [Google DeepMind](./03-deepmind.md) | AI Engineer / RE | 5 | ~1-2% | The "broken neural network" round + math quiz |
| 4 | [Meta](./04-meta.md) | AI Research Engineer | 6 | ~1-2% | Jedi round + new AI-assisted coding (2026) |
| 5 | [Microsoft](./05-microsoft.md) | Applied Scientist (Azure AI) | 5 | ~1-2% | Azure AI Search + Semantic Kernel, "As Appropriate" |
| 6 | [NVIDIA](./06-nvidia.md) | AI SWE (CUDA) | 4 | ~2-3% | 5 verbatim CUDA questions, 8× kernel take-home |
| 7 | [Apple](./07-apple.md) | ML Engineer (AFM) | 3-5 | ~2-3% | The "why Apple" round + on-device intelligence |
| 8 | [Databricks](./08-databricks.md) | ML Engineer (Spark) | 5-6 | ~2-3% | Spark internals + Bronze-Silver-Gold medallion |
| 9 | [Stripe](./09-stripe.md) | Senior SWE | 5 | ~2-3% | The Bug Squash round + idempotency |
| 10 | [Netflix](./10-netflix.md) | Senior SWE (L5+) | 4-5 | ~2-3% | The Keeper Test, no junior engineers |
| 11 | [Amazon](./11-amazon.md) | Applied Scientist | 5 | ~2-3% | The Bar Raiser + 16 Leadership Principles |

---

## The 5 patterns that show up in every company

After reading ~70 first-person interview reports and the official interview-prep pages across all 11 companies, the same 5 patterns show up in every successful and every failed loop:

1. **Coding is the floor, not the ceiling.** Every company tests medium-LeetCode coding, but the bar-raisers all test **something specific to that company's domain**: CUDA at NVIDIA, MLflow at Databricks, idempotency at Stripe, real-time Spark at DeepMind.
2. **System design is the differentiator.** Every loop has a system design round, and at every company the system design is themed to the company's core product: News Feed at Meta, vLLM at Anthropic, distributed GPU memory at NVIDIA, payment pipelines at Stripe. The candidate who treats system design as generic loses.
3. **The behavioral round is the offer-decider.** Meta (Jedi), Microsoft (As Appropriate), Amazon (16 LPs + Bar Raiser), Netflix (Keeper Test), Anthropic (safety-round). The candidate who treats behavioral as a formality loses.
4. **The 30-day plan is the interview.** Every article has a 30-day prep plan. ~30 hours over 30 days is the minimum. The candidate who can't commit the time loses.
5. **Real human voices matter more than question lists.** A list of 100 questions is noise. A list with **real quotes from tech leads saying what they actually test**, plus the *meta-answer pattern that wins*, is signal. Every article in this series has 4-7 attributed sources.

---

## The 5 things that differ across the 11 companies

| Dimension | Where it's heaviest | Where it's lightest |
|-----------|--------------------|--------------------|
| **Hardware-specific coding** | NVIDIA (CUDA kernels) | Stripe / Netflix (cloud only) |
| **Safety / alignment** | Anthropic (Constitutional AI) | Databricks / Stripe |
| **Research depth** | DeepMind (math + broken NN) | Stripe / Netflix |
| **Product sense** | Meta (News Feed) | NVIDIA / DeepMind |
| **Domain depth** | Stripe (payments), Apple (AFM), Databricks (Spark) | OpenAI / Anthropic |

**The wrong choice** is to treat all 11 companies the same and do generic LeetCode + system design prep.

**The right choice** is to pick the 2-3 companies where your strengths align with the loop, then spend the 30-day plan focused on those 2-3.

---

## How to use this series

- **Pick the 2-3 companies that match your strengths.** Each article's "60-second pitch" tells you what that company tests most heavily.
- **For each target company, do the 30-day plan in the corresponding article.** ~30 hours each. Run them in parallel if you have the time.
- **Read the "Voices from the Table" section first.** It tells you what real tech leads at that company actually test.
- **Practice the 5 meta-answers.** They're the patterns that work across all 15 most-asked questions.
- **Prep the behavioral round like a coding round.** STAR stories, specific metrics, named disagreements. Generic answers lose everywhere.

---

## The 100 questions, by topic

| Topic | OpenAI | Anthropic | DeepMind | Meta | MSFT | NVIDIA | Apple | Databricks | Stripe | Netflix | Amazon |
|-------|:------:|:---------:|:--------:|:----:|:----:|:------:|:-----:|:----------:|:------:|:-------:|:------:|
| Coding / LeetCode | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ |
| CUDA / GPU | | | ✓ | | | ✓✓✓ | | | | | |
| ML fundamentals | ✓✓ | ✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓ | ✓✓✓ | ✓✓ | | ✓ | ✓✓✓ |
| System design | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓ |
| Distributed systems | ✓✓ | ✓✓ | ✓✓✓ | ✓✓ | ✓ | ✓✓✓ | | ✓✓✓ | ✓✓ | ✓✓ | ✓✓ |
| Safety / alignment | ✓ | ✓✓✓ | ✓✓ | | ✓ | | | | | | |
| Behavioral / STAR | ✓ | ✓ | ✓ | ✓✓✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓✓✓ | ✓✓✓ |
| Domain-specific | | | | | ✓✓✓ (Azure) | | ✓✓✓ (AFM) | ✓✓✓ (Spark) | ✓✓✓ (payments) | ✓✓✓ (streaming) | ✓✓ (AWS/Rufus) |

---

## The 30-day plan, generalized

If you can't pick one company yet, here's the **generic 30-day plan** that covers the most ground across all 11 loops:

**Week 1 — Coding (8-10 hours):**
- [ ] Do 30 LeetCode mediums. Focus on: arrays, strings, trees, graphs, BFS/DFS, sliding window, two pointers, hash tables.
- [ ] Build an LRU cache from scratch. Make it thread-safe. Add tests.
- [ ] Practice talking out loud while coding. Every company grades the thought process.

**Week 2 — System design (8-10 hours):**
- [ ] Practice 4 system designs out loud (60 min each): News Feed (Meta), vLLM (Anthropic), Stripe Payment Pipeline (Stripe), Distributed Training Cluster (NVIDIA).
- [ ] For each, write the trade-off table: 3 options × 4 dimensions (scale, complexity, cost, failure mode).
- [ ] Read "Designing Data-Intensive Applications" chapters 5, 6, 9, 11.

**Week 3 — Behavioral + STAR (6-8 hours):**
- [ ] Write 5 STAR stories: conflict, failure, data-influenced decision, tight deadline, why [company]. Adapt each story to the company's framework (Meta Jedi, Microsoft As Appropriate, Amazon 16 LPs, Netflix Keeper Test).
- [ ] Practice each story out loud. Time yourself: 2-3 min per story.
- [ ] For each target company, prepare the company-specific "why" answer with a specific bet, a specific test, a specific disagreement.

**Week 4 — Final reps (6-8 hours):**
- [ ] Read 3 recent engineering blog posts per target company. Note the 1 bet you'd test.
- [ ] Do 1 full mock loop (5-6 hours) with a friend. Debrief. Repeat 2-3 times.
- [ ] Sleep. Hydrate. The loop is long; arrive rested.

**Total: ~30 hours over 30 days.**

---

## What's next

This series is the foundation. **Article 12 (the mega-guide)** will aggregate all 100+ questions into a single searchable document organized by company, by round type, and by topic — coming in the next 1-2 weeks.

After that, the **Top 100 System Design Questions** series (10 articles, one per company) and the **Top 100 Behavioral Questions** series (with per-company STAR examples) are coming Q1 2027.

---

— Vishnoi

*This series is published on Substack and Medium. The companion Substack version is at [vishnoi.substack.com](https://vishnoi.substack.com).*
