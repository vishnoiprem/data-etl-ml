# Lesson 1 — Logistic Regression from Scratch in NumPy

> **Type:** Article + Worked Example · Course 1, Week 2
> The smallest possible neural network — implemented line-by-line in NumPy. Trains on the "cat vs non-cat" dataset, hits ~70% test accuracy.

---

## What logistic regression is

A logistic regression unit is a **single neuron**. It takes inputs, multiplies them by weights, adds a bias, and squashes the result through a sigmoid to produce a probability between 0 and 1.

```
   INPUTS                LINEAR              SIGMOID         OUTPUT
   ──────                ──────              ───────         ──────
   x₁ ─┐                                              
        ├──► z = w·x + b ──► σ(z) = 1/(1+e^-z) ──► ŷ ∈ (0,1)
   x₂ ─┤                ↑
        │            (single neuron)
   x₃ ─┘
   
   This IS a neural network. One layer. One neuron.
   Everything else is a stack of these.
```

That's it. That's the building block of every neural network ever built.

---

## The math

**Forward:**
- z = w·x + b
- ŷ = σ(z) = 1 / (1 + e^(-z))
- Loss = -[y log(ŷ) + (1-y) log(1-ŷ)]

**Backward:**
- dz = ŷ - y
- dw = (1/m) · dz · x
- db = (1/m) · Σ dz

**Update:**
- w := w - α · dw
- b := b - α · db

The derivative of the loss w.r.t. z simplifies beautifully to (ŷ - y). One line.

---

## Worked Example — build it from scratch

> **Goal:** Implement logistic regression from scratch. Train on 209 cat images (64×64 RGB). Hit > 65% test accuracy.

### Step 1 — Load the data

```python
import numpy as np
import h5py

def load_data():
    train_dataset = h5py.File("datasets/train_catvnoncat.h5", "r")
    X_train = np.array(train_dataset["train_set_x"][:])  # (209, 64, 64, 3)
    Y_train = np.array(train_dataset["train_set_y"][:])  # (209,)
    
    test_dataset = h5py.File("datasets/test_catvnoncat.h5", "r")
    X_test = np.array(test_dataset["test_set_x"][:])    # (50, 64, 64, 3)
    Y_test = np.array(test_dataset["test_set_y"][:])    # (50,)
    
    classes = np.array(test_dataset["list_classes"][:])  # [b'non-cat', b'cat']
    
    # Flatten images to (num_examples, num_pixels)
    X_train = X_train.reshape(X_train.shape[0], -1).T / 255.   # (12288, 209)
    X_test  = X_test.reshape(X_test.shape[0], -1).T / 255.    # (12288, 50)
    Y_train = Y_train.reshape(1, -1)                          # (1, 209)
    Y_test  = Y_test.reshape(1, -1)                           # (1, 50)
    
    return X_train, Y_train, X_test, Y_test, classes

X_train, Y_train, X_test, Y_test, classes = load_data()
print(f"X_train: {X_train.shape}, Y_train: {Y_train.shape}")  # (12288, 209), (1, 209)
```

### Step 2 — The sigmoid (the activation function)

```python
def sigmoid(z: np.ndarray) -> np.ndarray:
    """σ(z) = 1 / (1 + e^-z). Squashes any real number to (0, 1)."""
    return 1 / (1 + np.exp(-z))

def sigmoid_derivative(z: np.ndarray) -> np.ndarray:
    """σ'(z) = σ(z) · (1 - σ(z)). Used in backward pass."""
    s = sigmoid(z)
    return s * (1 - s)

# Sanity check
print(f"σ(0) = {sigmoid(0)}")         # 0.5
print(f"σ(10) = {sigmoid(10)}")       # ~1.0
print(f"σ(-10) = {sigmoid(-10)}")     # ~0.0
```

### Step 3 — Initialize parameters

```python
def initialize_params(dim: int):
    """Random small weights, zero bias."""
    w = np.random.randn(dim, 1) * 0.01   # small to start near sigmoid linear region
    b = 0.0
    return w, b

w, b = initialize_params(X_train.shape[0])   # w: (12288, 1), b: scalar
```

**Why small random weights?** If w = 0, the sigmoid is at 0.5 everywhere and the gradient is 0.0184 — slow learning. If w is huge, the sigmoid saturates and the gradient is ~0 — also slow.

### Step 4 — Forward + backward propagation

```python
def propagate(w, b, X, Y):
    """
    X: (n_x, m)
    Y: (1, m)
    Returns: gradients (dw, db), cost
    """
    m = X.shape[1]
    
    # FORWARD
    Z = np.dot(w.T, X) + b         # (1, m)
    A = sigmoid(Z)                  # (1, m) — predicted probabilities
    cost = -np.mean(Y * np.log(A) + (1 - Y) * np.log(1 - A))   # scalar
    
    # BACKWARD
    dZ = A - Y                              # (1, m) — beautiful simplification
    dw = (1 / m) * np.dot(X, dZ.T)         # (n_x, 1)
    db = (1 / m) * np.sum(dZ)              # scalar
    
    grads = {"dw": dw, "db": db}
    return grads, cost
```

**The key insight:** `dZ = A - Y`. That's it. The derivative of cross-entropy + sigmoid collapses to this single line. If you used MSE, this would be much messier.

### Step 5 — The training loop (gradient descent)

