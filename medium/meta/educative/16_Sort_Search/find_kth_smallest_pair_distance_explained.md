# Find K-th Smallest Pair Distance — 0.0001% Expert Guide

> **LeetCode 719** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-th-smallest-pair-distance
> **Problem:** `smallest_distance_pair(nums, k)` — find k-th smallest pair distance.

---

## 📋 WHAT THE QUESTION ASKS

Given an integer array `nums` and integer `k`, return the **k-th smallest** distance among all pairs `(nums[i], nums[j])` where `i < j`. Distance = `|nums[i] - nums[j]|`.

### Constraints
- `2 <= n <= 10^4`
- `0 <= nums[i] <= 10^6`
- `1 <= k <= n*(n-1)/2`

### Examples

```
nums=[1,3,1], k=1 → 0  (pair (1,1) at indices 0,2)
nums=[1,3,1], k=2 → 2  (next smallest pair distance)
nums=[1,6,1], k=3 → 5
nums=[1,2,3,4,5]:
  pairs: 1-2, 1-3, 1-4, 1-5, 2-3, 2-4, 2-5, 3-4, 3-5, 4-5
  distances: 1, 2, 3, 4, 1, 2, 3, 1, 2, 1
  sorted: 1,1,1,1,2,2,2,3,3,4
  k=1: 1, k=4: 1, k=5: 2, k=10: 4
```

### Why This Is "Hard"
- Naive O(n²) generation is too slow.
- Binary search on distance + two-pointer count is the trick.
- Monotonicity insight is the key.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find k-th smallest among all O(n²) pair distances."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Binary search on distance + two-pointer count:** O(n log n). **Best.**
> 2. **Generate all pairs + sort:** O(n² log n²) = O(n² log n).
> 3. **Heap-based:** O(n log k). More complex.
>
> Best: Binary search."

### Step 3: KEY INSIGHT — Monotonicity (5 min)
> "For a given distance d, let f(d) = count of pairs with distance <= d.
> f(d) is MONOTONICALLY NON-DECREASING in d.
> 
> Why? As d grows, more pairs satisfy the condition.
> 
> This means: smallest d with f(d) >= k is the answer."

### Step 4: Counting Pairs Efficiently (5 min)
> "Sort nums first. After sorting, for j > i: |a[j] - a[i]| = a[j] - a[i].
> 
> count_le(d): use TWO-POINTER.
> - left starts at 0.
> - For each right, advance left while a[right] - a[left] > d.
> - After advancing, count += right - left (all pairs from left to right have distance <= d).
> 
> This is O(n) per query."

### Step 5: Binary Search (5 min)
```
lo, hi = 0, a[-1] - a[0]
while lo < hi:
    mid = (lo + hi) // 2
    if count_le(mid) < k:
        lo = mid + 1   # too small
    else:
        hi = mid       # candidate
return lo
```

### Step 6: Edge Cases (2 min)
- All same: distance is 0.
- k=1: smallest.
- k=n(n-1)/2: largest (max-min).

### Step 7: Code It (5 min)

