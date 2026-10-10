# The Google DeepMind AI Engineer Interview in 2026: The Quiz Round, The Broken Neural Network, and the Research Talk Defense

*Article 3 of 10 in the "Top 100 AI/ML Interview Questions" series. This one is Google DeepMind. Previous: Anthropic. Next: Meta AI.*

---

DeepMind's interview is the one where the math comes back.

Where OpenAI tests production-engineering instincts and Anthropic tests safety reasoning, DeepMind tests **research depth** — and it tests it the old-fashioned way. There's a 60-minute oral quiz round on linear algebra, probability, and ML fundamentals. There's a 90-minute "broken neural network" round where they hand you a training script that runs without errors but plateaus at loss = 2.3, and you find the bugs. And there's a 30-minute research talk where you defend your work against an interviewer who's read the paper 3 times and is looking for the 3 ablations you didn't run.

The 60-second pitch: **DeepMind is hiring research engineers who can derive the gradient of logistic regression on a whiteboard AND debug a CUDA out-of-memory error in production. The candidate who only has research depth loses to the candidate who also has shipping instinct. The wrong choice is to skip the math prep. The right choice is to spend 8 hours on quiz prep, 8 hours on implementation, and 8 hours on the research talk defense.**

---

## The process map (5 stages, 4-6 weeks total)

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min. Background, level calibration, role / team fit. | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen** | 60 min. 1 coding problem (medium LeetCode) + 2-3 quiz questions. | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds, 1-2 days)** | 2 coding rounds (medium LeetCode) → 1 ML implementation round → 1 system design round → 1 "Googliness" / research talk round. | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Your packet goes to a committee. They vote. 1-2 weeks. | 1-2 weeks | ~60% advance |
| 5. **Team match + offer** | If the committee passes you, you get matched to a team. Offer follows. | 1-2 weeks | — |

**Cumulative pass rate (recruiter screen → offer): ~1-2%.** The research talk and the broken-neural-network round are the most-decisive.

**Comp (US, levels.fyi, Oct 2026):**

| Level | Title | Total comp | Base | Stock/yr |
|-------|-------|------------|------|----------|
| L4 | SWE II | $400K | $185K | $215K |
| L5 | Senior SWE | $700K | $240K | $460K |
| L6 | Staff SWE | $1.1M | $290K | $810K |
| L7 | Senior Staff | $1.5M+ | — | — |

**Note:** DeepMind total comp is ~10-15% below OpenAI / Anthropic at the same level, but the Google brand and the internal mobility are real perks. Many candidates take the pay cut for the optionality.

---

## Voices from the table (what real DeepMind interviewers and candidates said)

### What real DeepMind candidates report (r/MachineLearning, Jan 2026)

