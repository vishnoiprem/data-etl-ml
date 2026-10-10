# 42. Comet

- **Role:** ML Engineer (Experiment Tracking / MLOps)
- **Tech stack:** Python, TypeScript, React, Go, Postgres, ClickHouse, Redis, Kubernetes, Docker, PyTorch, TensorFlow, LLM eval tooling
- **Comp band:** $170K-$350K (smaller than W&B, similar structure)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + ML | 1-2 weeks | ~40% advance |
| 3. **Onsite (3-4 rounds)** | Coding, system design, ML, behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Comet over W&B or MLflow?"
**Answer:** Three-bet: (1) Comet's LLM eval product is more mature (Comet has Opik, a real LLM eval + tracing product), (2) the metadata model is more flexible (nested panels, custom dashboards), (3) self-hosted enterprise offering is a real wedge for regulated customers.
**Tip:** Mention specific Opik features: hallucination detection, prompt versioning, side-by-side model comparison.

### Q1.2: "Tell me about your experience with experiment tracking"
**Answer:** Highlight at least one production workflow where you compared 50+ runs and used the tracking tool to drive a decision. Concrete numbers (e.g., "picked model X over Y because p99 latency was 30% lower").

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a streaming metric aggregator"
**Answer:**
```python
import bisect
class StreamingPercentile:
    def __init__(self):
        self.sorted = []
    def add(self, x):
        bisect.insort(self.sorted, x)
    def percentile(self, p):
        k = int(len(self.sorted) * p / 100)
        return self.sorted[min(k, len(self.sorted)-1)]
```
**Tip:** Discuss the O(n) alternative using two heaps (max-heap below, min-heap above the percentile) — Comet uses this for their live dashboards.

### Q2.2: ML — "How would you build an LLM evaluation pipeline?"
**Answer:** Three layers: (1) **offline eval** on golden datasets (accuracy, BLEU, custom rubric), (2) **online eval** with LLM-as-judge for open-ended outputs, (3) **production tracing** with span-level attribution. Mention tools: Opik, LangSmith, Braintrust.

## Stage 3: Onsite (3-4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a thread-safe metric writer (think: `comet_ml.log_metric` from many workers).
- **Q3.1.2:** Build a small Prometheus-like TSDB (rollup rules, downsampling).
- **Q3.1.3:** Parse experiment metadata from a config file and validate it against a schema.

### Round 3.2: System design
- **Q3.2.1:** "Design the panel system behind Comet's custom dashboards." Talk nested panel data model, panel-level permissions, real-time updates via WebSocket, materialized aggregations.
- **Q3.2.2:** "How do you build a production-grade LLM eval service?" Discuss: queue-based async eval, judge model selection, cost budgets, golden dataset curation, regression detection.

### Round 3.3: ML deep-dive
- **Q3.3.1:** Walk through a model you took from notebook to production.
- **Q3.3.2:** "How would you detect data drift in production?" PSI, KS test, embedding-space drift (UMAP + density estimation), and how Comet's production monitoring helps.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a time you made a tool that users actually loved."
- **Q3.4.2:** "A customer wants a feature only they need. What do you do?"

## Stage 4: Hiring committee
Comet is smaller (~$50M raised), so the committee is tight: usually 3-5 senior engs. They weigh: ML practitioner credibility, coding chops, and "do you actually use Comet?" (A red flag is a candidate who's only used W&B and has no clear opinion on Comet.)

## Stage 5: Offer
Base is slightly below W&B (10-20% lower); equity is the lever — Comet is private, Series B-ish, so equity has real upside if they IPO. Negotiation: push for refreshers and signing bonus.

## Tips for the Comet loop
1. **Sign up for Opik and run a real eval before the interview.** Have an opinion on it.
2. **Differentiate yourself from W&B** in your system design — show you know Comet's panel model.
3. **Practice ClickHouse-style OLAP queries** — Comet's backend uses it.
4. **Talk about LLM eval depth** — it's the hot area in 2026.
5. **Have a "tools for ML practitioners" project** — Comet founders are obsessed with DX.
6. **Read the Comet engineering blog** — they post about their eval pipelines.
7. **Be ready to compare Comet vs W&B vs MLflow vs Weights & Biases vs Arize vs WhyLabs** — expect it.

## Real candidate report
> "Phone screen was a LeetCode medium (LRU cache variant) plus an LLM eval design question. Onsite was 4 rounds in one day — coding, system design, ML, founder. Founder round was very values-driven (DX, customer obsession). I had used Opik on a side project, and that came up multiple times." — Reddit r/MachineLearning, 2025

## Sources
- [Comet careers](https://www.comet.com/site/careers/)
- [Comet engineering blog](https://www.comet.com/blog/)
- [Opik (Comet's LLM eval product)](https://www.comet.com/opik)
- [Comet interview reports on Glassdoor](https://www.glassdoor.com/Interview/Comet-Interview-Questions-E2634259.htm)
- [Levels.fyi Comet](https://www.levels.fyi/companies/comet-ml)
