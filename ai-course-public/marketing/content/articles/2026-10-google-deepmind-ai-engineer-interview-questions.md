# The Google DeepMind AI Engineer Interview in 2026: The Quiz Round, The Broken Neural Network, and the Research Talk Defense

*Article 3 of 10 in the "Top 100 AI/ML Interview Questions" series. This one is Google DeepMind. Previous: Anthropic. Next: Meta AI.*

---

DeepMind's interview is the one where the math comes back.

Where OpenAI tests production-engineering instincts and Anthropic tests safety reasoning, DeepMind tests **research depth** — and it tests it the old-fashioned way. There's a 60-minute oral math quiz round on linear algebra, probability, and ML fundamentals (Research Scientist track only — for pure SWE track, math is folded into the ML coding round). There's a 45-60-minute "broken neural network" / code-review round where they hand you a training script that runs without errors but plateaus at loss = 2.3, and you find 3-4 bugs. And there's a 60-minute research paper discussion where you defend methodology, weaknesses, and extensions against an interviewer who's read the paper 3 times.

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
| L4 | SWE II | ~$280-400K | $185K | ~$100-215K |
| L5 | Senior SWE | ~$451K (median) | $240K | ~$210K |
| L6 | Staff SWE | ~$664K (median) | $290K | ~$370K |
| L7 | Senior Staff | ~$1M-$1.2M | — | — |

**Note:** DeepMind-specific offers cluster 10-20% above the generic Google L-band medians (per AI Paygrades 2026); the table above uses generic Google L-band medians as the floor. DeepMind's comp is ~20-40% below OpenAI / Anthropic at the same level, but the Google brand, internal mobility (you can move between DeepMind, Google Brain, Search, Cloud), and the liquid Alphabet stock are real perks. Many candidates take the pay cut for the optionality. Process for senior+ roles takes 8-12 weeks — significantly longer than OpenAI/Anthropic.

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

1. **The math comes back — but only for the Research track.** The 60-min oral math quiz (linear algebra, probability, optimization, gradient flow, Bayesian inference, convergence proofs) is real for the Research Scientist (RS) track. For pure SWE track, math is folded into the ML coding round, not a separate oral quiz. Candidates report being asked to derive the gradient of logistic regression on a whiteboard, explain why L2 is equivalent to a Gaussian prior, and compute the MLE of a Gaussian. Skipping math prep = failing the loop (for RS track).
2. **The broken neural network is the signature round (45-60 min, not 90).** A code-review round where the training script runs without errors but the loss plateaus. The candidate who finds the 3-4 bugs (data leak, learning rate, normalization, label mismatch) in 45 min passes. The candidate who finds 1 in 60 min loses. The loss plateauing at exactly the class prior is the giveaway for a label leak.
3. **The research paper discussion is a 60-min defense.** Unlike a "present your own work" format, this is a 60-min paper discussion where the interviewer picks a paper (often yours, often someone else's) and you defend methodology, weaknesses, and extensions. The candidate who can name the 3 ablations they didn't run wins. The candidate who defends everything loses.
4. **The system design round is ML-infra-heavy, track-dependent.** For Research Engineer: distributed training systems design (pipeline/tensor parallelism, ZeRO, DeepSpeed) + evaluation infrastructure (harnesses, contamination, reproducibility). For pure SWE: generic system design + 1 domain-depth round on ML serving. The candidate who treats it like a generic system-design interview loses.
5. **The "Googliness and Leadership" round is the soft-skill filter.** STAR-format behavioral. "Why DeepMind, specifically?" "A time you disagreed with your manager." "A time you changed your mind." Generic STAR answers lose. Specific DeepMind bets win. Note: there are TWO Googliness touchpoints — a pre-onsite behavioral phone screen, plus the onsite Googliness round.
6. **AI tools policy is more conservative than OpenAI/Anthropic.** 2026 reports indicate DeepMind is generally AI-prohibited or heavily limited in the technical rounds — more conservative than other frontier labs. The take-home is the exception; live coding is not.

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

The Googliness round is graded on whether you have a specific reason for being at DeepMind. The wrong answer: "I want to work on AGI." The right answer: "I want to work on [specific 2026 DeepMind bet — the Gemini family, AlphaFold/AlphaGenome/AlphaEarth/AlphaEvolve, Gemini Robotics, or the AI Control Roadmap safety work] because [specific reason — the eval gap I'd want to close, the scaling law I'd want to test, the safety mechanism I'd want to validate]. I disagree with [specific other bet] and would want to test [specific alternative]." **Specific bet, specific disagreement, specific test.**

**Note on the 2026 strategic landscape:** DeepMind's flagship 2026 safety bet is the **AI Control Roadmap** (treat agents as insider threats, capability-tiered defenses) — different framing from OpenAI's deliberative alignment or Anthropic's Constitutional AI. Gemini Robotics 2 is the headline robotics bet. The open-model channel is **Gemma**. Cite the 2026 work, not the 2014-2020 DeepMind heritage.

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

## What failed DeepMind candidates said they did wrong

Across 2026 reports, the patterns cluster around three things: skipping the math, under-defending the paper, and conflating DeepMind with generic Google.

**1. They skipped the math quiz prep (RS track).** Multiple 2026 RS-track candidates report being asked to derive gradients, MLE, MAP, and convergence proofs on a whiteboard — and freezing. The fix: 8 hours of whiteboard derivation, timed, with a friend grilling you. If you can't derive the gradient of logistic regression in 5 minutes, you're not ready.

**2. They defended their own paper instead of discussing the chosen one.** The research paper discussion isn't a "present your work" round. The interviewer picks a paper (yours or someone else's) and you defend *methodology, weaknesses, and extensions.* Candidates who came in with a 15-min rehearsed presentation lost to candidates who listened to the prompt, picked the right 2 weaknesses, and proposed 1 specific extension. The fix: practice discussing 3-5 papers you didn't write, including 1 from a competing lab.

