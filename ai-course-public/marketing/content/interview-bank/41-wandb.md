# 41. Weights & Biases (W&B)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (e.g., a wandb dashboard with run comparison lines, parallel coordinates, and the wandb blue color). Color: W&B blue (#FFCC33 yellow accent on dark). Headline: "W&B / AI ML Engineer / 2026".

> **TL;DR:** W&B is the gold-standard ML experiment tracker; the loop is recruiter → coding+ML phone → 4-round onsite → committee → offer, and the question you'll answer twice is "why W&B over MLflow." The winning candidate has run a real sweep, can compare W&B vs MLflow at the data-model level, and brings a founder-fit story about building for ML practitioners.

```
Recruiter (50%) → Phone (40%) → Onsite (30%) → Committee (60%) → Offer
```

- **Role:** ML Engineer (Experiment Tracking / ML Platform)
- **Tech stack:** Python, TypeScript, React, GraphQL, Kubernetes, gRPC, Postgres, Redis, Kafka, PyTorch, TensorFlow, MLflow (interop), Sweep (HPO)
- **Comp band:** $180K-$380K total comp (L3-L5: SWE/ML Engineer) | RSUs/equity 4-year vest
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation + comp | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + ML systems | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Cross-functional panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written, equity-heavy | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Tell me about your ML background"
**Answer:** Frame as a practitioner who has actually run hundreds of training runs: "I'm an ML engineer at X, where I trained production models on tabular + vision data. The part of the job I love is the iteration loop — sweeping hyperparameters, comparing runs, debugging training. That's exactly why W&B interests me."
**Tip:** Mention specific W&B features you used (Sweeps, Reports, Artifacts) to show you're not just a fan but a power user.

### Q1.2: "Why W&B specifically over MLflow / Neptune / Comet?"
**Answer:** Three-part: (1) the data model (Artifacts + Tables + Runs) is richer than MLflow's, (2) the collaboration features (Reports, Teams) are best-in-class, (3) you're betting the W&B Models + Weave (LLM tracing) expansion is the right move as LLM workloads dominate.
**Tip:** Show you've used competitors. W&B values engineers who have migrated teams, not just adopted.

## Stage 2: Technical phone screen

### Q2.1: Coding: "Design a run comparison API"
**Answer:** A "run" is an immutable config + metrics + artifacts bundle. Compare two runs by:
```python
def diff_runs(run_a, run_b):
    return {
        "config_diff": {k: (run_a.config[k], run_b.config[k])
                        for k in set(run_a.config) ^ set(run_b.config)},
        "metric_diff": {k: run_a.metrics[k] - run_b.metrics[k]
                        for k in run_a.metrics},
        "artifact_diff": list(set(run_a.artifacts) ^ set(run_b.artifacts)),
    }
```
**Tip:** Bring up time-series bucketing and statistical significance (paired t-test on final metrics) — interviewers love that.

### Q2.2: ML: "How would you implement Bayesian optimization for HPO sweeps?"
**Answer:** Use Gaussian Process surrogate over (hyperparams → val_loss), Expected Improvement acquisition, then re-fit after each new trial. W&B Sweeps does exactly this.
**Tip:** Mention TPE and Hyperband as alternatives; W&B Sweeps supports all three.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (LeetCode medium-hard)
- **Q3.1.1:** Implement LRU cache (very common for W&B caching layers).
- **Q3.1.2:** Parse + aggregate streaming metrics: write a sliding-window p50/p95/p99 over a stream of latencies.
- **Q3.1.3:** Build a small DAG executor (W&B has internal DAG-like Artifacts graph).

### Round 3.2: System design
- Q3.2.1: Design the W&B experiment tracking backend. Discuss ingestion (gRPC streaming from `wandb.init`), storage (S3 for artifacts, Postgres for metadata, Redis for hot metrics), fan-out for live updates (WebSocket), and read replicas for Reports.
- Q3.2.2: How do you scale to 10M runs? Sharded Postgres, hot/cold tiering in S3, metric downsampling (keep raw 24h, 1m buckets for 30d, 1h for 1y).

### Round 3.3: ML deep-dive
- Q3.3.1: Walk through a real model you trained, end-to-end. How did you debug divergence? (gradient norms, learning rate sweeps, data leakage checks via group K-fold).
- Q3.3.2: How would you build a model registry with lineage? Reference W&B Artifacts: every model has parent dataset + parent code + parent run. You can reproduce any model from its DAG.

### Round 3.4: Behavioral (founder-ish)
- Q3.4.1: Tell me about a time you shipped a tool other engineers actually adopted. W&B's founders came from a failed ML tool at Google and they value this.
- Q3.4.2: A user is furious because their sweep is slow. Walk me through your triage.

## Stage 4: Hiring committee
The panel (3-4 senior engs) debates signal vs noise. They're looking for: (a) you've actually used W&B at scale, (b) you can write production Python + Go, (c) you care about developer experience — W&B's moat is DX. Strong negative signals: not knowing what an "artifact" is, or never having run a sweep. The bar here isn't "could you pass?" — it's "do you actually ship for ML practitioners, by ML practitioners?"

## Stage 5: Offer
Base is competitive with big tech; equity is the upside (W&B is late-stage private, ~$1.25B valuation). Refreshers vest over 4 years with 1-year cliff. Negotiation lever: sign-on bonus and equity refreshers. Most offers come back within 5 business days.

## Tips for the W&B loop
1. **Use the SDK before the interview.** Run `wandb sweep` on a toy example. Know the `init`/`log`/`finish` flow cold.
2. **Be opinionated about MLflow.** W&B will ask you to compare.
3. **Read the W&B engineering blog.** They've published on Artifacts, Sweeps, and Weave internals.
4. **Practice the system design round with sharding** — every W&B round touches scale.
5. **Brush up on time-series aggregation** (W&B's Plots product).
6. **Mention Weave (LLM tracing)** — it's their fastest-growing product.
7. **Have a strong founder-fit story** — W&B culture is "build for ML practitioners, by ML practitioners."

## Real candidate report
> "Two phone screens, then 4 rounds onsite. Coding was LeetCode medium (LRU cache, sliding window). System design was 'design experiment tracking for 10M runs.' They asked me to compare W&B vs MLflow vs Neptune in detail. I lost points by not knowing Weave. Offer came in 3 days: base $220K + 0.05% equity." — Levels.fyi anonymous, 2025

## Sources
- [Weights & Biases careers](https://wandb.ai/site/careers)
- [W&B engineering blog](https://wandb.ai/wandb/engineering)
- [W&B interview reports on Glassdoor](https://www.glassdoor.com/Interview/Weights-and-Biases-Interview-Questions-E3150808.htm)
- [Levels.fyi W&B compensation](https://www.levels.fyi/companies/weights-and-biases)
- [W&B docs](https://docs.wandb.ai)

---

## The 1 thing to remember

Run `wandb sweep` on a toy example before the onsite — every W&B interviewer asks about Artifacts, Sweeps, or Weave, and the candidate who has logged runs in the last week wins the committee round.
