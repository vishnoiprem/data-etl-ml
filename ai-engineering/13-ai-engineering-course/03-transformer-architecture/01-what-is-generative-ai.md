# Lesson 1 — What is Generative AI?

> **Type:** Article + Worked Example · Module 3
> The big picture: from discriminative to generative, with a from-scratch character-level Transformer that generates Shakespeare.

---

## The 30-second definition

**Generative AI is a class of models that creates new data (text, images, audio, video, code) by learning the distribution of the training data.**

```
   DISCRIMINATIVE MODEL                 GENERATIVE MODEL
   ────────────────────                 ────────────────
   Input: x                             Input: (sometimes nothing)
   Output: P(y | x)                     Output: P(x)  or  samples from P(x)
   "Is this email spam?"                "Write a new email that sounds like the
                                          emails I've seen."
```

The shift is from "judge this example" to "produce a new example that fits the pattern."

---

## What "generate" means here

The model doesn't copy. It samples from a distribution it has learned.

```
   Training:    "Here are 10 billion text examples. Learn what text looks like."
   Generation:  "Start with 'Once upon a'. Pick the most likely next word. Repeat."
```

Each "next word" is a sample from `P(next_word | all_previous_words)`. The model learned this probability distribution from the training data.

---

## The complete flow

```
   ┌─────────────────────────────────────────────────────────────┐
   │   GENERATIVE AI PIPELINE                                      │
   │                                                             │
   │   1. DATA           10B text documents                       │
   │   2. TOKENIZE       text → integers (BPE, WordPiece, etc.)  │
   │   3. EMBED          integers → 4096-dim vectors               │
   │   4. TRANSFORMER    stack of self-attention + FFN layers     │
   │   5. SAMPLING       pick the next token from the output      │
   │                       distribution                          │
   │   6. DETOKENIZE     integers → text                          │
   │                                                             │
   │   At inference, step 5 repeats until <stop>.                 │
   └─────────────────────────────────────────────────────────────┘
```

---

## What can a generative model create?

| Modality | Examples |
|---|---|
| Text | GPT-4, Claude, Llama, Mistral |
| Images | DALL-E, Stable Diffusion, Midjourney |
| Audio | Suno, ElevenLabs, MusicGen |
| Video | Sora, Runway, Pika |
| Code | Copilot, Cursor, Claude Code |
| 3D | Point-E, Shap-E |
| Protein structure | AlphaFold, ESMFold |

The architecture differs (Transformer for text, U-Net + diffusion for images, etc.) but the principle is the same: learn the distribution, sample from it.

---

## The autoregressive loop

Almost every generative model is autoregressive — it generates one piece at a time, conditioned on all the previous pieces.

```
   Prompt:  "The cat sat on the"
   Step 1:  model predicts P(next | "The cat sat on the")
            → 0.4 "mat", 0.2 "floor", 0.1 "couch", ...
            → sample "mat"
   Step 2:  model predicts P(next | "The cat sat on the mat")
            → 0.5 ".", 0.3 " and", 0.1 " again", ...
            → sample "."
   ...
```

This is the **chain rule of probability** in action:

```
   P(w_1, w_2, ..., w_n) = Π P(w_i | w_1, w_2, ..., w_{i-1})
```

A 100-word completion = 100 sequential samples.

---

## Worked Example — a tiny character-level Transformer that writes Shakespeare

> **Goal:** Build a 4-layer, 4-head Transformer from scratch in PyTorch. Train on a tiny Shakespeare corpus. Watch the loss fall. Sample text at different temperatures. Visualize the attention patterns.

### Step 1 — Data

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

# Tiny Shakespeare (or use any text file ~1MB)
text = open("data/tiny_shakespeare.txt").read()
chars = sorted(list(set(text)))
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for i, ch in enumerate(chars)}

# Encode the whole corpus as a tensor of integers
data = torch.tensor([stoi[c] for c in text], dtype=torch.long)
print(f"Corpus: {len(data)} chars, vocab: {len(chars)}")
# e.g., Corpus: 1115394 chars, vocab: 65
```

### Step 2 — Batched inputs

```python
block_size = 64       # context length
batch_size = 32

def get_batch():
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    return x, y
```

### Step 3 — A minimal Transformer block

```python
class Head(nn.Module):
    """One head of self-attention."""
    def __init__(self, head_size):
        super().__init__()
        self.key   = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x);   q = self.query(x);   v = self.value(x)
        wei = q @ k.transpose(-2, -1) * (C ** -0.5)          # scaled dot-product
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
        wei = F.softmax(wei, dim=-1)
        return wei @ v

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(n_embd, n_embd)

    def forward(self, x):
        return self.proj(torch.cat([h(x) for h in self.heads], dim=-1))

