# ML / MLOps / AI-Ready Platform Question Prep — "Solid understanding of machine learning, MLOps, and building AI-ready data platforms"

> **Purpose:** Full preparation file for the ML/MLOps/AI-platform qualification line on the role's "What you bring" list. This is a **qualifications** line (depth test), not a responsibility line. The interviewer is testing whether you can speak credibly about ML systems, MLOps practice, and the data foundations that make AI products safe to ship. First in the qualifications series.

---

## The Question

- **Round:** Onsite 1 (technical panel — Vu Bui, Que Tran, Son Dao) and Onsite 2 (Duke Nguyen, VP Engineering); can surface in Onsite 3 (Rajesh Krishnan, SVP Engineering) for the "AI transformation" angle
- **Source:** Job posting, "AI & Leadership" qualifications, line 48 of `README.md`
- **Verbatim:** *"Solid understanding of machine learning, MLOps, and building AI-ready data platforms."*
- **Likely probes:**
  - "Walk me through your MLOps stack."
  - "How do you build an AI-ready data platform?"
  - "Feature store — when does it earn its place?"
  - "How do you version models, prompts, and retrieval policies?"
  - "How do you detect model drift?"
  - "What's the difference between online and offline evaluation?"
  - "How do you prevent training-serving skew?"
  - "Shadow, canary, or A/B for models?"
  - "How do you handle model rollback?"
  - "What is a model card? A feature card?"
  - "How do you make a model reproducible?"

---

## Framework Used

- **Strategic:** **Job → Data → Model → Serve → Monitor → Govern** (the ML lifecycle spine)
- **Tactical:** **D-I-V-O** for any ML decision: **Data → Induction → Validation → Output**
- **Anchor sentence:** *"AI-ready means the data, labels, retrieval, and evaluation are treated as platform features — not as a notebook on someone's laptop."*

🔵 **Hook: "Job first. Data second. Eval before model. Eval after model. Then ship."**

---

## 60–90 Second Spoken Answer (lead with this)

> An AI-ready platform is one where the **ML lifecycle is a product**, not a notebook. Five things have to be platform features: **data and label pipelines**, **feature and retrieval stores**, **training and evaluation harnesses**, **serving and routing**, and **monitoring and governance**.
>
> For data: governed ingestion, versioned datasets, lineage, and PII/secret redaction **before** anything reaches a model. For features: an online + offline store with point-in-time correctness so training matches serving. For retrieval: hybrid (BM25 + vector) with tenant filters, citations, and abstention. For evaluation: a golden set, versioned prompts and models, and LLM-as-judge calibrated against humans. For serving: shadow, canary, kill switch, per-tenant budgets. For monitoring: drift, calibration, slice regressions, and the difference between model monitoring and product-outcome monitoring.
>
> I avoid **training-serving skew** by making the same feature code run in both paths. I avoid **silent regressions** by requiring eval to pass on a golden set *before* a model can be promoted.
>
> For Katalon: AI is the product. The flakiness model, failure triage, recommendations, and TestOps assistant all ride on this foundation. I'd build it once, well, then every new AI feature is a config, not a project.

⏱️ ~95 seconds. Trim if rushed.

---

## The ML Lifecycle Spine (memorize this)

```
1. JOB-TO-BE-DONE
   Task + user + decision + cost of being wrong
        │
        ▼
2. DATA
   Governed ingest, labels, lineage, PII/secret scan
        │
        ▼
3. FEATURES & RETRIEVAL
   Online + offline parity, point-in-time, tenant filter
        │
        ▼
4. TRAINING & EVAL
   Versioned golden set, metrics, LLM-as-judge, ablation
        │
        ▼
5. SERVE & ROUTE
   Shadow → canary → in-prod, kill switch, budgets
        │
        ▼
6. MONITOR & GOVERN
   Drift, calibration, slice regressions, audit, model card
        │
        ▼
7. RETIRE / EXPAND
   Verified value → expand; or sunset cleanly
```

🔵 **Hook: "If the eval isn't a product, the model isn't either."**

---

## What "AI-Ready Data Platform" Actually Means (the four categories)

