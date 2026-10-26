# Together AI — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~40–80
- **Comp**: $170K–$220K base; TC $250K–$400K
- **What they deploy**: Open-source model hosting + custom deployments via Together API / Dedicated
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding (medium LeetCode + Python)
3. ML inference system design
4. Loop — coding 2, inference case, customer scenario

---

## ✅ SUCCESS STORIES

### Inference design
**Q:** *"A customer wants Llama-3 70B with <100ms TTFT, 50 RPS."*
**A (winner):** *"Together Dedicated cluster with FlashAttention-2 + PagedAttention. Use Together's API key endpoints with reservation. Quantize to FP8 to fit on H100s. Add a request coalescing layer for high-concurrency prefix reuse. Measure p50/p95/p99 TTFT in a load test with k6."*
**Why it worked:** Right hardware (H100, FP8), addressed prefix reuse, named measurement.

---

## ❌ REJECTION STORIES
### Inference
**Q:** *"Reduce model serving cost."*
**A (loser):** "Use a smaller model."
**Why it failed:** Generic; didn't address tokens served, cache hit rate, batching.
**What they should have said:** Quantization (FP8, AWQ), batching, prefix caching, speculative decoding, dedicated vs serverless.

---

## 📚 Reading List
1. Together AI docs
2. FlashAttention-2 paper
3. vLLM / TGI docs
4. levels.fyi Together AI
