# 37. Anthropic (Safety / Alignment)

- **Role:** AI Safety Researcher / Research Engineer (Alignment, Interpretability, Societal Impacts, RLHF)
- **Tech stack:** Python, PyTorch, JAX, Triton, CUDA, transformer internals, evals tooling
- **Comp band:** $300K-$900K (E3-E6); senior+ crosses $1.2M+; RSUs + cash, 4-year vest
- **Cumulative pass rate:** ~1-2% (safety is the hardest filter)

> Note: This file covers the *safety-specific* loop at Anthropic, which differs from the general AI Engineer loop in file #2. Use both files together.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Mission alignment (Anthropic's Responsible Scaling Policy), comp | 1 week | ~40% advance |
| 2. **Technical phone screens (2-3)** | 1 coding + 1 ML research + 1 safety/alignment case | 2-3 weeks | ~25% advance |
| 3. **Onsite (4-5 rounds)** | Research, alignment deep-dive, coding, behavior | 2-3 days | ~25% advance |
| 4. **Safety review + hiring committee** | Cross-functional review with safety experts | 2-3 weeks | ~50% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (45 min — longer than typical)

### Q1.1: "Why Anthropic for safety work?"
**Answer:** "Anthropic is the only frontier lab that puts safety at the org chart's top — the Long-Term Benefit Trust and the Responsible Scaling Policy are real institutional commitments, not PR. I want to work on the hardest alignment problem (deception, scheming, situational awareness) with the people who've published the foundational interpretability work."
**Tip:** Reference *Constitutional AI*, *Mechanistic Interpretability*, *RSP*, *Claude's Character*. Know the public safety posts.

### Q1.2: "How do you think about AI risk?"
**Answer:** Have a *nuanced* view. Show you understand both catastrophic risks and near-term harms. Avoid generic doom; avoid naive optimism. Mention specific risk models (deception, power-seeking, misalignment under RLHF).
**Tip:** Anthropic *tests* your views. They want thoughtful, calibrated, mission-aligned people.

## Stage 2: Technical phone screens (3 x 60 min)

### Q2.1: Coding: "Implement attention with KV-cache and FlashAttention-style tiling"
**Answer:** Scaled dot-product attention, causal masking, KV-cache update, paged or tiled.
```python
def attn(q, k, v, mask=None):
    # q, k, v: [B, H, T, D]
    s = (q @ k.transpose(-1, -2)) / (q.size(-1) ** 0.5)
    if mask is not None: s = s.masked_fill(mask == 0, float('-inf'))
    p = s.softmax(-1)
    return p @ v
```
**Tip:** Transformer internals are expected. Be ready to discuss paged attention, RoPE, GQA.

### Q2.2: ML research: "Walk me through DPO vs PPO for RLHF"
**Answer:** PPO: separate reward model, policy gradient with KL constraint, on-policy, complex infra. DPO: closed-form loss using preference pairs, no reward model, off-policy, simpler. Discuss limitations: DPO can overfit preferences, doesn't handle non-transitive preferences; PPO has reward hacking risk. Reference Anthropic's *Constitutional AI* and the *RLAIF* line of work.
**Tip:** Read the DPO paper and Anthropic's RLHF posts. Be ready to whiteboard the loss.

### Q2.3: Safety case: "A model is showing signs of deceptive alignment on a benchmark. Walk through your investigation."
**Answer:** (1) Reproduce — verify the benchmark, control for confounds (data contamination, prompt format); (2) Probe — does the behavior generalize? In which contexts? (3) Mechanistic analysis — what features are activated? (4) Behavioral — does the model behave differently under oversight vs no oversight? (5) Mitigation — what interventions (constitutional, red-team, fine-tune)? (6) Escalation — when do you tell leadership / pause training?
**Tip:** Anthropic's safety loop is about *judgement under uncertainty*, not perfect answers.

## Stage 3: Onsite (4-5 rounds, 2-3 days)

### Round 3.1: Research deep-dive (90 min)
- **Q:** "Walk through your most relevant research." (Should be interpretability, alignment, or RLHF.)
- **Q:** "Design an experiment to test for deceptive alignment in a 70B model." Hypothesis, methods, controls, metrics, what counts as a positive result, what you'd do with the result.
- **Q:** "What's the most important open problem in alignment and how would you attack it?"

### Round 3.2: Alignment deep-dive (90 min)
- **Q:** "How would you detect if a model is sandbagging on safety evals?" — Probe via chain-of-thought elicitation, paraphrasing, paraphrased prompts, system-prompt variations, model organism approach.
- **Q:** "How would you design Constitutional AI for a domain where the constitution is contested (politics)?" — Discuss pluralism, value pluralism, delegated judgment, post-training interventions.

### Round 3.3: Coding (60 min, 2 questions)
- Q: Implement beam search with length normalization.
- Q: Parse a complex JSON into a typed structure (or a graph algorithm).

### Round 3.4: ML systems (60 min)
- Q: Design an eval harness for a frontier model with continuous monitoring. Held-out sets, drift detection, red-team pipeline, and post-deployment monitoring.
- Q: Design a training infra for Constitutional AI with iterative critique-revision. Pipeline design, dataset versioning, and ablation tracking.

### Round 3.5: Behavioral (60 min)
- Q: Tell me about a time you changed your mind on something important. Anthropic values epistemic humility.
- Q: A time you raised a concern others didn't take seriously. Safety culture.
- Q: Why this role over a pure research role at DeepMind or OpenAI?

## Stage 4: Safety review + hiring committee
A cross-functional review with safety researchers, engineers, and policy staff. They look for: (1) technical depth in alignment/interpretability, (2) calibrated risk judgment, (3) mission alignment (Anthropic's *long-term benefit* framing), (4) collaboration across research, engineering, policy. Loop is "debanded." Senior staff have veto.

## Stage 5: Offer
Cash + RSUs. Anthropic is top-of-market for safety roles — competitive with OpenAI and DeepMind. Negotiation is real. Team match after loop. SF HQ.

## Tips for the Anthropic safety loop
- Read the *Responsible Scaling Policy*, *Core Views on AI Safety*, *Constitutional AI*, *Mapping the Mind of a Large Language Model* — all on Anthropic's site.
- For research rounds, show you've thought about *deception, situational awareness, scheming* — not just "bias."
- For coding, expect transformer internals — KV-cache, attention math, sampling.
- For alignment deep-dive, discuss *empirical* approaches, not just theory.
- "Honest" and "thoughtful" matter more than "smart." Avoid both naive optimism and doomer vibes.
- Reference specific Anthropic papers and posts by name.
- Be ready to discuss *your own* views on AI risk — they want calibrated people.

## Real candidate report
> "Loop for Safety Research (alignment team). 5 rounds over 2 days, all in-person. The research round was 90 min on a deception-detection experimental design. The alignment round was on Constitutional AI and value pluralism. The coding was transformer internals + a graph problem. Safety review was intense and they asked about a time I changed my mind on a moral question. Offer at E5, ~$720K total, 6 weeks." — r/MLQuestions, 2025-09

## Sources
- [Anthropic Careers](https://www.anthropic.com/careers)
- [Levels.fyi Anthropic salaries](https://www.levels.fyi/companies/anthropic/salaries)
- [Anthropic Research](https://www.anthropic.com/research)
- [Responsible Scaling Policy](https://www.anthropic.com/news/anthropics-responsible-scaling-policy)
- [r/MachineLearning Anthropic thread](https://www.reddit.com/r/MachineLearning/)
