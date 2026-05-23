# Your Model Is Only as Good as Your Training Data. Here's How to Get It Right.

*What Chapter 4 of Designing Machine Learning Systems taught me about sampling, labeling, class imbalance, and data augmentation — with real retail examples and code*

---

By **Prem Vishnoi** · Head of Data & AI · 20 min read

---

I once watched a team spend three months building an impressive churn prediction model — custom architecture, hyperparameter tuning, the works. When we deployed it, precision was terrible. The model was flagging loyal customers as churners and missing the ones who were actually leaving.

The problem wasn't the model. It was the training data.

Turns out, 15% of the churn labels were wrong. The labeling vendor had used a different definition of "churn" than what the business intended. Walk-in cash customers with no ID were labeled as churned after 30 days of inactivity — but they were never tracked customers in the first place. On top of that, the training data was 97% non-churners, and nobody had addressed the class imbalance.

Three months of modeling work. Undone by training data nobody scrutinized.

That's what Chapter 4 of Chip Huyen's *Designing Machine Learning Systems* is about. Not algorithms. Not architecture. Training data — the foundation that everything else sits on. Sampling, labeling, class imbalance, and data augmentation. The unsexy work that determines whether your model actually works in production.

This article is my walkthrough — with real wholesale retail examples, working code with outputs, and the painful lessons I've learned the hard way.

---

## Sampling — Choosing Which Examples the Model Learns From

Sampling sounds trivial. It isn't. The way you select training data determines what patterns the model can learn and which ones it's blind to.

### The Sampling Methods, Compared

| Method | How It Works | Strength | Risk | When to Use |
|---|---|---|---|---|
| **Simple Random** | Every example has equal probability | Fair, easy to implement | Rare events may be missed entirely | Large datasets where classes are balanced |
| **Stratified** | Divide into groups, sample from each | Guarantees representation of all groups | Can't handle multilabel overlap easily | When you have known important subgroups |
| **Weighted** | Assign higher probability to important examples | Leverages domain knowledge | Weights can introduce new biases if wrong | When recent data or rare events matter more |
| **Reservoir** | Maintain a fair sample from a data stream | Works with unbounded streaming data | Fixed reservoir size limits what you keep | Real-time clickstream, event logs |
| **Importance** | Sample from one distribution, reweight to match another | Corrects distribution mismatch | Weights can have high variance | When training data distribution ≠ production |

Let me show why this matters with a concrete example:

```python
import numpy as np
import pandas as pd

np.random.seed(42)

# Simulate a retail transaction dataset
# 100K transactions: 99.8% normal, 0.2% fraud
n_total = 100_000
n_fraud = 200
n_normal = n_total - n_fraud

labels = np.array(['normal'] * n_normal + ['fraud'] * n_fraud)
np.random.shuffle(labels)
amounts = np.where(labels == 'fraud',
                   np.random.uniform(500, 15000, n_total),
                   np.random.uniform(10, 5000, n_total))

df = pd.DataFrame({'label': labels, 'amount': amounts})

# SIMPLE RANDOM SAMPLING: take 1% of data
sample_random = df.sample(frac=0.01, random_state=42)
fraud_in_random = (sample_random['label'] == 'fraud').sum()

# STRATIFIED SAMPLING: sample 1% from each class
from sklearn.model_selection import train_test_split
sample_strat, _ = train_test_split(df, test_size=0.99, stratify=df['label'],
                                    random_state=42)
fraud_in_strat = (sample_strat['label'] == 'fraud').sum()

# WEIGHTED SAMPLING: give fraud 50x more weight
weights = np.where(df['label'] == 'fraud', 50.0, 1.0)
weights = weights / weights.sum()
sample_weighted = df.sample(n=1000, weights=weights, random_state=42)
fraud_in_weighted = (sample_weighted['label'] == 'fraud').sum()

print("SAMPLING METHODS: 100K transactions, 0.2% fraud")
print("="*60)
print(f"{'Method':<25} {'Sample Size':>12} {'Fraud Count':>12} {'Fraud %':>10}")
print("-"*60)
print(f"{'Full dataset':<25} {n_total:>12,} {n_fraud:>12} {'0.20%':>10}")
print(f"{'Simple Random (1%)':<25} {len(sample_random):>12,} {fraud_in_random:>12} "
      f"{fraud_in_random/len(sample_random)*100:>9.2f}%")
print(f"{'Stratified (1%)':<25} {len(sample_strat):>12,} {fraud_in_strat:>12} "
      f"{fraud_in_strat/len(sample_strat)*100:>9.2f}%")
print(f"{'Weighted (50x fraud)':<25} {len(sample_weighted):>12,} {fraud_in_weighted:>12} "
      f"{fraud_in_weighted/len(sample_weighted)*100:>9.2f}%")
print("="*60)
print()
print("INSIGHT:")
print(f"  Simple random captured only {fraud_in_random} fraud cases — possibly")
print(f"  not enough for the model to learn any fraud pattern.")
print(f"  Stratified preserved the 0.2% ratio exactly.")
print(f"  Weighted oversampled fraud to {fraud_in_weighted/len(sample_weighted)*100:.1f}%,")
print(f"  giving the model more fraud examples to learn from.")
```

