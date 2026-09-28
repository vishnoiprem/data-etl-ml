# Lesson 1 — Evolution of LLM Architecture

> **Type:** Article + Worked Example · Module 5
> RNN → attention → Transformer → scale → MoE — with a tiny Mixture-of-Experts model you can train on a laptop.

---

## The 6 stages

Every modern LLM sits somewhere in this evolution. Understanding the stages is understanding why each design choice exists.

```
   STAGE 1: RNN (read one word at a time, forget)
   STAGE 2: Attention (look back at everything, but how?)
   STAGE 3: Transformer (parallel + attention + FFN + residuals)
   STAGE 4: Scaling (more layers, more data, more params)
   STAGE 5: Mixture of Experts (scale params without scaling compute)
   STAGE 6: New directions (Mamba/SSM, hybrid attention)
```

Each stage was a response to the previous one's bottleneck.

---

## Stage 1 — RNN (1990s–2014)

```
   x_1 → [RNN] → h_1 → output_1
   x_2 → [RNN] → h_2 → output_2     (one input each step, hidden state carries info)
   x_3 → [RNN] → h_3 → output_3
   ...
```

**Problem:** sequential (can't parallelize), forgets long-range dependencies (vanishing gradient).

---

## Stage 2 — Attention (2014–2017)

Bahdanau attention: at each step, look back at the input with weights.

```
   decoder_state_2 = RNN(decoder_input, prev_state)
   attention_weights = softmax(score(decoder_state_2, encoder_states))
   context = Σ attention_weights · encoder_states
```

**Problem:** still wrapped around an RNN. Sequential bottleneck.

---

## Stage 3 — Transformer (2017)

```
   ┌─────────────────────────────────────────────┐
   │  TRANSFORMER BLOCK                           │
   │                                             │
   │  x ─► LayerNorm ─► Multi-Head Attention ─► + ─► LayerNorm ─► FFN ─► +
   │      │                                      ▲                ▲    ▲
   │      └──────────────────────────────────────┘                │    │
   │      └───────────────────────────────────────────────────────┘    │
   │      └────────────────────────────────────────────────────────────┘
   │                          (residuals everywhere)
   ```

- Parallelizes across the sequence (no recurrence)
- Pure attention: every token sees every other token
- Residual connections: gradient flows through hundreds of layers

---

## Stage 4 — Scaling (2018–2023)

GPT-2 (1.5B) → GPT-3 (175B) → GPT-4. Same architecture, more layers, more data, more compute.

**The scaling laws (Kaplan 2020):** loss scales as a power law with N (params), D (data), and C (compute). The larger you go, the better the loss.

**Problem:** scaling compute linearly scales cost. 100B params costs 100× as much as 1B params to run.

---

## Stage 5 — Mixture of Experts (2023+)

Instead of one dense FFN per layer, have **N expert FFNs**. A router picks the top-K experts per token.

```
   TOKEN ─► ROUTER ─► [Expert 1]  [Expert 2]  [Expert 3]  ... [Expert 8]
                          ↓          ↓          ↓
                          └─── weighted sum (only K active) ───► OUTPUT

   N=8 experts, K=2 active → 8× more params, only 1.25× more compute
```

Mixtral 8×7B has 47B total params but only 13B active per token. Same inference cost as 13B, knowledge of 47B.

---

## Worked Example — a tiny MoE from the dense baseline

> **Goal:** Take a tiny dense Transformer (MLP per layer), replace the MLP with a MoE (8 experts, top-2 routing), train on a toy task, measure (a) total params, (b) active params per token, (c) per-expert utilization.

### Step 1 — The baseline dense model

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class DenseMLP(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
    def forward(self, x):
        return self.fc2(F.relu(self.fc1(x)))

class DenseBlock(nn.Module):
    def __init__(self, d_model=64, d_ff=256):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads=4, batch_first=True)
        self.mlp = DenseMLP(d_model, d_ff)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
    def forward(self, x):
        h = self.ln1(x)
        a, _ = self.attn(h, h, h)
        x = x + a
        x = x + self.mlp(self.ln2(x))
        return x
```

Total params for one block: ~33K (mostly in the MLP).

### Step 2 — The MoE version

```python
class MoE(nn.Module):
    """Mixture of Experts: 8 experts, top-2 routing."""
    def __init__(self, d_model, d_ff, n_experts=8, top_k=2):
        super().__init__()
        self.n_experts = n_experts
        self.top_k = top_k
        # N independent expert MLPs
        self.experts = nn.ModuleList([DenseMLP(d_model, d_ff) for _ in range(n_experts)])
        # Router: d_model -> n_experts
        self.router = nn.Linear(d_model, n_experts)

    def forward(self, x):
        # x: (B, T, d_model)
        B, T, D = x.shape
        x_flat = x.reshape(-1, D)        # (B*T, D)

        # Router scores
        router_logits = self.router(x_flat)              # (B*T, n_experts)
        top_k_logits, top_k_indices = router_logits.topk(self.top_k, dim=-1)
        top_k_weights = F.softmax(top_k_logits, dim=-1)  # (B*T, top_k)

        # Compute only the chosen experts
        out = torch.zeros_like(x_flat)
        for i, expert in enumerate(self.experts):
            # Which tokens chose this expert (in any of their top-k slots)?
            mask = (top_k_indices == i).any(dim=-1)      # (B*T,)
            if mask.any():
                idx = mask.nonzero(as_tuple=True)[0]
                expert_out = expert(x_flat[idx])
                # Weight each token's expert output by its router weight for this expert
                weight = (top_k_weights * (top_k_indices == i)).sum(dim=-1)[mask]
                out[idx] += expert_out * weight.unsqueeze(-1)

        return out.reshape(B, T, D)

class MoEBlock(nn.Module):
    def __init__(self, d_model=64, d_ff=256, n_experts=8, top_k=2):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads=4, batch_first=True)
        self.moe = MoE(d_model, d_ff, n_experts=n_experts, top_k=top_k)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x):
        h = self.ln1(x)
        a, _ = self.attn(h, h, h)
        x = x + a
        x = x + self.moe(self.ln2(x))
        return x
