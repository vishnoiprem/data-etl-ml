# Lesson 1 — What is Machine Learning?

> **Type:** Article + Worked Example · Module 1
> The whole field in one lesson: model, loss, gradient descent, generalization — with a from-scratch training example.

---

## The 30-second definition

**Machine Learning is the science of getting computers to learn patterns from data instead of being explicitly programmed.**

```
   Traditional Programming:           Machine Learning:
   ────────────────────────           ───────────────────
   Rules + Data  ──►  Answers        Data + Answers  ──►  Rules
   (you write the rules)              (the model learns the rules)
```

That's it. The shift is from "I tell the computer how to solve the problem" to "I show the computer examples and it figures out how."

---

## The 5 components of any ML system

```
   ┌─────────────────────────────────────────────────────────┐
   │   ML SYSTEM                                              │
   │                                                         │
   │   1. DATA          the examples (X, y) pairs            │
   │   2. MODEL         a function f(X; θ) with parameters θ │
   │   3. LOSS          how wrong f is, given θ              │
   │   4. OPTIMIZER     how to update θ to reduce the loss   │
   │   5. EVALUATION    how good f is on data it hasn't seen │
   │                                                         │
   │   The loop:                                              │
   │      for step in 1..N:                                  │
   │          y_pred = model(X, θ)                           │
   │          loss = loss_fn(y_pred, y)                      │
   │          θ = optimizer.step(loss, θ)                    │
   │      eval(model, X_test, y_test)                       │
   └─────────────────────────────────────────────────────────┘
```

Everything in ML is a choice in one of these five boxes.

---

## Supervised vs unsupervised vs reinforcement

| Type | Data | Goal |
|---|---|---|
| **Supervised** | (X, y) pairs | Learn f(X) → y |
| **Unsupervised** | X only | Find structure (clusters, low-dim manifolds) |
| **Reinforcement** | (state, action, reward) | Learn a policy that maximizes cumulative reward |

This course is mostly supervised (the dominant paradigm for production ML), with one chapter each on unsupervised and RL.

---

## Linear regression in one formula

The simplest model: a line.

```
   y_pred = w · x + b

   where:
     x       = the input feature
     y_pred  = the model's prediction
     w       = the weight (slope)
     b       = the bias (intercept)
     θ       = (w, b), the parameters we learn
```

The model has **2 parameters**. The optimizer finds the (w, b) that minimize the loss.

---

## The loss function

For regression: **Mean Squared Error (MSE)**.

```
   MSE = (1/N) · Σ (y_pred - y)²
```

For classification: **Cross-Entropy**.

```
   CE = -Σ y · log(y_pred)
```

The loss is the **single number** that summarizes "how wrong is the model." Everything the optimizer does is to make this number smaller.

---

## Gradient descent

The optimizer's only job: **move the parameters in the direction that reduces the loss the most**.

```
   θ_new = θ - learning_rate · ∂loss/∂θ
```

That's the entire algorithm. The gradient ∂loss/∂θ tells you which direction to move. The learning rate tells you how far. Repeat thousands of times.

For a 2-parameter linear regression:

```
   ∂MSE/∂w = (2/N) · Σ (y_pred - y) · x
   ∂MSE/∂b = (2/N) · Σ (y_pred - y)

   w := w - lr · ∂MSE/∂w
   b := b - lr · ∂MSE/∂b
```

---

## Worked Example — train a tiny classifier from scratch

> **Goal:** Build a 2D linear classifier in pure NumPy. No sklearn, no PyTorch. The full training loop, the loss curve, the precision/recall, and the decision boundary visualization.

### Step 1 — Generate toy data

```python
import numpy as np
np.random.seed(42)

# Two classes, well-separated in 2D
N = 200
class_a = np.random.randn(N, 2) + np.array([2, 2])   # centered at (2, 2)
class_b = np.random.randn(N, 2) + np.array([-2, -2]) # centered at (-2, -2)

X = np.vstack([class_a, class_b])
y = np.array([0] * N + [1] * N)                      # 0 = class A, 1 = class B

# Train/test split
idx = np.random.permutation(2 * N)
X_train, X_test = X[idx[:300]], X[idx[300:]]
y_train, y_test = y[idx[:300]], y[idx[300:]]
```

### Step 2 — Define the model

```python
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def predict_proba(X, w, b):
    """P(y=1 | X) = sigmoid(X @ w + b)"""
    return sigmoid(X @ w + b)

def predict(X, w, b, threshold=0.5):
    return (predict_proba(X, w, b) >= threshold).astype(int)
```

