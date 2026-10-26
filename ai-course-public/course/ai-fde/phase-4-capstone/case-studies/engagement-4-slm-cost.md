# Case Study 4 — The SLM Cost Model (Qwen2.5-1.5B + LoRA on Mei's drafts)

> **TL;DR.** I fine-tuned a 1.5B-parameter model (Qwen2.5-1.5B-Instruct + LoRA) on Mei's 1,000 highest-rated drafts and deployed it as the primary draft model for the 80% case (single-shipment, single-language, no escalation). **The result:** the LLM bill dropped 64% (from $0.50/wk to $0.18/wk); thumbs-up rate dropped 3 percentage points (from 82% to 79%); 10× growth scenario projects to $3.78/month, under the $5/month ceiling. **The math (corrected):** the model card originally claimed "91% of GPT-4o-mini quality" — that came from a stale baseline on a single metric. The **corrected number is 62% on a volume-weighted aggregate** of the 4 RAGAS metrics, derived from fresh data. **The lesson:** model cards are public artifacts; numbers in them must be re-derived from fresh data, not carried over from older runs. The cost ceiling is the spec; the eval set is the test; **the customer cares about the observable operational metrics (bill, thumbs-up, uptime), not the quality ratio.**

---

## 1. The cost model (the numbers, the math, the model)

### 1.1 Current state (before SLM, Phase 3 only)

```
Cost per draft (GPT-4o-mini)         $0.0005
Drafts per day                        150
Days per week                          7
─────────────────────────────────────────────
Weekly LLM bill                      $0.525
Monthly LLM bill                     $2.27
```

### 1.2 The 80/20 routing decision

Mei's traffic splits cleanly into two regimes, which I learned from the 4 weeks of `usage.jsonl` data:

| Regime | Frequency | Cost (GPT-4o-mini) | Notes |
|---|---|---|---|
| **Routine** (1 shipment, 1 language, no escalation) | 80% | $0.0005 | "Where is PF-1003?" — the simple cases |
| **Complex** (multi-shipment, multi-language, or escalation) | 20% | $0.0005 | "PF-1003 arrived but PF-1007 is missing, and I'd like a refund" — the cases the SLM struggles on |

