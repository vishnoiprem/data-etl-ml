# Module 12 — LLM Inference Engineering

> Source: Outcome School · Module 12 · 17 lessons

---

## Course Promise

> "Understand TTFT, TPOT, and throughput, and know which optimization fixes which bottleneck."

The deepest technical module: prefill vs decode, KV cache, KV cache compression, paged attention, continuous batching, speculative decoding, Medusa, EAGLE, quantization, GGUF, llama.cpp, vLLM, SGLang, TensorRT-LLM.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [LLM Inference Optimization](./01-llm-inference-optimization.md) | Article + Worked Example | The full map: TTFT, TPOT, throughput |
| 2 | Prefill vs Decode | Article | Compute-bound vs memory-bound |
| 3 | Prefill-Decode Disaggregation | Article | Two machines, two phases |
| 4 | KV Cache | Article | What gets cached and why |
| 5 | KV Cache Compression | Article | Quantization, token eviction, sharing, low-rank |
| 6 | Paged Attention | Article | The vLLM memory trick |
| 7 | Continuous Batching | Article | Replacing finished requests mid-batch |
| 8 | Speculative Decoding | Article | Draft + verify, exact output |
| 9 | N-gram Speculation | Article | Look up the prompt, no draft model |
| 10 | Medusa | Article | Multi-head speculation, tree attention |
| 11 | EAGLE | Article | Feature-level speculation |
| 12 | Quantization | Article | FP32 → INT8 → INT4, the math |
| 13 | GGUF | Article | The single-file model format |
| 14 | llama.cpp | Article | CPU inference, mmap, mixed GPU/CPU |
| 15 | vLLM | Article | PagedAttention + continuous batching |
| 16 | SGLang | Article | RadixAttention, the frontend DSL |
| 17 | TensorRT-LLM | Article | Kernel fusion, the NVIDIA path |

---

## The Lead Lesson

> **Lesson 1 — [LLM Inference Optimization](./01-llm-inference-optimization.md)** — the map. Worked example: take a 7B model, measure TTFT/TPOT/throughput at batch=1, then apply KV cache, then continuous batching, then speculative decoding, then quantization — measure each optimization, plot the cumulative improvement.