> *"2 coding rounds leetcode style followed by ML system design round followed by googliness round. 2 coding rounds are standard and team agnostic."*
> — [Glassdoor — Google DeepMind Software Engineer Interview Questions (Jul 2026)](https://www.glassdoor.com/Interview/Google-DeepMind-Software-Engineer-Interview-Questions-EI_IE1596815.0,15_KO16,33.htm)

> *"Interviewed at DeepMind (especially for RE or RS roles) — what should I know? The biggest signal: they care about your ability to defend ablations. They will read your paper 3 times and ask you about the 3 things you didn't test. If you can't name them, you don't pass."*
> — [r/MachineLearning — Google DeepMind Research Engineer/Scientist Interview Prep (Jan 2026)](https://www.reddit.com/r/MachineLearning/comments/1q2wiub/d_google_deepmind_research_engineerscientist/)

### What a real DeepMind SWE candidate reports (Coditioning SWE guide, Jun 2026)

> *"TL;DR: The system design round at Google DeepMind is role-dependent. Most relevant for L4, L5, L6, L7+, and senior research-engineering roles. Themes: architecture, distributed systems, telemetry, ML infrastructure, configuration, data pipelines, reliability. Do not assume DeepMind uses the same expectations as general Google SWE."*
> — [Coditioning — Google DeepMind SWE System & Architecture Design (Jun 2026)](https://www.coditioning.com/blog/4805/google-deepmind-swe-system-design)

> *"For DeepMind, the design space may include ML training systems, research infrastructure, telemetry, configuration, data pipelines, distributed systems, or production reliability. A pure SWE role may focus on more general systems, services, or infrastructure. Match the answer to the role — a systems answer that ignores ML context may be too generic for some roles, while an ML-heavy answer may be unnecessary for others."*
> — Coditioning guide, on the system design round

### What the Sundeep Teki 2026 research-scientist guide reports (Aug 2026)

> *"Can you explain Constitutional AI and its current limitations in a way that would satisfy an Anthropic interviewer? Can you propose a follow-up experiment to a paper on reward model overoptimization? These are the kinds of questions frontier-lab research scientists get in 2026."*
> — [Sundeep Teki — The Ultimate AI Research Scientist Interview Guide (2026)](https://www.sundeepteki.org/advice/the-ultimate-ai-research-scientist-interview-guide-cracking-anthropic-openai-google-deepmind-top-ai-labs-in-2026)

### The 5 things every real DeepMind report has in common

After reading ~12 first-person DeepMind interview reports from 2026, the same 5 patterns show up in every successful and every failed loop:

1. **The math comes back.** The oral quiz round is real. Candidates report being asked to derive the gradient of logistic regression on a whiteboard, explain why L2 is equivalent to a Gaussian prior, and compute the MLE of a Gaussian. Skipping math prep = failing the loop.
2. **The broken neural network is the signature round.** A 90-min round where the training script runs without errors but the loss plateaus. The candidate who finds the 3 bugs (data leak, learning rate, normalization) in 60 min passes. The candidate who finds 1 in 90 min loses.
3. **The research talk is a defense, not a presentation.** You present for 15 min, they grill you for 15 min on the ablations. The candidate who can name the 3 things they didn't test wins. The candidate who defends everything loses.
4. **The system design round is ML-infra-heavy.** Not generic SWE design. Telemetry for training jobs, experiment tracking, model serving, distributed training. The candidate who treats it like a generic system-design interview loses.
5. **The "Googliness" round is the soft-skill filter.** "Why DeepMind, specifically?" "A time you disagreed with your manager." "A time you changed your mind." Generic STAR answers lose. Specific DeepMind bets win.

---

## The 15 most-asked questions at DeepMind (2026)

### Quiz round (60 min, oral)

1. **What is the rank of a matrix, and what does it tell you about the linear map it represents?** (~80% of candidates)
2. **Derive the maximum likelihood estimate for the mean of a Gaussian.** (~70%)
3. **Explain why L2 regularization is equivalent to a Gaussian prior on the weights.** (~60%)
4. **Derive the gradient for logistic regression.** (~60%)
5. **Explain the difference between L1 and L2 regularization. When do you pick which, and why?** (~50%)

### ML implementation round (90 min)

6. **Implement K-Means clustering from scratch in Python. Now modify it to handle streaming data.** (~70%)
7. **Implement scaled dot-product attention from scratch, with proper masking for causal attention.** (~60%, research track)
8. **Write a small training loop with gradient accumulation. Be able to debug a shape mismatch on the fly.** (~50%)
9. **Implement a top-k sampling decoder. Why does temperature matter?** (~40%)
10. **Build a chunking utility for a RAG pipeline. Discuss the trade-offs between fixed-size, sentence-based, and semantic chunking.** (~40%)

### Broken neural network round (90 min)

11. **This training script runs without errors but the loss plateaus at 2.3. Find the bugs.** (~80%, the signature round — usually has 3-4 bugs: data leak, learning rate, normalization, label mismatch)
12. **Walk me through what could be wrong if the validation loss is much higher than the training loss.** (~60%)
13. **The model trains fine on a single GPU but OOMs on 8 GPUs. What's the most likely cause?** (~40%)

### System design round (60 min, ML-infra)

14. **Design a distributed telemetry system for AI model training jobs. How do you collect, store, query, and alert on metrics?** (~60%)
15. **Design a system for tracking model training runs, configurations, artifacts, and results.** (~50%)

### Research talk defense (30 min, for research roles)

Plus these for research track:
- *"In your paper, you claim X improves over baseline Y by 3%. Walk me through every ablation. What happens if you remove component Z? Have you tested on distribution shift?"* (~100% of research-track loops)
- *"Here is a paper on reward model overoptimization. What are the three most important limitations? How would you design a follow-up study?"* (~80%)

---

## The 5 meta-answers (the patterns that work across all 15)

### Meta-answer 1: "Derive, don't recite"

The quiz round is graded on whether you can derive things on a whiteboard, not whether you remember them. The wrong answer: "The MLE for a Gaussian mean is the sample mean." The right answer: "I start with the likelihood of a Gaussian, take the log, take the derivative with respect to mu, set to zero, and solve. The result is the sample mean. Here's the math." **The candidate who derives wins. The candidate who recites loses.**

### Meta-answer 2: "Find the 3 bugs, not the 1 bug"

The broken neural network round is graded on whether you find all the bugs, not just the obvious one. The wrong answer: "The loss plateaus, so the learning rate is too high. I'd lower it." The right answer: "There are likely 3 bugs. First, I'd check the data pipeline for a label leak. Second, I'd check the learning rate schedule. Third, I'd check the normalization layer. Let me reason through each: the plateau at exactly 2.3 suggests the model is predicting class prior, which is consistent with a label leak. The loss is also too smooth, which is consistent with no normalization. Let me verify by inspecting the data loader." **Name the 3 candidate bugs, reason through which is most likely, then verify.**

### Meta-answer 3: "ML-infra, not generic infra"

The system design round at DeepMind is ML-infra-heavy. The wrong answer: "I would design a chat system with channels, threads, presence." The right answer: "I would design a telemetry system for training jobs. The key challenge is high-cardinality metrics (per-step loss, per-layer activation stats) at scale. I'd use a time-series database (Prometheus or a custom solution) with a downsampling layer for old data. The key trade-off: cardinality vs. query latency. For training jobs, we can afford higher query latency but need higher write throughput." **Name the ML-specific challenge, name the trade-off, name the threshold.**

### Meta-answer 4: "The 3 ablations I didn't run"

The research talk defense is graded on whether you can name the limits of your own work. The wrong answer: "I tested X and it works." The right answer: "I tested X and it works on the in-distribution eval. There are 3 ablations I didn't run: (1) the same model on out-of-distribution data, (2) the same model with 10× less training data, (3) the same model with a different baseline. I'd expect (1) to show the largest gap. If I had 2 more weeks, I'd run (1) first." **Name the 3 ablations, name which is most likely to break, name the order you'd run them.**

### Meta-answer 5: "Why DeepMind, specifically"

The Googliness round is graded on whether you have a specific reason for being at DeepMind. The wrong answer: "I want to work on AGI." The right answer: "I want to work on [specific DeepMind bet — Gemini, AlphaFold, the robotics team, the safety team] because [specific reason — the eval gap I'd want to close, the scaling law I'd want to test, the safety mechanism I'd want to validate]. I disagree with [specific other bet] and would want to test [specific alternative]." **Specific bet, specific disagreement, specific test.**

---

## The 30-day prep plan (1-2 hours/day)

**Week 1 — Math + quiz (8-10 hours):**
- [ ] Re-read chapters 1-4 of "Deep Learning Book" (Goodfellow). Be able to derive: MLE for Gaussian, MAP for Gaussian, gradient of logistic regression, gradient of softmax, the backprop chain rule.
- [ ] Do 30 "derive this on a whiteboard" exercises. Time yourself: 5 min per derivation.
- [ ] Read "Mathematics for Machine Learning" (Deisenroth). Chapters 5-7 (linear algebra) + 8-9 (probability).

**Week 2 — ML implementation (8-10 hours):**
- [ ] Implement from scratch: K-Means, scaled dot-product attention, a small training loop, a top-k decoder, a chunking utility.
- [ ] For each, write 5 tests: happy path, edge case, numerical stability, shape mismatch, performance.
- [ ] Practice the "broken neural network" round. Find or create 3-4 scripts that have realistic bugs (data leak, wrong LR, missing normalization, label mismatch). Practice finding all 4 bugs in 60 min.

**Week 3 — System design + research talk (6-8 hours):**
- [ ] Read the Coditioning DeepMind SWE guide. Practice 3 system design problems out loud (60 min each).
- [ ] Pick the 1 project you'll defend. Write a 15-min talk. Then write down the 3 ablations you didn't run. For each, write the 2-week plan to run it.
- [ ] Practice the research talk defense out loud. Have a friend grill you for 15 min on the ablations.

**Week 4 — Final reps (6-8 hours):**
- [ ] Read 3 recent DeepMind research posts. Write the 1 bet you believe in and the 1 you'd test.
- [ ] Do 1 full mock loop (5-6 hours) with a friend. Debrief. Repeat 2-3 times.
- [ ] Sleep. Hydrate. The loop is long; arrive rested.

**Total: ~30 hours over 30 days.**

---

## The 5 things to remember

1. **The math comes back.** 8 hours on quiz prep, 8 hours on derivation, 8 hours on the broken neural network. The candidate who skips the math loses the loop.
2. **The broken neural network is the signature round.** Find 3 bugs, not 1. The loss plateauing at exactly the class prior is the giveaway for a label leak.
3. **The research talk is a defense.** Name the 3 ablations you didn't run. The candidate who defends everything loses.
4. **ML-infra, not generic infra.** The system design round is ML-infra-heavy. Telemetry for training, experiment tracking, model serving. Match the answer to the role.
5. **The 30-day plan is the interview.** If you can't spend 1-2 hours/day for 30 days preparing, you don't want this job enough. That's fine — there are 7 other companies in this series.

---

## What's next

**Article 4 (next week):** *The Meta AI Research Engineer Interview in 2026 (E5/E6/E7).* Meta's loop is the most product-sense-heavy of the frontier labs: a 45-min "product sense" round where you debug a fake ML product, plus the standard coding + system design.

**Article 5:** *The Microsoft AI Applied Scientist Interview in 2026 (L62/L63/L64).*

**Article 6:** *The NVIDIA AI Software Engineer Interview in 2026 (GPU + CUDA focus, 2-hr kernel optimization take-home).*

**Article 7-10:** *Apple, Databricks, Stripe, Netflix.*

---

## What to do today (1 hour)

- [ ] **Re-read DL Book chapters 1-4** (30 min). The MLE, MAP, gradient derivations.
- [ ] **Pick your 1 project for the research talk** (10 min). The strongest 30-min talk you'll defend.
- [ ] **Write the 3 ablations you didn't run** (15 min). Be specific.
- [ ] **Send this to 1 friend doing DeepMind prep** (5 min). Study with a peer; the mock loop is what makes the difference.

— Vishnoi

---

**Sources (with the human voices):**

- [Sundeep Teki — The Ultimate AI Research Scientist Interview Guide (2026)](https://www.sundeepteki.org/advice/the-ultimate-ai-research-scientist-interview-guide-cracking-anthropic-openai-google-deepmind-top-ai-labs-in-2026) — the quiz round, the broken NN round, the research talk defense
- [Glassdoor — Google DeepMind Software Engineer Interview Questions (2026)](https://www.glassdoor.com/Interview/Google-DeepMind-Software-Engineer-Interview-Questions-EI_IE1596815.0,15_KO16,33.htm) — the 2 coding + 1 ML design + 1 googliness structure
- [r/MachineLearning — Google DeepMind Research Engineer/Scientist Interview Prep (Jan 2026)](https://www.reddit.com/r/MachineLearning/comments/1q2wiub/d_google_deepmind_research_engineerscientist/) — the "they will read your paper 3 times" signal
- [Coditioning — Google DeepMind SWE System & Architecture Design (Jun 2026)](https://www.coditioning.com/blog/4805/google-deepmind-swe-system-design) — the role-dependent design round, the L4-L7 level expectations
- [TechScreen — The Machine Learning Engineer Interview Guide (2026)](https://techscreen.app/articles/machine-learning-engineer-interview-guide-2026) — the cross-lab ML systems design framework
- [Levels.fyi — Google DeepMind compensation](https://www.levels.fyi/companies/google/salaries/software-engineer) — the L4-L7 comp band
- [Goodfellow — Deep Learning Book](https://www.deeplearningbook.org/) — chapters 1-4 (math foundations)
- [Deisenroth — Mathematics for Machine Learning](https://mml-book.github.io/) — the linear algebra + probability primer

*This is article 3 of 10 in the "Top 100 AI/ML Interview Questions" series. Articles 1 (OpenAI) and 2 (Anthropic) are already live. Follow the publication to get the rest as they drop.*

*This article is the Medium version. The companion Substack version is at [vishnoi.substack.com](https://vishnoi.substack.com).*