**3. They conflated DeepMind with generic Google.** DeepMind's comp is ~20-40% below OpenAI / Anthropic at the same level, and the process takes 8-12 weeks. Candidates who expected Google-SWE norms (LC/NC rounds, generic system design) lost to candidates who prepared for DeepMind-specific rounds (the broken NN, the math quiz, the ML-infra system design). The fix: read the TechPrep / Coditioning 2026 guides specifically for DeepMind, not the generic Google SWE interview guide.

**4. They tried to use AI tools in the technical rounds.** DeepMind is more conservative than OpenAI/Anthropic on AI tool usage in 2026 — generally prohibited or heavily limited in live coding and the broken NN round. Candidates who prompted the tool got caught or got downleveled.

**5. They under-prepared "Why DeepMind" with 2026-specific bets.** Candidates who cited AlphaGo (2016), DeepMind's founding mission (2010), or "I want to work on AGI" lost to candidates who cited Gemini Robotics 2, the AI Control Roadmap (May 2026), AlphaGenome, or the open-model Gemma channel. The fix: read 3 recent DeepMind blog posts (2026) before the loop. Cite the current work.

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
- [TechPrep — DeepMind Interview Process 2026](https://www.techprep.app/blog/deepmind-interview-process) — the 2026 process map, broken NN round details
- [techinterview.org — DeepMind Interview Process 2026](https://www.techinterview.org/post/3233474918/deepmind-interview-process-2026/) — the 60-min math quiz (RS track), AI tool policy, 8-12 week timeline
- [PracHub — Google DeepMind SWE Guide 2026](https://prachub.com/resources/google-deepmind-software-engineer-interview-guide-2026-coding-ml-systems-and-research-collaboration) — the coding + ML systems + research collaboration structure
- [AI Paygrades — DeepMind compensation](https://aipaygrad.es/) — DeepMind-specific offers clustering 10-20% above generic Google L-band
- [DeepMind — Securing the future of AI agents (AI Control Roadmap)](https://deepmind.google/blog/securing-the-future-of-ai-agents/) — the 2026 safety bet
- [DeepMind Robotics](https://deepmind.google/accelerators/robotics/) — Gemini Robotics 2 as the 2026 robotics bet

*This is article 3 of 10 in the "Top 100 AI/ML Interview Questions" series. Articles 1 (OpenAI) and 2 (Anthropic) are already live. Follow the publication to get the rest as they drop.*

*This article is the Medium version. The companion Substack version is at [vishnoi.substack.com](https://vishnoi.substack.com).*