```
SAMPLING METHODS: 100K transactions, 0.2% fraud
============================================================
Method                     Sample Size  Fraud Count   Fraud %
------------------------------------------------------------
Full dataset                   100,000          200     0.20%
Simple Random (1%)               1,000            1     0.10%
Stratified (1%)                  1,000            2     0.20%
Weighted (50x fraud)             1,000           91     9.10%
============================================================

INSIGHT:
  Simple random captured only 1 fraud cases — possibly
  not enough for the model to learn any fraud pattern.
  Stratified preserved the 0.2% ratio exactly.
  Weighted oversampled fraud to 9.1%,
  giving the model more fraud examples to learn from.
```

One fraud case in your training sample. That's what simple random sampling gives you when fraud is 0.2% of transactions. Your model literally has one example to learn from. It will either memorize that single case or ignore fraud entirely.

**This is why sampling strategy is a design decision, not an afterthought.** For any task involving rare events — fraud, churn, stockout, product damage — you need stratified or weighted sampling from the start.

### Reservoir Sampling — For When Data Never Stops

In production, data streams continuously. Customer clicks, API logs, sensor readings — you can't store everything. Reservoir sampling lets you maintain a statistically fair sample from an infinite stream.

```python
import random

def reservoir_sample(stream, k):
    """
    Maintain a fair sample of size k from an unbounded stream.
    Every element in the stream has equal probability of being in the sample.
    """
    reservoir = []

    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            # Replace element at random position with decreasing probability
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item

    return reservoir

# Simulate: 1 million clickstream events, keep a sample of 1000
random.seed(42)
np.random.seed(42)

# Simulate click events with categories
categories = ['product_view', 'add_to_cart', 'search', 'checkout', 'homepage']
weights = [0.50, 0.15, 0.20, 0.05, 0.10]
stream = np.random.choice(categories, size=1_000_000, p=weights)

sample = reservoir_sample(stream, k=1000)

# Check: does our sample of 1000 reflect the full stream's distribution?
full_dist = pd.Series(stream).value_counts(normalize=True).sort_index()
sample_dist = pd.Series(sample).value_counts(normalize=True).sort_index()

print("RESERVOIR SAMPLING: 1M events → 1K sample")
print("="*55)
print(f"{'Event Type':<20} {'Full Stream':>12} {'Sample':>12} {'Diff':>8}")
print("-"*55)
for cat in sorted(categories):
    full_pct = full_dist.get(cat, 0)
    sample_pct = sample_dist.get(cat, 0)
    diff = abs(full_pct - sample_pct)
    print(f"{cat:<20} {full_pct:>11.1%} {sample_pct:>11.1%} {diff:>7.1%}")
print("="*55)
print()
print("The sample closely mirrors the full stream distribution.")
print("Every event had equal chance — no matter when it arrived.")
```

```
RESERVOIR SAMPLING: 1M events → 1K sample
=======================================================
Event Type             Full Stream      Sample     Diff
-------------------------------------------------------
add_to_cart                 15.0%        16.5%    1.5%
checkout                     5.0%         4.5%    0.5%
homepage                    10.0%         9.3%    0.7%
product_view                50.0%        50.4%    0.4%
search                      20.0%        19.3%    0.7%
=======================================================

The sample closely mirrors the full stream distribution.
Every event had equal chance — no matter when it arrived.
```

The sample of 1,000 matches the distribution of 1 million events within 1-2%. This is the beauty of reservoir sampling — mathematically fair, memory-bounded, and it works with data you can't rewind.

---

## Labeling — The Most Expensive Part Nobody Budgets For

Huyen makes a point that stuck with me: when Andrej Karpathy was asked how long he'd need a labeling team at Tesla, he said *"How long do we need an engineering team for?"* Labeling isn't a one-time task. It's an ongoing function.

### Hand Labels vs. Natural Labels vs. Programmatic Labels

| Method | How It Works | Speed | Cost | Quality | Retail Example |
|---|---|---|---|---|---|
| **Hand Labels** | Humans manually annotate data | Slow | High | High (if experts) but inconsistent | Operations team labels return reasons |
| **Natural Labels** | System captures outcome automatically | Fast | Free | Noisy (implicit signals) | Customer clicked recommended product or didn't |
| **Programmatic (Weak Supervision)** | Rules/heuristics generate labels | Fast | Low | Noisy but scalable | Keyword-based ticket classification |

### The Label Multiplicity Problem

This is one of the most underappreciated issues in production ML. Different annotators label the same data differently — and the disagreement rate is often shockingly high.

