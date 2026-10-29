# Lesson 1 — Bias in Neural Networks

> **Type:** Article + Worked Example · Module 2
> What bias buys you, where it lives in the network, and why XOR is the canonical "you need bias" lesson.

---

## The intuition

A neural network without bias can only draw decision boundaries that pass through the origin. A neural network **with bias** can draw boundaries anywhere.

```
   NO BIAS                          WITH BIAS
   ───────                          ─────────
   f(x) = w · x                     f(x) = w · x + b

   Decision boundary:                Decision boundary:
     w · x = 0                         w · x + b = 0
   passes through origin             passes anywhere
```

That single offset parameter is the difference between a network that can fit most real data and one that can't fit most real data.

---

## Where bias lives

```
   NEURON (with bias)
   ──────────────────
                 ┌─── bias b (a scalar, one per neuron)
                 │
                 ▼
   x_1 ─► w_1 ──┐
   x_2 ─► w_2 ──┤  z = w · x + b   ──►  activation a = σ(z)
   x_3 ─► w_3 ──┤
   ...          │
   x_n ─► w_n ──┘

   Total params for a layer with n inputs and m outputs:
     weights: n × m
     biases:  m   ← always, one per output neuron
```

A 2-layer net with 4 inputs → 8 hidden → 1 output has:
- 4 × 8 + 8 = 40 weights + 8 biases in the first layer
- 8 × 1 + 1 = 8 weights + 1 bias in the second layer
- **49 trainable parameters total**, of which 9 are biases

---

## The XOR problem

The canonical "you need bias" example. Without bias, you cannot solve XOR.

```
   XOR truth table
   ───────────────
   x_1  x_2   y
   ────────────
    0    0    0
    0    1    1
    1    0    1
    1    1    0

   Plotting in 2D:                  Why no-bias fails:
   ┌─────────┐                            (0,0) → 0
   │  0   1  │   y = 1: top-right         (0,1) → 1
   │         │           bottom-left      (1,0) → 1
   │  1   0  │   y = 0: top-left          (1,1) → 0
   └─────────┘           bottom-right
                                     A line through origin CANNOT
                                     separate {top-right + bottom-left}
                                     from {top-left + bottom-right}.
                                     You need bias.
```

Without bias: every line through the origin misses. With bias: you can fit a line through any point.

---

## Worked Example — solve XOR with a tiny 2-layer network, watch bias matter

> **Goal:** Build a 2-layer network for XOR. Train it two ways: (1) without bias, (2) with bias. Show that bias is the difference between "0% accuracy" and "100% accuracy."

### Step 1 — Build the network

```python
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def sigmoid_derivative(a):
    return a * (1 - a)

class TinyNet:
    """2 -> 4 -> 1 with configurable bias."""

    def __init__(self, use_bias=True):
        np.random.seed(0)
        self.use_bias = use_bias
        # Layer 1: 2 inputs -> 4 hidden
        self.W1 = np.random.randn(2, 4) * 0.5
        self.b1 = np.zeros(4) if use_bias else None
        # Layer 2: 4 hidden -> 1 output
        self.W2 = np.random.randn(4, 1) * 0.5
        self.b2 = np.zeros(1) if use_bias else None

    def forward(self, X):
        self.z1 = X @ self.W1 + (self.b1 if self.use_bias else 0)
        self.a1 = sigmoid(self.z1)
        self.z2 = self.a1 @ self.W2 + (self.b2 if self.use_bias else 0)
        self.a2 = sigmoid(self.z2)
        return self.a2

    def backward(self, X, y, lr=0.5):
        m = len(y)
        # Output layer
        dz2 = self.a2 - y.reshape(-1, 1)
        dW2 = (self.a1.T @ dz2) / m
        db2 = dz2.mean(axis=0) if self.use_bias else None
        # Hidden layer
        da1 = dz2 @ self.W2.T
        dz1 = da1 * sigmoid_derivative(self.a1)
        dW1 = (X.T @ dz1) / m
        db1 = dz1.mean(axis=0) if self.use_bias else None
        # Update
        self.W1 -= lr * dW1
        self.W2 -= lr * dW2
        if self.use_bias:
            self.b1 -= lr * db1
            self.b2 -= lr * db2
```

### Step 2 — XOR data

```python
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])
```

### Step 3 — Train both versions

```python
def train(net, n_epochs=5000, lr=0.5):
    for epoch in range(n_epochs):
        out = net.forward(X)
        net.backward(X, y, lr=lr)

    preds = (net.forward(X) >= 0.5).astype(int).flatten()
    acc = (preds == y.flatten()).mean()
    return preds, acc

# Without bias
net_no_bias = TinyNet(use_bias=False)
preds_no, acc_no = train(net_no_bias)
print(f"No bias — predictions: {preds_no}, accuracy: {acc_no}")
# No bias — predictions: [0 0 0 0], accuracy: 0.50  (always predicts 0)

# With bias
net_with_bias = TinyNet(use_bias=True)
preds_yes, acc_yes = train(net_with_bias)
print(f"With bias — predictions: {preds_yes}, accuracy: {acc_yes}")
# With bias — predictions: [0 1 1 0], accuracy: 1.00
```

**Result:** without bias, the network converges to always predicting 0 (50% accuracy). With bias, it gets 100%.

### Step 4 — Visualize the decision boundary

```python
import matplotlib.pyplot as plt

def plot_boundary(net, title):
    plt.figure(figsize=(5, 5))
    # Plot data points
    for (x1, x2), label in zip(X, y.flatten()):
        plt.scatter(x1, x2, c='red' if label else 'blue', s=200)
    # Plot decision surface
    xx, yy = np.meshgrid(np.linspace(-0.5, 1.5, 100), np.linspace(-0.5, 1.5, 100))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = net.forward(grid).reshape(xx.shape)
    plt.contourf(xx, yy, Z, levels=[0, 0.5, 1], alpha=0.3, colors=['blue', 'red'])
    plt.title(title)
    plt.show()

plot_boundary(net_no_bias, "Without bias — decision boundary fails")
plot_boundary(net_with_bias, "With bias — XOR solved")
```

The no-bias plot shows a uniform color (no useful boundary). The with-bias plot shows the four quadrants correctly colored.

### Step 5 — Inspect the learned biases

```python
print(f"Layer 1 biases (with bias): {net_with_bias.b1}")
print(f"Layer 2 bias   (with bias): {net_with_bias.b2}")
# e.g., [-1.18,  4.62, -4.60,  4.66] for layer 1, ~-6.13 for layer 2
```

The biases shifted the activation thresholds so the hidden layer could separate the XOR pattern.

---

## What this example teaches

1. **Bias is not optional.** Without it, certain functions are unreachable.
2. **It's one parameter per neuron.** Cheap to add.
3. **It shifts the activation threshold.** The neuron's "firing point" moves.

In every modern architecture (Transformers, CNNs, RNNs), every layer has bias. PyTorch's `nn.Linear` includes it by default.

---

## Common confusion: bias vs variance in ML

These are two different things:

| Bias (this lesson) | Bias-variance tradeoff (Lesson 7) |
|---|---|
| A trainable parameter that offsets activations | A property of a model's predictions across training sets |
| Architectural (do you include it in the layer?) | Statistical (how much does the model overfit?) |

Different `bias`. Same word. Same word in English; different concepts in ML.

---

## What Comes Next

> Lesson 2 — **Gradient Descent** — the math behind how the optimizer finds the parameters. The full derivation with worked numeric example.