```

### Step 3 — Compare param counts

```python
dense = DenseBlock()
moe = MoEBlock(n_experts=8, top_k=2)

dense_params = sum(p.numel() for p in dense.parameters())
moe_params   = sum(p.numel() for p in moe.parameters())
moe_active   = sum(p.numel() for p in moe.parameters()) - sum(
    p.numel() for e in moe.moe.experts for p in e.parameters()
) * (8 - 2) / 8  # only top_k/8 fraction of expert params active per token

print(f"Dense:    {dense_params:,} params, 100% active")
print(f"MoE 8x2:  {moe_params:,} params, ~{moe_active:,.0f} active per token")
# Dense:    ~33,000 params
# MoE 8x2:  ~132,000 params (4×), ~33,000 active per token
```

The MoE has **4× the params** but the **same active compute per token** as the dense model.

### Step 4 — Train both on a toy task

```python
# Toy task: predict the next character in a repeating pattern
torch.manual_seed(0)
seq_len = 32
batch_size = 64

def make_batch():
    # Repeating pattern: A B C D E F G H ...
    start = torch.randint(0, 26 - seq_len - 1, (batch_size,))
    x = torch.stack([torch.arange(s, s + seq_len) % 26 for s in start])
    y = torch.stack([torch.arange(s + 1, s + seq_len + 1) % 26 for s in start])
    return x.long(), y.long()

def train(model, steps=2000):
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    for _ in range(steps):
        x, y = make_batch()
        # Embedding + Transformer + head
        emb = nn.Embedding(26, 64)(x)
        h = model(emb)
        logits = nn.Linear(64, 26)(h)
        loss = F.cross_entropy(logits.reshape(-1, 26), y.reshape(-1))
        opt.zero_grad(); loss.backward(); opt.step()
    return loss.item()

# Wrap MoE into a stack of blocks
class TinyMoEModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = nn.ModuleList([MoEBlock() for _ in range(2)])
    def forward(self, x):
        for b in self.blocks: x = b(x)
        return x

# (similar for dense)

print("Dense final loss:", train(tiny_dense))
print("MoE   final loss:", train(tiny_moe))
```

MoE typically reaches lower loss with the same active compute, because each expert specializes.

### Step 5 — Visualize the routing

```python
# Count how often each expert was picked
expert_counts = torch.zeros(8)
for _ in range(100):
    x, _ = make_batch()
    emb = nn.Embedding(26, 64)(x)
    # Inspect router outputs
    router_logits = tiny_moe.blocks[0].moe.router(emb.reshape(-1, 64))
    top1 = router_logits.argmax(dim=-1)
    expert_counts += torch.bincount(top1, minlength=8)

expert_probs = expert_counts / expert_counts.sum()
print("Expert utilization:")
for i, p in enumerate(expert_probs):
    bar = "█" * int(p * 50)
    print(f"  Expert {i}: {p.item():.3f} {bar}")
```

A healthy MoE shows **balanced utilization** (no single expert at 90%). Production MoEs add an explicit load-balancing loss to enforce this — without it, the router collapses to using one expert and you lose the benefit.

---

## What this example teaches

1. **MoE = many expert MLPs + a router.** Sparse activation, dense knowledge.
2. **Active compute stays flat as you scale params.** This is the cost win.
3. **Load balancing matters.** Without it, the router collapses.
4. **Experts specialize.** Each one tends to handle certain inputs (model content type, syntactic role, etc.).
5. **MoE is the dominant pattern at scale.** Mixtral, DeepSeek-V4, GPT-4 (rumored) all use it.

This is the trajectory every modern LLM follows. Read this and you understand the shape of the field.

---

## What Comes Next

> Lesson 2 — **Mixture of Experts** — the deep dive: load balancing, expert routing algorithms, when MoE helps and when it doesn't.