```python
def smallest_distance_pair(nums, k):
    a = sorted(nums)
    n = len(a)

    def count_le(d):
        count = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            count += right - left
        return count

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

### Step 8: Verify (2 min)
For `[1,3,1], k=2`:
- sorted=[1,1,3], max-min=2.
- BS: lo=0, hi=2. mid=1, count_le(1)=2 (pairs (0,1)=0 and (0,2)=2... wait).
- Actually pairs in [1,1,3] with distance <=1:
  - (1,1) at indices 0,1: dist=0 <=1 ✓
  - (1,1) at indices 0,2: dist=2 >1 ✗
  - (1,3) at indices 1,2: dist=2 >1 ✗
  - count_le(1) = 1. < 2, so lo=2.
- lo=2, hi=2. Return 2. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **BS + count:** O(n log n). **Best.**
> 2. **Brute force + sort:** O(n² log n).
> 3. **Heap:** O(n log k). For specific k.
>
> BS is optimal for general k."

### Step 10: Final Clean Code (5 min)
Memorize the 12-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the k-th smallest distance among all pairs in nums.

KEY INSIGHT: For any distance d, the count of pairs with distance <= d
is MONOTONICALLY NON-DECREASING in d. So I can BINARY SEARCH on d.

ALGORITHM:
1. Sort nums.
2. Binary search on d in [0, max-min]:
   - For each d, count pairs with distance <= d using two-pointer.
   - Two-pointer: for each right, advance left while a[right]-a[left] > d.
   - Count += right - left.
3. Find smallest d with count >= k.

COMPLEXITY: O(n log n) sort + O(log(max)) BS, each iteration O(n).
Total: O(n log n). Space: O(1) extra.

EDGE CASES:
- All same elements: answer is 0.
- k=1: smallest distance.
- k=n(n-1)/2: largest distance.

THE TRICK: Binary search on DISTANCE, count with two-pointer.
Monotonicity of f(d) is the foundation."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Binary Search on Distance (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | BS + two-pointer (BEST) | O(n log n) | O(1) | **THE ANSWER** |
| 2 | BS + bisect_right | O(n log n) | O(1) | Pythonic |
| 6 | BS verbose | O(n log n) | O(1) | Readable |
| 8 | BS inline | O(n log n) | O(1) | Variant |
| 9 | BS + bisect | O(n log n) | O(1) | Variant |
| 10 | Class OOP | O(n log n) | O(1) | Reusable |
| 11 | BS + mid safety | O(n log n) | O(1) | Educational |
| 12 | Recursive BS | O(n log n) | O(log) | Functional |
| 13 | Numpy | O(n log n) | O(n) | Vectorized |
| 14 | BS + cumulative | O(n log n) | O(1) | Variant |
| 16 | BS + idx subtract | O(n log n) | O(1) | Variant |
| 18 | BS + early term | O(n log n) | O(1) | Optimized |
| 19 | Most concise | O(n log n) | O(1) | One-liner |
| 20 | Final cleanest | O(n log n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Generate & Sort

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Brute force pairs | O(n² log n) | O(n²) | Easy |
| 5 | Two-ptr enumerate | O(n² log n) | O(n²) | Variant |
| 15 | Tuple enumerate | O(n² log n) | O(n²) | Variant |
| 17 | Set dedup | O(n² log n) | O(n²) | Educational |

### 🟣 TIER 3: Heap-Based

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Heap-based | O(n log k) | O(n) | Specific k |
| 7 | For each d | O(n * max) | O(1) | Variant |

---

## 💎 THE 12-LINE SOLUTION (Memorize!)

```python
def smallest_distance_pair(nums, k):
    a = sorted(nums)
    n = len(a)

    def count_le(d):
        count = 0
        left = 0
        for right in range(n):
            while a[right] - a[left] > d:
                left += 1
            count += right - left
        return count

    lo, hi = 0, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) < k:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

**Time:** `O(n log n)`
**Space:** `O(1)` extra (after sort)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Sort + Two-Pointer = Pair Counter

> After sorting, two-pointer efficiently counts pairs in O(n) for a given difference.

The two-pointer trick: for each right, advance left while difference > threshold. Then count pairs (left, left+1, ..., right-1) all have difference <= threshold.

**Connection to:**
- **Sliding window:** Same structure.
- **Counting inversions:** Two-pointer.
- **Two-sum variants:** Pre-sort + binary search.

### Insight 2: Binary Search on the Answer

> The answer (k-th smallest distance) is monotonic in some parameter.

Specifically: f(d) = "pairs with distance <= d" is monotonic. Binary search finds smallest d with f(d) >= k.

**Connection to:**
- **Parametric search:** Same pattern as Koko Bananas.
- **Decision problems:** "Can we achieve ≤ k?" monotonic.
- **Threshold algorithms:** Find threshold.