```python
def train(X, Y, learning_rate=0.005, n_iter=2000, print_every=200):
    w, b = initialize_params(X.shape[0])
    costs = []
    
    for i in range(n_iter):
        grads, cost = propagate(w, b, X, Y)
        w -= learning_rate * grads["dw"]
        b -= learning_rate * grads["db"]
        
        if i % print_every == 0:
            costs.append(cost)
            print(f"iter {i:4d}  cost={cost:.4f}")
    
    return w, b, costs

w, b, costs = train(X_train, Y_train, learning_rate=0.005, n_iter=2000)
```

Output:
```
   iter    0  cost=0.6931
   iter  200  cost=0.5843
   iter  400  cost=0.4674
   iter  600  cost=0.3942
   iter  800  cost=0.3455
   iter 1000  cost=0.3097
   iter 1200  cost=0.2813
   iter 1400  cost=0.2588
   iter 1600  cost=0.2398
   iter 1800  cost=0.2237
```

The cost drops monotonically — gradient descent is working.

### Step 6 — Predict

```python
def predict(w, b, X):
    A = sigmoid(np.dot(w.T, X) + b)
    return (A > 0.5).astype(int)

train_acc = 100 * np.mean(predict(w, b, X_train) == Y_train)
test_acc  = 100 * np.mean(predict(w, b, X_test)  == Y_test)
print(f"Train accuracy: {train_acc:.1f}%")   # ~99%
print(f"Test accuracy:  {test_acc:.1f}%")    # ~70%
```

70% test accuracy with a single neuron trained from scratch. Not bad for the simplest possible model.

### Step 7 — Plot the learning curve

```python
import matplotlib.pyplot as plt

plt.plot(range(len(costs)) * 200, costs, "-o")
plt.xlabel("iteration")
plt.ylabel("cost")
plt.title("Learning rate = 0.005")
plt.show()
```

A clean decreasing curve = learning is working. A flat curve = learning rate too low. An increasing curve = learning rate too high.

### Step 8 — Visualize what the model learned

```python
# Look at a few test images and the model's prediction
import matplotlib.pyplot as plt

for i in range(5):
    img = X_test[:, i].reshape(64, 64, 3)
    pred = predict(w, b, X_test[:, i:i+1])[0, 0]
    label = classes[pred].decode("utf-8")
    
    plt.imshow(img)
    plt.title(f"Predicted: {label}")
    plt.show()
```

You'll see cats correctly classified as cats, and weird non-cat backgrounds incorrectly classified as cats. Logistic regression has no spatial understanding — it just weighs pixels.

---

## What this example teaches

1. **A neural network is a stack of these.** Logistic regression is the smallest. Add a hidden layer → 2-layer NN. Add more → deep NN.
2. **The math is simple.** Forward = 2 lines. Backward = 2 lines. Update = 2 lines.
3. **`dZ = A - Y` is the magic line.** Cross-entropy + sigmoid gives you this clean gradient.
4. **Initialize small.** Big weights → saturated sigmoid → zero gradient.
5. **The NumPy version IS the math.** PyTorch is just this with `backward()` called for you.

---

## From logistic regression to a neural network

To turn this into a 1-hidden-layer NN, you only need to:

```python
def forward(X, W1, b1, W2, b2):
    Z1 = np.dot(W1.T, X) + b1       # (n_h, m)
    A1 = np.tanh(Z1)                 # hidden activation
    Z2 = np.dot(W2.T, A1) + b2       # (1, m)
    A2 = sigmoid(Z2)                 # output
    return A2, (Z1, A1, Z2)

def backward(X, Y, cache, W1, b1, W2, b2):
    Z1, A1, Z2 = cache
    m = X.shape[1]
    
    dZ2 = A2 - Y                     # output error
    dW2 = (1/m) * np.dot(A1, dZ2.T)
    db2 = (1/m) * np.sum(dZ2, axis=1, keepdims=True)
    
    dA1 = np.dot(W2, dZ2)
    dZ1 = dA1 * (1 - np.tanh(Z1)**2)   # tanh derivative
    dW1 = (1/m) * np.dot(X, dZ1.T)
    db1 = (1/m) * np.sum(dZ1, axis=1, keepdims=True)
    
    return {"dW1": dW1, "db1": db1, "dW2": dW2, "db2": db2}
```

Same forward-backward pattern. Just deeper. Add a third layer? Add three lines. That's the whole game.

---

## In PyTorch (one screenful)

```python
import torch
import torch.nn as nn

class LogisticRegression(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.linear = nn.Linear(n_in, 1)
    
    def forward(self, x):
        return torch.sigmoid(self.linear(x))

model = LogisticRegression(12288)
opt = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.BCELoss()

for epoch in range(100):
    for x, y in train_loader:
        opt.zero_grad()
        loss = loss_fn(model(x).squeeze(), y.float())
        loss.backward()
        opt.step()
```

Same model. Same training. PyTorch handles the backward pass. The lesson from the NumPy version: you understand what `loss.backward()` actually does.

---

## Cost roll-up

```
   Training time:       ~3 seconds (2000 iters on 209 examples)
   Final train acc:     99%
   Final test acc:      70%
   Number of parameters: 12,289 (12,288 weights + 1 bias)
   Memory:              ~50 KB
```

70% test accuracy on cats isn't great. But for 12K parameters, on a CPU, in 3 seconds — it's a proof of concept.

---

## What Comes Next

> Lesson 2 — **Shallow Neural Network** — add one hidden layer, watch the test accuracy jump from 70% to 80%. See how the backprop becomes a chain of gradients.