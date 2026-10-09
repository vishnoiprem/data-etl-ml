# Lesson T3 — Fine-tuning and serving an SLM: when to distill, how to ship

> **Phase 4, Technical Track, Lesson 3.** When the cost ceiling
> forces a smaller model, and how to distill a 1.5B model on
> Mei's drafts without a GPU cluster.

## 🎯 Outcome

By the end of this lesson you can:

- **Recognize** when a cost ceiling forces a smaller model
  (the signs: 10× customer growth, $20/month projected spend,
  CFO asks "can we halve this?").
- **Build a training set** from the drafter's `usage.jsonl`,
  filtered to high-quality (thumbs-up) drafts.
- **LoRA-fine-tune** a 1.5B model on a Mac M-series or a single
  GPU, in ~30 minutes.
- **Serve** the adapter on top of the base model (ollama or
  vLLM) and verify it meets a quality bar against the eval set.

## 🧠 Mindset

The PacificFreight cost ceiling is $5/month. With GPT-4o-mini at
$0.50/week, Mei is fine. With 10× customer growth (5 customer
teams), the bill is $5/week = $20/month. **That's 4× the
ceiling.** The CFO asks: can we halve this?

The answer is **distillation:** fine-tune a smaller model on the
drafter's own outputs, so Mei's CS tool can use the SLM for
the 80% case (single-shipment, single-language, no
escalation) and fall back to GPT-4o-mini for the 20% case
(multi-shipment, multi-language, escalation).

**The lesson:** distillation is a *cost* optimization, not a
*quality* optimization. The SLM is ~91% of GPT-4o-mini's
quality at ~5% of the cost. The customer's acceptable threshold
is "≥ 90% of the larger model's quality at a fraction of the
cost." If the SLM meets that bar, ship it. If it doesn't,
don't.

**The eval set is the spec; the cost model is the test.** A
fine-tuned model that scores 99% of the larger model's quality
is a research result; a fine-tuned model that scores 91% at 5%
of the cost is a *production deployment.*

## 🛠️ Practice

You are extending the PacificFreight SLM pipeline to add a
**weekly re-train** step. The drafter's `usage.jsonl` is updated
every Monday at 09:00 SGT (after the weekend email backlog).
You want the SLM to track Mei's evolving style.

You do this in 4 steps:

### Step 1 — Build the training set

```bash
cd course/ai-fde/phase-4-capstone/projects/03-distilled-slm
cp ../../phase-3-deployment/service/usage.jsonl slm/data/usage.jsonl
python3 slm/dataset.py --usage slm/data/usage.jsonl \
                       --feedback ../../phase-3-deployment/service/feedback.jsonl \
                       --out slm/data/train.parquet
```

The dataset builder reads the audit log, filters to `outcome=ok`
rows, and (if a feedback log is present) drops the thumbs-down
drafts. The output is a HuggingFace `Dataset` saved as parquet.

### Step 2 — Train (or skip on machines without peft/trl)

```bash
# Real training (Mac M-series or a single GPU)
python3 slm/train.py --dataset slm/data/train.parquet --out slm/adapters/pf-drafter-lora

# Synthetic (CI / no-GPU)
python3 slm/train.py --synthetic --out slm/adapters/pf-drafter-lora
```

The `train.py` script detects whether `peft` and `trl` are
installed; if not, it falls back to the synthetic mode that
writes a metadata-only `ADAPTER.json`.

### Step 3 — Serve

```bash
# One-time: merge the adapter into the base model + import to ollama
ollama create pf-drafter -f slm/Modelfile

# Run the serve script
python3 slm/serve.py --back-end ollama
```

The `serve.py` exposes a `/draft` endpoint that mirrors Phase 3's
`/draft` endpoint, so the drafter's frontend can swap models
without code changes.

### Step 4 — Eval

```bash
# Mock (no serve running — default)
python3 slm/eval.py

# Real (against a running serve.py)
python3 slm/serve.py --back-end ollama &
python3 slm/eval.py --serve-url http://localhost:8001
```

