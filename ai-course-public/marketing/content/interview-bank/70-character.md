# 70. Character.AI

- **Role:** AI Engineer (Conversational LLM platform)
- **Tech stack:** Python, PyTorch, JAX, Triton, vLLM, custom LLM serving, Kubernetes
- **Comp band:** $200K-$500K base + equity (Series A post-Google-acquisition-rumors, Menlo Park)
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, mission fit | 30 min | ~50% |
| 2. Technical phone | Coding + LLM fundamentals | 90 min | ~35% |
| 3. Onsite (4 rounds) | Coding, system design, ML deep-dive, behavioral | 4-5 hrs | ~25% |
| 4. Hiring committee | Cross-team review | 1 wk | ~60% |
| 5. Offer | Comp, equity | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Character.AI?"
**Answer:** "Character pioneered the consumer conversational AI category — 200M+ users in 2025, and the roleplay use case is uniquely demanding for long-context coherence. I want to work on the inference stack that makes 100K-token conversations feel real-time."
**Tip:** Show you've used the product and know the c.ai Group (post-Google deal) dynamics.

### Q1.2: "What's the hardest problem in conversational AI?"
**Answer:** "Long-context coherence + persona consistency + safety at scale. Most models drift after 50K tokens; Character's research bet is making 200K-token roleplay indistinguishable from real chat."
**Tip:** Have a specific opinion.

## Stage 2: Technical phone screen

### Q2.1: LRU Cache.
**Answer:** See Writer's answer — OrderedDict O(1).
**Tip:** They use this pattern for KV cache eviction; explain how it applies to LLM serving.

### Q2.2: Design a streaming LLM inference service.
**Answer:** Token-by-token generation with KV cache reuse, paged attention (vLLM), continuous batching, prefix sharing across users with the same system prompt, model parallelism for large models, speculative decoding for low latency.
**Tip:** They care about cost-per-token at scale.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Implement a BPE tokenizer.
**Answer:** Standard implementation with greedy longest-match; unit-test on a small corpus.

### Round 3.2: System design
**Q:** Design Character.AI's real-time chat serving stack.
**Answer:** Front-end WebSocket → API gateway → inference cluster (vLLM, paged attention, prefix cache) → safety classifier → response stream. Handle persona context, memory, and tool calls. Cost target: <$0.001 per message.

### Round 3.3: ML deep-dive
**Q:** How would you improve long-context memory in a character chatbot?
**Answer:** Hierarchical memory: short-term scratchpad + long-term vector store with persona-conditioned retrieval. Reinforcement learning from user feedback to improve recall. Cite Character's research papers on memory.

### Round 3.4: Behavioral
**Q:** Tell me about a time you had to ship a feature fast and clean.
**Answer:** STAR with metrics.

## Stage 4: Hiring committee
Panel of 4 staff engineers + a research lead. They look for: (1) LLM systems depth, (2) persona product intuition, (3) cost efficiency mindset.

## Stage 5: Offer
Equity is meaningful. They are known to pay above market for staff+ engineers.

## Tips for the Character.AI loop
- Use Character daily; bring specific feedback on UX.
- Read their research papers (memory, persona).
- Memorize vLLM, paged attention, prefix cache.
- Practice cost-per-token analysis.
- Be ready to defend "what makes a character feel real."
- Show that you understand the teen-safety regulatory landscape.

## Real candidate report
> "Four rounds, heavy on systems. They asked me to design the serving stack for 10M concurrent users. They wanted Triton/FlashAttention expertise. The team is small, the loop was intense, the offer was very strong." — Levels.fyi, AI Engineer, 2025

## Sources
- [Character.AI careers](https://character.ai/careers)
- [Character.AI research](https://research.character.ai)
- [Levels.fyi — Character.AI](https://www.levels.fyi/companies/characterai)
- [Glassdoor — Character.AI](https://www.glassdoor.com/Interview/CharacterAI-Interview-Questions.htm)
- [vLLM paper](https://arxiv.org/abs/2309.06180)