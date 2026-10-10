# 18. Apple (AFM / Siri)

- **Role:** ML Engineer
- **Tech stack:** Python, PyTorch, Core ML, Swift, Metal, Neural Engine
- **Comp band:** $180K-$900K+ (ICT2-ICT6)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (Siri, Photos, AFM, Apple Pay) | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen (60-90 min)** | ML + coding (BERT, audio, LeetCode medium) | 1-2 weeks | ~40% advance |
| 3. **Virtual onsite (3-5 rounds in 1-2 days)** | ML deep-dive → coding → system design → techno-behavioral → optional research talk | 1-2 weeks | ~30% advance |
| 4. **Managerial round** | "Why Apple" + project defense | 1 week | ~50% advance |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in NLP and on-device inference — most recently at [X] where I shipped a Core ML pipeline that runs a 3B LLM on the Neural Engine at <30ms latency. Relevant: a paper on KV-cache compression for on-device LMs. I'm targeting Apple AFM because the on-device LLM bet is the bet I want to test.
**Tip:** Apple grades on-device + privacy depth; bring Core ML / Neural Engine specifics.

### Q1.2: "Why Apple?"
**Answer:** I want to work on the on-device LLM team because the privacy story is the only sustainable moat against cloud-based AI in 2026. The bet: as the 3B model gets better, the cloud-LLM advantage shrinks and the privacy advantage grows. The 1 thing I'd test: whether a 7B on-device model with 4-bit quantization can match the 3B on long-context tasks.
**Tip:** Specific team + specific bet + specific test + specific disagreement.

## Stage 2: Technical phone screen (60-90 min)

### Q2.1: "Walk through BERT and why it's bidirectional"
**Answer:** Transformer encoder with multi-head self-attention. Bidirectionality from masked language modeling: 15% tokens masked, model predicts from both left and right context. On-device: 3B BERT-base runs on the Neural Engine because the encoder is parallel-friendly.
**Tip:** Architecture + pre-training objective + on-device implication.

### Q2.2: "Implement a recommendation system with cold-start"
**Answer:** Two-tower (user embedding + item embedding, dot product). Cold-start: fall back to content features (item metadata) for new items, popularity prior for new users. On-device personalization: per-user LoRA adapter, periodically synced.
**Tip:** Two-tower + cold-start fallback is the Apple pattern.

## Stage 3: Virtual onsite (3-5 rounds)

### Round 3.1: ML deep-dive (60-90 min)

### Q3.1.1: "Implement Naive Bayes from scratch, extend to Gaussian"
**Answer:** `class GaussianNB` (as in AFM file Q2.2): Bayes + log-trick + Gaussian likelihood for continuous features. On-device adaptation: priors precomputed, shipped as a small lookup table; inference is log-likelihood sum.

### Q3.1.2: "Process audio: detect speech onset"
**Answer:** Short-time energy (sum of squares, 20ms windows) with FFT; threshold at adaptive level (2× background noise). Refine with zero-crossing rate to distinguish speech from music. For on-device: run on the input IO thread, <10ms latency.

### Round 3.2: Coding (60 min)

### Q3.2.1: "Dynamic programming for probability: HMM forward algorithm"
**Answer:** Forward algorithm computes P(O|λ) = Σ α_T(i) where α_t(j) = [Σ_i α_{t-1}(i) a_ij] b_j(o_t). Recursion in O(TN²), use log-space for stability.

### Q3.2.2: "Thread-safe cache, adapt for Neural Engine"
**Answer:** Standard LRU with `threading.Lock`; Neural Engine adaptation: shard by feature ID, each shard has its own memory region, avoid cross-shard atomics. Trade-off: cache hit rate vs. memory locality.
**Tip:** Hardware awareness is the Apple signal.

### Round 3.3: System design (60 min, privacy-first)

