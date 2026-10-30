# Maximum Number of Integers to Choose from a Range I — 0.0001% Expert Guide

> **LeetCode 2552** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-number-of-integers-to-choose-from-a-range-i
> **Problem:** `max_count(banned, n, max_sum)` — max integers from [1,n] skipping banned, sum ≤ max_sum.

---

## 📋 WHAT THE QUESTION ASKS

Given:
- `banned[]`: integers you cannot choose.
- `n`: range [1, n] of choosable integers.
- `max_sum`: sum constraint.

Return the **maximum count** of integers you can choose such that:
1. Each chosen integer is in `[1, n]`.
2. Each chosen at most once.
3. No banned integer is chosen.
4. Sum of chosen ≤ `max_sum`.

### Constraints
- `1 <= banned.length <= 10^3` (educative) / `10^4` (LC)
- `1 <= banned[i], n <= 10^4` (LC)
- `1 <= max_sum <= 10^6` (LC)

### Examples

```
banned=[1,6,5], n=5, max_sum=6 → 2 (choose 2 and 4, sum=6)
banned=[1,2,3,4,5,6,7], n=8, max_sum=1 → 0 (8 > max_sum)
banned=[11], n=7, max_sum=50 → 7 (all 1-7, sum=28)
banned=[], n=5, max_sum=15 → 5 (1+2+3+4+5=15)
```

### Why This Is "Medium"
- Greedy is non-obvious but provably optimal.
- Skip banned while iterating.
- Edge cases with empty banned and small n.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Max count of integers from [1,n], skipping banned, with sum ≤ max_sum."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Greedy: pick smallest first.** Provably optimal.
> 2. **DP: knapsack-like.** O(n * max_sum).
> 3. **Mathematical: solve for m directly.** O(log n * |banned|).
>
> Best: Greedy. O(n)."

### Step 3: KEY INSIGHT — Why Greedy Works (5 min)
> "To maximize COUNT under a sum constraint, pick the SMALLEST integers first.
> 
> Proof sketch:
> - Suppose we picked a set S with sum ≤ max_sum and |S| = k.
> - If S doesn't contain the smallest k non-banned integers, swap any larger
>   element with a smaller non-banned. The sum decreases (or stays equal),
>   and count is unchanged.
> - So an optimal solution uses the k smallest non-banned integers."

### Step 4: Algorithm (5 min)
```
1. banned_set = set(banned)
2. count = 0, total = 0
3. For i from 1 to n:
   - If i in banned_set: continue
   - If total + i > max_sum: break
   - total += i, count += 1
4. Return count
```

### Step 5: Edge Cases (2 min)
- All of [1,n] banned: return 0.
- max_sum = 0 or very small: return 0.
- Empty banned: count = max m where 1+2+...+m ≤ max_sum = ⌊(√(1+8*max_sum)-1)/2⌋.

### Step 6: Code It (5 min)

```python
def max_count(banned, n, max_sum):
    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count
```

### Step 7: Verify (2 min)
For `banned=[1,6,5], n=5, max_sum=6`:
- banned_set = {1, 5, 6}
- i=1: banned, skip.
- i=2: not banned, total=0+2=2 ≤ 6. total=2, count=1.
- i=3: total=2+3=5 ≤ 6. total=5, count=2.
- i=4: total=5+4=9 > 6. break.
- Return 2. ✓

### Step 8: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Greedy:** O(n + |banned|). **Best.**
> 2. **DP:** O(n * max_sum). For small max_sum.
> 3. **Mathematical BS:** O(log n * |banned|). Clever.
>
> Greedy is simplest and optimal here."

### Step 9: Why DP Doesn't Help (3 min)
> "DP works but is overkill. Greedy is provably optimal because:
> - Picking smaller integers 'saves' sum budget for more picks.
> - This is the inverse of minimizing sum for fixed count."

### Step 10: Final Clean Code (5 min)
Memorize the 8-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to maximize the count of integers chosen from [1, n], skipping
banned, with total sum <= max_sum.

KEY INSIGHT: To MAXIMIZE COUNT under a sum constraint, pick the
SMALLEST integers first. Smaller integers use less sum per item,
allowing more picks.

ALGORITHM:
1. Put banned in a set for O(1) lookup.
2. Iterate i from 1 to n:
   - Skip if i is banned.
   - If total + i > max_sum: break.
   - Else: take i, increment total and count.
3. Return count.

COMPLEXITY: O(n + |banned|) time, O(|banned|) space.

EDGE CASES:
- All banned: return 0.
- max_sum too small: return 0.
- Empty banned: count = floor of triangular number solution.

