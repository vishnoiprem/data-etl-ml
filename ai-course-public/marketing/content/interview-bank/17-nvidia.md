# 17. NVIDIA (CUDA / AI Software)

- **Role:** AI Software Engineer
- **Tech stack:** C++, CUDA, Python, PyTorch, TensorRT-LLM, Triton
- **Comp band:** $300K-$1.1M (L3-L5)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (CUDA kernel / distributed training / inference serving) | 1 week | ~50% advance |
| 2. **Technical phone screen (45-60 min)** | C++ or Python with GPU-aware follow-ups | 1-2 weeks | ~40% advance |
| 3. **Panel interviews (2 × 90 min)** | Panel 1: coding + project deep-dive; Panel 2: hardware-aware system design | 1-2 weeks | ~30% advance |
| 4. **Final technical round (60-90 min)** | Domain deep-dive with target team | 1-2 weeks | ~50% advance |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an AI SWE with 5 years in GPU computing — most recently at [X] where I shipped a TensorRT-LLM serving pipeline that hit 10K tokens/sec on H100. Relevant: a CUDA kernel for grouped-query attention that beat FlashAttention-2 by 18%. I'm targeting NVIDIA because TensorRT-LLM + NVSwitch is the inference cost-curve bet I want to be closest to.
**Tip:** NVIDIA grades hardware depth; bring CUDA, TensorRT-LLM, or NCCL specifics.

### Q1.2: "Why NVIDIA?"
**Answer:** I believe the inference cost curve is the most important bet in 2026 — if NVLink + NVSwitch + TensorRT-LLM can hit 10× tokens/sec/$ on Blackwell, we unlock a category of products. I disagree with the FP4-everywhere thesis — for serving, FP8 is still the right balance.
**Tip:** Hardware-specific bet + specific disagreement.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Producer-consumer with bounded buffer, clean shutdown"
**Answer:** `queue.Queue(maxsize=N)` + poison-pill sentinel. Producer stops on poison-pill; consumer drains remaining items, then exits. The clean-shutdown signal is what separates the answer from the right answer.
**Tip:** Shutdown semantics matter.

### Q2.2: "LRU Cache in C++ with smart pointers, move semantics, thread safety"
**Answer:** `class LRUCache { list<pair<int,int>> l; unordered_map<int, list::iterator> m; ... }`; on `get` move to front; on `put` at cap, evict back. `std::shared_ptr` for shared ownership; `std::move` for insertions. Sharded locks for concurrency.

## Stage 3: Panel interviews (2 × 90 min)

### Panel 1: Coding + project deep-dive

### Q3.1.1: "Memory access pattern detection in a GPU trace"
**Answer:** Sliding window or bucketing to detect coalesced (consecutive addresses within 128-byte cache line), strided (constant stride), or random access. Trade-off: O(n²) for exact, O(n log n) for bucketed approximate. For H100: cache line = 128 bytes; coalesced = addresses within the same 128-byte aligned region.
**Tip:** 128-byte cache line, naming the threshold.

### Q3.1.2: "Lock-free GPU queue for GPU→CPU"
**Answer:** Circular buffer with atomic CAS on head/tail + `__threadfence()` memory fence for cross-PCIe visibility. Handle wraparound with modulo. GPU threads can't use traditional locks; the pattern is CAS + fence.
**Tip:** Name the memory barrier, the wraparound, the fence semantics.

### Q3.1.3: "Floating-point error path in a binary tree"
**Answer:** Kahan summation or interval arithmetic to track error propagation. Per-node bound on rounding error. Worst-case O(n × machine_epsilon); in practice lower if values are well-conditioned.
**Tip:** Kahan summation, machine epsilon, error bound.

### Panel 2: System design (hardware-specific)

### Q3.2.1: "Distributed GPU memory manager for 1000 H100s"
**Answer:** Hierarchical allocation with local-first policy. NVLink: 900 GB/s between 8 GPUs in a node; InfiniBand: 400 Gb/s between nodes. Keep model params in NVLink-connected GPUs first; fall back to InfiniBand only when model doesn't fit in a single node. Memory defragmentation: live migration during a training step.
**Tip:** Name the bandwidth numbers, the topology, the local-first policy.

### Q3.2.2: "Multi-tenant LLM inference on H100 with cost attribution"
**Answer:** Per-tenant KV cache pools, weighted fair queuing at the scheduler, token-counting middleware writing per-tenant metrics to Prometheus. Cost attribution: nightly reconciliation against billing. Trade-off: cache pooling efficiency vs. tenant isolation.
**Tip:** Cost attribution is the multi-tenant differentiator.

### Q3.2.3: "Tensor-parallel inference with paged attention + KV cache management"
**Answer:** vLLM-style paged attention: KV cache stored in fixed-size pages (e.g., 16 tokens), paged in/out on demand. Tensor parallelism: split the model across 8 GPUs in an NVLink node; all-reduce on every layer. Trade-off: page size vs. fragmentation; 16 tokens is the sweet spot.

## Stage 4: Final technical round (60-90 min)

### Q4.1: "Fine-tuning pipeline for 70B model on 1024-H100 cluster"
**Answer:** Tensor parallelism (8 GPUs/node via NVLink), pipeline parallelism (16 stages), ZeRO-3 (optimizer state sharded across data-parallel replicas), activation checkpointing. Trade-off: TP degree vs. PP depth — TP=8, PP=16 is the right pick for a 1024-GPU cluster. Activation recomputation: every 4 layers.

## Stage 5: Hiring committee + offer

Committee weighs technical depth (CUDA, system design) + values (innovation, intellectual honesty, speed, One Team, excellence). NVIDIA comp negotiates: base + RSU + sign-on. Sign-on is real for senior candidates. The 2-3 week post-onsite wait is normal.

## Tips for the NVIDIA loop

- **CUDA is non-negotiable.** 10 hours on CUDA + 5 on the verbatim questions.
- **Memory hierarchy, named.** 128-byte cache line, occupancy, register pressure.
- **Lock-free + memory fences.** Cross-PCIe pattern is the signal.
- **Kahan summation.** Floating-point error is the differentiator.
- **NVLink vs. InfiniBand.** 900 GB/s vs. 400 Gb/s; local-first policy.
- **Register threshold.** 64 registers/thread; > 50% occupancy is the bar.
- **The loop is slow.** 3-5 weeks; 2+ weeks post-onsite is normal.

## Real candidate report

> *"Tests understanding of GPU memory hierarchy and coalescing patterns that are fundamental to NVIDIA's CUDA performance optimization. The interviewer wants to see you reason about memory access patterns at the cache line level."*
> — [Interview101 — NVIDIA Software Engineer Interview Guide](https://www.interview101.com/interviews/nvidia/software-engineer)

## Sources

- [Interview101 — NVIDIA Software Engineer Interview Guide](https://www.interview101.com/interviews/nvidia/software-engineer)
- [TechInterview.net — Top 20 CUDA & GPU Computing Interview Questions: 2026](https://www.techinterview.net/questions/cuda-gpu-computing-interview-questions)
- [TechScreen — The Machine Learning Engineer Interview Guide (2026)](https://techscreen.app/articles/machine-learning-engineer-interview-guide-2026)
- [Levels.fyi — NVIDIA compensation](https://www.levels.fyi/companies/nvidia/salaries/software-engineer)
- [NVIDIA Engineering Blog](https://developer.nvidia.com/blog/)