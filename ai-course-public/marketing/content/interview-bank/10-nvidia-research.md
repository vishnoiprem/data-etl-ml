# 10. NVIDIA Research

> **Hero image spec:** 1400×788 px. Mood: editorial-technical (Stripe Press meets MIT Tech Review). Composition: the company name + 1 signature visual from the company's domain (CUDA kernel hierarchy + Blackwell GPU die). Color: company brand color as accent (NVIDIA green). Headline on image: "NVIDIA Research / Research Software Engineer / 2026".

> **TL;DR:** NVIDIA Research's loop runs 4 stages and rejects ~97% of candidates — the signature is the 5 verbatim CUDA questions (vector-add coalescing, LRU in C++ with smart pointers, lock-free GPU queue, Kahan summation, 64-register occupancy threshold). The winning candidate names the 128-byte cache line, the NVLink 900 GB/s vs. InfiniBand 400 Gb/s bandwidths, and reasons at the warp-shuffle level — not the API level.

```
Recruiter (50%) → Phone (40%) → Panel (30%) → Domain round (50%) → Committee → Offer
                                     └── CUDA panel (verbatim) ──┘
```

- **Role:** Research Software Engineer
- **Tech stack:** C++, CUDA, Python, PyTorch, Triton, cuBLAS, NCCL
- **Comp band:** $300K-$1.1M total comp (L3-L5 SWE) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (CUDA / distributed training / inference) | 1 week | ~50% advance |
| 2. **Technical phone screen (45-60 min)** | C++ or Python with GPU-aware follow-ups | 1-2 weeks | ~40% advance |
| 3. **Panel interviews (2 × 90 min)** | Panel 1: coding + project deep-dive; Panel 2: hardware-aware system design | 1-2 weeks | ~30% advance |
| 4. **Final technical round (60-90 min)** | Domain deep-dive with target team | 1-2 weeks | ~50% advance |

The loop is the slowest of the GPU shops (3-5 weeks typical), and the 5 verbatim CUDA questions show up verbatim — candidates who only know PyTorch lose the panel. The hardware hierarchy is graded, not the syntax.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm a research SWE with 6 years in GPU computing — most recently at [X] where I built a CUDA kernel for sparse attention that hit 1.4 PFLOPS on H100. Relevant project: a Triton kernel for grouped-query attention that beat FlashAttention-2 by 18% on Llama inference. I'm targeting NVIDIA Research because the Megatron + Transformer Engine work is the bet I want to be closest to.
**Tip:** NVIDIA grades hardware depth; bring CUDA, NCCL, or TensorRT-LLM specifics.

### Q1.2: "Why NVIDIA, specifically?"
**Answer:** I believe the inference cost curve is the most important bet in 2026 — if NVLink + NVSwitch + TensorRT-LLM can hit 10× tokens/sec/$ on Blackwell, we unlock a category of products. I disagree with the FP4-everywhere thesis — for serving, FP8 is still the right balance.
**Tip:** Hardware-specific bet + specific disagreement.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Write a CUDA kernel for vector addition and explain coalescing"
**Answer:**
```cuda
__global__ void vecAdd(float* a, float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
// Host:
int blocks = (n + 255) / 256;
vecAdd<<<blocks, 256>>>(a, b, c, n);
```
Coalescing: threads in a warp should access consecutive 4-byte addresses, forming a single 128-byte transaction. The 128-byte cache line = 32 threads × 4 bytes. Strided access with stride < 128 bytes can be partially coalesced.
**Tip:** Name the cache line size, name the threshold, name the implication.

The phone screen is vector-add + coalescing. The onsite is the CUDA panel — coding, project deep-dive, hardware-aware system design. Memory hierarchy is the differentiator.

## Stage 3: Onsite (2 panels)

### Round 3.1: Panel 1 — coding + project deep-dive (90 min)

### Q3.1.1: "Implement an LRU cache in C++ with thread safety, smart pointers, and move semantics"
**Answer:** `class LRUCache { list<pair<int,int>> l; unordered_map<int, list::iterator> m; int cap; mutex mtx; }`; on `get` move node to front; on `put` at cap, evict back. Use `std::shared_ptr` for shared ownership; `std::move` for the inserted pairs. Lock per operation; finer-grained sharded locks for concurrency.

