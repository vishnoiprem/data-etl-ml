# 3. Google DeepMind

- **Role:** AI Engineer / Research Engineer
- **Tech stack:** Python, JAX, PyTorch, TensorFlow, CUDA, Colab
- **Comp band:** $400K-$1.5M+ (L4-L7)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, level calibration, team fit | 1-2 weeks | ~50% advance |
| 2. **Technical phone screen** | 1 LeetCode medium + 2-3 quiz questions | 1-2 weeks | ~40% advance |
| 3. **Onsite (5 rounds, 1-2 days)** | 2 coding → 1 ML implementation → 1 system design (ML-infra) → 1 Googliness | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Packet to committee; vote | 1-2 weeks | ~60% advance |
| 5. **Team match + offer** | Committee pass → team match | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm a research engineer with 5 years in ML systems — most recently at [X] where I built a JAX-based distributed training pipeline that scaled to 1024 TPU cores. Relevant project: [Y], a paper on reward model overoptimization that we published at NeurIPS. I'm targeting DeepMind because the Gemini scaling-laws work is the bet I want to be closest to.
**Tip:** DeepMind values research depth + shipping instinct; signal both.

### Q1.2: "Why DeepMind, specifically?"
**Answer:** I want to work on Gemini because the eval gap between closed and open models is what I want to close. I disagree with the AlphaFold-only biology focus — I'd want to test whether the same architectures transfer to materials science. The bet I believe in: the scaling-law story for reasoning models still has 2 more orders of magnitude.
**Tip:** Specific bet + specific disagreement + specific test.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Derive the MLE for the mean of a Gaussian"
**Answer:** Log-likelihood = -n/2 log(2π) - n/2 log(σ²) - (1/(2σ²)) Σ(xᵢ - μ)². d/dμ = (1/σ²) Σ(xᵢ - μ) = 0 → μ̂ = (1/n) Σxᵢ. The MLE is the sample mean. **Derive on the whiteboard, not recite.**
**Tip:** The candidate who derives wins; the candidate who recites loses.

### Q2.2: "Why is L2 regularization equivalent to a Gaussian prior?"
**Answer:** MAP estimate with Gaussian prior p(w) ~ N(0, σ²I) is argmin_w [-log p(D|w) - log p(w)] = argmin_w [NLL + (1/(2σ²)) ||w||²]. That's L2 regularization with λ = 1/(2σ²). Name the prior, derive the equivalence.

## Stage 3: Onsite (5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Implement scaled dot-product attention with causal masking"
**Answer:**
```python
import numpy as np
def attention(Q, K, V, mask=None):
    d = Q.shape[-1]
    scores = Q @ K.swapaxes(-2, -1) / np.sqrt(d)
    if mask is not None:
        scores = np.where(mask, -1e9, scores)
    weights = np.exp(scores - scores.max(-1, keepdims=True))
    weights /= weights.sum(-1, keepdims=True)
    return weights @ V
```
For causal mask: upper-triangular mask sets positions [i, j>i] to -inf before softmax.

### Q3.1.2: "Implement K-Means with streaming updates"
**Answer:** Standard Lloyd's loop; for streaming, use online k-means: for each new point, assign to nearest centroid, then update centroid as `c_new = c_old + (1/n)(x - c_old)`. Trade-off: streaming is O(1) per point but slower convergence.

### Round 3.2: ML implementation (broken neural network, 90 min)

### Q3.2.1: "Loss plateaus at 2.3 — find the 3 bugs"
**Answer:** Plateau at exactly 2.3 = log(10), suggesting class prior = 0.1. Three bugs: (1) **label leak** in the data loader (train and validation are shuffled together), (2) **learning rate too high** (loss is smooth, no noise), (3) **missing normalization** (input has std=10, breaking optimization). Verify by inspecting the data loader first, then the LR schedule, then the input pipeline.
**Tip:** Name 3 candidate bugs, reason through which is most likely, then verify. Plateau at class prior = label leak.

### Round 3.3: System design (ML-infra)

### Q3.3.1: "Design a distributed telemetry system for training jobs"
**Answer:** High-cardinality metrics (per-step loss, per-layer activation stats) at scale. Use a time-series DB (Prometheus or custom) with downsampling for old data. Cardinality vs. query latency: training jobs tolerate higher query latency but need higher write throughput. Right pick: write-heavy time-series DB with tiered storage (hot = recent, cold = downsampled).
**Tip:** ML-infra, not generic infra. Name the ML-specific challenge.

