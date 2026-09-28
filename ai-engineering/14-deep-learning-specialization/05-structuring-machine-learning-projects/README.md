# Course 5 — Structuring Machine Learning Projects

> **Instructor:** Andrew Ng · **Level:** Intermediate-to-advanced · **Time:** 2 weeks (shortest course)

The strategy course. No code. No math. Just decisions. This is the course most engineers skip and then regret.

---

## Why this course exists

Most ML failures aren't algorithmic. They're **strategic**. The team has a 90% accurate model, but it's been trained on the wrong task. They spend a month collecting more data when they should have fixed the labels. They deploy a model that's overfitting on a metric that doesn't matter to the business.

```
   WHERE ML PROJECTS FAIL                      WHERE THEY SUCCEED
   ──────────────────────                      ────────────────────
   Wrong objective metric                      Right metric chosen upfront
   Misdiagnosed error (bias vs variance)       Diagnosis before treatment
   No error analysis (manual review of failures) Regular error analysis
   End-to-end over-optimization                End-to-end vs modular decision
   No transfer learning                        Pretrained → fine-tune
   No human-level comparison                   "How does the model compare to humans?"
```

---

## Week 1 — ML strategy (1)

**Topics:**
- Why human-level performance?
- Avoidable bias
- Understanding what human-level performance means
- Surpassing human-level performance
- Improving your model performance

**The big idea:** When a model is worse than humans, you can use the human error rate as a proxy for "irreducible error." The gap between training error and human error is avoidable bias. The gap between dev error and training error is variance. Optimize the bigger gap first.

```
   SCENARIO                         YOUR MOVE
   ────────                         ────────
   Train: 8%  Human: 1%  Dev: 10%   Bias problem (8-1=7). Bigger model, train longer.
   Train: 1%  Human: 1%  Dev: 10%   Variance problem (10-1=9). More data, regularize.
   Train: 1%  Human: 1%  Dev: 1.5% Variance small (0.5%). Maybe more data, maybe ship.
```

---

## Week 2 — ML strategy (2)

**Topics:**
- Carrying out error analysis
- Cleaning up incorrectly labeled data
- Build your first system quickly, then iterate
- Training and testing on different distributions
- Bias and variance with mismatched data distributions
- Addressing data mismatch
- Transfer learning
- Multi-task learning
- What is end-to-end deep learning?
- Whether to use end-to-end learning

**The big idea:** Error analysis beats intuition. Look at 100 misclassified examples; you'll find a pattern. Multi-task and transfer learning are the cheat codes for limited data. End-to-end is great when you have lots of data and the steps are opaque; modular is better when you have less data or you need to debug.

---

## The decision frameworks

### Framework 1: Bias vs variance diagnosis

```
   STEP 1. Compute Bayes error (≈ human error) on a representative sample.
   STEP 2. Compute train error.
   STEP 3. Compute dev error.
   
   Bias gap = train - bayes       (model can't fit training set well)
   Variance gap = dev - train     (model overfits training set)
   
   If bias gap dominates → bigger network, train longer, better architecture.
   If variance gap dominates → more data, regularization, dropout.
   If both small → ship it.
```

### Framework 2: Error analysis

```
   1. Take 100 dev examples the model gets wrong.
   2. Tally the failure modes (manually).
   3. The dominant failure mode is your highest-leverage fix.
   
   E.g., 60 of 100 failures are dogs misclassified as cats.
   → Improving dog-vs-cat is worth more than the other 40 combined.
```

### Framework 3: When to use end-to-end

```
   USE END-TO-END                       USE MODULAR (PIPELINE)
   ────────────────                     ──────────────────────
   Large dataset (10K+ labeled)         Small dataset
   Simple input → output mapping        Complex, multi-step
   Domain is well-understood            Hard to collect end-to-end labels
   Opacity is acceptable                Need to debug individual steps
   Examples:                            Examples:
   - Image → label                      - Speech → phonemes → text
   - Sentence → sentiment               - Translation: parse → encode → generate
   - Audio → transcript (Whisper)       - ML pipeline with monitoring needs
```

### Framework 4: Transfer learning

```
   PRETRAIN                               FINE-TUNE
   ────────                               ─────────
   Big model trained on huge data         Same model, retrained on your small data
   
   When to do it:
   - You have a small dataset for your task
   - A pretrained model exists in a related domain
   - You can afford the fine-tuning compute
   
   Two flavors:
   - Feature extraction: freeze pretrained, train a new head on top
   - Fine-tuning: unfreeze and update with small learning rate
```

---

## Lead lesson

See `01-bias-variance-diagnosis.md` for the worked example: take a 3-layer NN on the cat-classifier, manually diagnose bias vs variance using the train vs dev gap, and apply the right fix (bigger model vs more data vs regularization). This is the decision loop every ML practitioner runs.