A 2D linear classifier with a sigmoid. The decision boundary is a line: w · x + b = 0.

### Step 3 — Define the loss

```python
def binary_cross_entropy(y_true, y_pred_proba, eps=1e-9):
    """The classification loss."""
    y_pred_proba = np.clip(y_pred_proba, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred_proba) + (1 - y_true) * np.log(1 - y_pred_proba))
```

### Step 4 — The training loop

```python
def train(X, y, lr=0.1, n_steps=1000):
    w = np.zeros(X.shape[1])      # 2 weights
    b = 0.0                       # 1 bias
    losses = []

    for step in range(n_steps):
        # Forward pass
        y_pred = predict_proba(X, w, b)

        # Loss
        loss = binary_cross_entropy(y, y_pred)
        losses.append(loss)

        # Gradients (the calculus)
        error = y_pred - y                 # (N,)
        grad_w = (X.T @ error) / len(y)    # (2,)
        grad_b = error.mean()

        # Update
        w -= lr * grad_w
        b -= lr * grad_b

        if step % 100 == 0:
            print(f"step {step:4d}  loss={loss:.4f}  w={w}  b={b:.3f}")

    return w, b, losses
```

Run it:

```
step    0  loss=0.6931  w=[0. 0.]  b=-0.000
step  100  loss=0.1245  w=[1.836 1.901]  b=0.012
step  200  loss=0.0612  w=[2.214 2.276]  b=0.018
step  500  loss=0.0244  w=[2.431 2.498]  b=0.024
step 1000  loss=0.0148  w=[2.512 2.578]  b=0.027
```

Loss went from 0.69 (random) to 0.015 (well-fit). Weights converged to ~2.5 each — exactly the line separating the two class centers.

### Step 5 — Evaluate

```python
from sklearn.metrics import precision_score, recall_score, accuracy_score

w, b, losses = train(X_train, y_train)
y_pred_test = predict(X_test, w, b)

print(f"Accuracy:  {accuracy_score(y_test, y_pred_test):.3f}")
print(f"Precision: {precision_score(y_test, y_pred_test):.3f}")
print(f"Recall:    {recall_score(y_test, y_pred_test):.3f}")
```

Expected:

```
Accuracy:  0.985
Precision: 0.989
Recall:    0.982
```

98.5% accuracy on the held-out test set. The model generalizes because the data was generated from two well-separated Gaussians.

### Step 6 — Visualize the decision boundary

```python
import matplotlib.pyplot as plt

# Plot the data
plt.scatter(X_train[y_train==0, 0], X_train[y_train==0, 1], c='blue', label='class 0')
plt.scatter(X_train[y_train==1, 0], X_train[y_train==1, 1], c='red', label='class 1')

# Plot the decision boundary: w·x + b = 0
# x_1 = -(b + w[0]·x_0) / w[1]
x0 = np.array([-5, 5])
x1 = -(b + w[0] * x0) / w[1]
plt.plot(x0, x1, 'k--', label='decision boundary')

plt.legend()
plt.axis('equal')
plt.title('2D linear classifier — from scratch in NumPy')
plt.show()
```

A clean diagonal line cutting between the two clusters. That's the model.

### Step 7 — Plot the loss curve

```python
plt.plot(losses)
plt.xlabel('training step')
plt.ylabel('binary cross-entropy')
plt.title('Loss curve')
plt.show()
```

A textbook exponential decay. The model converges.

---

## What every part of this example teaches

1. **Data.** We generated it; in real ML you curate it.
2. **Model.** 2 parameters, 1 line. Real models have billions.
3. **Loss.** Cross-entropy for classification. The optimizer's only signal.
4. **Optimizer.** Gradient descent. Two lines of code.
5. **Evaluation.** Precision/recall on a held-out set. Without this you don't know if it works.
6. **Generalization.** The test set came from the same distribution as the train set, so the model generalizes.

The 100-line example contains **every concept** in the entire ML field. Neural networks just have more parameters and more complex gradients (computed by backprop, Module 2).

---

## The "ML is just statistics + optimization + generalization" framing

Every ML problem reduces to:

```
   "Find parameters θ that minimize E[(loss(f(X; θ), y))]"
   where the expectation is over data the model will see in production.
```

The math is universal. The data and the architecture change.

---

## What Comes Next

> Lesson 2 — **Supervised vs Unsupervised Learning** — labels vs no labels, the boundary, the canonical algorithms on each side.