### Insight 3: Why Two-Pointer Works on Sorted Array

> After sorting, the property "|a[j] - a[i]| = a[j] - a[i] for j > i" simplifies counting.

For unsorted, we'd need absolute values and more complex logic. Sorting converts absolute to subtraction.

**Connection to:**
- **Order statistics:** Sort enables rank queries.
- **Convex hull:** Sort by angle.
- **Sweep line:** Sort by x-coordinate.

### Insight 4: The Space-Saving Insight

> Two-pointer counts pairs in O(1) extra space.

We don't store pairs explicitly. We just count as we go. This avoids O(n²) memory.

**Connection to:**
- **Streaming algorithms:** Constant memory.
- **Online algorithms:** Process as you go.
- **Memory hierarchy:** Cache-friendly.

### Insight 5: Comparison to Heap Approach

> Heap gives O(n log k) but only for SMALL k. For large k, BS is better.

Heap starts with smallest distances and pops k times. O(n log k).
BS is O(n log n) regardless of k.

For k near n², BS is way faster.

**Connection to:**
- **Selection algorithms:** Quickselect vs heap.
- **Order statistics:** Different algorithms for different sizes.
- **Top-k problems:** Heap vs sort.

### Insight 6: Connection to Kth Smallest in Sorted Matrix

> LC 378 (Kth Smallest in Sorted Matrix) uses similar stair-search idea.

Both use monotonicity of count to binary search.

**Connection to:**
- **Search in 2D:** Stair search.
- **Median finding:** Quickselect.
- **Selection algorithms:** Multiple approaches.

### Insight 7: Why This Pattern Generalizes

> "Count + Binary search" is a foundational algorithm.

Many problems:
- Koko Eating Bananas (LC 875)
- Capacity to Ship (LC 1011)
- Smallest Divisor (LC 1283)
- Min Speed to Arrive (LC 1870)
- This problem (LC 719)

All share: parameterize, count, binary search.

**Connection to:**
- **Parametric search:** General paradigm.
- **Decision problems:** Reduction to counting.
- **Optimization:** Decision → optimization.

### Insight 8: Complexity Analysis Deep Dive

> Why is f(d) O(n) per query?

Two-pointer: right goes from 0 to n, left goes from 0 to n at most. Total O(n).

**Connection to:**
- **Amortized analysis:** Each pointer moves at most n times.
- **Sliding window:** O(n) per query.
- **Counting inversions:** Same trick.

### Insight 9: Connection to Order Statistics

> "k-th smallest" is the ORDER STATISTIC.

For 1D sorted, it's O(1). For pairs (2D), it's the k-th in a sorted 2D structure (sorted by distance).

This is the 2D version of order statistics.

**Connection to:**
- **Order statistics trees:** O(log n) rank queries.
- **Quickselect:** O(n) average.
- **Median of medians:** O(n) worst case.

### Insight 10: Why "Distance" vs "Value"

> We search on DISTANCE (a derived quantity), not on the array values.

The search space is `[0, max - min]`, derived from the data. Different from "find k-th smallest element" which searches on indices.

**Connection to:**
- **Derived quantities:** Search on transformations.
- **Distributions:** Distance metrics.
- **Geometric search:** Distance-based queries.

### Insight 11: Real-World Applications

| Application | Use |
|-------------|-----|
| **Clustering** | K-th nearest neighbor distance |
| **Anomaly detection** | Find unusual pair distances |
| **Genomics** | SNP distance percentile |
| **Image processing** | Patch similarity |
| **Network analysis** | Latency percentiles |
| **Recommender systems** | User similarity ranking |
| **Geospatial** | Distance queries |

**Clustering** algorithms use k-th nearest distance to determine cluster boundaries.

### Insight 12: The Mathematical Beauty

> This problem = BINARY SEARCH on a MONOTONIC COUNT function.

