# Kth Smallest Number in Multiplication Table — 0.0001% Expert Guide

> **LeetCode 668** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-multiplication-table
> **Problem:** `findKthNumber(m, n, k)` — find kth smallest in m×n table where `mat[i][j] = i*j` (1-indexed)

---

## 📋 WHAT THE QUESTION ASKS

Given two integers `m` and `n` (the dimensions of a multiplication table) and an integer `k`:

```
1   2   3   ...   n
2   4   6   ...   2n
3   6   9   ...   3n
...
m   2m  3m  ...   mn
```

Find the **k-th smallest** number in this table.

### Constraints
- `1 <= m, n <= 3 * 10^4`
- `1 <= k <= m * n`

### Examples

| m | n | k | Table (sorted) | Answer |
|---|---|---|----------------|--------|
| 3 | 3 | 5 | 1,2,2,**3**,3,4,6,6,9 | **3** |
| 4 | 5 | 8 | 1,2,2,3,3,**4**,4,4,5,... | **4** |
| 2 | 3 | 6 | 1,2,2,3,4,**6** | **6** |
| 1 | 5 | 3 | 1,2,**3**,4,5 | **3** |
| 3 | 3 | 9 | 1,2,2,3,3,4,6,6,**9** | **9** |

### Why This Is Hard
- The matrix is **NOT row-sorted AND column-sorted in the usual sense**.
- Row `i`: `[i, 2i, 3i, ..., ni]` — sorted ascending.
- Column `j`: `[j, 2j, 3j, ..., mj]` — sorted ascending.
- But row `i+1` is NOT necessarily all greater than row `i`. The matrix isn't a "sorted matrix" in the Search-a-2D-Matrix sense.
- We need to find the **k-th smallest among all `m*n` elements**.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find kth smallest in a multiplication table where mat[i][j] = i*j (1-indexed)."

### Step 2: Brainstorm Brute Force (2 min)
> "Build the full table, flatten, sort, return arr[k-1]."
- Time: `O(m*n*log(m*n))`, Space: `O(m*n)`
- Works for small m, n. Will TLE for m = n = 30000.

### Step 3: Spot the Hidden Monotonicity (THE KEY INSIGHT) (5 min)
> "What if I don't search by INDEX, but search by VALUE?"

For any candidate value `x`, I can count how many elements in the table are `<= x`:
- Each row `i` is the arithmetic sequence `i, 2i, 3i, ..., ni`.
- The number of values in row `i` that are `<= x` is `min(x // i, n)`.
- Total count: `sum(min(x // i, n) for i in 1..m)`.

**This count function is MONOTONICALLY INCREASING in x:**
- `count(0) = 0`
- `count(m*n) = m*n`
- `x1 < x2 ⟹ count(x1) <= count(x2)`

### Step 4: Apply Binary Search on Value (5 min)
> "I want the SMALLEST x such that count(x) >= k."

This is exactly what binary search finds. The answer lies in `[1, m*n]`.

### Step 5: Optimize the Count (3 min)
- Swap m and n if m > n (iterate over the smaller dimension).
- Each `count(x)` call is `O(min(m,n))`.
- Total: `O(min(m,n) * log(m*n))`.

### Step 6: Sanity Check (2 min)
- `k = 1`: smallest is 1. ✓
- `k = m*n`: largest is `m*n`. ✓
- `m = 1`: row is `1, 2, 3, ..., n`. kth is k. ✓
- `n = 1`: column is `1, 2, 3, ..., m`. kth is k. ✓

### Step 7: Code It (10 min)
- Define `count_leq(x)`.
- Binary search with `[lo, hi]` invariants.
- Return `lo`.

