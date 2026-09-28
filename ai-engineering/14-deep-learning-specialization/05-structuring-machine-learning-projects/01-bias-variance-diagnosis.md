# Lesson 1 — Bias-Variance Diagnosis

> **Type:** Article + Worked Example · Course 5, Week 1
> The diagnostic loop that determines whether you need more data, a bigger model, or better regularization. With a worked case study on the cat classifier.

---

## The single most important ML decision

When your model's dev error is too high, you have four options:
1. Bigger model (more parameters, more layers)
2. More training data
3. Better regularization (L2, dropout, augmentation)
4. Better features / architecture

Most engineers guess. The best engineers **measure first**. The bias-variance diagnosis tells you which lever to pull.

---

## The setup

You need three error numbers:
- **Bayes error** — the irreducible error. Approximate with human error.
- **Training error** — how well the model fits the training set.
- **Dev error** — how well the model generalizes.

```
   THE TWO GAPS
   ────────────
   
   BIAS GAP       = training error − bayes error
                   How far the model is from optimal.
                   Big bias gap → model is too simple / undertrained.
   
   VARIANCE GAP   = dev error − training error
                   How much performance drops on unseen data.
                   Big variance gap → model is overfitting.
```

The bigger gap tells you the dominant problem. Fix that one first.

---

## Worked Example — diagnose and fix the cat classifier

> **Goal:** Take a 3-layer NN trained on 1000 cat images. It hits 85% on dev. Diagnose whether it's a bias or variance problem. Apply the right fix.

### Step 1 — Establish the baseline

```python
# Three numbers you need:
human_error = 0.01    # 1% — humans are very good at cat recognition
train_error = 0.10    # 10% — model gets 10% of training images wrong
dev_error   = 0.15    # 15% — model gets 15% of dev images wrong

bias_gap     = train_error - human_error   # 0.09
variance_gap = dev_error   - train_error   # 0.05

print(f"Bias gap:     {bias_gap:.1%}")
print(f"Variance gap: {variance_gap:.1%}")
# Bias gap (9pp) > Variance gap (5pp)
# → Bias problem dominates.
# → Bigger model, train longer.
```

### Step 2 — Apply the right fix (bigger model)

```python
# Train a 5-layer NN with more hidden units
model_v2 = CNN5Layer(input_shape=(64, 64, 3), n_classes=2)
train_error_v2 = 0.03   # down from 0.10 — model fits training set better
dev_error_v2   = 0.12   # down from 0.15 — also improved

bias_gap_v2     = train_error_v2 - human_error   # 0.02
variance_gap_v2 = dev_error_v2   - train_error_v2 # 0.09

print(f"After bigger model:")
print(f"  Bias gap:     {bias_gap_v2:.1%}")
print(f"  Variance gap: {variance_gap_v2:.1%}")
# Bias gap dropped from 9pp → 2pp.
# Variance gap INCREASED from 5pp → 9pp.
# → Bias fixed. Variance now dominates.
# → Need more data or regularization.
```

This is the key insight: **fixing one problem often reveals another.** The model's capacity went up, so it can fit better, but now it overfits.

### Step 3 — Apply the next fix (more data + dropout)

```python
# Add 10K more labeled images + dropout 0.5
train_error_v3 = 0.04   # up from 0.03 — dropout slightly hurts training fit
dev_error_v3   = 0.06   # down from 0.12 — regularization helps a lot

bias_gap_v3     = train_error_v3 - human_error   # 0.03
variance_gap_v3 = dev_error_v3   - train_error_v3 # 0.02

print(f"After more data + dropout:")
print(f"  Bias gap:     {bias_gap_v3:.1%}")
print(f"  Variance gap: {variance_gap_v3:.1%}")
# Both gaps small. → Ship it.
```

### Step 4 — The decision log

```
   ITERATION        TRAIN ERR    DEV ERR    BIAS    VARIANCE   ACTION
   ─────────        ─────────    ───────    ────    ─────────  ──────
   Baseline (v1)    10%          15%        9pp     5pp        Bigger model
   After v2          3%          12%        2pp     9pp        More data + dropout
   After v3          4%           6%        3pp     2pp        Ship
   
   Iteration time: 30 minutes total
   Result: 85% → 94% dev accuracy
```

The key: **don't apply regularization when you have a bias problem** (it makes training error worse, which is already bad). **Don't apply a bigger model when you have a variance problem** (it makes overfitting worse).

---

## The diagnosis flowchart

```
   STEP 1: Compare train error to Bayes (human) error.
   │
   ├── Large gap → BIAS PROBLEM
   │   │
   │   ├── Bigger network
   │   ├── Train longer
   │   ├── Better architecture
   │   └── Re-check after each change
   │
   STEP 2: Compare dev error to train error.
   │
   └── Large gap → VARIANCE PROBLEM
       │
       ├── More data
       ├── Regularization (L2, dropout)
       ├── Data augmentation
       ├── Early stopping
       └── Ensemble (rarely needed)
   
   STEP 3: Compare dev error to test error.
   │
   └── Large gap → DATA MISMATCH
       │
       ├── Analyze where they diverge
       ├── Make dev distribution more like test
       └── Don't regularize to match (it'll hurt training)
   
   STEP 4: If everything's small, ship.
```

