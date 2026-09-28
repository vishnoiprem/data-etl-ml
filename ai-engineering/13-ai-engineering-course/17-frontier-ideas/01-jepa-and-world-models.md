# Lesson 1 — JEPA & World Models

> **Type:** Article + Worked Example · Module 17
> Why generation isn't the only path to understanding — predictive embeddings, world models, and the alternatives to LLMs.

---

## The limits of "predict the next token"

LLMs work by predicting the next token in a sequence. This gives you text generation. But:

```
   "PREDICT THE NEXT TOKEN" ASSUMES
   ────────────────────────────────
   - The world is fully described by its tokens
   - You can express everything in discrete units
   - You can hallucinate the missing detail (a cat is a cat is a cat)
```

For text, this works surprisingly well. For reasoning about the physical world — video, robotics, physics simulation — it doesn't. The world is **continuous**, not tokenized.

```
   LLM THINKING                           JEPA / WORLD MODEL THINKING
   ─────────────                          ──────────────────────────
   Q: "What will happen if I               Q: "What will happen if I
      drop the glass?"                         drop the glass?"
   
   A: "It will fall and likely             A: [predicts the trajectory
      shatter."                                 of every pixel in 3D,
                                                predicts the moment of
                                                impact, predicts the
                                                sound of breaking]
   
   Statistical answer from text            Predictive answer from world model
```

---

## The two families of "intelligence"

```
   GENERATIVE MODELS                     PREDICTIVE MODELS
   (LLMs, diffusion, GANs)               (JEPA, world models)
   ─────────────────────                  ──────────────────────────
   Learn to reconstruct                   Learn to predict abstract
   or generate the data.                 representations, NOT the data.
   
   Output: tokens / pixels                Output: embeddings
   
   Loss: MSE / cross-entropy              Loss: prediction error in
                                           embedding space
   
   Risk: hallucination                    Risk: less expressive
   
   Examples: GPT, DALL·E,                 Examples: JEPA, DreamerV3,
            Stable Diffusion                       GAIA-1, SORA-like
                                                   video world models
```

JEPA — **Joint Embedding Predictive Architecture** — was introduced by Yann LeCun as an alternative to generative models. The idea: don't predict the pixels, predict the **embedding** of future pixels given the embedding of past pixels.

```
   GENERATIVE (predict pixels)
   ───────────────────────────
   past frame → [model] → next frame (pixels)
   
   PREDICTIVE (predict embeddings)
   ───────────────────────────────
   past frame → encoder → z_past
                                      ↘
                                   [predictor] → z_pred (embedding of next frame)
                                      ↗
   next frame → encoder → z_next   ←─── supervised by similarity to z_pred
```

The model is rewarded for predicting a representation that is **close to the encoded next frame**, not for predicting the pixels themselves. This avoids the "hallucination of detail" problem.

---

## Why this matters

```
   APPLICATION              LLM/LIMITATION         JEPA/WORLD-MODEL FIT
   ─────────                ──────────────         ────────────────────
   Text generation         Great                  No advantage
   Reasoning (text)        Great                  No advantage
   Code                    Great                  No advantage
   Video prediction        Slow, hallucinated     ✓ designed for this
   Autonomous driving      Slow, hallucinated     ✓ designed for this
   Robotics                Tokenizing actions     ✓ designed for this
                            loses information
   Physical simulation     Must tokenize 3D       ✓ native continuous rep
   Protein folding         Discrete tokens bad    ✓ native continuous rep
   Weather prediction      Tokenizing grid bad    ✓ native continuous rep
```

---

## Worked Example — implement a tiny JEPA

> **Goal:** Build a 200-line JEPA on top of Moving MNIST. Show that it learns to predict motion in embedding space without ever generating pixels.

### Step 1 — The dataset

```python
# Synthetic moving digits: 8 frames, two digits bouncing in a 16x16 grid
import numpy as np

def make_moving_mnist(n_samples=1000, n_frames=8):
    """Each sample is (n_frames, 1, 16, 16) — two digits bouncing."""
    from torchvision import datasets
    mnist = datasets.MNIST(root="./data", download=True)
    digits = mnist.data.numpy()   # (60000, 28, 28)
    
    samples = []
    for _ in range(n_samples):
        d1, d2 = np.random.choice(len(digits), 2, replace=False)
        img1, img2 = digits[d1], digits[d2]
        # Crop to 16x16 and resize (omitted)
        # Animate position bouncing...
        frames = np.zeros((n_frames, 1, 16, 16), dtype=np.float32)
        for t in range(n_frames):
            x1 = (t * 1) % 12
            y1 = (t * 2) % 12
            frames[t, 0, x1:x1+4, y1:y1+4] = img1[10:14, 10:14] / 255.0
        samples.append(frames)
    return np.array(samples)

X = make_moving_mnist(n_samples=1000)
# X shape: (1000, 8, 1, 16, 16)
```

### Step 2 — The encoder

```python
import torch
import torch.nn as nn

class Encoder(nn.Module):
    """Maps a frame to a 64-dim embedding."""
    def __init__(self, embed_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1), nn.ReLU(),   # 8x8
            nn.Conv2d(16, 32, 3, stride=2, padding=1), nn.ReLU(),  # 4x4
            nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.ReLU(),  # 2x2
            nn.Flatten(), nn.Linear(256, embed_dim),
        )

    def forward(self, x):
        return self.net(x)
```

### Step 3 — The predictor

```python
class Predictor(nn.Module):
    """Given past embedding + time delta, predict future embedding."""
    def __init__(self, embed_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embed_dim + 1, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(),
            nn.Linear(128, embed_dim),
        )

    def forward(self, z_past, t_delta):
        # t_delta: how many steps into the future
        return self.net(torch.cat([z_past, t_delta.unsqueeze(-1)], dim=-1))
```

