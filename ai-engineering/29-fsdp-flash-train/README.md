# Nvidia-style FSDP distributed training (memory math)

FSDP (Fully Sharded Data Parallel) splits model parameters, gradients, and optimizer states across N GPUs. Each GPU holds 1/N of the state. This toy computes the memory and compute budget for a given model + GPU count, so you can answer "will 7B params fit on 8x A10G?" before you start the run.

## Shape

```
                Model: N params, AdamW
                ┌────────────────────────────────────────────┐
                │ params (bf16)        2B × N                │
                │ grads  (bf16)        2B × N                │
                │ optimizer state     12B × N                │
                │   (fp32 master + m + v for AdamW)         │
                └────────────────────────────────────────────┘
                                 │
                                 │  FSDP
                                 ▼
                Per-GPU: (params + grads + opt) / N
                                 +
                Activations: bs × seq × hidden × L × dtype
                                 (gradient checkpointing reduces)
```

## What I built

- `dist/sharding.py` — `ModelConfig` + `ShardingPlan.per_gpu_memory_gb()`.
- Bytes-per-param accounting for `bf16/fp16` params, `bf16/fp16` grads, and the optimizer state (AdamW = 12B, SGD = 4B, Adafactor = 4B).
- FSDP vs DDP toggle: FSDP shards all three (params/grads/opt), DDP only shards optimizer state.
- Smoke test: plans a 7B / AdamW / 8-GPU run and reports the per-GPU memory budget. Then shows DDP would not fit on 24GB A10G.

## Real numbers

- 7B model, AdamW, bf16: 16 bytes/param total = 112 GB static state. FSDP/8 = 14 GB. FSDP/16 = 7 GB.
- DDP keeps the full params + grads on every GPU = 56 GB for 7B. Doesn't fit on 24 GB A10G. Does fit on 80 GB A100.
- Activation memory: 6-12 GB at bs=1 / seq=4K / 7B. Gradient checkpointing cuts this ~6x.
- FlashAttention-2 reduces attention memory from O(seq²) to O(seq), unlocking longer contexts.
- NCCL all-gather overhead: ~5-10% of step time at 8 GPUs, scales sub-linearly.

## What I learned the hard way

- **The optimizer is the biggest line item.** AdamW is 12B/param vs SGD's 4B. Adafactor or 8-bit Adam cuts the optimizer memory 3-12x.
- **Activation memory is the second-biggest and the one that surprises people.** Sequence length × batch size × hidden × layers — a 32K context at bs=8 will OOM on a 7B even with FSDP.
- **Gradient checkpointing is almost free** in compute cost (~30% slower) and saves 5-6x activation memory. Always on unless you have a reason.
- **FSDP communication is a real cost.** The all-gather of params before each forward is bandwidth-bound. NVLink helps, InfiniBand helps more, Ethernet-cross-rack will hurt you.

## When to use

- You're training a model that doesn't fit in a single GPU's memory even with offloading.
- You have NVLink or InfiniBand between GPUs (the bandwidth matters).
- You can tolerate the ~5-10% communication overhead.

## When NOT to use

- Model fits in single-GPU memory (use DDP; FSDP overhead is wasted).
- GPUs are connected by slow interconnects (use DeepSpeed ZeRO with offloading instead).
- Inference only (this is for training).

## Run

```bash
pip install -r requirements.txt
make smoke
```