| Category | What it means | Concrete |
|---|---|---|
| **Data foundations** | Governed, labeled, lineage-tracked datasets ready for training and retrieval | Catalog, contracts, PII redaction, label versioning, eval sets |
| **Feature & retrieval** | Online/offline parity, hybrid retrieval, tenant isolation | Feature store, vector index, BM25, metadata filters, citations |
| **Training & evaluation** | Reproducible training + golden-set eval before promotion | Training pipelines, golden set, LLM-as-judge, ablation harness |
| **Serving & monitoring** | Shadow/canary, drift/calibration monitoring, rollback | Model router, kill switch, per-tenant budgets, alert wiring |

🔵 **Hook: "Four categories. Build the foundation first. Features ride on it. Then models."**

---

## MLOps Stack: the 8 Layers

| Layer | What it does | Common picks (illustrative) |
|---|---|---|
| **Ingestion** | Capture events, logs, signals | Kafka/MSK, Kinesis, Pub/Sub |
| **Storage** | Durable, versioned, partitioned | S3 + Iceberg, Delta, GCS |
| **Transform** | Clean, conform, deduplicate | Spark, dbt, Beam |
| **Feature store** | Online + offline, point-in-time | Feast, Tecton, Databricks Feature Store, Vertex |
| **Training** | Reproducible, scalable | Ray, Spark, Vertex Training, SageMaker, custom |
| **Evaluation** | Golden set, metrics, LLM-as-judge | RAGAS, Promptfoo, custom harnesses |
| **Serving** | Online, batch, async, agentic | vLLM, Triton, SageMaker, Bedrock, Vertex |
| **Monitoring** | Drift, calibration, cost, latency | Evidently, whylogs, Arize, custom |

🔵 **Hook: "You don't need all eight on day one. You need ingestion + storage + transform + eval + serving. Features and monitoring earn their place as you scale."**

---

## Feature Store: When It Earns Its Place

**Default answer: skip until you feel the pain.**

| Pain | What feature store solves |
|---|---|
| Training-serving skew (model accuracy drops in prod) | Online + offline parity, point-in-time joins |
| Duplicate feature code across teams | Single source of truth per feature |
| Slow iteration (data scientist waits for engineering) | Self-serve feature definitions |
| Compliance audit (where did this feature come from?) | Lineage, owner, freshness, retention |

**Decision rubric:**
- ≥3 teams building features
- Production model accuracy is limited by data, not model
- Compliance asks for feature lineage
- Online + offline latency is a bottleneck

**If you don't have all four:** start with a feature catalog + versioned definitions, then graduate to a real store.

🔵 **Hook: "A feature store is a forcing function for hygiene. Don't buy it to look mature; buy it because the cost of not having it is visible."**

---

## Training-Serving Skew (the silent killer)

**What it is:** Features computed differently (or at different times) in training vs serving → model appears great offline, fails in production.

**How to prevent it:**

| Mechanism | What it does |
|---|---|
| **Same code path** | One feature definition runs in both batch and online |
| **Point-in-time joins** | No future leakage during training |
| **Schema + value validation** | Catch distributions shifting between paths |
| **Backfill discipline** | Reproduce training features exactly for debugging |
| **Parity tests in CI** | Train vs serve value distribution compared on a sample |

🔵 **Hook: "If your training notebook can't reproduce the features it saw last Tuesday, your model is on borrowed time."**

---

## Model Versioning (the actual practice)

A "model" in production is a **bundle**, not a file:

```yaml
model_version: failure-triage-v17
created_at: 2026-10-01
owner: ai-data-team
training_data:
  dataset: gold.test_results_labeled
  version: 2026-09-28
  sha256: a1b2c3...
features:
  spec: features/failure_triage.yaml
  sha256: d4e5f6...
prompt:
  template: prompts/failure_triage_v8.j2
  sha256: 9f8e7d...
retrieval:
  index: tenant_test_context
  version: 12
  policy: retrieval/tenant_filter_v3.yaml
serving:
  endpoint: endpoints/failure-triage-v17
  replicas: 3
  fallback_model: failure-triage-v15
evaluation:
  golden_set: evals/failure_triage_v17.jsonl
  metrics: {macro_f1: 0.81, citation_acc: 0.93, abstain_rate: 0.07}
safety:
  prompt_injection_tests: passed
  pii_redaction: enabled
```