The structure: f(d) monotonic → invert via BS.

This pattern recurs in: probability (CDF inverse), statistics (quantile), and optimization (Lagrangian).

**Connection to:**
- **Inverse function theorem:** Monotonic → invertible.
- **CDF inversion:** Same structure.
- **Lagrangian duality:** Decision + dual.

---

## 🧪 TEST CASES

| `nums` | `k` | Expected | Note |
|--------|-----|----------|------|
| `[1,3,1]` | 1 | 0 | Pair (1,1) |
| `[1,3,1]` | 2 | 2 | Pair (1,3) |
| `[1,3,1]` | 3 | 2 | Pair (1,3) |
| `[1,6,1]` | 3 | 5 | 3 pairs: 0, 5, 5 |
| `[1,1,1]` | 1 | 0 | All same |
| `[1,1,1]` | 3 | 0 | All 3 pairs |
| `[1,2,3,4,5]` | 1 | 1 | Adjacent pair |
| `[1,2,3,4,5]` | 4 | 1 | Adjacent |
| `[1,2,3,4,5]` | 5 | 2 | 2-apart |
| `[1,2,3,4,5]` | 10 | 4 | Max |
| `[9,10,7,10,6]` | 1 | 0 | 10-10 pair |
| `[9,10,7,10,6]` | 5 | 2 | Middle |
| `[9,10,7,10,6]` | 10 | 4 | Max |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **BS + count** | **O(n log n)** | **O(1)** | **✅ BEST** |
| Brute force + sort | O(n² log n) | O(n²) | ✅ Easy |
| Heap | O(n log k) | O(n) | ✅ For small k |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Kth Smallest in Sorted Matrix (LC 378) | BS + count | https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/ |
| Koko Eating Bananas (LC 875) | BS on speed | https://leetcode.com/problems/koko-eating-bananas/ |
| Capacity To Ship (LC 1011) | BS on capacity | https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/ |
| Smallest Divisor (LC 1283) | BS on divisor | https://leetcode.com/problems/find-the-smallest-divisor-given-a-threshold/ |
| K-th Pair Distance (LC 719) | **This problem** | https://leetcode.com/problems/find-k-th-smallest-pair-distance/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Binary search on distance** — find smallest d with f(d) >= k.
2. **Sort + two-pointer** counts pairs with distance <= d in O(n).
3. **f(d) is monotonic** — foundation of the algorithm.
4. **O(n log n) total** — beats brute force O(n² log n).
5. **Heap alternative** — O(n log k) for small k.
6. **Two-pointer advance left** as right increases — amortized O(n).
7. **Sort converts absolute to subtraction** for j > i.
8. **Generalizes to many "BS + count" problems.**
9. **Edge case: all same** → 0.
10. **Used in clustering, anomaly detection, genomics.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Clustering** | K-th nearest neighbor |
| **Anomaly detection** | Unusual pair distances |
| **Genomics** | SNP distance percentile |
| **Order statistics** | 2D version |
| **Streaming algorithms** | Constant memory |
| **Parametric search** | Binary search on parameters |
| **Probability** | CDF inversion |
| **Quantile estimation** | P² algorithm, t-digest |
| **Recommender systems** | Similarity ranking |
| **Geospatial queries** | Distance queries |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive monotonicity in 60 seconds
- [x] Can code the 12-line solution in 90 seconds
- [x] Know the complexity: O(n log n) time, O(1) space
- [x] Know why two-pointer works after sorting
- [x] Know the count_le function
- [x] Can compare with brute force and heap
- [x] Know related problems (Koko, Ship, Divisor)
- [x] Can list 5 real-world applications
- [x] Can generalize to "BS + count" paradigm

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 20 minutes.
**Lines of code to write:** 12.
**Insight:** "Sort. Binary search on distance d. For each d, count pairs with distance <= d using two-pointer. f(d) monotonic in d, so BS works."
