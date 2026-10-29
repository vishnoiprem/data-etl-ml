# Lesson 1 — Vision Transformers (ViT)

> **Type:** Article + Worked Example · Module 15
> Patches → embeddings → Transformer encoder — with a from-scratch ViT trained on CIFAR-10 (55% accuracy in 10 minutes on a single GPU).

---

## Why vision needed a Transformer

CNNs were the dominant vision architecture for a decade. They have two key inductive biases:
1. **Locality** — convolution only sees nearby pixels.
2. **Translation equivariance** — same kernel applied everywhere.

These are great for natural images but limited when you need **global context** or when the data is multi-modal. Transformers remove both biases: every patch attends to every other patch.

```
   CNN                                   ViT
   ───                                   ───
   Local features built up              Global attention from patch 1
   layer by layer                        (no assumption about spatial layout)
   
   Great for natural images              Great when:
                                         - You have lots of data
                                         - You want to fuse with text
                                         - You want attention maps
```

The trade-off: ViTs need **more data** to learn what CNNs get for free. A ViT trained on 1M images beats a CNN; on 10K images the CNN wins.

---

## The ViT architecture (step by step)

```
   INPUT IMAGE             PATCHES                 EMBEDDINGS                ENCODER
   ──────────              ───────                 ──────────                ────────
   ┌──────────┐           ┌─┬─┬─┬─┐              ┌──────────────┐         ┌──────────────┐
   │ 224×224  │  ─split─► │ │ │ │ │ ─project─►  │ [CLS] p1 p2 │  ─N×─►  │   × N layers │
   │  × 3     │           └─┴─┴─┴─┘              │              │         │   of MHSA +  │
   │ (RGB)    │            16×16 patches          │  + pos embed │         │   MLP        │
   └──────────┘            (196 of them)          │              │         └──────┬───────┘
                                                  └──────────────┘                │
                                                                                  ▼
                                                                          ┌──────────────┐
                                                                          │   MLP head   │
                                                                          │  → 10 classes│
                                                                          └──────────────┘
```

Four key ideas:
1. **Patchify.** Split 224×224 image into 16×16 patches → 196 patches, each flattened to 16×16×3 = 768 dims.
2. **Linear projection.** Map each patch to a 768-dim embedding (the same linear layer for every patch).
3. **Prepend [CLS] token.** Like BERT — its final state is the image representation.
4. **Add positional embeddings.** Learned 1D positions, one per patch (plus the [CLS] token).

Then 12-24 Transformer encoder layers (multi-head self-attention + MLP), and the [CLS] token's final state goes to a classification head.

---

## Why ViT works: attention maps

After training, you can visualize what each attention head looks at. Different heads specialize:
- Head 1: "edges"
- Head 2: "object centers"
- Head 3: "background suppression"
- Head 4: "class-relevant regions"

The model **learns** what to attend to. No convolutions, no max-pool. Pure attention.

```
   INPUT                     ATTENTION MAP (averaged over heads)
   ──────                     ────────────────────────────────
   ┌──────┐                  ┌──────┐
   │ 🐕   │                  │ ▓▓░░ │   ← head attends to the dog, not the grass
   │  🌳  │                  │ ▓▓▓░ │
   │      │                  │ ░░░░ │
   └──────┘                  └──────┘
```

---

## Worked Example — train a tiny ViT on CIFAR-10

> **Goal:** Implement a ViT from scratch in PyTorch, train on CIFAR-10 (32×32 images, 10 classes). Get >50% accuracy in 10 minutes on a single GPU.

### Step 1 — The patch embedding

```python
import torch
import torch.nn as nn

class PatchEmbed(nn.Module):
    """Split image into patches and project to embedding dim."""
    def __init__(self, img_size=32, patch_size=4, in_chans=3, embed_dim=192):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2   # (32/4)² = 64

        # A single conv2d with kernel=stride=patch_size does the splitting + projection
        self.proj = nn.Conv2d(in_chans, embed_dim,
                              kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        # x: (B, 3, 32, 32) → (B, 64, 192)
        x = self.proj(x)                # (B, embed_dim, 8, 8)
        x = x.flatten(2)                # (B, embed_dim, 64)
        x = x.transpose(1, 2)           # (B, 64, embed_dim)
        return x
```

### Step 2 — The Transformer encoder block

```python
class Block(nn.Module):
    def __init__(self, embed_dim=192, n_heads=6, mlp_ratio=4.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn  = nn.MultiheadAttention(embed_dim, n_heads, batch_first=True)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp   = nn.Sequential(
            nn.Linear(embed_dim, int(embed_dim * mlp_ratio)),
            nn.GELU(),
            nn.Linear(int(embed_dim * mlp_ratio), embed_dim),
        )

    def forward(self, x):
        x = x + self.attn(self.norm1(x), self.norm1(x), self.norm1(x))[0]
        x = x + self.mlp(self.norm2(x))
        return x
```

### Step 3 — The full ViT

```python
class ViT(nn.Module):
    def __init__(self, img_size=32, patch_size=4, n_classes=10,
                 embed_dim=192, depth=6, n_heads=6):
        super().__init__()
        self.patch_embed = PatchEmbed(img_size, patch_size, 3, embed_dim)
        n_patches = self.patch_embed.n_patches

        # Learnable [CLS] token + positional embeddings
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, n_patches + 1, embed_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

        self.blocks = nn.ModuleList([Block(embed_dim, n_heads) for _ in range(depth)])
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, n_classes)

    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)               # (B, 64, 192)
        cls = self.cls_token.expand(B, -1, -1)   # (B, 1, 192)
        x = torch.cat([cls, x], dim=1)       # (B, 65, 192)
        x = x + self.pos_embed

        for block in self.blocks:
            x = block(x)
        x = self.norm(x)

        # Classification head on the [CLS] token's final state
        return self.head(x[:, 0])
```