### Round 3.3.2: "Design a model training experiment tracker"
**Answer:** Three components: (1) config store (params, code version, data version), (2) metrics store (per-step, per-epoch), (3) artifact store (checkpoints, logs). Trade-off: a managed solution (Vertex AI, Weights & Biases) vs. custom (MLflow). For DeepMind scale: custom with a relational DB for metadata + object storage for artifacts.
**Tip:** Match the answer to ML-infra depth.

### Round 3.4: Research talk defense (30 min)

### Q3.4.1: "Walk me through every ablation in your paper"
**Answer:** Present for 15 min, then defend for 15. The grader asks for the 3 ablations you didn't run. The wrong answer: defend everything. The right answer: name 3 specific ablations, name which is most likely to break, name the order you'd run them.
**Tip:** "I don't know" + a 2-week investigation plan beats defending everything.

### Round 3.5: Googliness (45 min)

### Q3.5.1: "A time you changed your mind based on evidence"
**Answer:** I believed that dense retrieval beats sparse for long-tail queries. Evidence from a 10K-query eval set showed BM25 beat ColBERT on 18% of queries, mostly technical jargon. I changed the architecture to hybrid retrieval (BM25 + ColBERT with a learned combiner) and the long-tail metric improved 7%.

## Stage 4: Hiring committee

The committee grades research depth + Googliness (collaboration, mission fit, intellectual honesty). They look for: (1) coherent technical narrative across rounds, (2) research-track evidence (paper, open-source, NeurIPS-style contribution), (3) "would I want to be stuck in a research pit with this person for 6 months?" Committee can downgrade you if the math is shaky, even if coding went well.

## Stage 5: Offer

Google comp is structured: base + RSU + bonus + sign-on. DeepMind total comp is ~10-15% below OpenAI / Anthropic at the same level. The play: negotiate the level in the recruiter call; L5 vs. L6 is the call that matters. Google's internal mobility is a real perk — many candidates take the pay cut for the optionality.

## Tips for the DeepMind loop

- **Math comes back.** 8 hours on quiz prep, 8 hours on derivation, 8 hours on broken NN.
- **Find 3 bugs, not 1.** Plateau at class prior = label leak.
- **Research talk is a defense.** Name the 3 ablations you didn't run.
- **ML-infra, not generic infra.** Telemetry, experiment tracking, model serving.
- **"Why DeepMind" needs a specific bet.** Gemini, AlphaFold, robotics, safety.
- **JAX is increasingly preferred.** PyTorch is fine but signal JAX fluency.
- **The loop is long.** 4-6 weeks typical; plan accordingly.

## Real candidate report

> *"Interviewed at DeepMind (especially for RE or RS roles) — what should I know? The biggest signal: they care about your ability to defend ablations. They will read your paper 3 times and ask you about the 3 things you didn't test. If you can't name them, you don't pass."*
> — [r/MachineLearning — Google DeepMind Research Engineer Prep (Jan 2026)](https://www.reddit.com/r/MachineLearning/comments/1q2wiub/d_google_deepmind_research_engineerscientist/)

## Sources

- [Sundeep Teki — The Ultimate AI Research Scientist Interview Guide (2026)](https://www.sundeepteki.org/advice/the-ultimate-ai-research-scientist-interview-guide-cracking-anthropic-openai-google-deepmind-top-ai-labs-in-2026)
- [Glassdoor — Google DeepMind Software Engineer Interview Questions (2026)](https://www.glassdoor.com/Interview/Google-DeepMind-Software-Engineer-Interview-Questions-EI_IE1596815.0,15_KO16,33.htm)
- [r/MachineLearning — DeepMind RE/RS Interview Prep (Jan 2026)](https://www.reddit.com/r/MachineLearning/comments/1q2wiub/d_google_deepmind_research_engineerscientist/)
- [Coditioning — Google DeepMind SWE System Design (Jun 2026)](https://www.coditioning.com/blog/4805/google-deepmind-swe-system-design)
- [Levels.fyi — Google compensation](https://www.levels.fyi/companies/google/salaries/software-engineer)
- [Deisenroth — Mathematics for Machine Learning](https://mml-book.github.io/)