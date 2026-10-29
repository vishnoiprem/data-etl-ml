# Groq — FDE

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~40–80
- **Comp**: $170K–$230K; TC $280K–$460K
- **What they deploy**: LPU deployments for latency-critical customers
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium)
3. ML system design (latency / inference focused)
4. Loop — coding, latency case, customer scenario

---

## ✅ SUCCESS STORIES

### Latency case
**Q:** *"A bank wants sub-100ms responses for a fraud-detection LLM."*
**A (winner):** *"Groq LPU with Llama-3 8B Instant gives ~80ms TTFT. Use Groq Cloud with reserved capacity; auto-scaler kicks in 30 sec ahead of load. Stream tokens to the customer; first-token latency matters more than total. Add a fallback to a smaller cached decision tree for the easy cases. Latency budget split: 50ms model + 20ms app + 10ms network = 80ms p95."*
**Why it worked:** Groq-native, latency budgeting, named the model + SKUs.

---

## ❌ REJECTION STORIES
### Latency
**Q:** *"Inference is slow."*
**A (loser):** "Buy faster hardware."
**What they should have said:** *"Profile: TTFT vs TPOT vs end-to-end. Many cases are prefix-cache misses or improper batching. Quantize (FP8), use speculative decoding, batch requests, stream. Then yes — fast silicon (Groq LPU) is the answer for <100ms."*

---

## 📚 Reading List
1. Groq Cloud docs
2. LPU white paper
3. Speculative decoding papers
4. levels.fyi Groq