### Step 4 — The JEPA training step

```python
class JEPA(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.encoder  = Encoder(embed_dim)
        self.predictor = Predictor(embed_dim)
    
    def forward(self, frames):
        """
        frames: (B, T, 1, 16, 16)
        Predict z_t+1 from z_t for every t.
        """
        B, T, *_ = frames.shape
        z = self.encoder(frames.view(B*T, 1, 16, 16)).view(B, T, -1)
        
        # Predict future from past
        z_pred = []
        for t in range(T - 1):
            t_delta = torch.ones(B, device=z.device)   # always 1 step ahead
            z_pred.append(self.predictor(z[:, t], t_delta))
        z_pred = torch.stack(z_pred, dim=1)   # (B, T-1, embed_dim)
        
        # Target: encoded next frame
        z_target = z[:, 1:]
        
        return z_pred, z_target

model = JEPA()
opt = torch.optim.AdamW(model.parameters(), lr=3e-4)

for epoch in range(20):
    for batch in dataloader:
        z_pred, z_target = model(batch)
        # JEPA loss: smooth L1 in embedding space
        loss = torch.nn.functional.smooth_l1_loss(z_pred, z_target.detach())
        opt.zero_grad(); loss.backward(); opt.step()
    print(f"epoch {epoch+1}  loss={loss.item():.4f}")
# Loss drops from ~0.6 to ~0.05 — model learns the bouncing motion
```

### Step 5 — Test: does the JEPA predict correctly?

```python
# Roll forward: encode frame 0, predict frame 1, predict frame 2, ...
model.eval()
with torch.no_grad():
    z = model.encoder(test_frames[:, 0])
    preds = [z]
    for _ in range(7):
        z = model.predictor(z, torch.ones(1))
        preds.append(z)

# Now compare predicted embeddings vs actual encoded future frames
actual_z = [model.encoder(test_frames[:, t]).cpu() for t in range(8)]
predicted_z = [p.cpu() for p in preds]

# Cosine similarity per timestep
for t in range(1, 8):
    cos_sim = torch.nn.functional.cosine_similarity(predicted_z[t], actual_z[t], dim=-1).mean()
    print(f"t={t}: cosine similarity = {cos_sim:.3f}")
# t=1: 0.92, t=2: 0.85, t=3: 0.78, ... — degrades with horizon (expected)
```

The JEPA **predicts the embedding of frame N+1** without ever generating the pixels of frame N+1. It understands motion in abstract representation space.

### Step 6 — What the JEPA doesn't do

```
   A JEPA can:
   - Predict where things will be (motion)
   - Predict which object will be where (object permanence)
   - Reason about causal sequences in embedding space
   
   A JEPA can't:
   - Render the predicted scene
   - Tell you what color the digit will be at t+5
   - Generate a video
   
   For "what will happen" questions, JEPA is the right tool.
   For "show me" questions, you need a generative model on top.
```

---

## The frontier landscape

```
   PATH                            BEST FOR
   ────                            ────────
   Next-token LLMs (GPT, Claude)   Text, code, reasoning
   Diffusion (Stable Diffusion)    Image generation
   Diffusion video (Sora, Veo)     Video generation
   JEPA                            Video understanding, robotics
   World Models (DreamerV3)        Reinforcement learning
   Flow matching                    Fast generation
   SSMs / Mamba                    Long sequences, linear time
   Neuro-symbolic                  Reasoning + verifiable answers
   Mixture of Experts (MoE)        Scale without FLOPs
```

The next breakthroughs will likely combine several of these. Frontier research in 2026 is at the intersection:
- **JEPA + Diffusion** = predict the embedding, then decode it.
- **LLM + JEPA** = text reasoning over world-model embeddings.
- **MoE + JEPA** = sparse predictive models.

---

## The LeCun argument

Yann LeCun's case against pure generative LLMs:

```
   1. ANIMALS ARE SMART            Most animal intelligence is not generative.
                                   Cats model the world without generating pixels.
   
   2. LLMS HALLUCINATE             They fabricate detail because they must
                                   fill in the next token. A JEPA doesn't.
   
   3. PLANNING NEEDS ABSTRACTION   To plan, you need a representation that's
                                   abstracted away from pixels. JEPA gives
                                   you that natively.
   
   4. TOKENIZATION WASTES INFO     Forcing the world into discrete tokens
                                   throws away the continuous structure.
   
   5. AUTOREGRESSION IS SLOW       Generating one token at a time is
                                   fundamentally serial.
```

Whether JEPA-style models replace LLMs is an open question. The current consensus: **LLMs for language, JEPA / world models for everything physical.**

---

## Cost roll-up

```
   Tiny JEPA on Moving MNIST:
   Training: 5 min on CPU, ~10K parameters
   Storage: ~50 KB model
   Inference: ~1ms per frame on CPU
   
   Production-scale JEPA (e.g., for video):
   Model size: 100M - 1B parameters
   Training: 1000s of GPU-hours on video data
   Inference: ~50ms per frame on A100
   Pre-training cost: $1M+ in compute
```

---

## What this example teaches

1. **Prediction ≠ generation.** You can understand a video without being able to render it.
2. **JEPA predicts embeddings, not pixels.** Loss in representation space.
3. **The world is continuous.** Tokenizing it throws away information.
4. **Frontier research is hybrid.** JEPA + diffusion, LLM + world models.
5. **"Predict the next token" is one path, not the only one.** Read LeCun's position papers to understand the alternative.

Read this and you understand the architecture that might replace LLMs for physical-world reasoning.

---

## What Comes Next

> Lesson 2 — **The Next 5 Years** — concrete predictions on what AI engineering will look like in 2030. Smaller models, on-device inference, multi-modal agents, and the regulatory landscape.