---

## Worked Example — data mismatch (when train and dev come from different distributions)

This is the subtle case that bites everyone.

```
   SCENARIO
   ────────
   Your app takes user-uploaded, low-quality phone photos of cats.
   You trained on professionally-shot, high-quality cat photos.
   
   Train: 4% (low — your training data is easy)
   Dev:   10% (high — your dev data is hard because it's phone photos)
   
   What's the bias gap?
   What about variance?
   Is it the data, the model, or both?
```

The diagnosis:

```python
# Split the dev set into "train-like" and "dev-like"
# Train-like = professionally-shot photos
# Dev-like   = phone-uploaded photos

train_error = 0.04
train_like_dev_error = 0.05   # phone-uploaded photos... wait this is also train-like?
# Actually: train on pro photos, evaluate separately on pro photos vs phone photos

# CORRECTION:
# Train on 200K pro + 5K phone
# Dev on 5K phone (held out)
# "Train-dev" on 200K pro (held out from training)

human_error          = 0.01
train_error          = 0.04
train_dev_error      = 0.05   # pro photos, held out from training
dev_error            = 0.10   # phone photos

bias_gap        = train_error - human_error      # 3pp
variance_gap    = train_dev_error - train_error  # 1pp
mismatch_gap    = dev_error - train_dev_error    # 5pp  ← NEW!

print(f"Bias: {bias_gap:.0%}, Variance: {variance_gap:.0%}, Mismatch: {mismatch_gap:.0%}")
# Mismatch dominates → your training data is too easy / not representative.
# Fix: collect more phone-photo data. Synthetic phone-style augmentation.
```

**The lesson:** when train and dev come from different distributions, you need a separate "train-dev" set carved from training to disentangle variance from distribution mismatch.

---

## Error analysis — the 1-hour exercise that saves weeks

```python
# Take 100 dev examples the model gets wrong
failures = sample_dev_failures(100)

# Bucket them
categories = {
    "blurry_image":          0,
    "unusual_angle":         0,
    "occlusion (object)":    0,
    "lighting_extreme":      0,
    "wrong_label":           0,
    "other":                 0,
}

for img_path, true_label, pred_label in failures:
    img = load(img_path)
    if is_blurry(img):         categories["blurry_image"]      += 1
    if is_unusual_angle(img):  categories["unusual_angle"]    += 1
    if has_occlusion(img):     categories["occlusion"]        += 1
    # ... etc

print("Top failure modes:")
for cat, n in sorted(categories.items(), key=lambda x: -x[1])[:3]:
    print(f"  {cat}: {n}")
# occlusion (object): 45   ← biggest fix opportunity
# blurry_image:       32
# unusual_angle:      18
```

Now you know: improve robustness to occlusion and blur. Not the architecture. Not more data. Specific, high-leverage fixes.

---

## Cost roll-up

```
   Time spent on diagnosis:
   - Compute 3 error numbers:     10 minutes
   - Run one error analysis:      1 hour
   - Apply 1-2 fixes:             1 day
   
   Time SAVED by avoiding wrong fixes:
   - Wrong direction for a week: ~40 hours saved
   - Wrong architecture:         ~80 hours saved
   - Wrong data collection:      ~160 hours saved
   
   ROI: 5-10× the time invested
```

---

## What this example teaches

1. **Measure before fixing.** Three numbers tell you what to do.
2. **The dominant gap is the priority.** Don't regularize when bias is the problem.
3. **Fixes cascade.** A bigger model can shift variance gap from small to large.
4. **Data mismatch is a third category.** Train-dev set disentangles it from variance.
5. **Error analysis beats intuition.** 100 misclassified examples > 1 hour of guessing.

This is the single most useful skill in applied ML. Most failures are diagnostic failures, not algorithmic failures.

---

## The complete diagnostic playbook

```
   QUESTION                                          ACTION
   ────────                                          ──────
   My train error is high.                           Bigger model, train longer
   My train error is OK, dev error is high.          More data, regularization
   My dev error is OK, test error is high.           Bigger dev set (or you're overfitting to dev)
   My train is easy, dev is hard (different dist).   Make dev match reality; more real-world data
   My model fails on certain examples.               Error analysis → specific fix
   I have lots of data, complex pipeline.            Try end-to-end
   I have little data.                               Transfer learning from pretrained
   My model performs worse than humans.              Manually inspect errors → fix data
```

---

## What Comes Next

> Lesson 2 — **End-to-End vs Modular** — when to train one big model end-to-end and when to break the pipeline into stages. The decision framework with worked examples from speech recognition and translation.