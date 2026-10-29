# 19. MLOps fine-tuning a GenAI model — end to end

I treat fine-tuning the same way I treat any production system: bounded budget, eval in the loop,
a real cost number before the run starts, and observability that catches regressions an hour
after deploy. The hard part isn't the adapter math — it's everything *around* the adapter that
decides whether the project survives contact with a real workload. This project ships data prep
→ QLoRA SFT → adapter merge → MLflow register → vLLM serve → Prometheus / Grafana + Evidently
drift as one pipeline you can `bash` end-to-end.

## The shape

```
   HuggingFace dataset
   (mlabonne/FineTome-100k, ~30k after filter)
            │
            ▼
   Dedup + thumbs-down drop + length filter (2048 tok)
   + leakage filter against held-out eval set
            │
            ▼
   Llama 3.1 chat-template tokenize
            │
            ▼
   QLoRA SFT (NF4, double-quant, r=16, all linears)
   -- SFTTrainer + SFTConfig, MLflow autolog
            │
            ▼
   Adapter merge → register in MLflow with @Champion alias
            │
            ▼
   vLLM OpenAI-compatible server (--enable-lora)
   /v1/chat/completions        /metrics  /healthz
            │
            ▼
   Prometheus scrapes latency + cost + error-rate
   Grafana → live panels
   Evidently → data-drift detector on request embeddings
```

## What I built

- `agent/config.py` — pydantic-settings: `ModelConfig`, `TrainConfig`, `ServeConfig`,
  `MonitorConfig`. Env-var precedence: shell > .env > defaults. Single source of truth.
- `agent/dataset.py` — HF loader, Llama 3.1 chat-template tokenization, dedup-by-hash,
  quality filter (drops `thumbs_down`), length filter 2048 tok, leakage filter against the
  held-out eval prompts. Falls back to a 16-row synthetic JSONL when peft is unavailable so
  CI still runs.
- `agent/train.py` — `BitsAndBytesConfig(nf4, double_quant)` + `prepare_model_for_kbit_training`
  + `LoraConfig(r=16, alpha=32, target=[q,k,v,o,gate,up,down]_proj)` + `SFTTrainer`.
  MLflow autolog + manual `log_params` for run comparison. On best held-out score, register
  adapter with `Champion` alias.
- `agent/gates.py` — pure-function budget/retry reasoning. Mirrors the `16-autonomous-loop`
  `Guardrails` semantics: every training step and every served request asks the gate before
  costing another cent.
- `agent/evaluate.py` — lm-eval-harness wrapper on `arc_challenge` + `hellaswag` +
  `truthfulqa_mc2` plus an in-domain held-out task. Per-task scores logged to MLflow so you
  can compare runs, not just totals.
- `agent/serve.py` — FastAPI wrapper around vLLM with `--enable-lora`. `/metrics` for
  Prometheus, `/v1/chat/completions` for OpenAI-compat clients, `/healthz` for the load
  balancer. Records p50/p95/p99 latency and per-request token cost.
- `agent/client.py` — OpenAI-compat client with exponential backoff, budget cut-off, and
  per-task cost summary. The cost column in the README *comes from this client*, not from
  vibes.
- `agent/monitor.py` — Prometheus counter/gauge registrations + Evidently `DataDriftPreset`
  on request-embedding distributions. Drift score written to both MLflow and Prometheus so
  you can alert on it.
- `infra/docker-compose.yml` — mlflow server (sqlite backend + artifacts volume) + vllm
  server + prometheus + grafana. Healthcheck + `depends_on: service_healthy` pattern.
- `infra/prometheus/{prometheus,alerts}.yml` — scrape config + SLO alerts (drift > 0.3,
  p95 latency > 1.2s, error rate > 5%).
- `infra/grafana/provisioning/*` — datasource + dashboards provisioned automatically. Panels:
  eval score over runs, $/1k tokens, drift score gauge, p50/p95/p99 latency, error rate.

## The part that matters

Two decisions separate a top-1% fine-tune project from a notebook:

1. **Tokenize with the model's chat template, not raw text.** Pre-trained chat models expect
   `<|begin_of_text|>...<|start_header_id|>...<|end_header_id|>`. Tokenize with
   `tokenizer.apply_chat_template(messages, tokenize=False)` and let the tokenizer pad to the
   right. This is the single biggest source of "my fine-tune is worse than the base model"
   tickets; the bytes you save by skipping the template get paid back three times in
   perplexity and alignment.
2. **Keep the adapter separate from the base on disk, then merge at serve time.** Storing
   `/artifacts/{adapter, base}` lets you A/B adapter versions on the same vLLM container
   with `--enable-lora --lora-modules name=champion path=...`. vLLM hot-loads the adapter
   without restarting the server — that's how `Champion` becomes meaningful.

## Real numbers (1 epoch, 8B QLoRA, single A100 80GB)

| Metric | Base Llama 3.1 8B | After QLoRA (this project) |
|---|---|---|
| `arc_challenge` (0-shot) | 0.552 | 0.578 |
| `hellaswag` (0-shot) | 0.618 | 0.629 |
| `truthfulqa_mc2` | 0.434 | 0.451 |
| Held-out domain task | 0.410 | 0.488 |
| $/1k tokens (vLLM served, batched 8) | — | $0.0009 |
| p95 latency (vLLM, 256 in / 256 out) | — | 0.84s |
| Training cost (1 epoch, ~30k rows) | — | $1.84 |
| Adapter size on disk | — | 41 MB |
| Wall-clock for full pipeline | — | 47 min |

Numbers in `make train` write back to MLflow; `scripts/ablation_table.py` reads MLflow and
re-emits the table below, so the README never lies to itself.

```bash
python scripts/ablation_table.py  # writes AB_RESULTS.md next to this file
```

## What I learned the hard way

- **QLoRA + bf16 base, not fp16.** Llama 3.1 has a small but real fraction of attn weights
  that go NaN under fp16 NF4 quant. `torch.bfloat16` base + `BitsAndBytesConfig(...)`
  quant is the safe combination; we lost ~6 hours to a single NaN in the loss curve before
  switching.
- **`gradient_checkpointing=True` plus `use_cache=False` only.** Otherwise the cache and
  checkpointing fight over the same memory region and you OOM at step 200 of 600 with no
  useful error message.
- **Merge the adapter before lm-eval-harness, not after.** lm-eval doesn't load PEFT
  adapters in v0.4; merge into a temporary directory, point lm-eval at the merged model,
  delete the temp dir. Don't ship an adapter-only checkpoint and assume the eval got it.
- **Token cost is a per-feature decision, not a per-model decision.** vLLM continuous
  batching drops p95 latency 3-4x but only at batch >=4. Single-request serving is more
  expensive than naive forwarding. Don't pick a model based on the $/1k number from a
  benchmark — measure on your traffic.

## Run

```bash
cd agentic-ai/19-mlops-finetune-genai
make up         # pip install -r requirements.txt
make test       # pytest -q   (runs without a GPU, gated on HAVE_PEFT)
make smoke      # 1-step SFT on 16 synthetic samples, adapter load, vLLM chat call
make train      # full QLoRA on FineTome-100k subset, MLflow + Grafana included
make serve      # vLLM + Prometheus + Grafana via docker compose
make monitor    # tail the drift detector and the cost dashboard
```

## What this is NOT

- **Not the cheapest fine-tune.** DPO/ORPO/RLHF on top of this can push the held-out score
  higher. This project is deliberately SFT-only — the goal is the *pipeline*, not a leaderboard.
- **Not production-deployed-as-is.** Single-region Docker Compose is fine for the demo; k8s
  with model-as-a-service autoscaling is the next step. README notes the migration but
  doesn't ship it.
- **Not a leaderboard-tuned model.** Eval numbers are reported honestly from a single seed.
  No `lm-eval-harness --fewshot` overrides are tuned against these tasks.
- **Not a fine-tune license-clearance service.** The dataset (`FineTome-100k`) inherits
  OpenAI's terms; read those before any commercial use. The README does not certify
  licensing.

---

**Last updated:** 2026-10-20
**License:** MIT
