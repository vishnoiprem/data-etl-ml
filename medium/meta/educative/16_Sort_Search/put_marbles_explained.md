# Put Marbles in Bags - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/put-marbles-in-bags

## The Problem
```
You have k bags and a 0-indexed integer array weights. Divide marbles into
k bags:
- No bag empty.
- Bags contain contiguous marbles.
- Bag from index i to j has cost = weights[i] + weights[j].

Score = sum of costs. Return max - min possible scores.

Examples:
    weights=[1,3,5,1], k=2 -> 4
    weights=[7,3,9,1], k=3 -> 2

Constraints:
- 1 <= k <= weights.length <= 10^5
- 1 <= weights[i] <= 10^9
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Splitting weights into k contiguous bags means choosing k-1 split points
between adjacent marbles. Each split point contributes its two boundary
weights to the score.
```

### Step 2: The Trick
> "KEY INSIGHT: The total score = weights[0] + weights[n-1] + sum of pair
> sums at each split. The first and last terms are FIXED across all
> partitions.
>
> So max_score - min_score = (sum of k-1 largest adj sums) - (sum of k-1
> smallest adj sums), where adj[i] = weights[i] + weights[i+1]."

### Step 3: Why this works
> "Every bag starts at some index i and ends at some index j. The cost
> weights[i] + weights[j] is the sum of its two boundary marbles.
>
> Adjacent bags share a boundary marble. Across all bags, each internal
> marble is the END of one bag and the START of another (contributing
> twice). The first and last marbles are only boundary marbles once.
>
> So total = weights[0] + weights[n-1] + 2 * (sum of internal marbles).
> But the split contribution is cleaner: each split between i and i+1
> adds weights[i] + weights[i+1] to the score.
>
> Equivalently: total = weights[0] + weights[n-1] + sum of (weights[p] +
> weights[p+1]) at each split position p."

### Step 4: Algorithm
> "1. Build adj[i] = weights[i] + weights[i+1] for i in 0..n-2.
> 2. Sort adj.
> 3. max_score = sum of adj[-(k-1):] (k-1 largest).
> 4. min_score = sum of adj[:k-1] (k-1 smallest).
> 5. Return max_score - min_score."

### Step 5: Edge cases
> "- k == 1: no splits, max = min = base. Return 0.
> - k == n: every marble alone, all adj sums used.
> - All weights equal: all adj sums equal, diff = 0."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to divide marbles into k contiguous bags and return max - min score."

**Key Insight:**
> "Total score = weights[0] + weights[n-1] + sum of pair sums at each split. The first term is constant, so the difference reduces to picking k-1 splits with the largest vs smallest pair sums."

**Algorithm:**
> "1. Compute adj[i] = weights[i] + weights[i+1].
> 2. Sort adj.
> 3. max_score - min_score = (sum of k-1 largest) - (sum of k-1 smallest)."

**Why this works:**
> "Every split between i and i+1 contributes weights[i] + weights[i+1]. To maximize, pick splits with the highest contribution; to minimize, the lowest."

**Edge cases:**
- k == 1: no splits, return 0.
- k == n: all splits, return 0 (max = min).
- All equal weights: 0.

**Complexity:**
- Time:  O(n log n) — sort dominates.
- Space: O(n) for adj.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Adjacent sums + sort extremes (BEST - Memorize!)
```python
def put_marbles_1(weights, k):
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj.sort()
    return sum(adj[-(k - 1):]) - sum(adj[:k - 1])
```

### Way 2: Verbose
### Way 3: Brute force (combinations)
### Way 4: Heap-based selection
### Way 5: Manual partial sort
### Way 6: Class-based
### Way 7: numpy
### Way 8: enumerate
### Way 9: zip-based
### Way 10: Helper function
### Way 11: Functional with map
### Way 12: One-liner
### Way 13: Selection sort style
### Way 14: Pair difference formulation
### Way 15: nth_element
### Way 16: accumulate
### Way 17: bisect slice
### Way 18: max/min slice
### Way 19: Recursive
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Sort + slice |
| Small input        | Way 3    | Brute force  |
| numpy available    | Way 7    | Vectorized   |
| k << n             | Way 4    | Heap nlargest|
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + slice (Way 1) | O(n log n) | O(n) | Best |
| Brute force (Way 3) | O(C(n,k) * n) | O(n) | Slow |
| Heap (Way 4) | O(n log k) | O(n) | When k << n |

---

## Walkthrough Example

```
weights = [1, 3, 5, 1]
k = 2

Step 1: adj[i] = weights[i] + weights[i+1]:
  adj[0] = 1+3 = 4
  adj[1] = 3+5 = 8
  adj[2] = 5+1 = 6
  adj = [4, 8, 6]

Step 2: Sort.
  adj = [4, 6, 8]

Step 3: k-1 = 1 split.

Step 4: max = 8 (split after position 1, i.e., between 3 and 5).
  min = 4 (split after position 0, i.e., between 1 and 3).

Step 5: diff = 8 - 4 = 4.
```

