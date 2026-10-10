# 38. OpenAI (Research / Applied Research)

- **Role:** Research Engineer / Member of Technical Staff (Reasoning, Multimodal, Agents, Alignment)
- **Tech stack:** Python, PyTorch, JAX, Triton, CUDA, transformer internals, distributed training (FSDP, Megatron), RLHF infra
- **Comp band:** $400K-$1.5M+ (E3-E7); senior+ crosses $2M+; cash + RSUs + profit units, 4-year vest
- **Cumulative pass rate:** ~1%

> Note: This file covers the *research-focused* loop at OpenAI. For the general AI Engineer loop, see file #1. Use both together.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Mission alignment, comp, fit | 1 week | ~40% advance |
| 2. **Technical phone screens (2-3)** | 1 coding + 1 ML research + 1 systems | 2 weeks | ~25% advance |
| 3. **Onsite (4-5 rounds)** | Research, coding, ML, behavior, leadership | 2-3 days | ~25% advance |
| 4. **Research committee + hiring** | Cross-functional review, calibration | 2-3 weeks | ~50% advance |
| 5. **Offer** | Comp, team match, profit units | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why OpenAI for research?"
**Answer:** "Three reasons. First, OpenAI is the only place where I've seen researchers, engineers, and product ship AGI in the same room. Second, the compute access — I want to train at frontier scale. Third, the recent work on o1/o3 reasoning has changed what I think is possible, and I want to contribute to that line of research."
**Tip:** Reference specific OpenAI releases — *o1/o3*, *GPT-4o*, *Sora*, *Operator*, *o1 pro mode*. Know the public research.

### Q1.2: "What's the most interesting recent result in AI?"
**Answer:** Be specific. Mention a paper (or three) and what you find interesting. Show *you* think, not that you read the digest.
**Tip:** OpenAI researchers are deeply read. Hand-wavey answers score poorly.

## Stage 2: Technical phone screens (3 x 60 min)

### Q2.1: Coding — "Implement a transformer training loop with mixed precision"
**Answer:** PyTorch-style loop with autocast, gradient scaler, FSDP sharding, checkpoint.
```python
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
for batch in loader:
    with autocast(dtype=torch.bfloat16):
        loss = model(**batch).loss
    scaler.scale(loss).backward()
    scaler.step(opt); scaler.update(); opt.zero_grad()
```
**Tip:** Expect distributed training and optimization depth.

### Q2.2: ML research — "Walk me through how chain-of-thought reasoning might emerge from RL on a reasoning dataset"
**Answer:** Discuss: (1) base model has latent CoT ability; (2) RL on verifiable rewards (math, code) sharpens CoT; (3) inference-time scaling — longer CoT = better answers; (4) the o1 / R1 line of work; (5) process reward models vs outcome reward models. Show you understand both the empirical and theoretical angles.
**Tip:** Read the o1 system card and the DeepSeek-R1 paper. Reference both.

### Q2.3: Systems — "Design a training run for a 1T-parameter model"
**Answer:** (1) Model — MoE with 8-16 experts; (2) Parallelism — TP + PP + DP + ZeRO; (3) Activation recomputation, flash attention, mixed precision; (4) Pipeline schedule (Interleaved 1F1B); (5) Data pipeline with sharded web crawl; (6) Checkpoint every N steps to S3; (7) Monitoring with W&B-style tools; (8) Recovery from faults (NaN, OOM, hardware).
**Tip:** OpenAI builds *frontier-scale* infra. Show you understand the trade-offs.

## Stage 3: Onsite (4-5 rounds, 2-3 days)

### Round 3.1: Research deep-dive (90 min)
- **Q:** "Walk me through your most relevant research." (Should be at the frontier of what you're working on.)
- **Q:** "Design an experiment to test whether a model has internalized world knowledge vs memorized." (Probe for mechanistic interpretability / probing / out-of-distribution tests.)
- **Q:** "What's the most promising direction for agentic AI in 2026 and why?" Show you've thought about tool use, planning, and long-horizon reasoning.

### Round 3.2: ML research (90 min)
- **Q:** "Design a RLHF pipeline for a 100B+ model with verifiable rewards." Discuss data collection, reward model, PPO/DPO, KL constraint, calibration.
- **Q:** "How would you build an eval suite for a coding agent?" Discuss held-out problems, execution-based evaluation, LLM-as-judge, calibration.

### Round 3.3: Coding (60 min, 2 questions)
- **Q:** Implement beam search with diverse beam groups.
- **Q:** BFS/DFS in a graph with weighted edges.

### Round 3.4: Systems (60 min)
- **Q:** "Design the inference infra for a 100M-user LLM." Discuss batching (continuous), KV-cache management, prefix caching, speculative decoding, LoRA hot-swap.
- **Q:** "How would you design a multi-modal model that can take images, audio, and text?" Discuss modality-specific encoders, fusion (cross-attention, Q-Former), training data.

### Round 3.5: Behavioral / Mission (60 min)
- **Q:** "Why this mission?" OpenAI is *mission-driven* — they want people who care about AGI safety + benefit.
- **Q:** "A time you had to ship imperfect research to meet a deadline."
- **Q:** "A time you disagreed with a senior researcher."

## Stage 4: Research committee + hiring
A committee of senior researchers reviews. They look for: (1) research taste (do you ask good questions?), (2) technical depth, (3) mission alignment, (4) impact at scale. OpenAI's bar is *extremely* high — most "hire" votes still result in "no hire" because the bar is set by the very best.

## Stage 5: Offer
Cash + RSUs + *profit units* (a unique OpenAI compensation instrument). Total comp is the highest in industry for senior+. Negotiation is real but there's less room to negotiate than at other companies because the bands are tight. Team match after loop. SF HQ.

## Tips for the OpenAI research loop
- Be *current* on recent research — o1/o3, DeepSeek-R1, Llama 3, Claude 3.5/3.7, Sora, agent benchmarks.
- For research rounds, show *taste* — ask the question behind the question.
- For coding, expect transformer internals + distributed systems + algorithms.
- For systems, expect frontier-scale infra — training and inference.
- "Mission alignment" is real — they want AGI-safety-aware people.
- Reference OpenAI's published work by name and discuss implications.
- For senior+, "research taste" matters more than "number of papers."

## Real candidate report
> "Loop for Research Engineer (Reasoning team). 5 rounds over 2 days, in-person at SF. The research round was 90 min on RL for reasoning — they wanted me to discuss o1/R1 line of work. The ML round was on RLHF at 100B scale. The systems round was on inference infra for 100M users. Behavioral was mission-fit flavored. Offer at E5, ~$1.1M total (cash + RSUs + profit units). 5 weeks." — r/MLQuestions, 2025-10

## Sources
- [OpenAI Careers](https://openai.com/careers/)
- [Levels.fyi OpenAI salaries](https://www.levels.fyi/companies/openai/salaries)
- [OpenAI Research](https://openai.com/research/)
- [o1 system card](https://openai.com/index/openai-o1-system-card/)
- [r/MachineLearning OpenAI thread](https://www.reddit.com/r/MachineLearning/)
