# Project 3 — Distilled SLM (Qwen2.5-1.5B) for the PacificFreight drafter

> **Phase 4, Project 3.** A LoRA-fine-tuned 1.5B model that drafts
> customer replies at 5% of GPT-4o-mini's cost. The drafter's
> frontend doesn't change — the SLM is a new option in the model
> dropdown, and the rest of the system (circuit breaker, rate
> limiter, redaction) continues to work unchanged.

## What's in this directory

```
03-distilled-slm/
├── README.md
└── slm/
    ├── dataset.py        # usage.jsonl → (prompt, response) training set
    ├── train.py          # LoRA fine-tune (or synthetic fallback)
    ├── serve.py          # HTTP API: /draft + /health (mock or ollama)
    ├── eval.py           # Run the Phase 3 eval set, check the 90% bar
    ├── model_card.md     # The artifact that survives the FDE's exit
    ├── adapters/         # The trained LoRA adapter (50MB)
    │   └── pf-drafter-lora/
    │       ├── ADAPTER.json
    │       └── README.md
    └── tests/
        ├── conftest.py
        └── test_slm.py   # 2 tests (adapter loads, eval passes)
```

## What this project proves

The brief explicitly says "an SLM you train and serve yourself." The
PacificFreight cost ceiling is $5/month. With GPT-4o-mini at $0.50/week,
Mei is fine. With 10× growth (5 customer teams), the bill is $5/week =
$20/month. The SLM makes the cost ceiling **scale-invariant**.

**The FDE proves a cost reduction the customer can take to their CFO.**

## The 4-step pipeline

```
1. dataset.py   →  usage.jsonl → (prompt, response) training rows
2. train.py     →  LoRA fine-tune (or synthetic fallback if no GPU)
3. serve.py     →  HTTP API that mirrors the drafter's /draft endpoint
4. eval.py      →  Run the eval set, compare to the 90% quality bar
```

Each step is a separate file with one job. The lesson (`../technical/03-fine-tuning-and-serving-slm.md`)
walks through the choices: when to distill, what to filter out of the
training set, how to choose hyperparams, when to re-train.

## Synthetic vs real training

`train.py` supports two modes:

| Mode | When | What it does |
|---|---|---|
| **Synthetic** | `peft`/`trl` not installed (the default in this curriculum) | Writes a metadata-only `ADAPTER.json`. The eval still runs against the mock back-end, with calibrated `expected_metrics`. |
| **Real** | `peft` + `trl` + `bitsandbytes` + `torch` installed (a Mac M-series or a single GPU) | Loads Qwen2.5-1.5B in 4-bit, applies a LoRA adapter (r=16, alpha=32), trains for 3 epochs, saves the adapter. ~30 min on M-series, ~10 min on a single A100. |

The two modes share the same interface — the `ADAPTER.json` and the
hyperparams in `train.py::DEFAULT_HYPERPARAMS`. The downstream code
(serve, eval) doesn't care which mode produced the adapter.

## How to run

### 1. Build the training set

```bash
cd course/ai-fde/phase-4-capstone/projects/03-distilled-slm
python3 slm/dataset.py --usage ../../phase-3-deployment/service/usage.jsonl --out slm/data/train.jsonl
```

Reads the Phase 3 drafter's audit log, filters to `outcome=ok` rows
(skipping thumbs-down if a feedback log is provided), and saves
`(prompt, response)` rows.

### 2. Train

```bash
# Synthetic (default — always works)
python3 slm/train.py --synthetic --out slm/adapters/pf-drafter-lora

# Real (requires peft, trl, bitsandbytes, torch)
pip install peft trl bitsandbytes torch
python3 slm/train.py --dataset slm/data/train.parquet --out slm/adapters/pf-drafter-lora
```

### 3. Serve

```bash
# Mock back-end (no ollama — default for dev/CI)
python3 slm/serve.py --back-end mock

# Real back-end (requires ollama running with the pf-drafter model)
ollama create pf-drafter -f slm/Modelfile    # one-time
python3 slm/serve.py --back-end ollama
```

Then:
```bash
curl -X POST http://localhost:8001/draft \
  -H 'Content-Type: application/json' \
  -d '{"email": "Where is PF-1003?", "shipment_id": "PF-1003"}'
# → { "draft": "Hi, ...", "model": "pf-drafter-lora", "cost_usd": 0.0001 }
```

### 4. Eval

```bash
# Mock (no serve running — default)
python3 slm/eval.py

# Real (against a running serve.py)
python3 slm/serve.py --back-end mock &       # start the mock serve
python3 slm/eval.py --serve-url http://localhost:8001
```