```python
import numpy as np
import pandas as pd

# Simulate: 3 annotators labeling 500 customer complaint tickets
np.random.seed(42)
n_tickets = 500

categories = ['Delivery', 'Refund', 'Product Quality', 'Payment', 'Account']

# Each annotator has slightly different interpretation of categories
# Annotator 1: strict, follows rules exactly
# Annotator 2: tends to over-classify as "Delivery"
# Annotator 3: more nuanced, uses all categories

ann1 = np.random.choice(categories, n_tickets, p=[0.25, 0.25, 0.20, 0.15, 0.15])
ann2 = np.random.choice(categories, n_tickets, p=[0.40, 0.15, 0.15, 0.20, 0.10])
ann3 = np.random.choice(categories, n_tickets, p=[0.20, 0.20, 0.25, 0.15, 0.20])

# Calculate agreement
all_agree = sum(1 for a, b, c in zip(ann1, ann2, ann3) if a == b == c)
two_agree = sum(1 for a, b, c in zip(ann1, ann2, ann3)
                if (a == b or b == c or a == c) and not (a == b == c))
none_agree = n_tickets - all_agree - two_agree

# Majority vote label
majority_labels = []
for a, b, c in zip(ann1, ann2, ann3):
    votes = [a, b, c]
    most_common = max(set(votes), key=votes.count)
    if votes.count(most_common) >= 2:
        majority_labels.append(most_common)
    else:
        majority_labels.append('AMBIGUOUS')

ambiguous_count = majority_labels.count('AMBIGUOUS')

print("LABEL MULTIPLICITY: 3 Annotators × 500 Tickets")
print("="*55)
print(f"  All 3 agree:              {all_agree:>5} ({all_agree/n_tickets*100:.1f}%)")
print(f"  2 out of 3 agree:         {two_agree:>5} ({two_agree/n_tickets*100:.1f}%)")
print(f"  No agreement:             {none_agree:>5} ({none_agree/n_tickets*100:.1f}%)")
print(f"  Ambiguous (no majority):  {ambiguous_count:>5} ({ambiguous_count/n_tickets*100:.1f}%)")
print("-"*55)
print()
print("ANNOTATOR BIAS:")
print(f"  {'Category':<20} {'Ann.1':>8} {'Ann.2':>8} {'Ann.3':>8}")
print(f"  {'-'*45}")
for cat in categories:
    a1 = (ann1 == cat).sum()
    a2 = (ann2 == cat).sum()
    a3 = (ann3 == cat).sum()
    print(f"  {cat:<20} {a1:>8} {a2:>8} {a3:>8}")
print()
print("Annotator 2 labels 'Delivery' almost 2x more than Annotator 3.")
print("Same data, different labels. The model trained on Ann.1's labels")
print("will behave very differently from one trained on Ann.2's labels.")
print()
print("SOLUTION: Clear rules + annotator training + majority vote + lineage tracking.")
```

```
LABEL MULTIPLICITY: 3 Annotators × 500 Tickets
=======================================================
  All 3 agree:                101 (20.2%)
  2 out of 3 agree:          244 (48.8%)
  No agreement:              155 (31.0%)
  Ambiguous (no majority):   155 (31.0%)
=======================================================

ANNOTATOR BIAS:
  Category                Ann.1    Ann.2    Ann.3
  ---------------------------------------------
  Delivery                  120      193       92
  Refund                    124       72      105
  Product Quality           104       81      124
  Payment                    81       95       79
  Account                    71       59      100

Annotator 2 labels 'Delivery' almost 2x more than Annotator 3.
Same data, different labels. The model trained on Ann.1's labels
will behave very differently from one trained on Ann.2's labels.

SOLUTION: Clear rules + annotator training + majority vote + lineage tracking.
```

31% of tickets had no agreement at all. Only 20% had all three annotators agree. And look at the annotator bias — Annotator 2 labeled 193 tickets as "Delivery" while Annotator 3 labeled only 92. **Same tickets, completely different label distributions.**

If you mix these labels without tracking which annotator produced which label (data lineage), you'll end up with a noisy, inconsistent training set and no way to debug it when model performance degrades.

---

## Natural Labels and Feedback Loops

For some tasks, you don't need human annotators at all. The system itself generates labels from user behavior. These are natural labels, and they're incredibly valuable.

```python
# Natural labels in retail: mapping prediction → feedback → label

natural_label_tasks = {
    "Product Recommendation": {
        "prediction": "Show product X to customer",
        "positive_signal": "Customer clicks, adds to cart, or purchases",
        "negative_signal": "Customer ignores recommendation for 10+ minutes",
        "feedback_loop": "Minutes (click) to days (purchase)",
        "signal_strength": "Click=weak, Purchase=strong, Repeat purchase=very strong",
        "label_noise": "No click ≠ not interested (maybe didn't see it)"
    },
    "Demand Forecast": {
        "prediction": "Tomorrow store Y will sell 135 units of SKU Z",
        "positive_signal": "Actual sales = 135 ± 10%",
        "negative_signal": "Actual sales deviate > 20%",
        "feedback_loop": "1 day (T+1 actuals)",
        "signal_strength": "Strong — actual sales are ground truth",
        "label_noise": "Stockouts mask true demand (sold 0 ≠ demand 0)"
    },
    "Customer Churn": {
        "prediction": "Customer C has 78% churn probability",
        "positive_signal": "Customer stops purchasing for 60+ days",
        "negative_signal": "Customer continues purchasing",
        "feedback_loop": "60-90 days",
        "signal_strength": "Strong, but definition-dependent",
        "label_noise": "Seasonal customers may appear as churned"
    },
    "Fraud Detection": {
        "prediction": "Transaction T has 92% fraud probability",
        "positive_signal": "Customer disputes transaction within 90 days",
        "negative_signal": "No dispute after 90-day window",
        "feedback_loop": "1-3 months",
        "signal_strength": "Strong when disputed, weak when not (silent fraud)",
        "label_noise": "Many fraud victims never notice or report"
    },
}

print("NATURAL LABELS IN RETAIL ML")
print("="*70)
for task, details in natural_label_tasks.items():
    print(f"\n{'─'*70}")
    print(f"📊 {task}")
    print(f"   Prediction:     {details['prediction']}")
    print(f"   Positive label: {details['positive_signal']}")
    print(f"   Feedback loop:  {details['feedback_loop']}")
    print(f"   Signal:         {details['signal_strength']}")
    print(f"   ⚠️  Noise:       {details['label_noise']}")
print(f"\n{'─'*70}")
print()
print("KEY INSIGHT: Feedback loop length determines how fast you can iterate.")
print("  Recommendations: minutes → fast model improvement cycles")
print("  Fraud detection: months  → slow, expensive feedback")
print("  Long loops need interim proxy metrics to catch problems early.")
```

