# 66. Stability AI

- **Role:** AI Engineer / Researcher (Open foundation models)
- **Tech stack:** PyTorch, JAX, CUDA, Triton, Hugging Face, large-scale distributed training
- **Comp band:** $200K-$450K base + equity (post-restructuring, London/SF-remote)
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, mission fit | 30 min | ~50% |
| 2. Technical phone | Math + ML fundamentals | 60 min | ~40% |
| 3. Onsite (4 rounds) | Coding, ML deep-dive, system design, behavioral | 4-5 hrs | ~25% |
| 4. Hiring committee | Cross-team review | 1 wk | ~60% |
| 5. Offer | Comp negotiation | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Stability now?"
**Answer:** "After the 2024 restructure, Stability is doubling down on the open-weights mission — Stable Diffusion 3.5, Stable Audio 2, Stable Video — that's the bet I want in. I want to build open foundation models that actually win."
**Tip:** Show awareness of the new CEO and the 2025 product roadmap.

### Q1.2: "Open weights vs closed — what's your view?"
**Answer:** "Open weights win long-term for safety research, customization, and regulatory compliance. The 2024 model of closed labs hoarding capability isn't durable when regulators and enterprises demand transparency."
**Tip:** Have a real opinion, not a hedge.

## Stage 2: Technical phone screen

### Q2.1: Derive cross-entropy loss for a softmax classifier.
**Answer:** L = -Σ y_i log p_i, with p_i = exp(z_i) / Σ exp(z_j). Show gradient ∂L/∂z_i = p_i - y_i.
**Tip:** They want derivation fluency, not just recall.

### Q2.2: Implement top-p (nucleus) sampling.
**Answer:**
```python
def top_p(logits, p):
    probs = torch.softmax(logits, -1)
    sorted_p, sorted_idx = probs.sort(-1, descending=True)
    cumsum = sorted_p.cumsum(-1)
    keep = cumsum <= p
    keep[..., 0] = True
    masked = torch.zeros_like(probs).scatter(-1, sorted_idx, keep.float())
    masked = masked * probs
    return masked / masked.sum(-1, keepdim=True)
```
**Tip:** Talk about temperature, repetition penalty, why top-p vs top-k.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Implement RMSNorm in PyTorch.
**Answer:**
```python
class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__(); self.w = nn.Parameter(torch.ones(d)); self.eps = eps
    def forward(self, x):
        rms = (x.pow(2).mean(-1, keepdim=True) + self.eps).rsqrt()
        return x * rms * self.w
```
**Tip:** They ship this in Stable Diffusion 3; show you know why it's faster than LayerNorm.

### Round 3.2: System design
**Q:** Design a distributed training system for a 8B text-to-image model.
**Answer:** FSDP + ZeRO-3, mixed precision bf16, gradient checkpointing, flash attention, sequence packing, AWS H100 cluster, dataset sharded across nodes with webdataset. Discuss the loss spike mitigation from the SD3 technical report.

### Round 3.3: ML deep-dive
**Q:** Walk through the Stable Diffusion 3 architecture.
**Answer:** MMDiT (multimodal DiT) with separate text and image tokens joined by attention, flow-matching objective instead of DDPM, rectified flow, 16-channel VAE. Discuss why MMDiT > UNet for high-res.

### Round 3.4: Behavioral
**Q:** Tell me about a model you shipped that didn't work.
**Answer:** STAR: own it, explain what you learned, what you'd do differently.

## Stage 4: Hiring committee
Research leads from image + video + audio teams. They screen for breadth across modalities and willingness to ship.

## Stage 5: Offer
Post-restructure, equity refreshers are tighter; base is competitive.

## Tips for the Stability loop
- Read the SD3 technical report end-to-end.
- Know flow matching and rectified flow derivations.
- Practice CUDA kernel writing on paper.
- Have shipped open-source work to show — they value it.
- Be ready to defend a position on open vs closed weights.
- They value generalists across image, video, audio, 3D.

## Real candidate report
> "Three rounds of math, one system design. They asked me to derive the forward diffusion process, implement RMSNorm, and walk through SD3's MMDiT. Offer came in 10 days, equity was lighter than I expected post-restructure." — Levels.fyi, Research Engineer, 2025

## Sources
- [Stability AI careers](https://stability.ai/careers)
- [Stable Diffusion 3 report](https://stability.ai/news/stable-diffusion-3-research-paper)
- [Levels.fyi — Stability AI](https://www.levels.fyi/companies/stability-ai)
- [Glassdoor — Stability AI](https://www.glassdoor.com/Interview/Stability-AI-Interview-Questions.htm)
- [Reddit r/StableDiffusion — Stability threads](https://reddit.com/r/StableDiffusion)