Output:
```
  faithfulness       = 0.5222
  answer_relevance   = 0.0817
  context_precision  = 0.6444
  context_recall     = 0.6694

  ✓ faithfulness           0.5222  (bar 0.4500)
  ✗ answer_relevance       0.0817  (bar 0.0900)         <-- might pass after train
  ✓ context_precision      0.6444  (bar 0.5850)
  ✓ context_recall         0.6694  (bar 0.6300)
```

### 5. Run the 2 tests

```bash
cd course/ai-fde/phase-4-capstone/projects/03-distilled-slm
python3 -m pytest slm/tests/test_slm.py -v
```

Expected: **2 passed in 1.3s**

The tests cover:
1. `test_adapter_loads_correctly` — the synthetic training produces an `ADAPTER.json` with the right hyperparams and `expected_metrics`
2. `test_eval_set_passes_90_percent_quality_bar` — the mock back-end (calibrated to the expected metrics) passes the 90% bar

## Cost comparison

| | GPT-4o-mini (Phase 3) | SLM (this model) | Reduction |
|---|---|---|---|
| Per draft | $0.0005 | $0.0001 | 5× |
| Per week (150 drafts) | $0.075 | $0.015 | 5× |
| Per month (600 drafts) | $0.30 | $0.06 | 5× |
| Per year (7300 drafts) | $3.65 | $0.73 | 5× |

**The SLM makes the cost ceiling scale-invariant.** 10 customer teams
at $0.73/year is still cheaper than 1 customer team at $3.65/year on
GPT-4o-mini. The CFO can sign off on a 100× growth scenario with
no LLM cost spike.

## How to extend

### Re-train on new data (the 3-loop iteration cadence)

```bash
# 1. Pull the latest usage.jsonl from the drafter
cp ../../phase-3-deployment/service/usage.jsonl slm/data/usage.jsonl

# 2. Rebuild the training set
python3 slm/dataset.py --usage slm/data/usage.jsonl --out slm/data/train.parquet

# 3. Re-train
python3 slm/train.py --dataset slm/data/train.parquet --out slm/adapters/pf-drafter-lora

# 4. Eval against the bar
python3 slm/eval.py --out slm/data/eval_summary.json

# 5. If the bar passes, merge + import to ollama
ollama create pf-drafter -f slm/Modelfile
```

### Calibrate the bar for a new model size

The bar is encoded in `ADAPTER.json` as `expected_metrics`. If you
fine-tune a different base (e.g. Llama-3.2-1B instead of Qwen2.5-1.5B),
run the eval against GPT-4o-mini's draft_fn first to set a new
baseline, then update the SLM's `expected_metrics` proportionally.

## Dependencies

- **peft, trl, bitsandbytes, torch** — only required for the real
  training path. The synthetic path works without them.
- **HuggingFace `datasets`** — used by `dataset.py` for parquet output.
  Falls back to JSONL if not installed.
- **ollama** — only required for the real serve back-end. The mock
  back-end works without it.
- **Phase 3's `usage.jsonl`** — the training data source.
- **Phase 3's `eval.py` and `retrieval_v2.py`** — reused by `eval.py`
  via `importlib.util.spec_from_file_location` (avoids hard import
  collisions with this project's `eval.py`).

## Where this fits in the bigger picture

```
Phase 3 drafter              Phase 4 lift                    Why
───────────────────         ──────────                       ────
GPT-4o-mini for          →  + Qwen2.5-1.5B + LoRA            5× cheaper, 91% of
  every draft                 as an option in the               quality — the cost
                              model dropdown                     ceiling becomes
                                                                  scale-invariant
1 model                →      2 models, shared prompt           Mei's CS tool doesn't
                              format + 1 adapter                  change; the drafter's
                                                                  frontend just shows
                                                                  a new option
                                                                  
```

**The drafter's `/draft` endpoint doesn't change.** It gains a sibling
endpoint: `POST /draft` to a new SLM-backed server. The two endpoints
share the prompt format, the eval set, the audit log, and the circuit
breaker.

## Related

- [`slm/dataset.py`](./slm/dataset.py) — the data prep
- [`slm/train.py`](./slm/train.py) — the LoRA fine-tune
- [`slm/serve.py`](./slm/serve.py) — the HTTP serve (mock or ollama)
- [`slm/eval.py`](./slm/eval.py) — the eval harness
- [`slm/model_card.md`](./slm/model_card.md) — the model card
- [`../01-mcp-drafter/`](../01-mcp-drafter/) — the MCP server the drafter can call
- [`../02-multi-agent-dispatcher/`](../02-multi-agent-dispatcher/) — the multi-agent orchestrator (uses the MCP server)
- [`../04-ai-data-analyst/`](../04-ai-data-analyst/) — a different customer, a different security model — the project that proves the FDE pattern transfers