**Rule:** promote by reference (version), not by file copy. Every inference records which bundle produced it.

🔵 **Hook: "If you can't answer 'exactly what produced this prediction?', you don't have a model in production. You have a hope."**

---

## Evaluation: Offline + Online + Online-offline

| Layer | What it does | Examples |
|---|---|---|
| **Offline (golden set)** | Compare candidate against baseline before promotion | macro-F1, citation accuracy, abstention quality, calibration |
| **Pre-release (red-team)** | Safety, injection, PII leakage, edge cases | Adversarial prompts, cross-tenant tests, secret patterns |
| **Online (shadow)** | Side-by-side with baseline, no user impact | Acceptance, edit-distance, escalation, latency, cost |
| **Online (canary)** | 1–5% of traffic, with kill switch | Same metrics + business outcome (e.g. time-to-triage) |
| **Online (full A/B)** | Verified lift, with control group | Decision time, defect detection, retention |

**The mistake:** shipping on offline metric alone. **The other mistake:** shipping on thumbs-up alone.

🔵 **Hook: "Offline measures capability. Online measures value. You need both."**

---

## LLM-as-Judge: Use Carefully

**Good uses:**
- Scalable scoring across thousands of outputs
- Structured criteria (citation correctness, format compliance)
- Pre-filter before human review

**Danger zones:**
- Self-preference (judge ranks its own outputs higher)
- Style bias (ranks fluent text over correct text)
- Hidden calibration drift (judge silently changes)

**Calibration rule:** Periodically sample 200 LLM-judge scores, score them with humans, compute Cohen's kappa. If kappa < 0.7, recalibrate or fall back to humans.

🔵 **Hook: "LLM-as-judge is a force multiplier, not a verdict."**

---

## Drift: What to Monitor

| Layer | What you watch | How |
|---|---|---|
| **Input drift** | Distribution of features/queries shifted | PSI, KS test, embedding distance |
| **Output drift** | Distribution of predictions shifted | Label/feedback changes, score histograms |
| **Confidence calibration** | Stated confidence matches actual accuracy | Reliability diagram, ECE |
| **Slice regressions** | Performance dropped on a segment (tenant, language, framework) | Per-slice metrics, alert on trend |
| **Feedback drift** | Thumbs-down rate, override rate, escalation rate | Time series, alert on slope |
| **Cost / latency drift** | Provider pricing or latency changed | Per-request metrics, budget alarms |

🔵 **Hook: "Alert on trend, not just threshold. A slow drift is a fast outage waiting to happen."**

---

## Shadow / Canary / A/B: Which When

| Pattern | When | Risk | Reversibility |
|---|---|---|---|
| **Shadow** | New model, new retrieval, new prompt — must be safe | None (no user impact) | N/A |
| **Canary** | Verified offline, want first real-user signal | Low (1–5% of traffic) | High (kill switch) |
| **A/B** | Need causal evidence of business lift | Medium (50/50 split) | Medium (rollback possible) |
| **Full rollout** | Canary + A/B both passed, business sponsor signed off | Higher | Lower (now in production) |

**Always:** kill switch, rollback to last-known-good model, per-tenant opt-out.

🔵 **Hook: "Shadow is free safety. Canary is cheap signal. A/B is real evidence. Don't skip steps."**

---

## MLOps Governance (NIST AI RMF in practice)

| Function | What it means at Katalon |
|---|---|
| **Govern** | Model inventory, model cards, owner per model, intake for new AI |
| **Map** | Data lineage, customer opt-in, risk tier per use case |
| **Measure** | Eval harness, red-team, calibration, drift, cost/latency |
| **Manage** | Rollback plans, kill switches, incident process, periodic re-evaluation |

🔵 **Hook: "Same vocabulary as our enterprise buyers. NIST AI RMF."**

---

## Model Card (skeleton)