### Step 8: Verify with Examples (2 min)
- m=3, n=3, k=5: lo=1, hi=9.
  - mid=5: count(5) = min(5//1,3) + min(5//2,3) + min(5//3,3) = 3 + 2 + 1 = 6. 6 >= 5, hi=5.
  - mid=3: count(3) = 3 + 1 + 1 = 5. 5 >= 5, hi=3.
  - mid=2: count(2) = 2 + 1 + 0 = 3. 3 < 5, lo=3.
  - lo=3 = hi. Return 3. ✓

### Step 9: Discuss Trade-offs (5 min)
> "I have 3 options. Let me discuss each:

1. **Brute force**: O(mn log mn) — too slow for m,n = 30000.
2. **Heap**: O(k log m) — okay but k can be m*n.
3. **Binary search on value**: O(min(m,n) log(mn)) — best.

I'll go with binary search."

### Step 10: Final Cleanest Code (5 min)
The 5-line solution that every interviewer wants to see.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"The kth smallest in a sorted array uses binary search on INDEX.
But here, the table isn't fully sorted, so I can't directly use that.

KEY INSIGHT: I'll binary search on the VALUE, not the index.
For any value x, I can count how many elements in the table are <= x.
This count function is monotonically increasing in x.

COUNTING:
- Each row i has values i*1, i*2, ..., i*n.
- Number of values in row i that are <= x is min(x // i, n).
- Total count = sum over all rows.

ALGORITHM:
1. Binary search x in [1, m*n].
2. For each mid, compute count(mid).
3. If count(mid) >= k, answer is <= mid, so hi = mid.
4. Else, answer > mid, so lo = mid + 1.
5. Return lo.

COMPLEXITY: O(min(m,n) * log(m*n)) time, O(1) space.

OPTIMIZATION: Swap m and n if m > n, so we iterate fewer rows."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Brute Force (memorize for warmup)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Build + sort | O(mn log mn) | O(mn) | Small m, n only |
| 11 | Build full table inline | O(mn log mn) | O(mn) | Same as above |
| 12 | numpy + flatten | O(mn log mn) | O(mn) | When numpy is allowed |

### 🟡 TIER 2: Heap-Based (Lazy Expansion)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Heap with visited set | O(k log m) | O(m) | When k is small |
| 13 | Heap alt style | O(k log m) | O(m) | Variation |

### 🔴 TIER 3: Binary Search on Value (BEST)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Classic | O((m+n) log mn) | O(1) | **The answer to memorize** |
| 2 | Verbose naming | same | O(1) | For clarity |
| 3 | Swap dimensions | O(min(m,n) log mn) | O(1) | **Optimized** |
| 6 | Optimized counting | same | O(1) | Performance |
| 7 | Generator sum | same | O(1) | Pythonic |
| 8 | List comp | same | O(1) | Pythonic |
| 9 | Edge cases | same | O(1) | Production |
| 10 | Explicit count | same | O(1) | Educational |
| 14 | Right-exclusive BS | same | O(1) | Variant |
| 15 | While-true loop | same | O(1) | Variant |
| 16 | Classic | same | O(1) | Standard |
| 17 | Class-based OOP | same | O(1) | Reusable |
| 18 | Comprehensive | same | O(1) | Production |
| 19 | Most concise | same | O(1) | One-liner |
| 20 | Final cleanest | same | O(1) | **THE ONE** |

---

## 💎 THE 5-LINE SOLUTION (Memorize!)

```python
def findKthNumber(m, n, k):
    if m > n: m, n = n, m
    lo, hi = 1, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(min(mid // i, n) for i in range(1, m + 1)) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**Time:** `O(min(m,n) * log(m*n))`
**Space:** `O(1)`

This is the answer. 5 lines. Memorize it.

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Monotonicity is the Universal Key

> In any "kth smallest" problem, ask yourself: **"Is there a monotone function I can binary search on?"**

- Search a 2D matrix? Monotone = target comparison.
- Kth smallest in sorted matrix (LC 378)? Monotone = count of elements <= x.
- **Kth smallest in multiplication table?** Monotone = count of elements <= x.
- Kth smallest pair sum? Monotone = count of pairs with sum <= x.
- Median of two sorted arrays? Monotone = count of elements <= x.

**Pattern recognition:** Whenever you see "kth smallest/largest" + a structured 2D problem → think **binary search on value with a count predicate**.

### Insight 2: The Count Predicate is a CDF

In statistics, the **Cumulative Distribution Function (CDF)** `F(x) = P(X <= x)` is monotonically non-decreasing. Binary search on a value where you have a CDF is the standard way to find quantiles (median = 50th percentile = kth).

**Connection to data/AI:**
- **Quantile regression:** Same problem. Find the x where CDF(x) = p.
- **Order statistics trees:** Maintain a sorted structure where kth lookup is O(log n).
- **Order statistics in databases:** Postgres's `percentile_cont()` uses binary search with CDF.
- **Approximate quantiles in streaming:** t-digest, KLL, Greenwald-Khanna — all use binary search on value with a count predicate.
- **ML rank-loss (pairwise):** The gradient updates weights based on whether predicted value is "above" or "below" the kth item.

### Insight 3: The Multiplication Table as a Partial Order

> The set `{(i, j) : i*j <= x}` forms a **lattice** (specifically, a Young-diagram-like shape).

For each row `i`, the valid `j` values satisfying `i*j <= x` are `j <= x/i`, so `j in [1, floor(x/i)]`.

The total count is `sum(floor(x/i) for i in 1..m)`, capped at `n`.

**Geometric picture:** Draw a hyperbola `i*j = x` in the (i, j) plane. Everything below-left of the hyperbola counts.

**Connection to number theory:**
- This is exactly the **Dirichlet hyperbola method** for counting `{(i,j) : i*j <= x}`.
- The sum `sum_{i=1}^{m} floor(x/i)` has deep connections to the **summatory divisor function** `D(x) = sum_{d|x} 1`.
- For x = 100, this sum = 1 + 2 + 4 + 5 + 10 + 10 + 10 + 10 + 10 + 10 = 72. (Compare: D(100) = 1+2+4+5+10+10+20+25+50+100 = 9, since 100 has 9 divisors.)
- **Euler/Mertens-style asymptotic:** `sum_{i=1}^{m} floor(x/i) ≈ x*log(m) + (2γ-1)*x/2 + O(sqrt(x))`.

**AI/ML connection:**
- **Attention score counts:** The softmax attention matrix in transformers has the same monotone structure.
- **Top-k attention:** Finding the kth highest attention score = finding the kth smallest via binary search.
- **Sparse retrieval:** BM25 inverted indexes use the same count-based approach for kth smallest scores.

### Insight 4: Why Heap Loses to Binary Search

**Heap (Way 5, 13):**
- Time: `O(k log m)`.
- If `k = m*n/2`, this is `O(m*n*log(m))` — too slow.
- Memory: `O(m)` for the heap + visited set.

**Binary Search (Way 1, 20):**
- Time: `O(min(m,n) * log(m*n))`.
- For `m = n = 30000`: `30000 * log(9*10^8) ≈ 30000 * 30 = 9*10^5`.
- For `k = m*n/2 = 4.5*10^8`, heap would be `4.5*10^8 * log(30000) ≈ 7*10^9`. **MASSIVELY worse.**

**Connection to data structures:**
- This is the classic "**selection vs. enumeration**" tradeoff.
- Binary search on value = **selection** (find one specific value).
- Heap = **enumeration** (extract in order).
- Selection is `O(log N * cost(predicate))`, enumeration is `O(K * log N)`.
- When `K << N`: enumeration is fine. When `K ≈ N`: selection wins.

### Insight 5: The Monotonicity Invariant

Why does `count(x)` work? Because the table is **row-wise and column-wise sorted**:
- Within row `i`: values are `i, 2i, 3i, ..., ni` — strictly increasing.
- Within column `j`: values are `j, 2j, 3j, ..., mj` — strictly increasing.

But there's no guarantee that `row[i+1][j] > row[i][j+1]`. So the table is **NOT a "sorted matrix"** in the Search-a-2D-Matrix sense.

**The trick is that we don't need global order — we just need the count of values <= x, which is monotone in x regardless of the global order.**

**Connection to data engineering:**
- **CDFs in pipelines:** Every `percentile_approx()`, `approx_quantile()`, `percentile_cont()` uses a monotone count.
- **Spark DataFrame quantile:** Uses Greenwald-Khanna or t-digest — both use count-based binary search.
- **HyperLogLog / Count-min sketch:** These are *approximations* of the same monotone count function.

### Insight 6: Off-by-One Pitfalls

The binary search invariant is `lo <= answer <= hi`, and we want the **smallest** x with `count(x) >= k`.

If we use `count(x) > k`, we find the **largest** x with `count(x) <= k`, which is wrong.

**Common bugs:**
1. Using `count(mid) > k` instead of `>= k`. → Wrong (finds previous value).
2. Starting `hi = m*n + 1`. → Works but unnecessary.
3. Returning `lo - 1`. → Common confusion. **Return `lo` directly.**

**Test:** `m=3, n=3, k=5`:
- count(1) = 1, count(2) = 3, count(3) = 5, count(4) = 6, count(5) = 6, count(6) = 7, ...
- We want the smallest x with count(x) >= 5. That's x=3. ✓

### Insight 7: When m or n is 1

If `m = 1` or `n = 1`, the table is `1, 2, 3, ..., max(m, n)`. The kth smallest is just `k`. Add a fast path:

```python
if m == 1: return k
if n == 1: return k
```

Saves a logarithmic factor in degenerate cases.

### Insight 8: Symmetry — Why Swap m and n

The count function iterates over rows: `sum(min(mid // i, n) for i in 1..m)`. If `m > n`, swap so we iterate fewer rows. Same logic, fewer operations.

**Connection to cache efficiency:**
- In production code, the difference between iterating 30000 vs 30000 vs 3 vs 30000 is ~3x speedup.
- For very skewed tables (m=30000, n=3), the optimization is huge.

### Insight 9: Why This Problem Tests "Insight" Not "Implementation"

The brute force is straightforward. The binary search on value requires:
1. Recognizing that count is monotone.
2. Computing the count efficiently in O(min(m,n)).
3. Setting up binary search correctly.

This is a **"insight problem"** — the implementation is short, but the *idea* is the hard part. **Interviewers want to see the insight, not just the code.**

**Connection to AI:**
- This is similar to **NP-hard to heuristic** — easy to verify a solution, hard to find the structure.
- **Linear programming:** The dual of an LP is often the easier problem (here, the binary search is the "dual" of the sort).

### Insight 10: Generalization to Other Structures

The same technique works for:

1. **Kth smallest in a sorted matrix** (LC 378): `count_leq(x) = sum(min(x // row_max, n) for each row)`. Same pattern.
2. **Kth smallest pair sum** (LC 719): For value `x`, count pairs `(a, b)` with `a + b <= x` in two sorted arrays. Same pattern.
3. **Kth smallest in two sorted arrays** (LC 4 median variant): `count_leq(x) = count in A + count in B`. Same pattern.
4. **Kth smallest in N sorted arrays**: Generalizes naturally.

**The general pattern:**
```python
def find_kth(predicate, low, high):
    # predicate(x) is monotone: True ... True False ... False
    while low < high:
        mid = (low + high) // 2
        if predicate(mid):
            high = mid
        else:
            low = mid + 1
    return low
```

**This 5-line function solves a huge class of problems.**

---

## 🧪 TEST CASES

| m | n | k | Sorted Table | Answer |
|---|---|---|--------------|--------|
| 3 | 3 | 5 | 1,2,2,**3**,3,4,6,6,9 | 3 |
| 4 | 5 | 8 | 1,2,2,3,3,4,4,4,... | 4 |
| 2 | 3 | 6 | 1,2,2,3,4,**6** | 6 |
| 1 | 1 | 1 | **1** | 1 |
| 1 | 5 | 3 | 1,2,**3**,4,5 | 3 |
| 5 | 1 | 3 | 1,2,**3**,4,5 | 3 |
| 3 | 3 | 1 | **1**,... | 1 |
| 3 | 3 | 9 | 1,2,2,3,3,4,6,6,**9** | 9 |
| 2 | 2 | 1 | **1**,2,2,4 | 1 |
| 2 | 2 | 2 | 1,**2**,2,4 | 2 |
| 2 | 2 | 3 | 1,2,**2**,4 | 2 |
| 2 | 2 | 4 | 1,2,2,**4** | 4 |
| 10 | 10 | 50 | (verifies 24) | 24 |
| 30000 | 30000 | 1 | 1 | 1 |
| 30000 | 30000 | 9*10^8 | 9*10^8 | 9*10^8 |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| Brute force + sort | O(mn log mn) | O(mn) | ❌ TLE |
| Heap expansion | O(k log m) | O(m) | ⚠️ OK if k small |
| **Binary search on value** | **O(min(m,n) log(mn))** | **O(1)** | **✅ BEST** |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Search a 2D Matrix II (LC 240) | Sorted matrix + linear scan | https://leetcode.com/problems/search-a-2d-matrix-ii/ |
| Kth Smallest in Sorted Matrix (LC 378) | **Same binary search on value** | https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/ |
| Find K Pairs with Smallest Sums (LC 373) | Heap | https://leetcode.com/problems/find-k-pairs-with-smallest-sums/ |
| Kth Smallest Pair Sum (LC 719) | Binary search on value | https://leetcode.com/problems/find-k-th-smallest-pair-sum/ |
| Median of Two Sorted Arrays (LC 4) | Binary search on value | https://leetcode.com/problems/median-of-two-sorted-arrays/ |
| Kth Smallest Number in Multiplication Table (LC 668) | **This problem** | https://leetcode.com/problems/kth-smallest-number-in-multiplication-table/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Always ask: "Is there a monotone function I can binary search on?"** for any kth problem.
2. **The count predicate is your friend.** Sum of `min(x // i, n)` is the magic.
3. **Swap m and n** for the smaller iteration count.
4. **Heap is O(k log m), binary search is O(min(m,n) log mn).** When k is large, BS wins.
5. **The 5-line solution is the answer.** Memorize: `if m > n: m, n = n, m; lo, hi = 1, m*n; while lo < hi: mid = (lo+hi)//2; if sum(min(mid//i, n) for i in range(1, m+1)) >= k: hi = mid; else: lo = mid + 1; return lo`.
6. **Pattern: `count(x) >= k` → smallest x with count >= k** (binary search left).
7. **Pattern: `count(x) <= k` → largest x with count <= k** (binary search right).
8. **Test the boundary:** k=1, k=m*n, m=1, n=1.
9. **The Dirichlet hyperbola** connection: this problem is `sum floor(x/i)`, which is the summatory divisor function. A 0.0001% expert sees the number-theoretic depth.
10. **The CDF / quantile / order statistics** connection: this is the algorithmic heart of every quantile algorithm. From Postgres to Spark to ML rank-loss.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Database quantiles** | `percentile_cont()` in SQL uses binary search with monotone count |
| **Streaming quantiles** | t-digest, KLL, Greenwald-Khanna — all binary search on value with count |
| **ML rank loss** | Pairwise loss compares "is prediction above or below the kth label" |
| **Information retrieval** | Top-k BM25 scores = kth smallest in inverted index |
| **Transformer attention** | Top-k attention masks = kth smallest in score matrix |
| **Hyperparameter tuning** | Bayesian opt uses quantile regression (same idea) |
| **A/B testing** | Sequential testing uses "kth largest p-value" = same binary search |
| **Statistics** | Order statistics, M-estimators, quantile regression — all rely on this |
| **Number theory** | Dirichlet divisor problem, summatory divisor function |
| **Computational geometry** | Counting lattice points under hyperbola |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the count function in 60 seconds
- [x] Can code the 5-line solution in 90 seconds
- [x] Know the complexity: O(min(m,n) log(mn)) time, O(1) space
- [x] Can compare binary search vs heap
- [x] Can generalize to other kth problems
- [x] Know the off-by-one pitfalls
- [x] Can discuss the Dirichlet hyperbola connection
- [x] Can discuss the CDF / quantile connection
- [x] Can list 5 AI/data applications of this pattern

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 5.
**Insight:** "Binary search on VALUE, not INDEX, with a monotone count predicate."
