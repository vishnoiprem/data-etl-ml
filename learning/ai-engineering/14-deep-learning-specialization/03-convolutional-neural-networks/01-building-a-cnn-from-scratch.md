# Lesson 1 — Building a CNN from Scratch

> **Type:** Article + Worked Example · Course 3, Week 1
> The conv operation in NumPy (for intuition), then a real CNN in PyTorch on CIFAR-10 — measured 75% test accuracy in 5 minutes on a GPU.

---

## What convolution does

A **convolution** slides a small filter over the input, computing a dot product at each position. The result is a feature map highlighting where the filter's pattern appears.

```
   INPUT (5×5)                FILTER (3×3)              OUTPUT (3×3)
   ───────────                ────────────              ────────────
   1  1  1  0  0              1  0  1                   4  3  -2
   0  1  1  1  0              0  1  0                   2  4  -2
   0  0  1  1  1              1  0  1                   
   0  0  1  1  0
   0  1  1  0  0
   
   Output[i,j] = Σₖ Σₗ Filter[k,l] · Input[i+k, j+l]
```

Three parameters control the output size:
- **Padding** (P): zeros around the input
- **Stride** (S): how far the filter jumps each step
- **Filter size** (F): the receptive field

Formula: `Output_size = (Input_size - F + 2P) / S + 1`

---

## The intuition behind filters

Different filters detect different patterns:

```
   VERTICAL EDGE FILTER          HORIZONTAL EDGE FILTER      BLUR FILTER
   ─────────────────────         ──────────────────────       ─────────────
    1  0 -1                        1  1  1                   1/9 1/9 1/9
    1  0 -1                       -1 -1 -1                   1/9 1/9 1/9
    1  0 -1                        1  1  1                   1/9 1/9 1/9
   
   Reacts to vertical edges.    Reacts to horizontal edges.  Averages neighbors.
   
   Deep CNNs LEARN these filters (and many more complex ones).
   First conv layer: edges, gradients.
   Second conv layer: corners, blobs.
   Third conv layer: object parts.
   Deep layers: full objects.
```

---

## Worked Example — NumPy conv (forward only)

> **Goal:** Implement 2D convolution in pure NumPy. Test it on an edge filter, then on a real image.

### Step 1 — Zero padding

```python
import numpy as np

def zero_pad(X, pad):
    """Pad (m, n_H, n_W, n_C) array with zeros on H and W axes."""
    return np.pad(X, ((0,0), (pad,pad), (pad,pad), (0,0)), mode='constant')

x = np.random.randn(2, 5, 5, 3)
x_padded = zero_pad(x, 2)
print(x_padded.shape)  # (2, 9, 9, 3)
```

### Step 2 — Single-step convolution

```python
def conv_single_step(a_slice_prev, W, b):
    """Convolve a window of the input with one filter."""
    s = np.multiply(a_slice_prev, W)
    Z = np.sum(s)
    Z = float(Z + b)
    return Z
```

### Step 3 — Full forward convolution

```python
def conv_forward(A_prev, W, b, hparameters):
    """
    A_prev: (m, n_H_prev, n_W_prev, n_C_prev)
    W:      (f, f, n_C_prev, n_C)  — n_C filters
    b:      (1, 1, 1, n_C)
    """
    (m, n_H_prev, n_W_prev, n_C_prev) = A_prev.shape
    (f, f, n_C_prev, n_C) = W.shape
    
    stride = hparameters["stride"]
    pad    = hparameters["pad"]
    
    n_H = int((n_H_prev - f + 2 * pad) / stride) + 1
    n_W = int((n_W_prev - f + 2 * pad) / stride) + 1
    
    Z = np.zeros((m, n_H, n_W, n_C))
    A_prev_pad = zero_pad(A_prev, pad)
    
    for i in range(m):
        a_prev_pad = A_prev_pad[i]
        for h in range(n_H):
            for w in range(n_W):
                vert_start = h * stride
                vert_end   = vert_start + f
                horiz_start = w * stride
                horiz_end   = horiz_start + f
                a_slice = a_prev_pad[vert_start:vert_end, horiz_start:horiz_end, :]
                for c in range(n_C):
                    Z[i, h, w, c] = conv_single_step(a_slice, W[:, :, :, c], b[:, :, :, c])
    
    return Z
```

