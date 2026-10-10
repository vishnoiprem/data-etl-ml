# 13. Together AI

- **Role:** ML Engineer
- **Tech stack:** Python, PyTorch, CUDA, Triton, vLLM, FlashAttention
- **Comp band:** $200K-$700K (L3-L6)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, open-source + GPU-systems fit | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + GPU/ML systems | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds, 1 day)** | Coding → GPU systems → ML deep-dive → behavioral | 1-2 days | ~30% advance |
| 4. **Reference + offer** | Comp negotiation real | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in GPU systems — most recently at [X] where I built a FlashAttention kernel that hit 1.4 PFLOPS on H100. Relevant: my open-source PR to [vLLM / FlashAttention] that added [specific feature]. I'm targeting Together because the open-weights inference stack is the bet I want to be closest to.
**Tip:** Together grades GPU-systems + open-source; signal both.

### Q1.2: "Why Together?"
**Answer:** I want to work on the inference stack because the open-weights + custom-kernels thesis is what differentiates you from a wrapper-on-OpenAI company. The 1 thing I'd test: whether FlashAttention-3 with custom Triton kernels can hit 2× FlashAttention-2 on H100. I disagree with the closed-Enterprise features — keep the stack open.
**Tip:** GPU systems + open-weights is the Together bet.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement a CUDA reduction kernel"
**Answer:**
```cuda
__global__ void reduce(float* in, float* out, int n) {
    __shared__ float sdata[256];
    int tid = threadIdx.x; int i = blockIdx.x * blockDim.x + tid;
    sdata[tid] = (i < n) ? in[i] : 0; __syncthreads();
    for (int s = 128; s > 0; s >>= 1) {
        if (tid < s) sdata[tid] += sdata[tid + s];
        __syncthreads();
    }
    if (tid == 0) out[blockIdx.x] = sdata[0];
}
// Two-pass: block reductions → single block reduces the partials.
```
Warp shuffle for the last 32 elements (faster than shared memory).
**Tip:** Reduction is the Together warmup.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Top-K elements in a stream, O(n log K)"
**Answer:** Min-heap of size K. For each new element, push and pop if size > K. Final heap = top K. Trade-off: heap is O(n log K); quickselect is O(n) average but O(n²) worst case.

### Q3.1.2: "LRU cache, thread-safe, with TTL"
**Answer:** `OrderedDict` for LRU + expiry timestamp; on `get` check TTL, evict if expired. Sharded locks for concurrency.

### Round 3.2: GPU systems (60 min)

### Q3.2.1: "Walk through the FlashAttention algorithm"
**Answer:** FlashAttention computes attention in tiles, keeping Q, K, V tiles in SRAM (not HBM). The softmax is computed in a numerically stable online fashion. For each block: load K, V tiles, compute QKᵀ/√d, update online softmax (running max + running sum), accumulate output. Memory: O(n) vs. O(n²) for standard attention.
**Tip:** Tile-based + online softmax is the canonical answer.

### Q3.2.2: "Compare tensor parallelism vs. pipeline parallelism"
**Answer:** TP: split each layer across GPUs (e.g., 8 GPUs in NVLink node); all-reduce on every layer; tight communication. PP: split layers across GPUs; each GPU processes one stage; async with microbatching; less communication but pipeline bubbles. Trade-off: TP degree (8 typical, NVLink-bound) vs. PP depth (16-32 typical, throughput vs. latency).
**Tip:** NVLink + TP-8 is the canonical pattern.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "Implement grouped-query attention (GQA) with KV cache reuse"
**Answer:** Multiple query heads share the same K/V head; cache size reduces by the GQA ratio. On inference: cache shape = (n_kv_heads, seq, d); query shape = (n_heads, seq, d); broadcast K/V to query shape before attention.
**Tip:** GQA is the inference-cost-cutter.

### Q3.3.2: "Walk through paged attention (vLLM)"
**Answer:** KV cache stored in fixed-size pages (e.g., 16 tokens), paged in/out on demand. Trade-off: page size vs. fragmentation; 16 tokens is the sweet spot. Trade-off: implementation complexity vs. ~4× throughput gain over contiguous allocation.
**Tip:** Paged attention + 16-token pages is the canonical answer.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "A time you shipped a kernel optimization"
**Answer:** I shipped a custom Triton kernel for grouped-query attention that beat FlashAttention-2 by 18% on Llama inference at batch=8. The trick: fusing the QKV projection + RoPE + attention into a single kernel. Latency dropped 18%.
**Tip:** Specific kernel + specific gain + specific metric.

### Q3.4.2: "Why Together?"
**Answer:** I want to work on the inference stack because the open-weights + custom-kernels thesis is what differentiates you. The 1 thing I'd test: whether FlashAttention-3 with custom Triton kernels can hit 2× FlashAttention-2 on H100. I disagree with closed-Enterprise features — keep the stack open.

## Stage 4: Hiring committee

The committee weighs GPU systems + open-source + Together mission fit. They look for: (1) shipping instinct (kernel PR, model shipped), (2) infrastructure depth (TP/PP/FlashAttention), (3) "would I trust this person with the inference stack?" 1-2 week turnaround.

## Stage 5: Offer

Together comp is base + RSU + sign-on. Cash component is decent; equity is meaningful (well-funded startup). The play: anchor with a competing offer (if you have one). Sign-on is real for senior candidates.

## Tips for the Together loop

- **GPU systems is the test.** CUDA, Triton, FlashAttention.
- **TP vs. PP.** Name the bandwidth, the topology, the trade-off.
- **GQA + paged attention.** The inference-cost-cutter combo.
- **Open-weights is the moat.** Custom kernels differentiate from wrappers.
- **Triton fluency matters.** Practice writing a Triton kernel.
- **Why Together needs the open-stack disagreement.**
- **FlashAttention-3 is the frontier.** Know the online-softmax trick.

## Real candidate report

> *"Together's interview is GPU-heavy — every system design question assumes the inference context. The 'why Together' answer needs to be about the open-stack thesis: we compete on kernels, not on the model. The candidate who only knows PyTorch loses. CUDA + Triton + FlashAttention is the signal."*
> — Glassdoor candidate report, paraphrased from 2026 loops

## Sources

- [Together AI](https://www.together.ai/)
- [Together AI Inference Stack](https://www.together.ai/blog)
- [FlashAttention paper](https://arxiv.org/abs/2205.14135)
- [vLLM — PagedAttention paper](https://arxiv.org/abs/2309.06180)
- [Levels.fyi — Together AI compensation](https://www.levels.fyi)