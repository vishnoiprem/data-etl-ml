# Deep Learning Specialization (deeplearning.ai / Andrew Ng)

> **The foundational deep learning course.** 5 courses, taught by Andrew Ng. Math-first, code-second, intuition always present.
>
> Status: principal-engineer-grade notes with worked examples per lead lesson.

---

## Why this specialization

Before you can build a transformer, you need to know what a neural network *is*. Before you can fine-tune an LLM, you need to know what a forward pass and backward pass are. Before you can debug a vanishing gradient, you need to know why it happens.

```
   THIS SPECIALIZATION             THE 13-AI-ENGINEERING COURSE
   ──────────────────             ───────────────────────────
   Foundations of deep learning    Building production AI systems
   Math: linear algebra, calculus  Math: vector search, batched matmuls,
   Code: NumPy from scratch         code in PyTorch
   "How does a neuron learn?"      "How does a 70B model serve at scale?"
```

Read this first, then move to the AI Engineering course. The two tracks complement each other.

---

## The 5 courses

### Course 1 — Neural Networks and Deep Learning
**The basics.** Logistic regression, shallow NN, deep NN, forward/backward prop. All from scratch in NumPy.

- Week 1: Introduction to deep learning
- Week 2: Neural networks basics
- Week 3: Shallow neural networks
- Week 4: Deep neural networks

### Course 2 — Improving Deep Neural Networks: Hyperparameter Tuning, Regularization and Optimization
**Production-ability.** Train/dev/test splits, regularization (L2, dropout), optimization (mini-batch, momentum, Adam), batch normalization, hyperparameter tuning, TensorFlow intro.

- Week 1: Practical aspects of deep learning
- Week 2: Optimization algorithms
- Week 3: Hyperparameter tuning, regularization, batch norm

### Course 3 — Convolutional Neural Networks
**The vision track.** Convolution, pooling, ResNets, object detection (YOLO), face recognition (FaceNet), style transfer.

- Week 1: Foundations of CNNs
- Week 2: Deep convolutional models
- Week 3: Object detection
- Week 4: Special applications

### Course 4 — Sequence Models
**The NLP track.** RNN, LSTM/GRU, attention, speech recognition, audio & waveform.

- Week 1: Recurrent neural networks
- Week 2: NLP & word embeddings
- Week 3: Sequence-to-sequence models
- Week 4: Attention mechanism, speech recognition

### Course 5 — Structuring Machine Learning Projects
**The strategy track.** How to think about ML projects. End-to-end, multi-task, error analysis, transfer learning, multi-task learning, what is end-to-end learning, whether to use end-to-end.

- Week 1: ML strategy (1)
- Week 2: ML strategy (2)

---

## How to use these notes

Each course folder contains:
- `README.md` — the course overview, weekly breakdown, what you'll build
- `01-first-lesson.md` — the lead lesson with worked example (in our standard principal-engineer pattern)

**Suggested order:**
1. Course 1, 2, 3, 4, 5 — in sequence.
2. After Course 1, jump to the AI Engineering Course (13) and come back for 2-5 as needed.
3. Course 5 (Structuring Projects) is short — read it any time, but especially before starting a real project.

---

## Prerequisites

- Python (intermediate)
- Linear algebra basics (vectors, matrices, dot products)
- Calculus basics (derivatives, chain rule)
- Some high-school statistics

If you're shaky on linear algebra or calculus, do the "Matrix calculus for deep learning" warm-up at the top of Course 1 before moving on.