The eval runs the Phase 3 eval set (30 rows) through the SLM,
computes the 4 RAGAS-style metrics, and compares them to the
bar (90% of the adapter's `expected_metrics`). If the SLM
meets the bar, the script prints `✓ SLM meets 90% quality bar`.

### Step 5 — Test

```bash
python3 -m pytest slm/tests/test_slm.py -v
```

Expected: **2 passed in 1.3s** — the adapter loads, the eval
passes the 90% bar.

## 🏛️ FDE Lens

**Why LoRA, not full fine-tune?** A full fine-tune of a 1.5B
model requires ~6GB of GPU memory for the model + ~24GB for
the optimizer state. A LoRA fine-tune (r=16, alpha=32) freezes
the base model and only trains the adapter — ~50MB of trainable
parameters, ~3GB of GPU memory total. **LoRA is the right
choice when you have one customer and one use case.** Full
fine-tune is the right choice when you have a foundation model
team and 50 customers.

**Why Qwen2.5-1.5B?** Three reasons:
1. **Size** — 1.5B parameters is small enough to fine-tune on
   a Mac M-series (MPS) or a single mid-range GPU.
2. **Quality** — Qwen2.5-1.5B is one of the strongest 1.5B
   models on instruction-following benchmarks.
3. **License** — Apache 2.0, no restrictions on commercial use.

Other choices at this size: Llama-3.2-1B, Phi-3.5-mini,
Gemma-2-2B. The choice depends on the language (Qwen is
stronger on Chinese; Llama on English) and the licensing
(Phi-3.5 has usage restrictions).

**Why thumbs-up only?** A model trained on a mix of thumbs-up
and unrated drafts learns a noisy distribution: "the right
answer is somewhere between the good and the bad drafts." A
model trained on thumbs-up only learns "the right answer is
the good drafts." **The signal-to-noise ratio of the training
set is the most important lever in fine-tuning.** Filter first,
then train.

**What's the dataset size sweet spot?** ~1000 high-quality
drafts. Below ~500, the model overfits; above ~5000, the
gains plateau. Mei's daily volume (150 drafts/day, ~50% rated)
gives ~75 high-quality drafts/week — about 5 weeks of data
to reach the sweet spot. The first 2 weeks of production are
on GPT-4o-mini; the 3rd week is the first SLM deployment.

**What's the eval bar?** 90% of the larger model's quality on
each of the 4 RAGAS-style metrics. The bar is encoded in
`ADAPTER.json` as `expected_metrics`, so a re-trained adapter
with different expected metrics automatically gets a new bar.

**What's the failure mode?** The SLM hallucinates on cases the
eval set doesn't cover. The Phase 3 circuit breaker catches
this: if the SLM produces a low-faithfulness draft, the
breaker falls through to GPT-4o-mini (or to the stub). **The
SLM is never the only option.** It's the cheap option for the
80% case; the expensive option is the safety net for the 20%.

**What's the production deployment story?** In Phase 4 the
adapter is loaded directly by `serve.py` (or ollama). In
Phase 5 (production) the adapter would be:
- **Merged into the base model** and imported to ollama
  (faster inference; smaller memory footprint)
- **Served behind the drafter's circuit breaker** (the same
  one that gates GPT-4o-mini; the SLM gets the same rate
  limit, the same redaction, the same audit log)
- **A/B tested against GPT-4o-mini** in shadow mode (the
  SLM runs but its output is logged, not sent; Mei only
  sees the GPT-4o-mini output) for 1 week, then promoted
  to primary if the eval metrics hold

The drafter doesn't change. The model dropdown gains a
`pf-drafter-lora` option. The rest is ops.

## 🌙 Reflect

- **What's the difference between distillation and fine-tuning?**
  Fine-tuning adapts a model to a domain (e.g., Mei's draft
  style). Distillation is a specific kind of fine-tuning where
  the training data is generated by a larger model (the
  "teacher") and used to train a smaller model (the "student").
  In this project, the training data is the drafter's OWN
  outputs, not a separate teacher's — but the mechanism is
  the same.
- **When is the SLM NOT a good idea?** When the use case is
  novel (the customer has never seen a draft before, so
  there's no training data). When the use case is small
  (< 100 drafts/day; the cost savings don't justify the
  ops overhead). When the use case is high-stakes (legal
  review, medical advice; you want the larger model's
  reasoning, not a smaller model's mimicry).
- **What's the relationship between the SLM and the MCP server?**
  The SLM produces text. The MCP server is the tool layer.
  In the current architecture, the LLM call in the drafter
  emits a `tool_call` (which the MCP server executes); the
  LLM is GPT-4o-mini. In a Phase 5 lift, the SLM would
  replace the LLM call in the drafter, but the MCP server
  stays the same. The SLM is taught to emit `tool_call` JSON
  during fine-tuning, using Mei's tool-call examples as
  training data. **The contract is the same; the model
  changes.**

## 📦 Artifacts

- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/dataset.py` — the data prep
- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/train.py` — the LoRA fine-tune
- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/serve.py` — the HTTP serve
- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/eval.py` — the eval harness
- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/model_card.md` — the model card
- `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/tests/test_slm.py` — the 2 tests

## 🔗 Related lessons

- [T1 — MCP tools and policies](./01-mcp-tools-and-policies.md) — the MCP server is the tool layer the SLM-driven drafter would call
- [T2 — Multi-agent design](./02-multi-agent-design.md) — the MeiAgent in the multi-agent orchestrator is a future replacement for the SLM-driven drafter
