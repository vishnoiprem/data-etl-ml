# 67. Runway

- **Role:** AI Engineer / Applied Researcher (Video generation)
- **Tech stack:** PyTorch, JAX, CUDA, Triton, custom video diffusion stack, distributed training
- **Comp band:** $220K-$450K total comp (Senior → Staff) | Base + meaningful equity (Series C/D, $3B+ valuation)
- **Cumulative pass rate:** ~3-4%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: a film strip unfurling into a latent video diffusion cascade with temporal-attention layers highlighted. Color: Runway green (#00E5A0). Headline: "Runway / AI Video Generation / 2026".

> **TL;DR:** Runway wants researchers who think like filmmakers — temporal consistency and product sense matter as much as raw modeling chops. The signature round is the system design: a 1000-user video inference service. The winning candidate has shipped creative work and can defend a Gen-4 vs Sora opinion.

```
Recruiter → Phone (math + code) → Onsite (4 rounds) → Founder chat → Offer
```

The founder round with Cristóbal Valenzuela is where taste and creative empathy are screened. Strong researchers with no creative side projects get cut here.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, video AI interest | 30 min | ~50% |
| 2. Technical phone | Coding + ML + math | 90 min | ~35% |
| 3. Onsite (4 rounds) | Coding, ML deep-dive, system design, behavioral | 4-5 hrs | ~25% |
| 4. Founder chat | Vision fit | 45 min | ~70% |
| 5. Offer | Comp + equity | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards video-AI opinions — be ready to name a model you admire and explain why, not just list features.

### Q1.1: "Why Runway for video?"
**Answer:** "Runway is the only company that owns the full video stack — research (Gen-4), product (RunwayML Studio), and creative tools for Hollywood. I want to work on the temporal-consistency problem that's still open, and Runway's the team most likely to crack it."
**Tip:** Reference Gen-4, Gen-3 Alpha Turbo, and the Lionsgate partnership.

### Q1.2: "Tell me about a video model you admire."
**Answer:** "Gen-4's character consistency across shots. The way it solves multi-shot coherence is novel, and the Lionsgate partnership is a real signal that it ships for production. Sora was a great single-shot demo, but Gen-4 is what editors actually use."
**Tip:** Have taste. Show you've used the product.

## Stage 2: Technical phone screen

The phone tests both coding (multi-head attention) and variational inference foundations (reparameterization trick).

### Q2.1: Implement multi-head self-attention.
**Answer:**
```python
import torch
import torch.nn as nn
import torch.nn.functional as F
class MHA(nn.Module):
    def __init__(self, d, h):
        super().__init__(); self.h = h; self.qkv = nn.Linear(d, 3*d)
        self.proj = nn.Linear(d, d)
    def forward(self, x):
        B,N,_ = x.shape; q,k,v = self.qkv(x).chunk(3,-1)
        q,k,v = [t.view(B,N,self.h,-1).transpose(1,2) for t in (q,k,v)]
        out = F.scaled_dot_product_attention(q,k,v)
        return self.proj(out.transpose(1,2).reshape(B,N,-1))
```
**Tip:** Use FlashAttention via SDPA; mention causal vs full attention.

### Q2.2: Derive the reparameterization trick.
**Answer:** To sample z = μ + σ·ε with ε ~ N(0,1), the gradient ∂L/∂μ, σ is computable as if z were deterministic in the forward pass.
**Tip:** Variational inference foundation; they expect fluency.

## Stage 3: Onsite

Four rounds covering 3D convolution, video inference at scale, temporal consistency research, and a behavioral that probes creative shipping history.

### Round 3.1: Coding
**Q:** Implement a 3D convolution in PyTorch.
**Answer:** Use F.conv3d with appropriate padding; discuss temporal receptive fields, factorized 3D convs (spatial + temporal).

### Round 3.2: System design
**Q:** Design a video generation inference service for 1000 concurrent users.
**Answer:** Latent video VAE encode → video diffusion (cascade of temporal attention) → decode → post-process. Use a GPU pool with model sharding, async queue, prioritization for paying users, caching of prompt embeddings.

### Round 3.3: ML deep-dive
**Q:** How would you improve temporal consistency in video diffusion?
**Answer:** Shared noise schedule across frames, temporal attention layers, keyframe conditioning, motion-controlled generation. Cite AnimateDiff, Gen-3/4 technical details.

### Round 3.4: Behavioral
**Q:** Tell me about a creative project you shipped.
**Answer:** STAR with an actual creative artifact — Runway loves filmmakers.

## Stage 4: Founder chat
Cristóbal Valenzuela (CEO) often joins. He cares about creative empowerment and shipping the tool that changes a working artist's life.

## Stage 5: Offer
Equity is meaningful; Runway is private and valued >$3B.

## Tips for the Runway loop

Most candidates over-prep on attention math and under-prep on temporal consistency techniques. Both axes matter.
- Use Gen-4 before the loop; bring specific feedback.
- Memorize temporal consistency techniques.
- Practice CUDA/Triton kernel writing.
- Read the Stable Video Diffusion paper.
- Have shipped creative work; show taste.
- Be ready to discuss Hollywood workflows and creator pain points.

## Real candidate report
> "Two coding rounds + system design + founder chat. They asked me to implement multi-head attention and design a video inference pipeline. They cared about my creative side projects more than my LeetCode stats." — Glassdoor, Applied Research Engineer, 2025

## Sources
- [Runway careers](https://runwayml.com/careers)
- [Runway research](https://runwayml.com/research)
- [Levels.fyi — Runway](https://www.levels.fyi/companies/runway)
- [Glassdoor — Runway](https://www.glassdoor.com/Interview/Runway-Interview-Questions.htm)
- [Reddit r/StableDiffusion — Runway threads](https://reddit.com/r/StableDiffusion)

---

## The 1 thing to remember

Runway rewards diffusion and foundation-model depth with a creative twist — if you can't derive the reparameterization trick AND talk about a real creative project, you don't pass the founder round.