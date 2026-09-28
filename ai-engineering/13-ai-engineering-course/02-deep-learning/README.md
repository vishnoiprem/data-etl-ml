# Module 2 — Deep Learning and Neural Networks

> Source: Outcome School · Module 2 · 10 lessons

---

## Course Promise

> "Explain how a neural network trains, from the forward pass to the weight update, with the math."

This module goes inside the network: gradient descent and backpropagation step by step, the techniques that make training stable (dropout, normalization), and the framework mechanics (PyTorch, TensorFlow).

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Bias in Neural Networks](./01-bias-in-neural-networks.md) | Article + Worked Example | What bias buys you, where it lives |
| 2 | Gradient Descent | Article | Loss landscape, learning rate, batch/ stochastic |
| 3 | Backpropagation | Article | The chain rule, forward + backward pass |
| 4 | Cross-Entropy Loss | Article | Why log, binary vs categorical, gradient math |
| 5 | Dropout | Article | Co-adaptation, training vs inference, variants |
| 6 | Batch Norm vs Layer Norm | Article | Where each goes, why transformers use LayerNorm |
| 7 | RMSNorm | Article | The faster LayerNorm, used in Llama/Mistral |
| 8 | RNNs | Article | Sequential models, the vanishing gradient |
| 9 | PyTorch | Article | Tensors, autograd, the computation graph |
| 10 | TensorFlow | Article | Graphs, sessions, the static-graph era |

---

## The Lead Lesson

> **Lesson 1 — [Bias in Neural Networks](./01-bias-in-neural-networks.md)** — the often-missed first lesson of deep learning. Worked example: build a tiny 2-layer network for XOR from scratch in NumPy, watch how adding bias unlocks the problem, then visualize the decision boundary before/after.