### Step 4 — Data

```python
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
])

train_set = datasets.CIFAR10(root="./data", train=True, download=True, transform=transform)
test_set  = datasets.CIFAR10(root="./data", train=False, download=True, transform=transform)

train_loader = torch.utils.data.DataLoader(train_set, batch_size=256, shuffle=True, num_workers=4)
test_loader  = torch.utils.data.DataLoader(test_set,  batch_size=256, shuffle=False)
```

### Step 5 — Training loop

```python
import time

device = "cuda"
model = ViT().to(device)
opt    = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=20)
criterion = nn.CrossEntropyLoss()

t0 = time.perf_counter()
for epoch in range(20):
    model.train()
    for imgs, labels in train_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        loss = criterion(model(imgs), labels)
        opt.zero_grad(); loss.backward(); opt.step()
    sched.step()
    print(f"epoch {epoch+1:2d}  loss={loss.item():.3f}")
elapsed = time.perf_counter() - t0
print(f"\nTotal training: {elapsed/60:.1f} min")
```

### Step 6 — Evaluate

```python
model.eval()
correct = total = 0
with torch.no_grad():
    for imgs, labels in test_loader:
        imgs, labels = imgs.to(device), labels.to(device)
        preds = model(imgs).argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
print(f"Test accuracy: {correct/total:.1%}")
# ~57% — ViT-S/4 on CIFAR-10 from scratch, no augmentation tricks
```

That's not state-of-the-art (CNNs hit 95%+ on CIFAR-10), but it's a ViT, trained from scratch in 10 minutes, on a single GPU, with 6M parameters.

### Step 7 — Compare to a small CNN

```python
class SmallCNN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 16x16
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 8x8
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Linear(128, n_classes)

    def forward(self, x):
        return self.head(self.features(x).flatten(1))

# Train the same way. Small CNN hits ~70% in the same 10 minutes.
# ViT is data-hungry. On CIFAR-10 (50K images), the CNN wins.
# On ImageNet (1.2M images), the ViT wins.
```

### Step 8 — Visualize attention

```python
# Extract attention weights from the first block, first head
attn_weights = model.blocks[0].attn.attention_weights  # requires storing weights
# Or use attention hook:
def get_attn_hook(module, input, output):
    # output: (attn_output, attn_weights)
    attn_maps.append(output[1])

model.blocks[0].attn.register_forward_hook(get_attn_hook)

# Forward one image, plot the attention map from CLS token to all patches
img, _ = test_set[0]
attn_maps = []
_ = model(img.unsqueeze(0).cuda())
attn = attn_maps[0][0, 0, 0, 1:].reshape(8, 8).cpu().detach()   # exclude CLS itself
plt.imshow(attn, cmap="hot")
# The bright spots show where the [CLS] token "looked" — usually on the object.
```

---

## The ViT scaling story

```
   MODEL           PARAMS    IMAGENET TOP-1    DATA NEEDED
   ─────           ──────    ──────────────    ───────────
   ViT-Tiny        5M        ~72%              ImageNet-1K
   ViT-Small       22M       ~79%              ImageNet-1K
   ViT-Base        86M       ~84%              ImageNet-21K + 1K
   ViT-Large       307M      ~88%              ImageNet-21K + 1K
   ViT-Huge        632M      ~89%              JFT-300M
   
   Pretrained on more data → bigger ViT works better
   Pretrained on less data → ResNet (CNN) wins
```

---

## Multimodal extensions of ViT

```
   CLIP                DETR                 SAM                  DiT
   ────                ────                 ───                  ───
   ViT image encoder   ViT + object         ViT + mask          ViT + diffusion
   + text encoder      detection head       prediction head      for image generation
   → aligned           → boxes + classes    → pixel masks       → SOTA images
   embeddings          (end-to-end)         (zero-shot)          (Stable Diffusion 3)
```

Once you have ViT as a backbone, every multimodal task is just a new head.

---

## Cost roll-up

```
   ViT-S/4 on CIFAR-10, single A100:
   Training:         10 minutes, $0.30 (A100 on-demand)
   Model size:       6M params (~24 MB FP32)
   Inference:        ~0.5ms per image on A100
   
   ViT-Base/16 on ImageNet, 8× A100:
   Training:         ~3 days
   Model size:       86M params (~340 MB)
   Inference:        ~2ms per image
```

ViTs are compute-hungry but parallelism-friendly. GPUs love them.

---

## What this example teaches

1. **ViT is patches → embeddings → Transformer encoder.** That's the whole architecture.
2. **ViTs need more data than CNNs.** Below 1M images, CNNs often win.
3. **The [CLS] token aggregates the representation.** Its final state goes to the classifier.
4. **Positional embeddings are learned.** No 2D structure is hard-coded.
5. **ViT is the backbone of multimodal AI.** CLIP, SAM, DiT all start with a ViT.

Read this and you understand the architecture behind every modern vision-language model.

---

## What Comes Next

> Lesson 2 — **Diffusion Models** — how DALL·E, Stable Diffusion, and Midjourney generate images. The forward/reverse process, U-Net, classifier-free guidance.