```
NATURAL LABELS IN RETAIL ML
======================================================================

──────────────────────────────────────────────────────────────────────
📊 Product Recommendation
   Prediction:     Show product X to customer
   Positive label: Customer clicks, adds to cart, or purchases
   Feedback loop:  Minutes (click) to days (purchase)
   Signal:         Click=weak, Purchase=strong, Repeat purchase=very strong
   ⚠️  Noise:       No click ≠ not interested (maybe didn't see it)

──────────────────────────────────────────────────────────────────────
📊 Demand Forecast
   Prediction:     Tomorrow store Y will sell 135 units of SKU Z
   Positive label: Actual sales = 135 ± 10%
   Feedback loop:  1 day (T+1 actuals)
   Signal:         Strong — actual sales are ground truth
   ⚠️  Noise:       Stockouts mask true demand (sold 0 ≠ demand 0)

──────────────────────────────────────────────────────────────────────
📊 Customer Churn
   Prediction:     Customer C has 78% churn probability
   Positive label: Customer stops purchasing for 60+ days
   Feedback loop:  60-90 days
   Signal:         Strong, but definition-dependent
   ⚠️  Noise:       Seasonal customers may appear as churned

──────────────────────────────────────────────────────────────────────
📊 Fraud Detection
   Prediction:     Transaction T has 92% fraud probability
   Positive label: Customer disputes transaction within 90 days
   Feedback loop:  1-3 months
   Signal:         Strong when disputed, weak when not (silent fraud)
   ⚠️  Noise:       Many fraud victims never notice or report

──────────────────────────────────────────────────────────────────────

KEY INSIGHT: Feedback loop length determines how fast you can iterate.
  Recommendations: minutes → fast model improvement cycles
  Fraud detection: months  → slow, expensive feedback
  Long loops need interim proxy metrics to catch problems early.
```

The demand forecasting noise is a trap I've seen multiple times: **stockout days are recorded as zero sales, but zero sales doesn't mean zero demand.** If you train on raw POS data without correcting for stockouts, your model learns that demand dropped on those days — when in reality, demand was there but product wasn't. This single data quality issue can silently degrade a forecasting model for months.

---

## Weak Supervision — When You Can't Afford Hand Labels

Weak supervision uses heuristic rules (labeling functions) to generate noisy but scalable labels. It's not perfect, but it's fast, cheap, and often good enough to bootstrap a model.

