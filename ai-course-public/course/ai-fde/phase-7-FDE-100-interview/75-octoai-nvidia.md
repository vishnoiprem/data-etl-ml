# OctoAI (NVIDIA) — AI Inference Deployment

## Company Snapshot
- **HQ**: Seattle, WA
- **Team Size**: ~20–40
- **Comp**: $170K–$230K; TC $280K–$450K
- **What they deploy**: AI inference platform deployments
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Inference platform design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Inference scenario
**Q:** *"Customer wants low-latency multi-model serving."*
**A (winner):** *"OctoAI endpoints with model multiplexing. Triton backend + dynamic batching. Quantization (FP8 / AWQ). Cost: per-second metering. Eval: latency p50/p95/p99 across models. Pilot: 2 endpoints, 4 weeks."*
**Why it worked:** Right inference-platform framing.

---

## ❌ REJECTION STORIES
### Inference
**Q:** *"Latency spiked at peak."*
**A (loser):** "Add GPUs."
**What they should have said:** *"Profile: queue depth? GPU util? cold start? Often it's queue depth + a single hot model. Add autoscaling + warm-pool + dynamic batching."*

---

## 📚 Reading List
1. OctoAI docs (post-NVIDIA)
2. NVIDIA Triton Inference Server docs
3. TensorRT paper
4. levels.fyi OctoAI