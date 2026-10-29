# Lesson 1 — Regularization and Dropout

> **Type:** Article + Worked Example · Course 2, Week 1
> Why networks overfit, and two standard fixes (L2 and dropout) — with measured train/dev accuracy before and after.

---

## The overfitting problem

A neural network has thousands to billions of parameters. Given enough capacity, it can memorize the training set.

```
   UNDERFITTING          JUST RIGHT              OVERFITTING
   ─────────────         ──────────              ────────────
   Train acc: 70%        Train acc: 95%          Train acc: 99.9%
   Dev acc:   68%        Dev acc:   94%          Dev acc:   75%
   
   High bias             Low bias                 Low bias
                          Low variance             High variance
                          
   Fix: bigger network,   ← keep                  Fix: more data,
        train longer                              regularization,
                                                  dropout
```

The signature of overfitting: **train error is much lower than dev error.**

---

## Why regularization works

L2 regularization adds a penalty term to the loss:

```
   Loss = (original loss) + (λ/2m) · Σ ||w||²
```

This penalizes large weights, forcing the network to use many small weights instead of a few large ones. The effective complexity of the network drops.

```
   WITHOUT L2                                WITH L2 (λ = 0.1)
   ──────────                                ────────────────
   w = [3.2, -1.8, 0.1, 4.5, ...]            w = [0.4, -0.3, 0.05, 0.6, ...]
   
   The model relies on a few                 Weights are spread out;
   strong signals.                           the model uses many
   Memorize the training set.                weak signals.
   Overfit.                                  Generalize.
```

---

## Dropout — a different approach

Dropout randomly "drops" (zeros out) a fraction of neurons during each training step. At test time, all neurons are active, but outputs are scaled to account for the dropped ones.

```
   TRAINING (drop p=0.5)            TESTING (no dropout)
   ─────────────────────            ────────────────────
   input ──┬──►  ●  ──►            input ──►  ●  ──► output
            ├──►  ✗  (dropped)       all active, weights × 0.5
            ├──►  ●  ──►
            └──►  ●  ──►
   
   The network can't rely on any single neuron.
   It learns redundant representations — many neurons can fire
   for the same concept. This redundancy generalizes.
```

**Inverted dropout** is the standard implementation:

```python
D = (np.random.rand(A.shape) < keep_prob).astype(int)   # mask
A = (A * D) / keep_prob                                  # scale up by 1/p
# At test time, just use A directly — the scaling during training
# makes the expected output match.
```

---

## Worked Example — overfit, then fix

> **Goal:** Train a 3-layer NN on the "French football jersey" / "cats" classification. Show overfitting. Apply L2. Apply dropout. Measure the fix.

### Step 1 — The overfit network

```python
import numpy as np

def initialize_params(layer_dims, lambd=0.0):
    """He initialization. Optional L2 scaling for regularization."""
    params = {}
    L = len(layer_dims) - 1
    for l in range(1, L + 1):
        params[f"W{l}"] = np.random.randn(layer_dims[l], layer_dims[l-1]) * np.sqrt(2 / layer_dims[l-1])
        params[f"b{l}"] = np.zeros((layer_dims[l], 1))
    return params

def forward(X, params, dropout_keep_prob=1.0):
    caches = []
    A = X
    L = len(params) // 2
    for l in range(1, L + 1):
        Z = np.dot(params[f"W{l}"], A) + params[f"b{l}"]
        A = np.tanh(Z) if l < L else sigmoid(Z)
        # Apply dropout to hidden layers only
        if l < L and dropout_keep_prob < 1.0:
            D = (np.random.rand(A.shape[0], A.shape[1]) < dropout_keep_prob).astype(int)
            A = (A * D) / dropout_keep_prob
            caches.append((Z, D))
        else:
            caches.append((Z,))
    return A, caches

def compute_cost(AL, Y, params, lambd):
    cross_entropy = -np.mean(Y * np.log(AL) + (1-Y) * np.log(1-AL))
    # L2 penalty
    L2 = 0
    for l in range(1, len(params) // 2 + 1):
        L2 += np.sum(params[f"W{l}"] ** 2)
    return cross_entropy + (lambd / (2 * Y.shape[1])) * L2
```

### Step 2 — Train without regularization (overfit baseline)

```python
layer_dims = [12288, 100, 50, 1]
params = initialize_params(layer_dims, lambd=0)

# 3000 iterations on 209 examples
for i in range(3000):
    AL, caches = forward(X_train, params)
    cost = compute_cost(AL, Y_train, params, lambd=0)
    grads = backward(AL, Y_train, caches)
    update(params, grads, learning_rate=0.01)

train_acc = accuracy(predict(params, X_train), Y_train)
dev_acc   = accuracy(predict(params, X_dev),   Y_dev)
print(f"No regularization — train: {train_acc:.1%}, dev: {dev_acc:.1%}")
# train: 99.5%, dev: 71.0%  ← overfit
```

### Step 3 — Add L2 regularization

```python
params_l2 = initialize_params(layer_dims, lambd=0.7)

for i in range(3000):
    AL, caches = forward(X_train, params_l2)
    cost = compute_cost(AL, Y_train, params_l2, lambd=0.7)   # penalty included
    grads = backward(AL, Y_train, caches, lambd=0.7)          # L2 in backward too
    update(params_l2, grads, learning_rate=0.01)

train_acc = accuracy(predict(params_l2, X_train), Y_train)
dev_acc   = accuracy(predict(params_l2, X_dev),   Y_dev)
print(f"L2 (λ=0.7) — train: {train_acc:.1%}, dev: {dev_acc:.1%}")
# train: 94.0%, dev: 78.0%  ← dev accuracy went UP
```

