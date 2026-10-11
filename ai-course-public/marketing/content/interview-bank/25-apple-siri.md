# 25. Apple (Siri / Apple Intelligence)

- **Role:** ML Engineer / Applied Scientist (Siri, Apple Intelligence, Foundation Models)
- **Tech stack:** Python, Swift (some), PyTorch/JAX, Core ML, MLX (Apple's framework), C++, Objective-C, XCode
- **Comp band:** $250K-$700K (ICT3-ICT5); senior+ crosses $1M+; RSUs vest 4-year, cash high
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Siri/AFM/ML), comp | 1-2 weeks | ~50% advance |
| 2. **Technical phone screens (2-3)** | Coding, ML, system design | 2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, ML, system design, deep specialty, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (cross-functional)** | Senior panel, calibration | 2-3 weeks | ~50% advance |
| 5. **Offer** | Comp negotiation, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Apple for ML?"
**Answer:** Three reasons. First, on-device ML is the most important unsolved problem in consumer AI — privacy, latency, and battery constraints force real engineering, and Apple leads here. Second, the Apple Intelligence launch showed Apple can ship foundation models. Third, I want to ship to a billion devices, and only Apple has that distribution.
**Tip:** Apple recruiters value *user privacy framing*. Reference on-device inference.

### Q1.2: "Describe an on-device ML project you've worked on"
**Answer:** I shipped a Core ML model that ran at 30ms on an iPhone 12. I had to quantize from FP32 to INT8, prune 60% of weights, and retrain with quantization-aware training. Final model: 4.2MB, 92% accuracy of the FP32 baseline.
**Tip:** Apple *loves* on-device constraints. Quantization, pruning, distillation are bread-and-butter.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "LRU cache with O(1) get/put"
**Answer:** Doubly linked list + dict. ~50 lines.
**Tip:** Apple CS is similar to FAANG — LeetCode mediums. Some roles use Swift.