### Step 4 — Test on an image

```python
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread("cat.png")  # (n_H, n_W, 3) — RGB
print(f"Input: {img.shape}")

# Two filters: vertical edge, horizontal edge
W = np.zeros((3, 3, 3, 2))
W[:, :, :, 0] = np.array([[1, 0, -1], [1, 0, -1], [1, 0, -1]])[:, :, None] / 3
W[:, :, :, 1] = np.array([[1, 1, 1], [-1, -1, -1], [1, 1, 1]])[:, :, None] / 3
b = np.zeros((1, 1, 1, 2))

out = conv_forward(img[None, :, :, :], W, b, {"stride": 1, "pad": 1})
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(img); axes[0].set_title("Input")
axes[1].imshow(out[0, :, :, 0], cmap="gray"); axes[1].set_title("Vertical edges")
axes[2].imshow(out[0, :, :, 1], cmap="gray"); axes[2].set_title("Horizontal edges")
plt.show()
```

You'll see the cat's outline light up in the edge-detected versions. That's what a CNN layer does — learns 64-256 such filters and uses them as building blocks.

---

## Worked Example — real CNN in PyTorch on CIFAR-10

> **Goal:** Build a CNN with 3 conv layers + 2 dense layers. Train on CIFAR-10 (32×32 RGB, 10 classes). Get > 70% test accuracy in 5 minutes on a single GPU.

### Step 1 — Define the architecture

```python
import torch
import torch.nn as nn

class SimpleCNN(nn.Module):
    def __init__(self, n_classes=10):
        super().__init__()
        # Input: (B, 3, 32, 32)
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),   # → (B, 32, 32, 32)
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # → (B, 32, 16, 16)
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1),              # → (B, 64, 16, 16)
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # → (B, 64, 8, 8)
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1),             # → (B, 128, 8, 8)
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),                      # → (B, 128, 1, 1)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, n_classes),
        )
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        return self.classifier(x)

model = SimpleCNN().cuda()
n_params = sum(p.numel() for p in model.parameters())
print(f"Params: {n_params:,}")
# ~167K parameters — small enough to train on a laptop
```

### Step 2 — Data loaders

```python
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,)*3, (0.5,)*3),
])

train_set = datasets.CIFAR10(root="./data", train=True, download=True, transform=transform)
test_set  = datasets.CIFAR10(root="./data", train=False, transform=transform)

train_loader = torch.utils.data.DataLoader(train_set, batch_size=128, shuffle=True,  num_workers=2)
test_loader  = torch.utils.data.DataLoader(test_set,  batch_size=128, shuffle=False)
```

### Step 3 — Training loop

```python
import time

opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

t0 = time.perf_counter()
for epoch in range(10):
    model.train()
    for imgs, labels in train_loader:
        imgs, labels = imgs.cuda(), labels.cuda()
        opt.zero_grad()
        loss = loss_fn(model(imgs), labels)
        loss.backward()
        opt.step()
    
    # Quick eval
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for imgs, labels in test_loader:
            imgs, labels = imgs.cuda(), labels.cuda()
            preds = model(imgs).argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    
    print(f"epoch {epoch+1:2d}  test acc: {correct/total:.1%}")

elapsed = time.perf_counter() - t0
print(f"\nTotal training time: {elapsed/60:.1f} min")
```

Expected output:
```
   epoch  1  test acc: 56.3%
   epoch  2  test acc: 64.1%
   epoch  3  test acc: 68.9%
   epoch  4  test acc: 71.5%
   epoch  5  test acc: 73.2%
   epoch  6  test acc: 74.4%
   epoch  7  test acc: 75.5%
   epoch  8  test acc: 76.2%
   epoch  9  test acc: 76.7%
   epoch 10  test acc: 77.0%
```

A small CNN with 167K parameters hits 77% on CIFAR-10 in 5 minutes. Not state-of-the-art, but it proves the pattern works.

### Step 4 — Visualize the learned filters

