# 68. Pika

- **Role:** AI Engineer (Video generation)
- **Tech stack:** PyTorch, CUDA, Triton, custom diffusion stack, distributed training
- **Comp band:** $200K-$420K total comp (L5-L7: Senior → Staff) | Base + meaningful equity (Series B)
- **Cumulative pass rate:** ~3-4%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: a Pikaffect icon (e.g., "Melt it") frame-decomposed into scene ingredients, with VAE latent codes under each frame. Color: Pika lavender (#A48BFF). Headline: "Pika / AI Video Effects / 2026".

> **TL;DR:** Pika bets on controllable-edit over raw scale — small models that ship creative tools, not big models that chase benchmarks. The signature round is the ELBO derivation and a 3D GroupNorm implementation. The winning candidate can defend "small controllable models" and has shipped under creative deadline pressure.

```
Recruiter → Phone (math + code) → Onsite (3 rounds) → Founder chat → Offer
```

The funnel filters for research generalists. Candidates who can ONLY do math or ONLY ship product get cut — Pika wants both, in one person.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, video AI passion | 30 min | ~50% |
| 2. Technical phone | Coding + ML + diffusion | 90 min | ~35% |
| 3. Onsite (3 rounds) | Coding, ML deep-dive, system design | 4 hrs | ~25% |
| 4. Founder chat | Vision | 45 min | ~70% |
| 5. Offer | Comp + equity | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards video-AI passion and taste — be ready to pick a Pikaffect and explain it technically.

### Q1.1: "Why Pika over Runway/Sora?"
**Answer:** "Pika's bet is video as a creative canvas. Pikaffects, scene ingredients, lip-sync — every release feels like a creative tool, not just a generator. I want to be on the team that ships that, especially since controllable-edit is a harder product bet than raw scale."
**Tip:** Reference Pika 2.2 and the recent scene-ingredient model.

### Q1.2: "What's your favorite Pikaffect?"
**Answer:** Pick one (try "Melt it") and explain technically what it does. The honest answer is usually a controlled-edit or sparse-attention approach to a known failure mode. Don't bluff the details.

## Stage 2: Technical phone screen

The phone tests both derivations (ELBO) and code fluency (GroupNorm). They expect math on the board.

### Q2.1: Implement GroupNorm.
**Answer:**
```python
import torch
import torch.nn as nn
class GroupNorm(nn.Module):
    def __init__(self, c, g, eps=1e-5):
        super().__init__(); self.g = g; self.eps = eps
        self.w = nn.Parameter(torch.ones(c)); self.b = nn.Parameter(torch.zeros(c))
    def forward(self, x):
        B,C,H,W = x.shape; x = x.view(B, self.g, -1)
        mu = x.mean(-1, keepdim=True); var = x.var(-1, keepdim=True, unbiased=False)
        x = (x - mu) / (var + self.eps).sqrt()
        return (x.view(B,C,H,W) * self.w + self.b)
```
**Tip:** They use GroupNorm heavily in Pika's models; explain why over BatchNorm for small batches.

### Q2.2: Derive ELBO for VAE.
**Answer:** log p(x) ≥ E_q[log p(x|z)] - KL(q(z|x) || p(z)). Walk through the derivation.
**Tip:** This is core to latent video diffusion.

## Stage 3: Onsite

Three rounds: a sinusoidal-embedding implementation, real-time video inference design, and the scene-ingredients ML deep-dive.

### Round 3.1: Coding
**Q:** Implement a sinusoidal timestep embedding.
**Answer:**
```python
import math
import torch
def timestep_embed(t, dim, max_period=10000):
    half = dim // 2
    freqs = torch.exp(-math.log(max_period) * torch.arange(half) / half)
    args = t[:, None] * freqs[None]
    return torch.cat([torch.cos(args), torch.sin(args)], -1)
```
**Tip:** This is in every diffusion model.

### Round 3.2: System design
**Q:** Design a real-time video inference service.
**Answer:** Latent encode → small diffusion with aggressive distillation → temporal smoothing → VAE decode. Optimize for first-frame latency using progressive decoding; discuss model cascade for short clips.

### Round 3.3: ML deep-dive
**Q:** Walk me through Pika's "scene ingredients" model.
**Answer:** Treat reference images as soft prompts injected via cross-attention; discuss conditioning with IP-Adapter-style tokens; explain how to keep identity across frames.

### Round 3.4: Behavioral
**Q:** Tell me about a time you shipped under deadline pressure.
**Answer:** STAR with creative constraint.

## Stage 4: Founder chat
Demi Guo (CEO) often joins. She cares about creative democratization.

## Stage 5: Offer
Equity is meaningful; private company with strong investor backing.

## Tips for the Pika loop

Most candidates over-index on scale-only arguments. Pika's bet is the opposite — know why "small controllable models" win on product.
- Use Pika 2.2 before the interview; bring feedback.
- Read AnimateDiff and SVD papers.
- Memorize VAE, ELBO, and diffusion derivations.
- Have shipped creative projects.
- Be ready to discuss why "small controllable models" beat "scale only."
- They prefer generalists who can do research and engineering.

## Real candidate report
> "Three rounds, math-heavy. They asked me to derive ELBO and implement GroupNorm. Founder round was about creative empathy, not pure research. Got an offer in 8 days." — Glassdoor, AI Engineer, 2025

## Sources
- [Pika careers](https://pika.art/careers)
- [Levels.fyi — Pika](https://www.levels.fyi/companies/pika)
- [Glassdoor — Pika](https://www.glassdoor.com/Interview/Pika-Interview-Questions.htm)
- [AnimateDiff paper](https://arxiv.org/abs/2307.04785)
- [Reddit r/StableDiffusion — Pika threads](https://reddit.com/r/StableDiffusion)

---

## The 1 thing to remember

Pika rewards diffusion and foundation-model depth with a creative-bet twist — if you can't derive the ELBO AND defend why small controllable models beat scale-only, you don't pass the founder round.