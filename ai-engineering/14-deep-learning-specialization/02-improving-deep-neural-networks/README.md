# Course 2 — Improving Deep Neural Networks: Hyperparameter Tuning, Regularization and Optimization

> **Instructor:** Andrew Ng · **Level:** Intermediate · **Time:** 3 weeks

The gap between "the network learns" and "the network works well in production." This course is where most beginners spend months getting stuck without realizing there's a system.

---

## What you'll learn

```
   COURSE 1 ASKED                  COURSE 2 ANSWERS
   ────────────────                 ────────────────
   "Can I train a NN?"              "Yes — and here's how to train
                                     it WELL."
   
   "My loss goes down               "That's overfitting. Here's
    but test acc is bad"             regularization, dropout,
                                     early stopping."
   
   "GD is slow."                    "Here's Adam, learning-rate
                                     scheduling, mini-batching."
   
   "I have 100 hyperparameters."    "Here's a systematic way to
                                     tune them."
```

---

## Week 1 — Practical aspects of deep learning

**Topics:**
- Train / dev / test splits
- Bias vs variance diagnosis
- Recipe for machine learning (the "loop" of improvement)
- Regularization (L2, dropout)
- Input normalization
- Vanishing / exploding gradients (and Xavier initialization)
- Numerical approximation of gradients (gradient checking)

**The big idea:** Diagnose first, then fix. Look at train vs dev error. Train error high → high bias (bigger network, train longer). Dev error high → high variance (more data, regularization). Most leaks appear 80% here.

---

## Week 2 — Optimization algorithms

**Topics:**
- Mini-batch gradient descent
- Exponentially-weighted training
- Bias correction in EW
- Gradient descent with momentum
- RMSprop
- Adam optimizer
- Learning rate decay
- The local-optima myth

**The big idea:** Vanilla GD is too slow. Mini-batch + momentum + adaptive learning rates (Adam) makes training 10-100× faster. Almost everyone uses Adam these days.

---

## Week 3 — Hyperparameter tuning, regularization, batch norm

**Topics:**
- Tuning process (which to tune in which order)
- Using appropriate scales for hyperparameters
- Pandas vs caviar hyperparameter search
- Normalizing activations (Batch Norm)
- Batch norm at test time
- Softmax regression (multi-class)
- TensorFlow intro (the framework)

**The big idea:** Hyperparameter tuning is mostly empirical. BatchNorm makes training faster and more stable. TensorFlow / PyTorch lets you build all of this without writing the backprop.

---

## Lead lesson

See `01-regularization-and-dropout.md` for the full worked example: take a 3-layer network on the "French football jerseys" / "cats" dataset, see it overfit, then apply L2 regularization and dropout to fix it. Measure train and dev accuracy before/after.