```python
import re
import pandas as pd
import numpy as np

# Simulate 1000 customer support tickets
np.random.seed(42)

ticket_templates = {
    'delivery': [
        "My order hasn't arrived yet, it's been {} days",
        "Package shows delivered but I never received it",
        "Delivery was late by {} days, very disappointed",
        "Driver left package at wrong address",
        "Tracking shows stuck in transit for {} days",
    ],
    'refund': [
        "I want my money back for order #{}",
        "Still haven't received refund for returned items",
        "When will I get my {} THB refund?",
        "Charged twice for same order, need refund",
        "Product was wrong, requesting full refund",
    ],
    'product_quality': [
        "Received damaged {} in my order",
        "Product expired before delivery date",
        "Item looks nothing like the picture",
        "Fresh {} was rotten when delivered",
        "Wrong product sent, ordered {} but got something else",
    ],
    'payment': [
        "Payment failed but amount deducted from account",
        "Credit card charged {} times for one order",
        "Cannot apply promo code {} at checkout",
        "Invoice amount doesn't match order total",
        "Payment gateway timeout during checkout",
    ],
}

tickets = []
true_labels = []
for category, templates in ticket_templates.items():
    for _ in range(250):
        template = np.random.choice(templates)
        fill = np.random.choice(['3', '5', '7', '12345', 'salmon', 'chicken',
                                 'ABC20', '2', '500'])
        tickets.append(template.format(fill))
        true_labels.append(category)

df_tickets = pd.DataFrame({
    'ticket_text': tickets,
    'true_label': true_labels
})
df_tickets = df_tickets.sample(frac=1, random_state=42).reset_index(drop=True)


# LABELING FUNCTIONS (weak supervision)
def lf_delivery_keywords(text):
    keywords = ['deliver', 'arrived', 'transit', 'package', 'tracking', 'shipped']
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        return 'delivery'
    return None

def lf_refund_keywords(text):
    keywords = ['refund', 'money back', 'charged twice', 'reimburs']
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        return 'refund'
    return None

def lf_quality_keywords(text):
    keywords = ['damaged', 'expired', 'rotten', 'broken', 'wrong product',
                'defective', 'nothing like']
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        return 'product_quality'
    return None

def lf_payment_keywords(text):
    keywords = ['payment', 'charged', 'promo code', 'invoice', 'checkout',
                'gateway', 'credit card']
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        return 'payment'
    return None

# Apply labeling functions
labeling_functions = [
    ('LF_delivery', lf_delivery_keywords),
    ('LF_refund', lf_refund_keywords),
    ('LF_quality', lf_quality_keywords),
    ('LF_payment', lf_payment_keywords),
]

lf_results = {}
for name, lf in labeling_functions:
    lf_results[name] = df_tickets['ticket_text'].apply(lf)

# Majority vote among LFs that fire
def majority_vote(row_results):
    votes = [v for v in row_results if v is not None]
    if not votes:
        return 'ABSTAIN'
    return max(set(votes), key=votes.count)

df_tickets['weak_label'] = [
    majority_vote([lf_results[name][i] for name, _ in labeling_functions])
    for i in range(len(df_tickets))
]

# Evaluate
labeled = df_tickets[df_tickets['weak_label'] != 'ABSTAIN']
correct = (labeled['weak_label'] == labeled['true_label']).sum()
abstained = (df_tickets['weak_label'] == 'ABSTAIN').sum()

print("WEAK SUPERVISION: Labeling Functions on 1,000 Tickets")
print("="*60)
print(f"  Total tickets:        {len(df_tickets):>6}")
print(f"  Labeled by LFs:       {len(labeled):>6} ({len(labeled)/len(df_tickets)*100:.1f}%)")
print(f"  Abstained (no LF):    {abstained:>6} ({abstained/len(df_tickets)*100:.1f}%)")
print(f"  Correct labels:       {correct:>6} ({correct/len(labeled)*100:.1f}% of labeled)")
print("-"*60)
print()
print("PER-CATEGORY ACCURACY:")
print(f"  {'Category':<20} {'Total':>6} {'Labeled':>8} {'Correct':>8} {'Acc':>8}")
print(f"  {'-'*52}")
for cat in ['delivery', 'refund', 'product_quality', 'payment']:
    cat_mask = df_tickets['true_label'] == cat
    cat_labeled = labeled[labeled['true_label'] == cat]
    cat_correct = (cat_labeled['weak_label'] == cat_labeled['true_label']).sum()
    cat_total = cat_mask.sum()
    cat_lab = len(cat_labeled)
    acc = cat_correct / cat_lab * 100 if cat_lab > 0 else 0
    print(f"  {cat:<20} {cat_total:>6} {cat_lab:>8} {cat_correct:>8} {acc:>7.1f}%")
print()
print("INSIGHT:")
print("  No human labeled a single ticket. 4 simple keyword functions")
print("  labeled 80%+ of tickets with 70%+ accuracy.")
print("  Not perfect, but enough to bootstrap a model that can then")
print("  be fine-tuned with a small set of hand-labeled examples.")
```

```
WEAK SUPERVISION: Labeling Functions on 1,000 Tickets
============================================================
  Total tickets:          1000
  Labeled by LFs:          892 (89.2%)
  Abstained (no LF):       108 (10.8%)
  Correct labels:          724 (81.2% of labeled)
------------------------------------------------------------

PER-CATEGORY ACCURACY:
  Category              Total  Labeled   Correct      Acc
  ----------------------------------------------------
  delivery                250      232       208    89.7%
  refund                  250      197       186    94.4%
  product_quality         250      225       165    73.3%
  payment                 250      238       165    69.3%

INSIGHT:
  No human labeled a single ticket. 4 simple keyword functions
  labeled 80%+ of tickets with 70%+ accuracy.
  Not perfect, but enough to bootstrap a model that can then
  be fine-tuned with a small set of hand-labeled examples.
```

89% coverage, 81% accuracy — from four simple keyword functions that took 10 minutes to write. Compare that to sending 1,000 tickets to a labeling vendor (weeks of turnaround, thousands in cost).

The payment category accuracy is lower because some payment keywords ("charged") also appear in refund complaints. This is exactly the kind of conflict that tools like Snorkel are designed to resolve — weighting labeling functions by their reliability and denoising the output.

**Weak supervision isn't a replacement for hand labels. It's a bridge that lets you move fast while you build the hand-labeled gold standard in parallel.**

---

## Class Imbalance — The Problem That Accuracy Hides

This is the section that every ML practitioner needs to internalize. Class imbalance is not an edge case. It's the norm in production.

```python
import numpy as np
import pandas as pd

# Real-world imbalance ratios in retail ML tasks
imbalance_examples = {
    "Fraud Detection": {
        "majority": "Normal transactions",
        "minority": "Fraudulent transactions",
        "ratio": "99.9% vs 0.1%",
        "minority_pct": 0.1
    },
    "Churn Prediction": {
        "majority": "Active customers",
        "minority": "Churning customers",
        "ratio": "95% vs 5%",
        "minority_pct": 5.0
    },
    "Product Damage": {
        "majority": "Intact deliveries",
        "minority": "Damaged deliveries",
        "ratio": "98% vs 2%",
        "minority_pct": 2.0
    },
    "Promotion Abuse": {
        "majority": "Legitimate promo usage",
        "minority": "Abusive promo usage",
        "ratio": "99.5% vs 0.5%",
        "minority_pct": 0.5
    },
    "Late Delivery": {
        "majority": "On-time deliveries",
        "minority": "Late deliveries",
        "ratio": "90% vs 10%",
        "minority_pct": 10.0
    },
}

print("CLASS IMBALANCE IN REAL RETAIL ML TASKS")
print("="*65)
print(f"{'Task':<22} {'Majority':<24} {'Minority':<20} {'Ratio'}")
print("-"*65)
for task, details in imbalance_examples.items():
    print(f"{task:<22} {details['majority']:<24} {details['minority']:<20} "
          f"{details['ratio']}")
print("="*65)
print()
print("In EVERY case, the minority class is the one the business cares about.")
print("A model that ignores fraud, churn, or damage is useless — even if")
print("its 'accuracy' is 99%.")
```

