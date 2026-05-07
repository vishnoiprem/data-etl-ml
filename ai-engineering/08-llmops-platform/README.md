# 08 — LLMOps Platform

> **Customer problem:** GenAI use cases are being built as one-offs with no shared platform — every team rebuilding ingestion, eval, deployment, and observability. Build the **internal platform** that turns idea-to-production from 14 weeks → 3 weeks.

This project is the **capstone** of the portfolio — it composes the previous seven into a working, end-to-end pipeline that takes a use case from registered prompt → eval gate → deployment → observability → drift alarm.

---

## 1. Theory: LLMOps ≠ MLOps + LLM

Classic MLOps assumes a model has weights, accuracy, and a fixed prediction shape. LLMOps inherits some of that but adds:

| New concern | Why |
|---|---|
| **Prompt as artifact** | Prompts change weekly; weights monthly; version both |
| **Eval is the bottleneck** | LLM judges are expensive; can't gate every commit on full eval |
| **Cost is per-token, not per-request** | Cost varies 60× across model tiers |
| **Drift is in the **inputs** as much as the model** | Topic drift, data drift, prompt-injection rate |
| **Observability is the only ground truth** | No "ground truth label" for free-form responses in prod |

LLMOps composes the work in the other 7 projects:

| Capability | Implemented in |
|---|---|
| Inference + RAG | Project 1 |
| Model artifact / fine-tune | Project 2 |
| Agentic flows | Project 3 |
| Eval gates | Project 4 |
| Cost & routing | Project 5 |
| Security & audit | Project 6 |
| Prompt registry | Project 7 |
| **Pipeline + observability + drift** | **Project 8 (this one)** |

## 2. Pipeline stages

```
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ 1. ingest   │───▶│ 2. evaluate │───▶│ 3. promote  │───▶│ 4. observe  │
   │ register    │    │ regression  │    │ canary →    │    │ drift       │
   │ prompt      │    │ check       │    │ full        │    │ alarms      │
   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

Each stage is independent and idempotent. Failures roll back automatically; everything emits structured events to the event bus.

## 3. Architecture (production)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SageMaker Pipelines / Step Functions                   │
│                                                                              │
│   ingest ──▶ evaluate ──▶ promote (canary 5% → 25% → 100%) ──▶ monitor      │
│       │            │             │                                  │       │
│       ▼            ▼             ▼                                  ▼       │
│   Prompt      Eval harness   Bedrock         CloudWatch metrics + alarms    │
│   Registry    (Project 4)    Prompt Mgmt     EventBridge → SNS / Slack      │
│   (Project 7)                                                               │
│                                                                              │
│             EventBridge bus carries pipeline events for observability       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Drift detection

Three drift signals on production traffic:
1. **Topic drift** — distribution of intents shifts week-over-week (KL divergence)
2. **Length drift** — input/output token distributions change (Kolmogorov-Smirnov-style)
3. **Quality drift** — sampled LLM-as-judge scores trend down (CUSUM)

Drift alarms don't auto-rollback; they raise an alert and link to the most recent diffs in the prompt registry + model registry.

## 5. Quick Start

```bash
pip install -r requirements.txt
make demo
```

The demo runs an end-to-end pipeline:
1. **Ingest** — register a new prompt version
2. **Evaluate** — run regression eval (using Project 4's harness, embedded)
3. **Promote** — canary 5% → 25% → 100% with auto-rollback on bad telemetry
4. **Observe** — collect telemetry, compute drift, trigger alarm

You'll see structured events on the event bus, a deployment record, and a drift report.

## 6. What "Done" Looks Like

| Metric | Target |
|---|---|
| Idea → prod (golden path) | < 3 weeks |
| Pipeline runs / week | ≥ 50 |
| Auto-rollback rate (saves) | ≥ 1/month |
| Drift alarms with > 0.8 precision | ≥ 90% |
| Platform engineering NPS | ≥ +40 |
