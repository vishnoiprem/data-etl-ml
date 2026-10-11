# 65. Midjourney

- **Role:** AI Engineer / Applied Researcher (Image generation)
- **Tech stack:** PyTorch, JAX, CUDA, Triton, custom diffusion stack, large-scale GPU infra
- **Comp band:** $250K-$500K total comp (Senior → Staff) | Base + meaningful equity (private, cash-flow positive)
- **Cumulative pass rate:** ~2-3% (very small, very selective)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + diffusion latent space visualized as a swirling low-dimensional manifold with denoising arrows. Color: Midjourney violet (#8E5BFF). Headline: "Midjourney / AI Image Generation / 2026".

> **TL;DR:** Midjourney is small, taste-obsessed, and math-strict — the loop tests derivation fluency, not trivia. The signature round is the 90-min phone: derive forward/reverse diffusion, then code a 2D convolution in NumPy. The winning candidate has a portfolio and opinions on V6 vs V7 stylization.

```
Recruiter → Phone (math + code) → Onsite (3 rounds) → David Holz chat → Offer
```

The funnel filters for taste AND derivations. Hedge-y answers on either axis get cut, and there's no HR buffer to soften the founder round.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, taste | 30 min | ~40% |
| 2. Technical phone | Math + coding + diffusion theory | 90 min | ~30% |
| 3. Onsite (3 rounds) | Coding, research deep-dive, system design | 4-5 hrs | ~25% |
| 4. David Holz (founder) chat | Vision, taste | 45 min | ~70% |
| 5. Offer | Comp, equity | 1-2 wks | — |

## Stage 1: Recruiter screen

The screen is taste-first. Expect to be challenged on image-model opinions and pushed back on hedge-y answers.

### Q1.1: "Why Midjourney over Stability/OpenAI?"
**Answer:** "I want to work at the only image lab that's been independent and product-led. That pressure-cooker of taste plus research is unique. The V7 launch with consistent character + style refs is the kind of bet I want to be inside."
**Tip:** Show deep familiarity with each Midjourney version's distinctive choices (v5.2 stylize, v6 natural language, v7 personalization).

### Q1.2: "What's your favorite recent image model?"
**Answer:** "Midjourney V7's draft mode + personalization pass. The two-stage pipeline is novel, and the personalization embed is a clean product trick. I think it beats OpenAI's GPT-image-1 on aesthetics, even if it loses on prompt adherence."
**Tip:** Have specific opinions. David Holz values taste and pushes back on hedge-y answers.

## Stage 2: Technical phone screen

The phone tests derivation fluency — they want the math on the board, not terminology recited from memory.

### Q2.1: Derive the forward and reverse diffusion process.
**Answer:** Forward: q(x_t | x_{t-1}) = N(x_t; √(1-β_t) x_{t-1}, β_t I). Marginal: q(x_t | x_0) = N(x_t; √(α̅_t) x_0, (1-α̅_t) I) where α̅_t = ∏_{s≤t}(1-β_s). Reverse is a learned Gaussian with mean μ_θ(x_t, t) and (usually fixed) variance σ_t² I, trained by predicting the noise ε. Score-matching equivalence: ∇_x log p_t(x) = -ε_θ(x,t)/σ_t, so noise prediction is score prediction up to scaling.
**Tip:** They want derivations on the board, not just terminology. Be ready to derive α̅ from the recurrence.

### Q2.2: Coding — implement a 2D convolution in NumPy.
**Answer:**
```python
import numpy as np
def conv2d(x, k):
    H, W = x.shape; h, w = k.shape
    out = np.zeros((H-h+1, W-w+1))
    for i in range(H-h+1):
        for j in range(W-w+1):
            out[i, j] = (x[i:i+h, j:j+w] * k).sum()
    return out
```
**Tip:** They want you to talk about im2col and Winograd for speed.

## Stage 3: Onsite

The onsite pushes deeper into the U-Net block, the inference serving stack, and a research deep-dive on character consistency.

### Round 3.1: Coding
**Q:** Implement a small U-Net downsampling block.
**Answer:** 2× Conv-ReLU-GroupNorm + Downsample. Mention FlashAttention, GroupNorm vs BatchNorm in small batches, and why SiLU over ReLU.

### Round 3.2: System design
**Q:** Design the inference serving stack for Midjourney's web tier.
**Answer:** Triton Inference Server with custom kernels, request router with priority for paying users, model warm-pool on H100s, image cache keyed by seed + prompt hash, GPU autoscaling on Kubernetes.

### Round 3.3: Research deep-dive
**Q:** How would you improve Midjourney's character consistency?
**Answer:** Reference attention with per-image IP-Adapter tokens, region-based LoRA, identity-preserving loss. Discuss V7 personalization; show you've read the IP-Adapter and PhotoMaker papers.

### Round 3.4: Behavioral + taste
**Q:** Tell me about a piece of generated art that impressed you.
**Answer:** Pick a real, specific image and explain the techniques used.

## Stage 4: Founder chat
David Holz is hands-on. He wants to know what you'd build next — and why. He dislikes jargon and loves concrete product intuition.

## Stage 5: Offer
Equity is the in-house norm. Midjourney has historically offered meaningful equity grants because they're private and cash-flow positive.

## Tips for the Midjourney loop

Most candidates over-prepare LeetCode and under-prepare diffusion derivations. The loop rewards math on the whiteboard.
- Memorize the math of diffusion and flow matching.
- Be ready to write CUDA/Triton kernels on a whiteboard.
- Talk about Midjourney versions with specific dates.
- Have taste: bring a portfolio of images you generated and explain why.
- Read IP-Adapter, PhotoMaker, and ControlNet papers.
- They have no HR infrastructure — be ready for an informal, intense loop.

## Real candidate report
> "Three rounds, all deep technical. They wanted me to derive the DDPM forward process and explain classifier-free guidance. Last round was David asking me what I'd build next. Got the offer a week later, equity was substantial." — Levels.fyi, Applied Research Engineer, 2025

## Sources
- [Midjourney careers](https://www.midjourney.com/jobs)
- [Levels.fyi — Midjourney](https://www.levels.fyi/companies/midjourney)
- [Glassdoor — Midjourney](https://www.glassdoor.com/Interview/Midjourney-Interview-Questions.htm)
- [DDPM paper (Ho et al., 2020)](https://arxiv.org/abs/2006.11239)
- [Reddit r/StableDiffusion — Midjourney threads](https://reddit.com/r/StableDiffusion)

---

## The 1 thing to remember

Midjourney rewards diffusion and foundation-model depth — if you can't derive the forward process, score-matching equivalence, and classifier-free guidance on a whiteboard, you don't pass the phone screen.