WHY GREEDY WORKS:
Suppose we picked k integers not all smallest. Replacing a larger one
with a smaller non-banned reduces sum (good) and keeps count. So
optimal = k smallest non-banned integers."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Greedy (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Set + greedy (BEST) | O(n) | O(B) | **THE ANSWER** |
| 2 | Boolean array | O(n) | O(n) | Educational |
| 3 | Sort banned | O(n log B) | O(B) | Variant |
| 4 | Brute greedy | O(n) | O(B) | Easy |
| 5 | With prefix sum | O(n) | O(B) | Readable |
| 7 | Class OOP | O(n) | O(B) | Reusable |
| 10 | Sort+accumulate | O(n log B) | O(B) | Variant |
| 11 | One-liner | O(n) | O(B) | Concise |
| 15 | Generator | O(n) | O(B) | Pythonic |
| 16 | While loop | O(n) | O(B) | Explicit |
| 17 | With sum check | O(n) | O(B) | Variant |
| 18 | Sort+pointer | O(n log B) | O(B) | Variant |
| 19 | Filter | O(n) | O(n) | Functional |
| 20 | Final cleanest | O(n) | O(B) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Mathematical / Binary Search

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | BS on count | O(log n * B) | O(B) | Clever |

### 🟣 TIER 3: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 8 | Min-heap | O(n log n) | O(n) | Educational |
| 9 | Bisect on banned | O(n log B) | O(B) | Variant |
| 12 | Numpy | O(n) | O(n) | Vectorized |

### ⚪ TIER 4: Dynamic Programming

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 13 | Recursive memo | O(n * max_sum) | O(n * max_sum) | Optimal count |
| 14 | Iterative DP | O(n * max_sum) | O(max_sum) | General |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def max_count(banned, n, max_sum):
    banned_set = set(banned)
    count = 0
    total = 0
    for i in range(1, n + 1):
        if i in banned_set:
            continue
        if total + i > max_sum:
            break
        total += i
        count += 1
    return count
```

**Time:** `O(n + |banned|)`
**Space:** `O(|banned|)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Greedy When Goal is COUNT, Not Sum

> "Maximize count" reverses the priority: prefer small over large.

In most knapsack variants, we maximize value or minimize cost. Here, we maximize count given a cost cap. Smallest first is optimal.

**Connection to:**
- **Greedy algorithms:** Always locally optimal choice.
- **Matroid theory:** Independent set maximization.
- **Exchange argument:** Swap to improve.

### Insight 2: The Exchange Argument

> "If optimal doesn't include smallest, swap to include it (and reduce sum)."

This is the formal proof technique for greedy:
1. Take any optimal solution.
2. If it doesn't include the smallest available, exchange.
3. Exchange doesn't reduce count, may reduce sum.
4. Conclude: optimal includes smallest.

**Connection to:**
- **Matching theory:** Exchange arguments.
- **Matroids:** Greedy works on matroids.
- **Scheduling:** Exchange to improve schedule.

### Insight 3: Why "Smallest First" Is Different from "Biggest Value"

> Standard knapsack: maximize value, take best value/weight ratio.
> Here: maximize count, take smallest weight.

Different objective → different greedy.

**Connection to:**
- **Linear programming:** Different objectives, different optima.
- **Multi-objective:** Pareto frontier.
- **Resource allocation:** Different priorities.

### Insight 4: Triangular Number Solution

> For empty banned, sum of 1..m = m(m+1)/2. Solve m² + m - 2*max_sum ≤ 0.
> m ≤ (-1 + √(1 + 8*max_sum)) / 2.

Closed-form solution exists for the simple case.

**Connection to:**
- **Quadratic formulas:** Closed-form.
- **Triangular numbers:** T(m) = m(m+1)/2.
- **Tetrahedral numbers:** Higher-dim analogues.

### Insight 5: Connection to Knapsack

> This is 0/1 knapsack where value = 1 for every item and weight = value.

Knapsack is NP-hard in general, but this special case (uniform value) is solvable greedily.

**Connection to:**
- **Special-case tractability:** NP-hard in general, easy in special cases.
- **Approximation algorithms:** Greedy for hard problems.
- **Pseudo-polynomial:** DP works when max_sum is small.

### Insight 6: Why DP Doesn't Help Here

> DP would be O(n * max_sum). Greedy is O(n).
> 
> Greedy wins because the objective (count) is aligned with smallest-first.

**Connection to:**
- **Problem structure:** Greedy works when local = global.
- **Matroid intersection:** Greedy is optimal.
- **Approximation:** Greedy approximation for hard problems.

### Insight 7: Connection to Budget Allocation

> "Spend budget on small items to maximize purchases."

Real-world analogy: shopping on a budget, picking smallest items first.

**Connection to:**
- **Budget allocation:** Spending strategy.
- **Inventory management:** Buy cheap first.
- **Resource-constrained scheduling:** Smallest jobs first.

### Insight 8: The Banned Set as a Filter

> Set membership is O(1). Total filter cost: O(n).

Using set vs sorted list vs boolean array — different trade-offs.