### Q3.3.1: "Design Apple Intelligence: 3B on-device + 100B+ server"
**Answer:** On-device 3B for privacy-sensitive path (Siri voice, Photos face recognition). Server-side 100B+ via Private Cloud Compute for quality-sensitive path (App Store search, long-context summarization). On-device model fine-tuned per user via LoRA-style adapters. Federated learning updates ship weekly; raw data never leaves the device.
**Tip:** Name the 3B/100B split, the latency budget, the federated learning update.

### Q3.3.2: "Design a friend-recommendation system, keep the social graph on-device"
**Answer:** Compute friend embeddings on-device using a small GNN; store the social graph in an encrypted local store. Server: only sees aggregate embeddings for matching. The match: dot product of two users' embeddings, thresholded. The privacy story: raw social graph never leaves the device.
**Tip:** Privacy is the first-class design constraint.

### Round 3.4: Techno-behavioral (45 min)

### Q3.4.1: "Why Apple, specifically?"
**Answer:** I want to work on the AFM team. The bet: as the 3B model gets better, the privacy advantage grows. The 1 thing I'd test: whether a 7B on-device model with 4-bit quantization can match the 3B on long-context tasks. The 1 thing I disagree with: Apple is too conservative on the server-side model — the 100B+ should be in the same league as GPT-4 class.
**Tip:** Specific team + specific bet + specific test + specific disagreement.

### Q3.4.2: "How do you handle conflicts within a team?"
**Answer:** I separate the person from the position. I ask for the underlying interest, not just the stated position. I look for the third option that satisfies both. If none exists, I propose a time-boxed experiment to test both positions. The data resolves it.
**Tip:** Interest-based negotiation + time-boxed experiment.

## Stage 4: Hiring committee

The committee weighs "why Apple" + AFM literacy + on-device implementation depth. They look for: (1) coherent on-device narrative, (2) AFM knowledge (3B/100B, on-device adapter), (3) product taste — would you ship this on your own iPhone? 1-2 week turnaround.

## Stage 5: Offer

Apple ML comp is more cash-heavy than RSU-heavy (50-60% base). RSUs vest 4 years, 1-year cliff. Negotiation is real but the band is tighter than OpenAI / Meta. The play: anchor with a competing offer if you have one; otherwise, accept the initial offer.

## Tips for the Apple loop

- **"Why Apple" is the offer-decider.** Prep like a coding round.
- **AFM is required reading.** 3B/100B split, on-device adapter, pre-training data mix.
- **Privacy is baked in.** Every system design gets the privacy follow-up.
- **Practical implementation > exotic LeetCode.** Naive Bayes, audio, Neural Engine.
- **Neural Engine matters.** Talk about Metal + Core ML + the APU.
- **Cash-heavy comp.** Pick Apple for cash + brand + hardware access.
- **The comp is more base-weighted.** Don't anchor to RSU-heavy offers.

## Real candidate report

> *"I was asked to implement a Naive Bayes classifier from scratch in 30 minutes, then extend it to handle continuous features. The interviewer's first question after I finished was 'how would you adapt this to run on the Neural Engine?' That's the Apple signal — they think about the hardware, not just the algorithm."*
> — [r/MachineLearning, Apple ML Interview threads (2025-2026)](https://www.reddit.com/r/MachineLearning/)

## Sources

- [Prepfully — Apple Machine Learning Engineer Interview Guide (2026)](https://prepfully.com/interview-guides/apple-machine-learning-engineer)
- [Apple Intelligence Foundation Language Models paper (arXiv, Jul 2024)](https://arxiv.org/html/2407.21075v2)
- [r/MachineLearning — Apple ML Interview threads (2025-2026)](https://www.reddit.com/r/MachineLearning/)
- [TechScreen — The Machine Learning Engineer Interview Guide (2026)](https://techscreen.app/articles/machine-learning-engineer-interview-guide-2026)
- [Levels.fyi — Apple compensation](https://www.levels.fyi/companies/apple/salaries/software-engineer)
- [Apple Machine Learning Research](https://machinelearning.apple.com/)