### Q3.1.2: "Lock-free GPU queue for GPU→CPU communication"
**Answer:** Circular buffer with atomic CAS on head/tail + `__threadfence()` memory fence to ensure producer writes are visible to consumer before head update. Handle wraparound with modulo. The key insight: GPU threads can't use traditional locks; the right pattern is CAS + memory fence across the PCIe boundary.
**Tip:** Name the memory barrier, name the wraparound, name the fence semantics.

### Q3.1.3: "Floating-point error path in a binary tree"
**Answer:** Track error propagation with Kahan summation or interval arithmetic. Per-node bound on rounding error. Worst-case error O(n × machine_epsilon); in practice much lower if values are well-conditioned.
**Tip:** Kahan summation, machine epsilon, error bound.

### Round 3.2: Panel 2 — system design (hardware-specific) (90 min)

### Q3.2.1: "Design a distributed GPU memory manager for 1000 H100s across 125 nodes"
**Answer:** Hierarchical allocation with local-first policy. NVLink: 900 GB/s between 8 GPUs in a node; InfiniBand: 400 Gb/s between nodes. Try to keep a model's parameters in NVLink-connected GPUs first; fall back to InfiniBand only when the model doesn't fit. Cross-node memory sharing via NVSwitch + RDMA. Memory defragmentation: live migration during a training step.
**Tip:** Name the bandwidth numbers, the topology, the local-first policy.

### Q3.2.2: "Design a CUDA kernel fusion pipeline"
**Answer:** Build dependency graphs; analyze register pressure and shared memory constraints; implement memory access pattern analysis. Fusion reduces kernel launch overhead but increases register pressure. Threshold: if fused kernel uses > 64 registers per thread, occupancy drops below 50% and fusion becomes a net loss.
**Tip:** Name the register threshold, the occupancy impact, the trade-off.

## Stage 3.3: ML + domain (across both panels)

### Q3.3.1: "Walk through a CUDA reduction kernel. Why is warp divergence a problem?"
**Answer:** Reduction: each thread holds a partial sum; warp-level shuffle (`__shfl_down_sync`) reduces within a warp; shared memory reduces across warps; one thread writes the final result. Warp divergence: if threads in a warp take different branches, the warp executes both serially → 2× latency for 2-way divergence. Fix: structure the kernel so threads in a warp always take the same branch.

### Q3.3.2: "Implement scaled dot-product attention in CUDA"
**Answer:** Use shared memory for Q, K, V tiles; one block per (batch, head, query block); each thread loads a few elements; compute QKᵀ/√d in shared memory; softmax with online normalization; multiply by V. Key: shared memory usage < 48KB (default per block); thread block size = 128 or 256 for occupancy.

## Stage 4: Hiring committee

The committee weighs technical depth (CUDA, system design) and values (innovation, intellectual honesty, speed, One Team, excellence). They look for: (1) production-quality code without IDE support, (2) "I don't know, but here's how I'd reason through it" over confident-wrong, (3) hardware-aware system design. The 2-3 week post-onsite wait is normal.

## Stage 5: Offer

NVIDIA comp is base + RSU + sign-on. Total $300K-$1.1M L3-L5. Sign-on is real for senior candidates. The play: anchor with a competing GPU-adjacent offer (AMD, Intel, Apple Silicon). Negotiation is expected; the band is wide.

## Tips for the NVIDIA Research loop

- **CUDA is non-negotiable.** 10 hours on CUDA + 5 on the 5 verbatim questions.
- **Memory hierarchy, named.** 128-byte cache line, occupancy, register pressure.
- **Lock-free + memory fences.** The cross-PCIe pattern is the signal.
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

---

## The 1 thing to remember

At NVIDIA Research, name the 128-byte cache line, the 64-register occupancy threshold, and the NVLink 900 GB/s vs. InfiniBand 400 Gb/s bandwidths — the candidate who only knows PyTorch loses the panel.