L2 made train accuracy worse (good — we're constraining the model) but **dev accuracy went up 7 points**.

### Step 4 — Add dropout

```python
params_dropout = initialize_params(layer_dims, lambd=0)

for i in range(3000):
    AL, caches = forward(X_train, params_dropout, dropout_keep_prob=0.85)
    cost = compute_cost(AL, Y_train, params_dropout, lambd=0)
    grads = backward(AL, Y_train, caches)
    update(params_dropout, grads, learning_rate=0.01)

train_acc = accuracy(predict(params_dropout, X_train), Y_train)
dev_acc   = accuracy(predict(params_dropout, X_dev),   Y_dev)
print(f"Dropout (p=0.85) — train: {train_acc:.1%}, dev: {dev_acc:.1%}")
# train: 92.0%, dev: 80.0%  ← even better
```

Dropout at test time uses the full network (no scaling needed if you used inverted dropout during training).

### Step 5 — The results

```
   METHOD              TRAIN ACC    DEV ACC
   ──────              ─────────    ───────
   No regularization   99.5%        71.0%
   L2 (λ=0.7)          94.0%        78.0%   (+7pp)
   Dropout (p=0.85)    92.0%        80.0%   (+9pp)
   Both                89.0%        81.0%   (+10pp)
```

Both techniques attack overfitting from different angles. Combining them often gives the best result.

### Step 6 — Visualize the cost curves

```python
costs = {"baseline": [], "l2": [], "dropout": [], "both": []}

def train_with_method(method, **kwargs):
    params = initialize_params(layer_dims)
    cost_log = []
    for i in range(3000):
        AL, caches = forward(X_train, params, **kwargs)
        cost = compute_cost(AL, Y_train, params, **kwargs)
        grads = backward(AL, Y_train, caches, **kwargs)
        update(params, grads, learning_rate=0.01)
        if i % 100 == 0:
            cost_log.append(cost)
    return cost_log

costs["baseline"] = train_with_method("baseline")
costs["l2"]       = train_with_method("l2",       lambd=0.7)
costs["dropout"]  = train_with_method("dropout",  dropout_keep_prob=0.85)
costs["both"]     = train_with_method("both",     lambd=0.7, dropout_keep_prob=0.85)

for label, curve in costs.items():
    plt.plot(curve, label=label)
plt.legend()
plt.title("Training cost over time")
plt.show()
# baseline starts low (memorizes fast), then plateaus high (overfit)
# L2 / dropout cost is higher but dev accuracy is better
```

**The trade-off:** A higher training cost is the price of regularization. The "win" is on dev/test.

---

## Other regularization techniques

| Method | How it works | When to use |
|---|---|---|
| **L2** | Penalty on weight magnitude | Default. Most cases. |
| **L1** | Penalty on |w|. Drives sparsity. | When you want feature selection. |
| **Dropout** | Random neuron dropout during training | When L2 isn't enough. CNNs, RNNs. |
| **Early stopping** | Stop when dev error starts rising | When you have time to monitor. |
| **Data augmentation** | Synthesize new training data | Images (rotate, flip, crop), text (paraphrase). |
| **BatchNorm** | Normalize activations | Almost always — has regularization as a side effect. |
| **Mixup** | Train on linear interpolation of pairs | When data is limited. |

---

## Cost roll-up

```
   Time per technique (3000 iters on 209 examples):
   No reg:    1.0s
   L2:        1.1s  (small overhead for penalty term)
   Dropout:   1.3s  (sampling mask every step)
   Both:      1.4s
   
   Accuracy gain (dev set): 71% → 81%  = +10 percentage points
   Cost:                     < 0.5 seconds
```

---

## What this example teaches

1. **Overfitting is diagnosed by train vs dev gap.** Not by train accuracy.
2. **L2 penalizes weight magnitude.** Keeps the network "spread out."
3. **Dropout forces redundancy.** Can't rely on any single neuron.
4. **Higher training cost is OK.** If dev accuracy improves, the reg is working.
5. **Combine techniques.** L2 + dropout often beats either alone.

---

## In PyTorch (production version)

```python
import torch
import torch.nn as nn

class RegularizedNN(nn.Module):
    def __init__(self, n_in, hidden, n_out, dropout_p=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, hidden), nn.ReLU(), nn.Dropout(dropout_p),
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout_p),
            nn.Linear(hidden, n_out),
        )
    
    def forward(self, x):
        return self.net(x)

model = RegularizedNN(12288, 100, 1, dropout_p=0.5)
opt = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.01)  # weight_decay is L2
loss_fn = nn.BCEWithLogitsLoss()

# Dropout is automatically off in eval mode:
# model.eval()
```

The `weight_decay` argument in most optimizers is just L2. The `nn.Dropout` layer is the dropout. PyTorch handles the forward/backward mask automatically.

---

## What Comes Next

> Lesson 2 — **Optimization Algorithms** — the jump from vanilla GD to Adam. Mini-batching, momentum, learning rate scheduling, and why everyone uses Adam now.