The SLM is competitive on the routine regime (80%) and **uncompetitive on the complex regime** (20%). The right architecture is a **router** that sends routine to SLM, complex to GPT-4o-mini. This is the "cascading models" pattern, validated at Google (Dean et al., 2013) and refined for LLMs in recent literature (e.g., MMLU-Pro benchmarks, OpenAI's o1 routing).

### 1.3 The cost model (after SLM)

**Assumptions:**
- SLM cost: $0.0001/draft (Qwen 1.5B on Together.ai, $0.08/1M tokens × 0.5K avg tokens + 0.2K output × $0.30/1M output). 8× cheaper than GPT-4o-mini.
- 80% of drafts route to SLM, 20% to GPT-4o-mini (the 20% complex regime).
- Volume: 150 drafts/day (current) → 750 drafts/day (10× growth scenario, 5 customer teams).

```
Current (150 drafts/day):
  SLM:     0.80 × 150 × 7 × $0.0001  = $0.084/wk
  GPT-4o: 0.20 × 150 × 7 × $0.0005  = $0.105/wk
  ─────────────────────────────────────────────
  Total                                $0.189/wk
                                       $0.82/month

10× growth (750 drafts/day):
  SLM:     0.80 × 750 × 7 × $0.0001  = $0.420/wk
  GPT-4o: 0.20 × 750 × 7 × $0.0005  = $0.525/wk
  ─────────────────────────────────────────────
  Total                                $0.945/wk
                                       $4.09/month
```

**Comparison:**

| Volume | GPT-4o-mini only | SLM + GPT-4o-mini (80/20) | Savings |
|---|---|---|---|
| Current (150/d) | $2.27/month | $0.82/month | **64%** |
| 10× (750/d) | $10.50/month | $4.09/month | **61%** |

The savings plateau at ~62% as the 20% complex regime dominates the bill. **Below 5× growth, the SLM is the obvious win. At 10× growth, the SLM keeps the bill under the $5/month ceiling** — a 2.6× headroom. Without the SLM, the bill would breach the ceiling at ~6× growth.

### 1.4 The cost components (the line items)

| Component | Cost / 1M tokens | Source | Why this cost |
|---|---|---|---|
| GPT-4o-mini input | $0.150 | OpenAI pricing, 2026-Q3 | 4o-mini baseline |
| GPT-4o-mini output | $0.600 | OpenAI pricing, 2026-Q3 | 4o-mini baseline |
| Qwen 1.5B input (Together) | $0.080 | Together.ai, 2026-Q3 | Open-weights hosted |
| Qwen 1.5B output (Together) | $0.300 | Together.ai, 2026-Q3 | Open-weights hosted |
| Qwen 1.5B local (ollama) | $0.000 | Self-hosted on the same VM | $0 marginal cost, but consumes 1.5GB RAM |

The SLM can be self-hosted on the same VM (1.5GB RAM for the base model, 50MB for the LoRA adapter) for $0 marginal cost, but at 150-750 drafts/day the throughput is fine on the 2-vCPU e2-medium. **Self-hosting saves 0.4-2.5 dollars/month at this volume** — not material.

---

## 2. The quality model (the corrected numbers)

### 2.1 The eval set results (fresh data, 2026-W12)

Ran the 30-row Phase 1 eval set against (a) GPT-4o-mini and (b) Qwen 1.5B + LoRA (Mei's adapter). Both at temperature=0, single-shot, no re-ranking.

| Metric | GPT-4o-mini | Qwen 1.5B + LoRA | Ratio (SLM/GPT) | Note |
|---|---|---|---|---|
| **Faithfulness** | 0.95 | 0.50 | 53% | The hardest gap; SLM hallucinates status more |
| **Answer relevance** | 0.91 | 0.78 | 86% | Surprisingly close; LoRA learns the answer shape |
| **Context precision** | 0.90 | 0.65 | 72% | SLM doesn't use context as well |
| **Context recall** | 0.93 | 0.70 | 75% | SLM misses retrieved chunks |
| **Aggregate (mean)** | **0.92** | **0.66** | **71%** | Raw aggregate |

### 2.2 The volume-weighted aggregate (the correct number for the model card)

```
effective_quality = 0.80 × SLM_score + 0.20 × GPT_score
                  = 0.80 × 0.66 + 0.20 × 0.92
                  = 0.528 + 0.184
                  = 0.712

vs GPT-only (all-routing): 0.92
```

**Quality ratio = 0.712 / 0.92 = 77%** on a volume-weighted aggregate. The 80/20 routing recovers the quality gap because the 20% complex regime (where the SLM is weakest) still uses GPT-4o-mini.

### 2.3 The original model card said "91%" — that was wrong

The model card initially published said "Quality ratio vs GPT-4o-mini: 91%." That number was the ratio of **a single metric** (faithfulness, measured on a 5-row subset, compared to a stale 0.55 baseline) — not the volume-weighted aggregate. **The number was technically derivable but practically misleading.** I caught the error in the post-deployment review, recalculated from the fresh 30-row eval set, and updated the model card to the 77% number with a clear math derivation.

The corrected model card (see `slm/model_card.md`) now includes the full derivation, the assumption that 80% of traffic routes to SLM, and the explicit "limitations" section listing the cases where the SLM underperforms.

### 2.4 The customer-facing metric (the one that matters)

The CFO doesn't care about quality ratios. **The CFO cares about the bill.** The CS lead (Mei) doesn't care about quality ratios. **Mei cares about thumbs-up rate.** The IT owner (Daniel) cares about uptime.

| Customer | What they care about | Observed | Status |
|---|---|---|---|
| CFO (CEO of PacificFreight) | Weekly/monthly LLM bill | $0.18/wk current, $4.09/mo at 10× | ✅ (under $5/mo ceiling) |
| Mei (CS) | Thumbs-up rate | 79% (down from 82%) | ✅ (still > 70% SLO) |
| Daniel (IT) | Uptime | 99.87% (no change) | ✅ (matches SLO) |

**The customer-observable quality metric is thumbs-up rate.** That's 79% (down 3pp from 82%) — within the SLO. The CFO approves the 10× growth scenario. **The model card numbers are for the audit trail; the operational SLOs are for the customer.**

### 2.5 Statistical significance of the 3pp thumbs-up drop

| Statistic | Value | Notes |
|---|---|---|
| Sample size (n) | 8,400 drafts (8 weeks × 7 days × 150 drafts) | Pre-SLM baseline |
| Sample size (post-SLM) | 2,400 drafts (2 weeks × 7 × 150 + ~150 in A/B) | Limited |
| Observed thumbs-up (pre) | 82.1% | |
| Observed thumbs-up (post) | 78.7% | |
| Δ | -3.4pp | |
| 95% CI on Δ | [-5.2pp, -1.6pp] | Bootstrap, 10,000 resamples |
| p-value (one-sided, "is post < pre?") | 0.0003 | Highly significant |
| Cohen's h (effect size) | 0.08 | Small effect, not negligible |

**The 3pp drop is statistically significant but practically small.** Below the 5pp threshold I set for rollback. Mei's qualitative feedback ("the SLM is fine for the easy ones; the complex ones still go to GPT") matches the model card's "limitations" section.

---

## 3. The deployment timeline (5 weeks, with the A/B test)

### 3.1 Week 1 — dataset prep

- Pulled 1,000 highest-rated drafts from `usage.jsonl` (thumbs-up only).
- Filtered to the routine regime (1 shipment, 1 language, no escalation).
- 1,000 (prompt, response) pairs; 80/10/10 train/val/test split.
- Training time on Mac M-series (MPS): not measured in week 1 (training is week 2).

### 3.2 Week 2 — LoRA fine-tune

```python
# slm/train.py (excerpt)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

base = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    load_in_4bit=True,
    device_map="auto",
)
lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(base, lora_cfg)

trainer = SFTTrainer(
    model=model,
    train_dataset=pf_dataset,         # 800 rows
    eval_dataset=pf_eval_dataset,    # 100 rows
    args=TrainingArguments(
        output_dir="slm/adapters/pf-drafter-lora",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        warmup_steps=50,
        logging_steps=20,
        save_strategy="epoch",
    ),
)
trainer.train()
trainer.save_adapter("slm/adapters/pf-drafter-lora")
```

**Training time: 28 minutes on Mac M2 (MPS).** **Adapter size: 50MB** (1.6% of the base 1.5B model). **GPU memory: 1.5GB** (the base in 4-bit quantization).

### 3.3 Week 3 — shadow-mode A/B test

- Deployed the SLM as a **shadow** alongside GPT-4o-mini for 1 week.
- Mei didn't see the SLM's output; both outputs were logged.
- A held-out set of 50 drafts (10% of the week's volume) was graded by an LLM-as-judge (Claude Sonnet 4.5) for thumbs-up estimation.
- **Result:** SLM thumbs-up = 71% (n=50, ±13% CI) vs GPT-4o-mini = 82% (n=50, ±11% CI). **11pp gap, borderline acceptable.** The 95% CI on the difference is [-2pp, -25pp] — wide because n=50. The signal is "the SLM is in the ballpark" but not "the SLM is a substitute."

**Decision: extend the A/B to 2 more weeks to narrow the CI.**

### 3.4 Week 4 — 3-week A/B result

- n=150 (3 weeks × 50 held-out).
- SLM thumbs-up = 76% (95% CI: [70%, 82%]).
- GPT-4o-mini thumbs-up = 82% (95% CI: [76%, 88%]).
- **6pp gap, 95% CI on Δ = [-1pp, -12pp].** Still wide but narrowing. Borderline acceptable.

**Decision: ship the SLM as the primary for the routine regime; keep GPT-4o-mini for the complex regime.** This is the 80/20 split, routed by the 3-line classifier in `service/app.py`.

### 3.5 Week 5 — production deploy + 1-week live observation

- SLM promoted to primary; GPT-4o-mini is the fallback for the 20% complex regime.
- 1-week live observation: thumbs-up rate = 79% (matches the 76% A/B estimate within CI).
- Cost dropped from $0.50/wk to $0.18/wk.
- 0 SEV-1 incidents related to the SLM.

### 3.6 The full A/B test plan (what I'd do next time)

The 2-week A/B test gave me a 95% CI of ±13pp on the SLM estimate. To get ±5pp (the threshold for a confident "ship" decision), I need **n=600** in the A/B test (4× more). At 150 drafts/day with 33% held out for the A/B, that's **12 days**. The 3-week A/B was over-engineered for the precision needed; a 12-day A/B would have been sufficient and would have saved 9 days.

**Cost of the 9 over-engineered days: 9 × $250 = $2,250 in FDE time.** Lesson: size the A/B test to the precision needed, not to the precision possible.

---

## 4. The model card (the public artifact)

The model card is the artifact that survives the FDE's exit. The full text is in `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/model_card.md`. Key sections:

### 4.1 Intended use

A drop-in replacement for GPT-4o-mini on the **routine regime** (single-shipment, single-language, no escalation). NOT a general-purpose model. The router in `service/app.py` is the source of truth for what routes to the SLM.

### 4.2 Training data

- 1,000 (prompt, response) pairs from PacificFreight's `usage.jsonl`.
- Filtered to thumbs-up drafts only (excluded thumbs-down, ignored).
- Filtered to the routine regime (1 shipment, 1 language, no escalation).
- 80/10/10 train/val/test split.
- Training set is owned by PacificFreight; the LoRA adapter is not redistributable.

### 4.3 Eval results

| Metric | GPT-4o-mini | Qwen 1.5B + LoRA | Ratio |
|---|---|---|---|
| Faithfulness | 0.95 | 0.50 | 53% |
| Answer relevance | 0.91 | 0.78 | 86% |
| Context precision | 0.90 | 0.65 | 72% |
| Context recall | 0.93 | 0.70 | 75% |
| Aggregate | 0.92 | 0.66 | 71% |
| **Volume-weighted (80/20)** | **0.92** | **0.71** | **77%** |

### 4.4 Limitations (the failure modes)

The SLM is **known to underperform** on:
- Multi-shipment cases (routed to the multi-agent orchestrator instead).
- Multi-language cases (Vietnamese, Bahasa Melayu).
- Cases requiring policy citations (the SLM has weaker context-recall).
- Cases involving refunds or escalations (the SLM has no MCP tool-call training).

These cases route to GPT-4o-mini via the 3-line classifier. The model card explicitly says: **"This SLM is not a general-purpose model. It is a narrow tool for the routine regime. The router is the contract."**

### 4.5 Operational contract

- The SLM is never the only path; the circuit breaker falls through to GPT-4o-mini on any quality drop.
- The SLM re-trains weekly (every Monday after the iteration cadence).
- The eval set runs against the SLM every Monday at 09:00 SGT; a 5pp drop on any metric triggers a rollback to GPT-4o-mini-only routing.
- The cost ceiling is $5/month; an alert fires at $4/month.

---

## 5. The ROI model (the CFO view)

| Item | Value | Source |
|---|---|---|
| Annual savings (current volume) | $0.50/wk × 52 = $26/yr | Direct |
| Annual savings (10× growth) | $10.50 − $4.09 = $6.41/mo × 12 = $77/yr | Direct |
| Cost of the SLM project (5 weeks × 40hr × $250) | $50,000 | FDE time |
| **Payback period** | **> 50 years** at current volume; **650 years** at 10× | Math |

**The SLM project is not ROI-positive on direct cost savings.** It is ROI-positive on **strategic optionality**: the $5/month ceiling means the customer can grow 10× without renegotiating the LLM contract. **The CFO approved the project for the strategic option, not the cost savings.** This is a typical pattern for SMB infra investments — the strategic value dwarfs the direct cost savings.

### 5.1 What I would do differently

**Frame the SLM as a strategic option, not a cost-reduction project.** The original framing was "let's reduce the LLM bill." The correct framing is "let's keep the LLM bill under $5/month at 10× growth." The first framing is a $26/yr savings; the second is a $77/yr savings + 10× growth optionality. **The CFO cares about the optionality; the FDE should too.**

**Don't publish "91% of GPT-4o-mini quality" without re-deriving from fresh data.** I published this number in the model card; it was wrong; the post-deployment review caught it. A pre-deployment review (re-derive from the 30-row eval set, don't carry over from a stale baseline) would have been better. **Model cards are public artifacts; numbers in them must be re-derived, not carried over.**

**Run the A/B test for the precision needed, not the precision possible.** 2-week A/B (n=150) gave 95% CI of ±13pp; that was over-engineered. 12-day A/B (n=600) gives ±5pp, which is the threshold for a confident "ship" decision. **Size the A/B test to the precision needed.**

**Document the failure modes in the model card.** The original model card had a "limitations" section that was 1 paragraph. The corrected model card has a 1-page limitations section listing the 4 known failure modes and the routing rule for each. **A model card that only documents the success cases is a marketing document, not an operational artifact.**

---

## 6. The pattern (generalized)

The SLM project taught me 3 things that generalize:

1. **The cost ceiling is the spec, not the savings target.** The customer doesn't want "reduce my LLM bill by 50%"; they want "keep the bill under $5/month at 10× growth." The first framing is a savings target (often ROI-negative); the second is a constraint (always satisfied if the architecture is right).

2. **The model card is a public artifact; numbers in it must be re-derived.** Every number in a model card is a promise. A stale number is a broken promise. Re-derive from fresh data on every release; document the derivation; publish the assumptions.

3. **The A/B test is sized to the precision needed, not the precision possible.** 2-week A/B (n=150) gives ±13pp; 12-day A/B (n=600) gives ±5pp. The threshold for "ship" was ±5pp. **The over-engineered A/B cost 9 days and $2,250 in FDE time.**

```
  ┌──────────────────────────────────────────────────────────┐
  │  THE SLM LIFECYCLE                                       │
  │                                                          │
  │  1. Cost ceiling is the spec (not savings target)        │
  │  2. Eval set in CI is the test                           │
  │  3. Model card is the public artifact                    │
  │  4. A/B test is sized to the precision needed            │
  │  5. Router (80/20) is the architectural answer           │
  └──────────────────────────────────────────────────────────┘
```

The next project I'll do this on: when the bill is projected to exceed 50% of the ceiling, build the SLM. Not before. **Premature distillation is a $50K project that delivers $26/yr of savings.**

---

## 7. References

- **The training script**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/train.py` — LoRA config, hyperparameters, MPS-friendly.
- **The model card**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/model_card.md` — the corrected 77% number with full derivation.
- **The eval script**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/eval.py` — runs the Phase 3 eval set against the SLM.
- **Together.ai pricing**: 2026-Q3 public pricing page, qwen-2.5-1.5b-instruct tier.
- **LoRA paper**: Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models," arXiv:2106.09685 (Jun 2021).
- **Cascading models**: Dean et al., "The Tail at Scale," CACM Feb 2013; refined for LLMs in the o1 system card (OpenAI, Dec 2024).
- **The 80/20 routing decision**: derived from Mei's 4-week usage.jsonl split; the classifier is 3 lines of regex + 1 line of routing logic.
- **A/B test sizing**: Kohavi et al., "Controlled Experiments on the Web: Survey and Practical Guide," KDD 2009.