```yaml
name: failure-triage-classifier
version: 17
owner: ai-data-team@company.com
intended_use: Suggest failure category for failed test results, internal tooling
out_of_scope: Production pass/fail decisions, customer-visible verdicts
training_data:
  source: gold.test_results_labeled
  window: 2025-04-01 to 2026-09-15
  tenant_opt_in: required
metrics:
  macro_f1: 0.81
  citation_accuracy: 0.93
  abstain_rate: 0.07
  cross_tenant_leakage: 0
safety:
  prompt_injection: tested
  pii_redaction: enabled
  tenant_isolation: enforced at retrieval
limitations:
  - English-language stack traces only
  - Newer frameworks may underperform
monitoring:
  drift_check: daily
  calibration_check: weekly
  slice_review: monthly
rollback:
  fallback_model: failure-triage-v15
  kill_switch: features/failure_triage/disabled
```

🔵 **Hook: "No model card, no production. Same as no runbook, no on-call."**

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "Walk me through your MLOps stack."

🟢 *"Five layers, built bottom-up. Ingest and store on governed foundation. Feature/retrieval store with online + offline parity. Training + eval harness with versioned golden set. Serving with shadow/canary and kill switch. Monitor drift, calibration, cost, latency. Pick tools per layer based on workload; don't buy a vendor that promises all eight layers if you only need four."*

### Q2: "How do you build an AI-ready data platform?"

🟢 *"Four categories of capability. (1) Data foundations — governed ingest, labels, lineage, PII/secret redaction. (2) Features and retrieval — online + offline parity, hybrid retrieval, tenant filter. (3) Training and evaluation — reproducible training, golden set, LLM-as-judge calibrated against humans. (4) Serving and monitoring — shadow/canary, drift/calibration, rollback. Build the foundation first; everything else is a config."*

### Q3: "Feature store — when does it earn its place?"

🟢 *"When you have three signals: ≥3 teams building features, production accuracy is limited by data not model, compliance asks for lineage. Until then, a feature catalog with versioned definitions and point-in-time joins gets you 80% of the value at 20% of the cost."*

### Q4: "How do you version models, prompts, and retrieval policies?"

🟢 *"Bundle, not file. Each model version records training data version, feature spec, prompt template, retrieval index version, and policy. Promote by reference. Every inference records which bundle produced it. If you can't answer 'exactly what produced this prediction?', you don't have a model in production — you have a hope."*

### Q5: "How do you detect model drift?"

🟢 *"Three layers. Input drift — PSI, KS, embedding distance. Output drift — label/feedback distribution, score histograms. Confidence calibration — reliability diagram, ECE. Slice regressions on critical segments (tenants, languages, frameworks). Alert on the trend, not just the threshold."*

### Q6: "What's the difference between offline and online evaluation?"

🟢 *"Offline measures capability on a fixed set. Online measures value in production. Offline lets you compare candidates cheaply and safely. Online is the only way to measure verified task outcomes. You need both — offline gates promotion, online gates expansion."*

### Q7: "How do you prevent training-serving skew?"

🟢 *"Same feature code in both paths. Point-in-time joins for training. Schema and value validation between paths. Parity tests in CI. Reproducible backfills. The cardinal sin is a notebook feature definition that no one else can re-run."*

### Q8: "Shadow, canary, or A/B for a new model?"

🟢 *"All three, in order. Shadow first — no user impact, side-by-side with baseline. Canary next — 1–5% of traffic, with kill switch. A/B last — when you need causal evidence of business lift. Don't skip shadow. Don't go straight to A/B. Each step has a different cost and a different risk."*

### Q9: "How do you handle model rollback?"

🟢 *"Last-known-good model version is always loaded as fallback. Kill switch is a config, not a redeploy. Per-feature, per-tenant opt-out. Rollback tested in chaos game days. Rollback decision is the model owner's call, not the on-call engineer's."*

### Q10: "What is a model card? A feature card?"

🟢 *"Model card is a 1-page record of what the model is for, what it's not for, who owns it, what data trained it, what metrics it scored, what its safety checks were, and how to roll it back. Feature card is the same shape for a feature: definition, owner, freshness, lineage, downstream consumers, retention. If the card doesn't exist, the artifact isn't production-ready."*

### Q11: "How do you make a model reproducible?"

🟢 *"Three things. (1) Pin the bundle — data version, feature spec, prompt, retrieval policy, hyperparameters, environment. (2) Capture the run — code commit, container image, seed, runtime. (3) Re-run is a single command. If any of the three is missing, the model is a hope."*

### Q12: "How do you scale AI from one team to many?"