class Block(nn.Module):
    """Transformer block: attention + FFN."""
    def __init__(self, n_embd, n_head):
        super().__init__()
        self.sa = MultiHeadAttention(n_head, n_embd // n_head)
        self.ffn = nn.Sequential(nn.Linear(n_embd, 4 * n_embd),
                                  nn.ReLU(),
                                  nn.Linear(4 * n_embd, n_embd))
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))    # residual + attn
        x = x + self.ffn(self.ln2(x))   # residual + ffn
        return x
```

### Step 4 — The full model

```python
n_embd = 128
n_head = 4
n_layer = 4

class TinyGPT(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, n_embd)
        self.pos_emb = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.tok_emb(idx)                                  # (B,T,C)
        pos = self.pos_emb(torch.arange(T, device=idx.device))   # (T,C)
        x = tok + pos
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)

        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

model = TinyGPT(len(chars))
print(f"Params: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")
# ~0.6M params for the default settings
```

### Step 5 — Training loop

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

for step in range(2000):
    xb, yb = get_batch()
    logits, loss = model(xb, yb)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if step % 200 == 0:
        print(f"step {step:4d}  loss {loss.item():.3f}")
```

Expected loss curve:

```
step    0  loss 4.174
step  200  loss 2.451
step  500  loss 1.873
step 1000  loss 1.512
step 2000  loss 1.298
```

The model goes from random (loss ≈ log(65) ≈ 4.17) to ~1.3 — it has learned the local structure of the corpus.

### Step 6 — Generate text at different temperatures

```python
def generate(model, prompt, max_new_tokens=200, temperature=1.0):
    idx = torch.tensor([stoi[c] for c in prompt], dtype=torch.long)[None, :]
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -block_size:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / temperature
        probs = F.softmax(logits, dim=-1)
        idx_next = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, idx_next], dim=1)
    return "".join([itos[i] for i in idx[0].tolist()])

print("Temperature 0.5 (coherent):")
print(generate(model, prompt="ROMEO:", temperature=0.5))
print("\nTemperature 1.2 (creative):")
print(generate(model, prompt="ROMEO:", temperature=1.2))
```

Sample output (real training is on the full Shakespeare):

```
Temperature 0.5:
ROMEO:
The night is dark and full of fear,
And I will speak to thee no more.
...

Temperature 1.2:
ROMEO:
ghosts'dplsj;wqn ftwz?
K'mrt trwxc,vbgfb qlwk
...
```

Temperature controls the tradeoff: low = safe/ repetitive, high = chaotic/creative.

### Step 7 — Visualize one attention head

```python
import matplotlib.pyplot as plt

def visualize_attention(model, prompt="ROMEO:"):
    idx = torch.tensor([stoi[c] for c in prompt], dtype=torch.long)[None, :]
    # Hook to capture attention weights
    attn_weights = {}
    def hook(module, input, output):
        # Re-run the head to get the softmax weights
        x = input[0]
        B, T, C = x.shape
        k = module.key(x); q = module.query(x)
        wei = q @ k.transpose(-2, -1) * (C ** -0.5)
        wei = wei.masked_fill(module.tril[:T, :T] == 0, float('-inf'))
        wei = F.softmax(wei, dim=-1)
        attn_weights[T] = wei[0].detach().cpu().numpy()

    handle = model.blocks[0].sa.heads[0].register_forward_pre_hook(hook)
    model(idx)
    handle.remove()

    last_T = max(attn_weights)
    plt.imshow(attn_weights[last_T], cmap='hot')
    plt.xlabel('key position')
    plt.ylabel('query position')
    plt.title('Attention pattern, layer 0 head 0')
    plt.show()

visualize_attention(model, "ROMEO:")
```

The lower-triangular mask is visible. Each row shows which previous positions the current token attends to. Real models develop structured patterns (e.g., one head attends to the previous token, another to syntactic siblings).

---

## What this example teaches

1. **Generative AI is autoregressive sampling.** Pick the next token, repeat.
2. **The Transformer is the architecture.** Attention + FFN + residuals + LayerNorm.
3. **Training is just next-token prediction.** Cross-entropy loss on `(input, shifted_input)`.
4. **Sampling is what makes it generative.** Temperature and top-k control the output.
5. **Attention patterns emerge.** Different heads learn different syntactic/semantic roles.

The 200-line example is a working GPT. Modern LLMs are the same code with `n_layer=80, n_embd=8192, block_size=8192` and a few more tricks.

---

## What Comes Next

> Lesson 2 — **Autoregressive Models** — the math (chain rule), the loop, the connection to KV cache (Module 12).