### Q2.2: ML — "Design an on-device speech recognition model"
**Answer:** (1) Acoustic model — small transformer with pruning; (2) decoder — transducer (RNN-T) for streaming; (3) quantize to INT8 with QAT; (4) cache precomputed features; (5) latency budget 1× real-time; (6) accuracy vs size Pareto. Discuss Apple Silicon optimizations (NEON, AMX, MLX).
**Tip:** Reference MLX (Apple's ML framework) and Core ML Tools by name.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Thread-safe bounded queue"
**Answer:** `threading.Condition` with a counter. `put` waits on `not full`, `get` waits on `not empty`. Sharded queues with a dispatcher for higher concurrency.

### Q3.1.2: "Longest substring without repeating characters"
**Answer:** Sliding window + hash set; expand right, contract left on duplicate. O(N).

### Round 3.2: System design (60 min)

### Q3.2.1: "Design Siri's on-device intent classifier"
**Answer:** Multi-label, hierarchical intents. Distillation from a large server-side teacher (logit + feature distillation). Core ML packaging (.mlpackage with weights + preprocessor). Latency budget 50ms. Fallback to server when confidence < 0.7 — but only for non-sensitive intents.
**Tip:** On-device first, server fallback second. Privacy follows the path.

### Q3.2.2: "Design Apple's app recommendation engine"
**Answer:** Privacy-preserving: differential privacy + on-device aggregation. Federated learning for personalization (per-user LoRA adapter, updates ship weekly via DP). Secure enclave for sensitive features (location, contacts). The bet: privacy *enables* better personalization, not the other way around.
**Tip:** "Privacy as a feature" is the Apple frame.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "How would you distill a 70B server LLM into a 3B on-device model?"
**Answer:** Two-stage distillation: (1) logit distillation (KL divergence on the teacher's output distribution), (2) feature distillation (MSE on the hidden states of selected layers). Synthetic data generation: sample 100K prompts, generate teacher responses, train student on (prompt, response) pairs. Hybrid arch: attention + SSM (Mamba-style) for long context. Eval on Apple's internal benchmarks (held-out domain tasks + on-device latency).
**Tip:** Two-stage distillation + synthetic data is the canonical answer.

### Q3.3.2: "How would you evaluate a model running on-device vs server-only?"
**Answer:** Five layers: (1) quality parity tests (held-out eval set, same prompts on both), (2) latency p50/p95/p99 on the target device, (3) battery drain over 1 hour of continuous use, (4) thermals (does the device throttle?), (5) offline behavior (no network). User studies on a 100-person panel for subjective quality.
**Tip:** Latency + battery + thermals is the on-device eval stack.

### Round 3.4: Specialty deep-dive (60 min)

This is a sub-area deep-dive matched to your background — e.g., ASR, NMT, on-device LLM, speech synthesis, computer vision for AR/VR. Prepare 2-3 whiteboard problems in your area.
**Tip:** Confirm the specialty with the recruiter; rehearse derivations.

### Round 3.5: Behavioral (45 min)

### Q3.5.1: "A time you shipped something under extreme constraints (size/latency/battery)"
**Answer:** I shipped a Core ML model that ran at 30ms on iPhone 12, 4.2MB. The constraint: <5MB, <50ms, <1% battery per hour. I cut the model from 50M params to 8M, used grouped-query attention (4× KV reduction), INT8 with QAT. The trade-off: 8% accuracy loss vs. the server baseline, accepted because the alternative was "doesn't fit on device."
**Tip:** Specific constraints + specific cuts + specific outcome.

### Q3.5.2: "A time you had to balance quality vs. shipping"
**Answer:** A 1% accuracy gain required a 2× model size. I argued for shipping at 99% of peak because the 1% gain wasn't worth the battery hit. The PM agreed; we shipped at ICT4 launch. Two quarters later, hardware improved, and we shipped the 100% version.
**Tip:** Trade-off articulation, not "I was right."

### Q3.5.3: "When have you changed your approach based on user feedback?"
**Answer:** After launch, user research showed 30% of [feature X] users turned it off. I dug into the opt-out reason codes; the top was "too slow on my phone." I prioritized a model-size reduction over a quality improvement. Result: opt-out dropped to 8%.
**Tip:** Specific user signal + specific action + specific result.

## Stage 4: Hiring committee

Apple uses a calibration-based committee. Each interviewer scores against an internal rubric. The committee debates "is this person a 'yes' for the level?" They look for: (1) technical depth in the specific sub-area, (2) shipped-to-production evidence, (3) Apple values (privacy, simplicity, quality), (4) bar for the level. Apple errs conservative — strong hires only.

## Stage 5: Offer

Cash + RSUs. Apple cash is competitive but equity is below Meta/Google for senior+ roles. Negotiation exists but Apple is less aggressive. Team match happens *after* the loop. Relocation support is strong.

## Tips for the Apple loop

- For ML roles, *on-device constraints* are the meta. Quantization, distillation, pruning are expected knowledge.
- Reference Core ML, MLX, Create ML by name.
- For Siri/NLP, expect transducer (RNN-T) and streaming ASR questions.
- For Apple Intelligence, expect LLM distillation and evaluation questions.
- Apple values "focus" — don't brag about 10 projects, brag about ONE project deeply.
- Behavioral rounds probe *user obsession* and *craft* — Apple's culture.
- Confirm the team before the loop. Siri, AFM, Vision, Apple Intelligence, ML Research are all different.

## Real candidate report

> "Loop for Siri Speech team. 5 rounds in 2 days. The ML deep-dive was on RNN-T and streaming — they pushed me on beam search latency vs greedy. The system design was on-device intent classification. Behavioral was 'craft obsessed' — they asked about a time I obsessed over 1% accuracy. Offer at ICT4, ~$450K total. 4 weeks total."
> — Blind, 2025-09

## Sources

- [Apple Careers](https://www.apple.com/careers/)
- [Levels.fyi Apple salaries](https://www.levels.fyi/companies/apple/salaries)
- [Apple Machine Learning Research](https://machinelearning.apple.com/)
- [Core ML docs](https://developer.apple.com/documentation/coreml)
- [r/MachineLearning Apple thread](https://www.reddit.com/r/MachineLearning/)