```
weights = [7, 3, 9, 1]
k = 3

Step 1: adj = [10, 12, 10]
Step 2: sorted = [10, 10, 12]
Step 3: k-1 = 2.

Step 4: max = 10 + 12 = 22 (split at 0 and 2, or 0 and 1)
        Actually, we need to verify: splits at positions 1 and 2.
        Split 1: adj[1]=12, Split 2: adj[2]=10. Score = 7+3+9+1+12+10 = ...
        Wait, total = weights[0] + weights[n-1] + adj[split1] + adj[split2]
        = 7+1 + 12+10 = 30 (with splits at 1,2)
        Hmm, but k-1=2 means 2 splits.
        splits at 0,1: max contrib = adj[0]+adj[1] = 10+12 = 22 (with weights[0]+weights[n-1] = 7+1 = 8)
        splits at 1,2: max contrib = adj[1]+adj[2] = 12+10 = 22

        min = 10+10 = 20 (splits at 0 and 2)

Step 5: diff = 22 - 20 = 2.
```

---

## Best Answer to Memorize

```python
def put_marbles(weights, k):
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(adj[-(k - 1):]) - sum(adj[:k - 1])
```

**~5 lines. O(n log n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why cancel the base?
> "weights[0] + weights[n-1] appears in EVERY valid score. It doesn't
> contribute to the difference, so we ignore it entirely."

### Why adj sums?
> "A split between positions i and i+1 contributes weights[i] + weights[i+1]
> to the score. This is the cost of 'cutting' at that point."

### Why pick k-1 largest vs smallest?
> "Maximizing the score: choose splits with the LARGEST contribution.
> Minimizing: choose splits with the SMALLEST contribution."

### What if k == 1?
> "No splits. Only one bag containing all marbles. Score = weights[0] +
> weights[n-1]. Max = Min. Difference = 0."

### What if k == n?
> "Every marble alone. Each adj sum is used exactly once in both max and
> min (since all adj sums are used). Difference = 0."

### What if all weights equal?
> "All adj sums equal. Any k-1 splits give the same score. Difference = 0."

---

## Test Cases

| weights | k | Expected | Notes |
|---------|---|----------|-------|
| [1,3,5,1] | 2 | 4 | Standard |
| [7,3,9,1] | 3 | 2 | Standard |
| [1,2,3,4] | 1 | 0 | One bag |
| [1,2,3,4] | 4 | 0 | Each alone |
| [5,5,5,5] | 2 | 0 | All same |
| [100] | 1 | 0 | Single |
| [1,10] | 2 | 0 | Two |
| [1,4,2,3,5] | 3 | 4 | Mixed |
| [1,5,10,2,8] | 2 | 9 | Distinct |

---

## Common Pitfalls

1. **Off-by-one in adj sums**: adj has n-1 elements, not n.
2. **k-1 vs k**: We need k-1 splits, not k.
3. **Edge case k=1**: Must return 0 (no splits, no difference).
4. **Edge case k=n**: Must return 0 (all splits, no difference).
5. **Wrong slicing**: adj[-k1:] is last k1 elements, adj[:k1] is first k1.

---

## Why This Problem Matters

> "Tests:
> 1. Identifying what's constant vs variable (base cancellation).
> 2. Reducing complex optimization to simple selection.
> 3. Sort + sum extremes pattern.
> 4. Foundation for: partition problems, subarray sums."

---

## Beyond This Problem: Related Patterns

### 1. Partition Array for Maximum Sum (LC 1043)
```python
# DP variant: maximize sum after partitioning with replacements.
```

### 2. Largest Sum of Averages (LC 813)
```python
# Partition array into k groups maximizing sum of averages.
```

### 3. Split Array Largest Sum (LC 410)
```python
# Binary search on max subarray sum.
```

### 4. Minimum Difference Between Largest and Smallest in Subarray
```python
# Different: choose contiguous subarray.
```

---

## Connection to Partition Problems

This problem has a unique structure:

```
KEY OBSERVATION:
Total score = fixed_base + sum of adj sums at split positions.
Diff = sum of (k-1 largest adj) - sum of (k-1 smallest adj).

This decouples the choice of split points from the bag boundaries.
The base ALWAYS appears regardless of splits.
```

This is a special case — most partition problems (like Largest Sum of Averages)
require DP because the optimization isn't just about split-point selection.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the score formula?
- [ ] What's fixed across all valid configurations?
- [ ] Does the optimization reduce to picking k-1 from a sorted array?
- [ ] Handle k == 1 (return 0)
- [ ] Handle k == n (return 0)
- [ ] Edge case: all equal

---

## Mathematical Formulation

For sorted array `adj` of length n-1:

```
Let k1 = k - 1.

max_score_contribution = sum(adj[n-1-i] for i in range(k1))
                      = sum(adj[-(k1):])

min_score_contribution = sum(adj[i] for i in range(k1))
                      = sum(adj[:k1])

Answer = max_score_contribution - min_score_contribution.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 2551 - Put Marbles in Bags](https://leetcode.com/problems/put-marbles-in-bags/)