**Connection to:**
- **Hash tables:** O(1) membership.
- **Bitsets:** O(1) membership, O(1) operations.
- **Bloom filters:** Probabilistic.

### Insight 9: Why Early Termination Is Critical

> Once sum exceeds max_sum, ALL remaining integers are larger, so we can break.

Sorted iteration enables early termination. Unsorted would require full scan.

**Connection to:**
- **Short-circuit evaluation:** Stop when done.
- **Greedy with proof:** Provable termination.
- **Sliding window:** Bounded iteration.

### Insight 10: Real-World Applications

| Application | Use |
|-------------|-----|
| **Budget shopping** | Max items within budget |
| **Knapsack variants** | Maximize count |
| **Resource allocation** | Pick smallest first |
| **Project selection** | Cheap projects first |
| **Hiring** | Minimize salary for max hires |
| **Inventory** | Stock small items first |
| **Course selection** | Minimize cost |
| **Menu optimization** | Maximize dishes under budget |

**Hiring decisions** often use this logic: max new hires within budget → hire cheapest first.

### Insight 11: Generalization to Weighted Case

> If each item has a value and weight, this becomes 0/1 knapsack (NP-hard).

Greedy works only when value is uniform (= count).

**Connection to:**
- **NP-hardness:** Different complexity class.
- **Approximation:** Greedy for hard problems.
- **Special cases:** Tractable instances.

### Insight 12: The Combinatorial Insight

> Greedy works because the integers [1, n] form a CHAIN under ordering.

For arbitrary sets, greedy may not work. The ordered structure (1 < 2 < ... < n) makes it work.

**Connection to:**
- **Order theory:** Chains, antichains.
- **Dilworth's theorem:** Chain decomposition.
- **Poset:** Partially ordered sets.

---

## 🧪 TEST CASES

| `banned` | `n` | `max_sum` | Expected | Note |
|----------|-----|-----------|----------|------|
| `[1,6,5]` | 5 | 6 | 2 | Choose 2,4 |
| `[1,2,3,4,5,6,7]` | 8 | 1 | 0 | 8 > 1 |
| `[11]` | 7 | 50 | 7 | All of 1-7 |
| `[]` | 5 | 15 | 5 | 1+2+3+4+5=15 |
| `[3,5]` | 5 | 10 | 3 | Choose 1,2,4 |
| `[1]` | 1 | 1 | 0 | All banned |
| `[2]` | 3 | 4 | 2 | Choose 1,3 |
| `[5]` | 5 | 10 | 4 | 1+2+3+4=10 |
| `[5]` | 5 | 6 | 3 | 1+2+3=6 |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Greedy** | **O(n)** | **O(B)** | **✅ BEST** |
| DP | O(n * max_sum) | O(max_sum) | ✅ Optimal |
| Mathematical BS | O(log n * B) | O(B) | ✅ Clever |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Maximum Number of Integers (LC 2552) | **This problem** | https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-i/ |
| Max Number of Integers II (LC 2557) | Variant with II | https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-ii/ |
| Knapsack 0/1 (LC 494) | DP variant | https://leetcode.com/problems/target-sum/ |
| Coin Change (LC 322) | Greedy+DP | https://leetcode.com/problems/coin-change/ |
| Partition Equal Subset (LC 416) | DP | https://leetcode.com/problems/partition-equal-subset-sum/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Greedy: smallest first.** Provably optimal for max count.
2. **Skip banned** using set membership.
3. **Early termination** when sum would exceed max_sum.
4. **O(n) time, O(B) space** — clean and efficient.
5. **Triangular numbers** give closed form for empty banned.
6. **DP is overkill** here — greedy suffices.
7. **Exchange argument** proves greedy optimal.
8. **Real-world: budget shopping, hiring.**
9. **Generalizes to matroid theory.**
10. **Connection to budget allocation and resource-constrained scheduling.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Budget allocation** | Max items within budget |
| **Knapsack** | Uniform value case |
| **Resource scheduling** | Smallest jobs first |
| **Hiring decisions** | Maximize hires |
| **Combinatorial optimization** | Greedy on chains |
| **Matroid theory** | Greedy optimality |
| **Approximation algorithms** | NP-hard special cases |
| **Linear programming** | Different objectives |
| **Order theory** | Chains, posets |
| **Real-world shopping** | Budget constraints |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive greedy optimality in 60 seconds
- [x] Can code the 8-line solution in 60 seconds
- [x] Know the complexity: O(n) time, O(B) space
- [x] Know why greedy works (exchange argument)
- [x] Know the early termination condition
- [x] Know the triangular number closed form
- [x] Can compare with DP and BS approaches
- [x] Know related problems (Knapsack variants)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 8.
**Insight:** "Greedy: pick smallest non-banned first. Skip banned. Stop when next integer would exceed max_sum."
