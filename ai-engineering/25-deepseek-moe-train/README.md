# DeepSeek-style MoE training (toy)

Mixture-of-Experts at the trillion-parameter scale, with the load-balancing losses that keep all experts actually working. This is a 4-expert / top-1 toy in pure NumPy — the real DeepSeek uses 8-160 experts, top-2 routing, and a learned gate.

## Shape

```
            ┌──────────────────┐
            │   input tokens   │  x: [N, D]
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │   gate W_g       │  logits = x @ Wg -> [N, E]
            └────────┬─────────┘
                     ▼
            top-k routing -> expert_id per token
                     ▼
        ┌────────┬───┴───┬────────┐
        ▼        ▼       ▼        ▼
   ┌────────┐┌────────┐┌────────┐┌────────┐
   │expert 0││expert 1││expert 2││expert 3│
   └───┬────┘└───┬────┘└───┬────┘└───┬────┘
       └─────────┴────┬────┴─────────┘
                     ▼
              weighted sum
```

## What I built

- `moe/router.py` — `top1_route()` (the gate) + `softmax()` + `load_balance_loss()` (the auxiliary loss).
- A `__main__` smoke test that builds a 1024-token / 64-dim / 4-expert router, then runs 100 pseudo-training steps and watches the expert load converge to balanced.
- The "load-balance loss" formula is the same one DeepSeek's paper uses: `E * sum_e (P_e * f_e)` where `P_e` is the gate's average probability for expert `e` and `f_e` is the actual fraction of tokens routed there.

## Real numbers

- DeepSeek-V3: 256 routed experts + 1 shared, top-8 routing, 671B total / 37B active per token.
- Load-balance loss coefficient: ~0.01 (small — it's an aux loss, not the main objective).
- Expert utilization stddev: < 5% in production; > 15% means something's stuck.
- Training memory: routed-experts need ~6× the activation memory of a dense model of the same active-param count, but compute is the same.

## What I learned the hard way

- **Without the load-balance loss, one expert eats the whole batch.** Within 200 steps the gate converges to "always pick expert 0" and the rest of the network is dead weight. The aux loss is not optional.
- **Capacity factor (the dropout-style buffer per expert)** is the other knob. Set it too low and tokens get dropped; too high and the compute advantage disappears. Real value: 1.25.
- **Token dropping is silent.** Tokens that exceed an expert's capacity are dropped, not queued. Without a `drop_count` in the metrics, you'll think the model is working while it's quietly throwing away 10% of the batch.
- **MoE needs more GPUs, not more data.** The model parallel is expert-parallel, which is harder to schedule than data-parallel. Plan for it.

## When to use

- You're past dense scaling and the next model size has to be cheap at inference (only the active params fire per token).
- You have enough training tokens to keep all experts learning (otherwise they specialize and then atrophy).

## When NOT to use

- Sub-billion-param models — the routing overhead eats the savings.
- Inference paths that can't tolerate the 100ms+ tail latency from a cold expert.
- Single-GPU serving (no expert parallelism possible).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not DeepSeek-V3.** DeepSeek-V3 is a 671B-param
  model trained on 14.8T tokens with 256 routed
  experts + 1 shared, top-8 routing, FP8 mixed
  precision, and multi-month training on 2048
  H800s. This is the *routing + load-balance loss*
  pattern in 100 lines of NumPy. The scaling
  realities (expert parallelism, FP8, multi-month
  runs) are not in the toy.
- **Not a dense-model replacement.** MoE is cheaper
  at inference (only the active params fire per
  token) but more expensive in training (the
  routing + aux loss + expert parallelism). Use
  MoE when the inference cost is the binding
  constraint; use dense when the training cost is.
- **Not a free lunch on quality.** The active params
  per token (37B for DeepSeek-V3) is what determines
  the model's expressiveness. A 671B MoE is roughly
  equivalent to a ~37B dense model on quality, not
  a ~600B dense model.
- **Not single-GPU serving.** Without expert
  parallelism, the whole model has to fit on one
  GPU. For 256 experts × 2.6B each, that's a
  non-starter. Plan for multi-GPU serving from
  day one.

---

## Related directories

- [`../29-fsdp-flash-train/`](../29-fsdp-flash-train/) —
  the distributed-training patterns (FSDP +
  FlashAttention) that MoE training builds on
  top of. Expert parallelism is a separate
  axis.
- [`../30-triton-kernels/`](../30-triton-kernels/) —
  the kernel-level optimizations (fused routing,
  grouped GEMM) that MoE inference needs for
  the per-expert compute.
- [`../18-paged-attention-serving/`](../18-paged-attention-serving/) —
  the per-GPU efficiency pattern; MoE serving
  extends it with per-expert KV cache management.
- [`../28-rlhf-dpo-train/`](../28-rlhf-dpo-train/) —
  the alignment training that applies to MoE
  models the same way it does to dense ones.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