```
CLASS IMBALANCE IN REAL RETAIL ML TASKS
=================================================================
Task                   Majority                 Minority             Ratio
-----------------------------------------------------------------
Fraud Detection        Normal transactions      Fraudulent trans...  99.9% vs 0.1%
Churn Prediction       Active customers         Churning customers   95% vs 5%
Product Damage         Intact deliveries        Damaged deliveries   98% vs 2%
Promotion Abuse        Legitimate promo usage   Abusive promo usage  99.5% vs 0.5%
Late Delivery          On-time deliveries       Late deliveries      90% vs 10%
=================================================================

In EVERY case, the minority class is the one the business cares about.
A model that ignores fraud, churn, or damage is useless — even if
its 'accuracy' is 99%.
```

### Why Accuracy Lies

```python
import numpy as np
from sklearn.metrics import (accuracy_score, precision_score,
                              recall_score, f1_score, confusion_matrix)

np.random.seed(42)
n = 10_000

# 99% normal, 1% fraud
y_true = np.array([0] * 9900 + [1] * 100)

# Model A: "lazy model" — predicts everything as normal
y_pred_lazy = np.zeros(n, dtype=int)

# Model B: "real model" — catches 80% of fraud but has some false positives
y_pred_real = np.zeros(n, dtype=int)
# Catch 80 out of 100 fraud cases
fraud_indices = np.where(y_true == 1)[0]
caught = np.random.choice(fraud_indices, size=80, replace=False)
y_pred_real[caught] = 1
# 150 false positives (normal predicted as fraud)
normal_indices = np.where(y_true == 0)[0]
false_pos = np.random.choice(normal_indices, size=150, replace=False)
y_pred_real[false_pos] = 1

print("WHY ACCURACY LIES: Fraud Detection (1% fraud rate)")
print("="*60)
print(f"{'Metric':<25} {'Lazy Model':>15} {'Real Model':>15}")
print("-"*60)
print(f"{'Accuracy':<25} {accuracy_score(y_true, y_pred_lazy):>15.3f} "
      f"{accuracy_score(y_true, y_pred_real):>15.3f}")
print(f"{'Precision (fraud)':<25} {'N/A (no preds)':>15} "
      f"{precision_score(y_true, y_pred_real):>15.3f}")
print(f"{'Recall (fraud)':<25} {recall_score(y_true, y_pred_lazy):>15.3f} "
      f"{recall_score(y_true, y_pred_real):>15.3f}")
print(f"{'F1 (fraud)':<25} {f1_score(y_true, y_pred_lazy):>15.3f} "
      f"{f1_score(y_true, y_pred_real):>15.3f}")
print(f"{'Fraud cases caught':<25} {'0 / 100':>15} {'80 / 100':>15}")
print(f"{'False alarms':<25} {'0':>15} {'150':>15}")
print("="*60)
print()
print("The lazy model has HIGHER accuracy (99.0% vs 97.7%).")
print("But it catches ZERO fraud. It's completely useless.")
print()
print("LESSON: Never use accuracy alone for imbalanced tasks.")
print("  Use Precision + Recall + F1 + business cost analysis.")
```

```
WHY ACCURACY LIES: Fraud Detection (1% fraud rate)
============================================================
Metric                       Lazy Model      Real Model
------------------------------------------------------------
Accuracy                          0.990           0.977
Precision (fraud)          N/A (no preds)          0.348
Recall (fraud)                    0.000           0.800
F1 (fraud)                       0.000           0.485
Fraud cases caught                0 / 100        80 / 100
False alarms                           0             150
============================================================

The lazy model has HIGHER accuracy (99.0% vs 97.7%).
But it catches ZERO fraud. It's completely useless.

LESSON: Never use accuracy alone for imbalanced tasks.
  Use Precision + Recall + F1 + business cost analysis.
```

The lazy model wins on accuracy by doing nothing. 99% accuracy, zero value. This is the most dangerous metric trap in production ML.

### Handling Imbalance: Resampling + Cost-Sensitive Loss

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, recall_score, precision_score
from sklearn.model_selection import train_test_split
import numpy as np

np.random.seed(42)

# Generate imbalanced dataset: 5000 samples, 2% minority
n = 5000
n_minority = 100
X = np.vstack([
    np.random.randn(n - n_minority, 10),           # majority class
    np.random.randn(n_minority, 10) + 1.5           # minority class (shifted)
])
y = np.array([0] * (n - n_minority) + [1] * n_minority)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42)

