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
**Answer:** "Three reasons. First, on-device ML is the most important unsolved problem in consumer AI — privacy, latency, and battery constraints force real engineering, and Apple leads here. Second, the Apple Intelligence launch showed Apple can ship foundation models. Third, I want to ship to a billion devices, and only Apple has that distribution."
**Tip:** Apple recruiters value *user privacy framing*. Reference on-device inference.

### Q1.2: "Describe an on-device ML project you've worked on"
**Answer:** "I shipped a Core ML model that ran at 30ms on an iPhone 12. I had to quantize from FP32 to INT8, prune 60% of weights, and retrain with quantization-aware training. Final model: 4.2MB, 92% accuracy of the FP32 baseline."
**Tip:** Apple *loves* on-device constraints. Quantization, pruning, distillation are bread-and-butter.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "LRU cache with O(1) get/put"
**Answer:** Doubly linked list + dict. ~50 lines.
**Tip:** Apple CS is similar to FAANG — LeetCode mediums. Some roles use Swift.

### Q2.2: ML — "Design an on-device speech recognition model"
**Answer:** (1) Acoustic model — small transformer with pruning; (2) decoder — transducer (RNN-T) for streaming; (3) quantize to INT8 with QAT; (4) cache precomputed features; (5) latency budget 1× real-time; (6) accuracy vs size Pareto. Discuss Apple Silicon optimizations (NEON, AMX, MLX).
**Tip:** Reference MLX (Apple's ML framework) and Core ML Tools by name.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- **Q:** Implement a thread-safe bounded queue (concurrency, locks, condition variables).
- **Q:** Find longest substring without repeating characters → sliding window O(N).
- (Optional 3rd): Tree traversal / graph problem.

### Round 3.2: System design (60 min)
- **Q: "Design Siri's on-device intent classifier"** — Multi-label, hierarchical intents, distillation from a large server-side teacher, Core ML packaging, latency budget 50ms, fallback to server when confidence low.
- **Q: "Design Apple's app recommendation engine"** — Privacy-preserving (differential privacy + on-device aggregation), federated learning for personalization, secure enclave for sensitive features.

### Round 3.3: ML deep-dive (60 min)
- **Q: "How would you distill a 70B server LLM into a 3B on-device model?"** — Two-stage distillation (logit + feature), synthetic data generation, hybrid arch (attention + SSM for long context), evaluation on Apple's internal benchmarks.
- **Q: "How would you evaluate a model running on-device vs server-only?"** — Quality parity tests, latency, battery, thermals, offline behavior, user studies.

### Round 3.4: Specialty deep-dive (60 min)
This is a sub-area deep-dive matched to your background — e.g., ASR, NMT, on-device LLM, speech synthesis, computer vision for AR/VR.

### Round 3.5: Behavioral (45 min)
- **Q:** "Describe a time you shipped something under extreme constraints (size/latency/battery)."
- **Q:** "Tell me about a time you had to balance quality vs shipping."
- **Q:** "When have you changed your approach based on user feedback?"

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
> "Loop for Siri Speech team. 5 rounds in 2 days. The ML deep-dive was on RNN-T and streaming — they pushed me on beam search latency vs greedy. The system design was on-device intent classification. Behavioral was 'craft obsessed' — they asked about a time I obsessed over 1% accuracy. Offer at ICT4, ~$450K total. 4 weeks total." — Blind, 2025-09

## Sources
- [Apple Careers](https://www.apple.com/careers/)
- [Levels.fyi Apple salaries](https://www.levels.fyi/companies/apple/salaries)
- [Apple Machine Learning Research](https://machinelearning.apple.com/)
- [Core ML docs](https://developer.apple.com/documentation/coreml)
- [r/MachineLearning Apple thread](https://www.reddit.com/r/MachineLearning/)