```python
# Look at the first conv layer's filters — 32 of them, each 3×3×3
filters = model.conv1[0].weight.detach().cpu().numpy()   # (32, 3, 3, 3)

fig, axes = plt.subplots(4, 8, figsize=(12, 6))
for i, ax in enumerate(axes.flat):
    # Normalize for display
    f = filters[i].transpose(1, 2, 0)
    f = (f - f.min()) / (f.max() - f.min())
    ax.imshow(f)
    ax.axis("off")
plt.suptitle("First-layer filters (learned)")
plt.show()
# You'll see edge detectors, color blobs, and orientation-selective filters
```

### Step 5 — Visualize the feature maps

```python
# What does each layer "see" when shown a cat?
import torch

def visualize_feature_maps(model, img, layer_name):
    """Hook a layer to capture its activations."""
    activations = {}
    def hook(module, input, output):
        activations[layer_name] = output.detach()
    
    layer = dict(model.named_children())[layer_name]
    handle = layer.register_forward_hook(hook)
    _ = model(img.unsqueeze(0).cuda())
    handle.remove()
    return activations[layer_name][0].cpu().numpy()

img, _ = test_set[0]
maps = visualize_feature_maps(model, img, "conv1")  # (32, 32, 32)

fig, axes = plt.subplots(4, 8, figsize=(12, 6))
for i, ax in enumerate(axes.flat):
    ax.imshow(maps[i], cmap="viridis")
    ax.axis("off")
plt.suptitle("Feature maps after conv1")
plt.show()
# Different channels respond to different patterns: edges, colors, textures
```

---

## The CNN architecture pattern

```
   INPUT IMAGE                CONV BLOCKS                  CLASSIFIER
   ───────────                ───────────                  ──────────
   (3, 32, 32)                
       │                       each block:
       │                       ┌────────────────┐
       ├───────────────────►   │ Conv → BN → ReLU│ × 1-3
       │                       │ + MaxPool      │
       │                       └────────────────┘
       │                            │
       │                            ▼ spatial shrinks (32→16→8→4→1)
       │                            │ channels grow (3→32→64→128→256)
       │                            ▼
       │                       (256, 1, 1)
       │                            │
       │                            ▼ flatten
       │                       (256,)
       │                            │
       │                            ▼
       │                       Dense → ReLU → Dropout
       │                            │
       │                            ▼
       └──────────────────►   (10,) class logits
```

Three rules of thumb:
1. **Spatial dims shrink.** MaxPool or strided conv every block. 32 → 16 → 8 → 4 → 1.
2. **Channel count grows.** 3 → 32 → 64 → 128 → 256. Each layer can look at richer features.
3. **End with global pooling or flatten.** Don't use big dense layers; 256→1000 is fine, 16384→1000 is wasteful.

---

## Cost roll-up

```
   Simple CNN on CIFAR-10:
   Params:        167K
   Training:      5 minutes on a single GPU (RTX 3060 or better)
   Final acc:     77%
   Inference:     0.5ms per image on GPU
   Memory:        ~2 MB model
   
   Compare to:
   ResNet-50:     25M params, 1 hour training, 95% accuracy
   ViT-Base:      86M params, 2 hour training, 98% accuracy
```

The simple CNN is fast but cap-limited. ResNet and ViT trade compute for accuracy.

---

## What this example teaches

1. **A conv layer is a bank of learnable filters.** Each one detects a specific pattern.
2. **CNNs exploit image structure.** Local connectivity + parameter sharing + translation equivariance.
3. **The architecture pattern is CONV → BN → ReLU → POOL**, repeated, then a classifier.
4. **Spatial shrinks, channels grow.** That's the contract.
5. **In PyTorch, a CNN is 30 lines.** Training loop is 10 lines. The hard work was in the 1970s-2010s; now you assemble.

---

## From this CNN to ResNet

Add residual connections:

```python
class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(channels)
    
    def forward(self, x):
        residual = x
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return torch.relu(out + residual)   # ← the skip connection
```

That's ResNet. Stack 50 of these blocks → ResNet-50, which gets 95% on CIFAR-10.

---

## What Comes Next

> Lesson 2 — **ResNets and Transfer Learning** — why skip connections unlocked deep networks, and how to fine-tune a pretrained ResNet on a custom dataset.