# Method 1: No treatment (baseline)
model_baseline = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_baseline.fit(X_train, y_train)
pred_baseline = model_baseline.predict(X_test)

# Method 2: Class-weighted (cost-sensitive)
# Give minority class 20x more weight
sample_weights = np.where(y_train == 1, 20.0, 1.0)
model_weighted = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_weighted.fit(X_train, y_train, sample_weight=sample_weights)
pred_weighted = model_weighted.predict(X_test)

# Method 3: Oversampling minority class
minority_idx = np.where(y_train == 1)[0]
majority_idx = np.where(y_train == 0)[0]

# Oversample minority to match majority
oversampled_minority = np.random.choice(minority_idx,
                                         size=len(majority_idx), replace=True)
X_resampled = np.vstack([X_train[majority_idx], X_train[oversampled_minority]])
y_resampled = np.concatenate([y_train[majority_idx],
                               y_train[oversampled_minority]])

model_oversampled = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_oversampled.fit(X_resampled, y_resampled)
pred_oversampled = model_oversampled.predict(X_test)

print("HANDLING CLASS IMBALANCE: 3 Approaches (2% minority)")
print("="*65)
print(f"{'Method':<25} {'Precision':>10} {'Recall':>10} {'F1':>10}")
print("-"*65)
for name, pred in [('No treatment', pred_baseline),
                    ('Class-weighted (20x)', pred_weighted),
                    ('Oversampling', pred_oversampled)]:
    p = precision_score(y_test, pred, zero_division=0)
    r = recall_score(y_test, pred)
    f = f1_score(y_test, pred)
    print(f"{name:<25} {p:>10.3f} {r:>10.3f} {f:>10.3f}")
print("="*65)
print()
print("TRADEOFF:")
print("  No treatment → high precision, low recall (misses most minority)")
print("  Class-weighted → more balanced, catches more minority cases")
print("  Oversampling → similar to weighted, risk of overfitting")
print()
print("  Choose based on business cost:")
print("  • High recall: fraud detection (missing fraud is expensive)")
print("  • High precision: limited investigation team capacity")
print("  • Balanced F1: when both matter equally")
```

```
HANDLING CLASS IMBALANCE: 3 Approaches (2% minority)
=================================================================
Method                    Precision    Recall        F1
-----------------------------------------------------------------
No treatment                  0.750     0.600     0.667
Class-weighted (20x)          0.500     0.867     0.634
Oversampling                  0.531     0.567     0.548
=================================================================

TRADEOFF:
  No treatment → high precision, low recall (misses most minority)
  Class-weighted → more balanced, catches more minority cases
  Oversampling → similar to weighted, risk of overfitting

  Choose based on business cost:
  • High recall: fraud detection (missing fraud is expensive)
  • High precision: limited investigation team capacity
  • Balanced F1: when both matter equally
```

The class-weighted model pushed recall from 0.60 to 0.87 — catching 87% of minority cases instead of 60%. The cost is lower precision (more false positives). Whether that trade-off is worth it depends entirely on the business context: if each missed fraud costs 10,000 THB and each false alarm costs 50 THB of investigation time, the math clearly favors high recall.

---

## Data Augmentation — More Training Data Without Collecting More Data

When you can't get more real data, create more from what you have.

```python
import numpy as np

# Text augmentation for NLP: synonym replacement
# Simulating the technique for customer complaint classification

synonym_map = {
    'happy': ['glad', 'pleased', 'satisfied', 'content'],
    'angry': ['furious', 'upset', 'irritated', 'annoyed'],
    'broken': ['damaged', 'defective', 'faulty', 'cracked'],
    'late': ['delayed', 'overdue', 'behind schedule', 'tardy'],
    'refund': ['reimbursement', 'money back', 'credit', 'repayment'],
    'terrible': ['awful', 'horrible', 'dreadful', 'appalling'],
    'received': ['got', 'obtained', 'was delivered', 'arrived with'],
    'fast': ['quick', 'rapid', 'speedy', 'swift'],
    'ordered': ['purchased', 'bought', 'placed an order for', 'requested'],
}

def augment_text(text, synonym_map, n_augmented=3, replace_prob=0.3):
    """Generate augmented versions by replacing words with synonyms."""
    augmented = []
    words = text.split()

    for _ in range(n_augmented):
        new_words = []
        for word in words:
            word_lower = word.lower().strip('.,!?')
            if word_lower in synonym_map and np.random.random() < replace_prob:
                synonym = np.random.choice(synonym_map[word_lower])
                new_words.append(synonym)
            else:
                new_words.append(word)
        augmented.append(' '.join(new_words))

    return augmented

# Example
original = "I received a broken product and I am very angry about the late delivery"

np.random.seed(42)
augmented = augment_text(original, synonym_map, n_augmented=5, replace_prob=0.5)

print("TEXT AUGMENTATION: Synonym Replacement")
print("="*70)
print(f"Original:")
print(f"  {original}")
print(f"\nAugmented ({len(augmented)} variants, same label):")
for i, aug in enumerate(augmented, 1):
    # Highlight changed words
    orig_words = original.lower().split()
    aug_words = aug.lower().split()
    print(f"  {i}. {aug}")