🟢 *"Platform the common parts. Shared eval harness. Shared feature store. Shared retrieval. Shared serving infra. Shared model card template. Then each team is a config, not a project. The mistake is letting each team build its own stack — the org pays for it in MTTR and inconsistency."*

### Q13: "How do you handle a customer demanding deletion of data that contributed to a model?"

🟢 *"Document the policy with Legal first. If the customer's data was used in training with their opt-in, document whether technical removal is possible — for many models, it's not. If not, the customer contract + product policy define what happens. Either way, the lineage + consent records are the evidence. Don't bluff — say what you can and can't do, then offer alternatives (delete from retrieval, exclude from future re-trains)."*

### Q14: "What is the difference between model monitoring and product-outcome monitoring?"

🟢 *"Model monitoring = drift, calibration, latency, errors at the model level. Product-outcome monitoring = does the user accept it, does it reduce their time-to-decision, does the business metric move. Both are needed. Product-outcome is the ultimate one — a great model with no business impact is a great waste."*

### Q15: "How do you decide between fine-tuning and RAG?"

🟢 *"Default to RAG. RAG is the right answer when the knowledge is constantly changing, when you need citations, when the same model must serve many tenants, and when you can't afford a per-tenant training run. Fine-tune when the task is well-defined, the data is stable, the latency budget is tight, and a smaller fine-tuned model beats a larger prompted one. The trap: fine-tuning as a first move."*

---

## Anti-Patterns (red-flag answers)

- ❌ "We use SageMaker / Vertex / Databricks for everything" — that's vendor gravity, not design
- ❌ "We have a feature store" without saying what pain it solved
- ❌ "Models are versioned in git" — models are bundles, not files
- ❌ "Accuracy is 92%" without baseline, calibration, or guardrails
- ❌ "We'll fine-tune" as the first move — usually RAG + better prompts win first
- ❌ "Our LLM judge is reliable" — calibrated against humans, on a sample, every release
- ❌ "We'll add governance later" — without it, customer data leaks into training
- ❌ "Users like it" — engagement, not task outcome
- ❌ "We'll deploy with canary" — without kill switch, that's wishful thinking

---

## Three Things Katalon Is Hiring For (tied to this line)

Per Section 1 of `Katalon_Head_of_Data_Interview_Prep.md`:

1. **Builder-leader** — hands-on credible. *Demonstrated by:* naming real tools in the eight-layer stack and saying why.
2. **AI-readiness owner** — RAG, eval, governance. *Demonstrated by:* the lifecycle, the bundle, the eval-before-promotion discipline.
3. **Cross-functional translator** — speak CFO / lawyer / engineer. *Demonstrated by:* the ROI + risk framing.

🔵 **This qualification IS the AI-readiness signal. Treat it as a system-design question, not a definition question.**

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Sections 9–10 (AI platform + flakiness), Section 14 (platform selection)
- **Sister files:**
  - `strategy-question-prep.md` (responsibility line 1)
  - `platform-architecture-question-prep.md` (responsibility line 2)
  - `governance-question-prep.md` (responsibility line 3)
  - `partnerships-question-prep.md` (responsibility line 4)
  - `ai-adoption-question-prep.md` (responsibility line 5)
  - `tech-evaluation-question-prep.md` (responsibility line 6)
  - `team-leadership-question-prep.md` (responsibility line 7)
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find S4 (AI prototype → production)
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] ML lifecycle spine (7 steps) said in 30 sec
- [ ] Eight-layer MLOps stack named with examples
- [ ] Four AI-ready categories named
- [ ] "Feature store — when does it earn its place?" answer ready
- [ ] Model versioning as a bundle (yaml example ready)
- [ ] Training-serving skew mitigation (5 mechanisms)
- [ ] Shadow / canary / A/B order stated
- [ ] Drift: input / output / calibration / slice / cost
- [ ] LLM-as-judge calibration caveat ready
- [ ] Model card skeleton ready
- [ ] One real ML/MLOps story (S4) from your own career
- [ ] No invented tools or numbers

---

## Closing Sentence (if asked "anything else?")

> AI-readiness isn't a feature you buy. It's a **discipline you install**: bundle before deploy, eval before promotion, monitoring before scale, rollback before regret. **Job first. Data second. Eval third. Model fourth. Then ship — and watch.**
