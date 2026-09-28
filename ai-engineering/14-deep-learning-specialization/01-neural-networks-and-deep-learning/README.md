# Course 1 — Neural Networks and Deep Learning

> **Instructor:** Andrew Ng · **Level:** Beginner-to-intermediate · **Time:** 4 weeks

The first principles of deep learning. Build a neural network from scratch in NumPy. Understand what each layer and each parameter does. By the end, you'll know exactly what happens inside a forward pass and a backward pass.

---

## What you'll build

| Week | Project | Difficulty |
|---|---|---|
| 1 | No code — intro, the "housing price" intuition | — |
| 2 | Logistic regression from scratch (NumPy) | Easy |
| 3 | Shallow NN with one hidden layer | Easy |
| 4 | Deep NN with L layers | Medium |

All projects use the same pattern:
1. Define the architecture
2. Initialize parameters
3. Forward prop
4. Compute loss
5. Backward prop
6. Update parameters
7. Predict and evaluate

Once you've done it from scratch, **PyTorch is a one-line replacement** for steps 2-6. But you have to understand them first.

---

## Week 1 — Introduction to deep learning

**Topics:**
- What is a neural network (the housing-price intuition)
- Supervised learning setup: (x, y) → model → ŷ
- Why deep learning is suddenly working (data, compute, algorithms)
- The course map

**The big idea:** A neural network is just a function approximator. Given enough parameters and enough data, it can learn any pattern.

---

## Week 2 — Neural networks basics

**Topics:**
- Binary classification
- Logistic regression as a 1-neuron "network"
- Loss function (cross-entropy)
- Gradient descent
- Computational graphs (the basis for backprop)
- Vectorization (the speed trick)

**The big idea:** A logistic regression unit is the smallest possible neural network. Once you understand it, you understand the building block of every larger network.

---

## Week 3 — Shallow neural networks

**Topics:**
- The hidden layer
- Activation functions (sigmoid, tanh, ReLU)
- Forward propagation with matrices
- Backward propagation with matrices
- Random initialization

**The big idea:** Adding one hidden layer turns a linear classifier into a universal function approximator (in theory). In practice, you need more layers, more data, and the right activations.

---

## Week 4 — Deep neural networks

**Topics:**
- L-layer deep networks
- Forward / backward prop as matrix chain
- Building blocks of deep networks (layer, activation, loss)
- Parameters vs hyperparameters
- The deep learning "meta" — how to think about depth

**The big idea:** Depth lets the network build up hierarchical features. Layer 1 learns edges. Layer 2 learns shapes. Layer 3 learns objects. Layer 4 learns scenes.

---

## What's next

Course 1 teaches you what a neural network **is**. Course 2 teaches you how to make one **work in practice** (regularization, optimization, debugging).

---

## Lead lesson

See `01-logistic-regression-from-scratch.md` for the full worked example: build a logistic regression classifier on the "cats vs non-cats" dataset, implement forward + backward prop in NumPy, hit 70% accuracy.