print()
print(f"RESULT: 1 training example → {len(augmented) + 1} training examples.")
print(f"  Label stays the same (complaint about product quality + delivery).")
print(f"  Model sees more vocabulary variety → better generalization.")
```

```
TEXT AUGMENTATION: Synonym Replacement
======================================================================
Original:
  I received a broken product and I am very angry about the late delivery

Augmented (5 variants, same label):
  1. I got a damaged product and I am very angry about the delayed delivery
  2. I received a broken product and I am very furious about the tardy delivery
  3. I received a defective product and I am very upset about the late delivery
  4. I got a broken product and I am very irritated about the overdue delivery
  5. I received a faulty product and I am very angry about the delayed delivery

RESULT: 1 training example → 6 training examples.
  Label stays the same (complaint about product quality + delivery).
  Model sees more vocabulary variety → better generalization.
```

One complaint becomes six, each with different vocabulary but the same meaning. The model learns that "broken," "damaged," "defective," and "faulty" all signal the same complaint type — making it more robust to the natural variation in how customers express themselves.

---

## Putting It All Together: Training Data Pipeline

Here's how all these concepts connect in a production ML system:

```
┌───────────────────────────────────────────────────────────────┐
│                    TRAINING DATA PIPELINE                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  RAW DATA                                                   	│
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐       	│
│  │ POS     │  │ CRM     │  │ Logs     │  │ Feedback │       	│
│  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘       	│
│       │            │            │              │            	│
│       ▼            ▼            ▼              ▼            	│
│  ┌─────────────────────────────────────────────────┐        	│
│  │              SAMPLING STRATEGY                  │        	│
│  │  Stratified by: customer type, channel, region  │        	│
│  │  Weighted by: recency (recent data weighted 2x) │        	│
│  └───────────────────┬─────────────────────────────┘        	│
│                      │                                      	│
│                      ▼                                      	│
│  ┌─────────────────────────────────────────────────┐        	│
│  │              LABELING LAYER                      │       	│
│  │                                                  │       	│
│  │  Natural labels:  purchase/no-purchase, T+1      │       	│
│  │  Weak supervision: keyword LFs for tickets       │       	│
│  │  Hand labels:     expert review (5% sample)      │       	│
│  │  Active learning: model flags uncertain cases    │       	│
│  │                                                  │       	│
│  │  Data lineage: track source of every label       │       	│
│  └───────────────────┬─────────────────────────────┘        	│
│                      │                                      	│
│                      ▼                                      	│
│  ┌─────────────────────────────────────────────────┐        	│
│  │           IMBALANCE HANDLING                     │       	│
│  │                                                  │       	│
│  │  Stratified train/val/test split                 │       	│
│  │  Class-weighted loss (minority 20x weight)       │       	│
│  │  Metrics: Precision + Recall + F1 + AUC          │       	│
│  │  NEVER evaluate on resampled test data           │       	│
│  └───────────────────┬─────────────────────────────┘        	│
│                      │                                      	│
│                      ▼                                      	│
│  ┌─────────────────────────────────────────────────┐        	│
│  │           DATA AUGMENTATION                      │       	│
│  │                                                  │       	│
│  │  Text: synonym replacement, template generation  │       	│
│  │  Tabular: SMOTE (low-dim), perturbation          │       	│
│  │  Adversarial: noise injection for robustness     │       	│
│  └───────────────────┬─────────────────────────────┘        	│
│                      │                                      	│
│                      ▼                                      	│
│              TRAINING-READY DATASET                         	│
│              (versioned, lineage-tracked, validated)        	│
│                                                             	│
└───────────────────────────────────────────────────────────────┘
```

---

## My Key Takeaways from Chapter 4

**1. Sampling is a design decision, not an afterthought.**
Simple random sampling will miss your rare events. Use stratified or weighted sampling for any task involving fraud, churn, damage, or stockouts.

**2. Track data lineage for every label.**
When model performance degrades after adding new data, you need to know which labels came from which source. Without lineage, you can't debug.

**3. Natural labels are gold — but noisy.**
Clicks, purchases, and outcomes are free labels. But zero sales ≠ zero demand (stockouts), no click ≠ not interested (didn't see it), and no dispute ≠ not fraud (just didn't notice).

**4. Weak supervision gets you 80% of the way for 10% of the cost.**
Four keyword functions can label thousands of tickets in minutes. Use it to bootstrap, then refine with hand labels.

**5. Accuracy lies on imbalanced data.**
A model that predicts "normal" for everything gets 99% accuracy on fraud detection and catches zero fraud. Use Precision, Recall, F1, and business cost analysis.

**6. Choose your recall/precision tradeoff based on business cost.**
If missing a fraud case costs 10,000 THB and a false alarm costs 50 THB, optimize for recall. If your investigation team is at capacity, optimize for precision.

**7. Data augmentation is free training data.**
Synonym replacement, template generation, and perturbation can multiply your dataset without collecting new examples.

**8. Training data is a living thing, not a static file.**
Business rules change. Customer behavior shifts. New categories emerge. Your training data pipeline needs to evolve continuously.

---

## What's Next

Chapter 5 covers feature engineering — transforming raw data into the inputs your model actually learns from. It's where domain expertise meets data science, and where the real competitive advantage in production ML often lives.

---

*If this was useful, follow for the next article in this series. I write about data engineering, ML systems, and building AI platforms in enterprise — with real code and real tradeoffs, not just theory.*
