# Put Marbles in Bags — 0.0001% Expert Guide

> **LeetCode 2551** | **Difficulty:** Hard | **Avg Solve Time:** 25 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/put-marbles-in-bags
> **Problem:** `put_marbles(weights, k)` — diff between max and min scores.

---

## 📋 WHAT THE QUESTION ASKS

You have `weights` marbles. Distribute into `k` bags (contiguous groups in original array). Each bag must have at least 1 marble. **Score** = sum of (first marble + last marble) for each bag. Return max_score − min_score.

### Constraints
- `1 <= k <= weights.length <= 10^5`
- `1 <= weights[i] <= 10^9`

### Examples

```
weights=[1,3,5,1], k=2 → 4
  cuts = [4, 8, 6]. k-1=1. top-bottom = 8-4 = 4. ✓

weights=[1,3], k=2 → 0
  Only split: [1] | [3]. Same score both ways. Diff=0.

weights=[10,14,12,1,5,4], k=3 → 35
  cuts = [24, 26, 13, 6, 9]. Sorted: [6,9,13,24,26].
  top 2 = 50, bottom 2 = 15. Diff = 35.
```

### Why This Is "Hard"
- The KEY insight (Score = w[0]+w[n-1] + sum of cuts) is non-obvious.
- Without it, the problem looks like an O(n choose k-1) DP nightmare.
- With it, it's a simple O(n log n) sort.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Distribute n marbles into k bags (contiguous). Score = sum of bag endpoints. Return max - min."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort cuts + top/bottom k-1:** O(n log n). **Best.**
> 2. **Brute force DP:** O(C(n-1, k-1)). Exponential.
> 3. **Greedy:** doesn't work.
>
> Best: Sort cuts."

### Step 3: KEY INSIGHT — Score Decomposition (5 min)
> "Score = (w[0] + w[n-1]) + sum of (k-1) CUT VALUES.
> 
> Where cut[i] = w[i] + w[i+1].
> 
> Proof: For cuts at positions i_1 < i_2 < ... < i_{k-1}:
> - Bags: [0..i_1], [i_1+1..i_2], ..., [i_{k-1}+1..n-1]
> - Score = (w[0]+w[i_1]) + (w[i_1+1]+w[i_2]) + ... + (w[i_{k-1}+1]+w[n-1])
> - Reorganize: w[0] + w[n-1] + (w[i_1]+w[i_1+1]) + ... + (w[i_{k-1}]+w[i_{k-1}+1])
> - = w[0] + w[n-1] + sum(cut[i_j]).
>
> w[0] and w[n-1] are FIXED. So maximize/minimize the cut sum."

### Step 4: Greedy Cut Selection (3 min)
> "Max score = sum of k-1 LARGEST cuts.
> Min score = sum of k-1 SMALLEST cuts.
> Diff = top k-1 - bottom k-1."

### Step 5: Algorithm (5 min)
```
1. Compute cuts = [w[i]+w[i+1] for i in 0..n-2]. (n-1 cuts.)
2. Sort cuts.
3. If k-1 == 0: return 0.
4. Return sum(cuts[-(k-1):]) - sum(cuts[:k-1]).
```

### Step 6: Edge Cases (2 min)
- k = 1: no cuts. Score = w[0]+w[n-1]. Diff = 0.
- k = n: each marble its own bag. Score = 2*sum(weights). Diff = 0.
- n = 1: only one marble, k must be 1, diff = 0.

### Step 7: Code It (5 min)

```python
def put_marbles(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(cuts[-(k - 1):]) - sum(cuts[:k - 1])
```

### Step 8: Verify (2 min)
For `[1,3,5,1], k=2`:
- cuts = [1+3, 3+5, 5+1] = [4, 8, 6]. Sorted: [4, 6, 8].
- k-1 = 1. top = cuts[-1:] = [8]. bottom = cuts[:1] = [4]. diff = 8-4 = 4. ✓

For `[10,14,12,1,5,4], k=3`:
- cuts = [24, 26, 13, 6, 9]. Sorted: [6, 9, 13, 24, 26].
- k-1 = 2. top = [24, 26] = 50. bottom = [6, 9] = 15. diff = 35. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Sort + greedy:** O(n log n). **Best.**
> 2. **DP brute:** O(C(n-1,k-1)). TLE for large.
> 3. **Sort + heap:** O(n log k). Slight optimization.
>
> I'll use sort + greedy."

### Step 10: Why Sort Is Optimal (3 min)
> "After sort, picking top/bottom k-1 is O(1) per element. Total: O(n log n) sort + O(k) selection = O(n log n)."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the difference between max and min scores when
distributing n marbles into k bags.

KEY INSIGHT: Score = w[0] + w[n-1] + sum of cut values.
- Each cut at position i contributes w[i] + w[i+1].
- w[0] and w[n-1] are CONSTANT.
- So max - min = sum of top (k-1) cuts - sum of bottom (k-1) cuts.

ALGORITHM:
1. Compute cuts = [w[i] + w[i+1] for i in 0..n-2].
2. Sort cuts.
3. If k = 1: return 0.
4. Return sum(top k-1 cuts) - sum(bottom k-1 cuts).

COMPLEXITY: O(n log n) time, O(n) space.

EDGE CASES:
- k = 1: 0.
- k = n: 0.
- n = 1: 0.

THE TRICK: The decomposition Score = fixed + sum(cuts). Cuts are
independent. Just pick biggest/smallest k-1.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + Greedy (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort + top/bottom (BEST) | O(n log n) | O(n) | **THE ANSWER** |
| 2 | Sort + manual sum | O(n log n) | O(n) | Educational |
| 5 | Sort desc | O(n log n) | O(n) | Variant |
| 6 | Bisect | O(n log n) | O(n) | Variant |
| 8 | Sort + ends | O(n log n) | O(n) | Variant |
| 9 | Accumulate | O(n log n) | O(n) | Functional |
| 10 | Class OOP | O(n log n) | O(n) | Reusable |
| 11 | Sort desc slice | O(n log n) | O(n) | Variant |
| 13 | One-liner | O(n log n) | O(n) | Concise |
| 14 | Reduce | O(n log n) | O(n) | Functional |
| 15 | Map + sum | O(n log n) | O(n) | Functional |
| 16 | Manual extract | O(n log n) | O(n) | Educational |
| 17 | Zip | O(n log n) | O(n) | Variant |
| 18 | Statistics | O(n log n) | O(n) | Variant |
| 19 | Prefix sums | O(n log n) | O(n) | Educational |
| 20 | Final cleanest | O(n log n) | O(n) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Heap

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | heapq nsmallest/nlargest | O(n log k) | O(k) | Partial sort |
| 7 | Partial heapselect | O(n log k) | O(k) | Custom |

### 🟣 TIER 3: DP Brute

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | DP brute | O(C(n-1,k-1)) | O(n*k) | Tiny n only |

### ⚪ TIER 4: Vectorized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 12 | Numpy | O(n log n) | O(n) | Vectorized |

---

## 💎 THE 7-LINE SOLUTION (Memorize!)

```python
def put_marbles(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(cuts[-(k - 1):]) - sum(cuts[:k - 1])
```

**Time:** `O(n log n)`
**Space:** `O(n)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: The Score Decomposition Trick

> Score = (constant) + sum(cuts).

The magic: the score has a FIXED part (w[0]+w[n-1]) and a VARIABLE part (sum of cuts). This decomposes a complex combinatorial problem into simple sorting.

**Connection to:**
- **Problem decomposition:** Break complex into simple.
- **Linear algebra:** Sum decomposition.
- **Convex optimization:** Decompose objective.

### Insight 2: Contiguous Bags = Cuts

> "k contiguous bags" = "k-1 cuts in n-1 positions".

The problem transforms from "how to partition" to "which k-1 positions to cut". This is a much cleaner formulation.

**Connection to:**
- **Combinatorics:** Choose k-1 from n-1.
- **Stars and bars:** Standard transformation.

### Insight 3: Why Cut at Position i = w[i] + w[i+1]

> When we cut between marbles i and i+1, marble i is the LAST of its bag and marble i+1 is the FIRST of the next. Both contribute to the score.

This is the key observation. Each cut "double-counts" its two endpoints.

**Connection to:**
- **Boundary effects:** Endpoints matter.
- **Inclusion-exclusion:** Both endpoints included.

### Insight 4: Why Sort Is Greedy-Optimal

> To maximize sum of k-1 selected items, sort and pick top k-1.

Trivially optimal for independent items. The cuts are independent (one cut doesn't affect another cut's contribution).

**Connection to:**
- **Greedy optimality:** Independent items.
- **Selection sort:** Standard.

### Insight 5: Why Heap Doesn't Help Much Here

> We need ALL cuts sorted eventually to know top vs bottom.

Heap only saves if k << n. For k ≈ n/2, sorting is faster.

**Connection to:**
- **Quickselect vs sort:** Same complexity here.
- **Partial sort:** When k << n.

### Insight 6: Connection to Partition Problems

> LC 410 (Split Array), LC 1043 (Partition Array), LC 813 (Largest Sum of Averages).

All are partition problems. The "score = fixed + variable" trick applies to similar problems.

**Connection to:**
- **Problem family:** Partition DP.
- **Optimization:** Common structure.

### Insight 7: Why DP Brute Is Exponential

> Choosing k-1 cuts from n-1 positions = C(n-1, k-1). For k=n/2, this is exponential.

DP is impractical for large n. The cut trick converts to O(n log n).

**Connection to:**
- **Combinatorial explosion:** Why DP fails.
- **Greedy proof:** Why sort works.

### Insight 8: Real-World Applications

| Application | Use |
|-------------|-----|
| **Inventory allocation** | Distribute goods into warehouses |
| **Task scheduling** | Time blocks to workers |
| **Budget allocation** | Money across departments |
| **Course scheduling** | Classes to time slots |
| **Resource distribution** | Items to bins |
| **Production planning** | Batch sizes |

**Inventory allocation** is the canonical use case.

### Insight 9: The "Cost Per Cut" View

> Each cut has a "cost" w[i]+w[i+1]. Maximizing sum = picking biggest costs.

This is like a knapsack where we MUST pick exactly k-1 items. With all positive weights, just pick biggest.

**Connection to:**
- **Knapsack variant:** Fixed cardinality.
- **Optimization:** Easy sub-problem.

### Insight 10: When Decomposition Fails

> If score = something nonlinear in cuts, this trick fails.

E.g., if score = max(cuts) instead of sum(cuts), or product. The decomposition relies on linearity.

**Connection to:**
- **Linearity assumption:** Critical.
- **Nonlinear optimization:** Different techniques.

### Insight 11: Generalization to k-Way Cuts

> Score = w[0] + w[n-1] + sum of k-1 selected cuts. Extends naturally.

Same formula works for any k. Algorithm unchanged.

**Connection to:**
- **Generalization:** Natural.
- **Recursive structure:** Same.

### Insight 12: Why `k-1` and Not `k`

> k bags require k-1 cuts. Last bag has no cut after it.

Standard partition logic.

**Connection to:**
- **Boundary conditions:** Off-by-one.
- **Combinatorics:** C(n-1, k-1) not C(n, k-1).

### Insight 13: Connection to Order Statistics

> "Find sum of top k-1 cuts" is order statistics.

The top k-1 cuts are the (k-1)-th order statistic and above.

**Connection to:**
- **Order statistics:** Top-k queries.
- **Selection algorithms:** Quickselect.

---

## 🧪 TEST CASES

| `weights` | `k` | Expected | Note |
|-----------|-----|----------|------|
| `[1,3,5,1]` | 2 | 4 | Standard |
| `[1,3]` | 2 | 0 | Only cut |
| `[1]` | 1 | 0 | Single marble |
| `[1,2,3,4,5]` | 5 | 0 | All bags |
| `[1,2,3,4,5]` | 1 | 0 | One bag |
| `[10,14,12,1,5,4]` | 3 | 35 | Complex |
| `[1,4,2,5,3]` | 2 | 3 | Cuts [5,6,7,8] |
| `[2,2,2,2,2]` | 2 | 0 | All same |
| `[1,2]` | 2 | 0 | Cuts=[3] |
| `[1,2,3]` | 2 | 2 | Cuts=[3,5] |
| `[1,2,3,4]` | 2 | 4 | Cuts=[3,5,7] |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Sort + greedy** | **O(n log n)** | **O(n)** | **✅ BEST** |
| Heap-based | O(n log k) | O(k) | ✅ When k << n |
| DP brute | O(C(n-1,k-1)) | O(n*k) | ❌ TLE large |
| Numpy | O(n log n) | O(n) | ✅ Vectorized |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Split Array Largest Sum (LC 410) | Partition DP | https://leetcode.com/problems/split-array-largest-sum/ |
| Largest Sum of Averages (LC 813) | Partition DP | https://leetcode.com/problems/largest-sum-of-averages/ |
| Partition Array Max Sum (LC 1043) | DP | https://leetcode.com/problems/partition-array-for-maximum-sum/ |
| Max Value of K Coins (LC 2611) | Greedy | https://leetcode.com/problems/mice-and-cheese/ |
| Put Marbles in Bags (LC 2551) | **This problem** | https://leetcode.com/problems/put-marbles-in-bags/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Score = w[0]+w[n-1] + sum(cuts)** — the magic decomposition.
2. **Pick top (k-1) and bottom (k-1) cuts.** Independent items.
3. **Sort + greedy** is O(n log n).
4. **DP brute** is exponential — avoid.
5. **k-1 cuts for k bags** — off-by-one awareness.
6. **Heap** doesn't help much when k ≈ n.
7. **Linear decomposition** — only works for sum-based scores.
8. **Real-world: inventory, scheduling, allocation.**
9. **Quickselect** can give top k in O(n) average.
10. **Always test k=1, k=n, n=1 edge cases.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Inventory allocation** | Goods to warehouses |
| **Task scheduling** | Time blocks to workers |
| **Budget allocation** | Money to departments |
| **Course scheduling** | Classes to time slots |
| **Resource distribution** | Items to bins |
| **Production planning** | Batch sizes |
| **Order statistics** | Top-k selection |
| **Partition DP** | Related problems |
| **Combinatorial optimization** | Independent items |
| **Linear decomposition** | Score = fixed + variable |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive score decomposition in 60 seconds
- [x] Can code the 7-line solution in 60 seconds
- [x] Know the complexity: O(n log n) time, O(n) space
- [x] Know why score = w[0]+w[n-1] + sum(cuts)
- [x] Know why pick top/bottom k-1 cuts
- [x] Know edge cases (k=1, k=n, n=1)
- [x] Can compare with DP and heap
- [x] Know related problems (Split Array, Partition)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 7.
**Insight:** "Score = w[0]+w[n-1] + sum(cuts where cut[i] = w[i]+w[i+1]). Diff = sum(top k-1 cuts) - sum(bottom k-1 cuts)."
