# Valid Triangle Number — 0.0001% Expert Guide

> **LeetCode 611** | **Difficulty:** Medium | **Avg Solve Time:** 25 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/valid-triangle-number
> **Problem:** `triangle_number(nums)` — count triplets that can form a valid triangle.

---

## 📋 WHAT THE QUESTION ASKS

Given integer array `nums`, return the number of triplets `(i, j, k)` with `i < j < k` that can form a valid triangle. Three sides form a triangle iff the **triangle inequality** holds: for sorted `a ≤ b ≤ c`, we need `a + b > c` (the other two are automatic).

### Constraints
- `1 <= nums.length <= 1000`
- `0 <= nums[i] <= 1000`

### Examples

```
nums=[2,2,3,4] → 3
  Triplets: (2,2,3), (2,3,4), (2,2,4)

nums=[4,2,3,4] → 4
  Sort: [2,3,4,4]
  (2,3,4), (2,3,4), (2,4,4), (3,4,4)

nums=[0,1,1,1] → 1
  Only (1,1,1) is valid; (0,1,1) needs 0+1>1 = false

nums=[3,3,4,4,5,5] → 20
  All 6C3=20 triplets satisfy 3+3>5
```

### Why This Is "Medium"
- Two-pointer after sort is the canonical approach.
- O(n²) after O(n log n) sort.
- The "count += hi - lo" trick requires careful insight.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Count triplets forming a valid triangle. After sorting a ≤ b ≤ c, only need a + b > c."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort + two-pointer:** O(n²). **Best.**
> 2. **Sort + binary search:** O(n² log n).
> 3. **Brute force:** O(n³).
>
> Best: Sort + two-pointer."

### Step 3: KEY INSIGHT — The "count += hi - lo" Trick (5 min)
> "After sorting, fix `c = a[i]`. Use two-pointer `(lo, hi)` to find pairs with `a[lo] + a[hi] > c`.
>
> When `a[lo] + a[hi] > c`:
> - Increasing `lo` makes sum BIGGER (since array is sorted).
> - So ALL pairs `(lo, hi), (lo+1, hi), ..., (hi-1, hi)` are valid.
> - That's `hi - lo` pairs.
> - Decrement `hi` to try smaller sums."

### Step 4: Why Decrement hi (Not lo) (3 min)
> "When `a[lo] + a[hi] > c`, we found `hi - lo` valid pairs. To find MORE, we need smaller sums → decrement `hi`.
> When `a[lo] + a[hi] <= c`, sum is too small → increment `lo`."

### Step 5: Algorithm (5 min)
```
1. Sort nums.
2. count = 0.
3. For i from 2 to n-1 (longest side c = a[i]):
   - lo = 0, hi = i - 1.
   - While lo < hi:
     - If a[lo] + a[hi] > a[i]: count += hi - lo; hi -= 1
     - Else: lo += 1
4. Return count.
```

### Step 6: Edge Cases (2 min)
- All zeros: return 0 (0+0 not > 0).
- Single/two elements: return 0.
- All same positive: C(n, 3) (all valid).
- Mix of zeros: only zeros won't form triangles.

### Step 7: Code It (5 min)

```python
def triangle_number(nums):
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count
```

### Step 8: Verify (2 min)
For `[2,2,3,4]` (sorted same):
- i=2 (c=3): lo=0, hi=1. 2+2=4>3 ✓, count += 1, hi=0. Exit. count=1.
- i=3 (c=4): lo=0, hi=2. 2+3=5>4 ✓, count += 2, hi=1. 2+2=4 not >4, lo=1. Exit. count=3.
- Return 3. ✓

For `[4,2,3,4]` (sorted=[2,3,4,4]):
- i=2 (c=4): lo=0, hi=1. 2+3=5>4 ✓, count += 1, hi=0. Exit. count=1.
- i=3 (c=4): lo=0, hi=2. 2+4=6>4 ✓, count += 2, hi=1. 2+3=5>4 ✓, count += 1, hi=0. Exit. count=4.
- Return 4. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Two-pointer:** O(n²). **Best.**
> 2. **Binary search:** O(n² log n).
> 3. **Brute force:** O(n³).
>
> I'll use two-pointer."

### Step 10: Why Two-Pointer Is Optimal (3 min)
> "For each i, we process pairs in O(i) with two-pointer. Total: sum over i of O(i) = O(n²). Binary search adds log factor. Brute is O(n³)."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count triplets forming a valid triangle. After sorting
sides a <= b <= c, the only check needed is a + b > c.

KEY INSIGHT: Sort the array. For each i (longest side c = a[i]),
use two-pointer to count pairs (lo, hi) with a[lo] + a[hi] > c.

When a[lo] + a[hi] > c, increasing lo makes the sum BIGGER
(since array is sorted), so ALL pairs (lo, hi), (lo+1, hi), ...,
(hi-1, hi) are valid. That's hi - lo pairs. So count += hi - lo
and decrement hi.

ALGORITHM:
1. Sort nums.
2. count = 0.
3. For i from 2 to n-1:
   - lo = 0, hi = i - 1.
   - While lo < hi:
     - If a[lo] + a[hi] > a[i]: count += hi - lo; hi -= 1
     - Else: lo += 1
4. Return count.

COMPLEXITY: O(n²) time, O(1) space.

EDGE CASES:
- All zeros: 0 (0+0 not > 0).
- n < 3: 0.
- All same positive: C(n, 3).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + Two-Pointer (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort + 2-ptr (BEST) | O(n²) | O(1) | **THE ANSWER** |
| 2 | 2-ptr verbose | O(n²) | O(1) | Educational |
| 8 | Helper fn | O(n²) | O(1) | Reusable |
| 9 | Recursive | O(n²) | O(1) | Functional |
| 10 | Class OOP | O(n²) | O(1) | Reusable |
| 14 | One-liner | O(n²) | O(1) | Concise |
| 16 | Reverse 2-ptr | O(n²) | O(1) | Educational |
| 17 | Early break | O(n²) | O(1) | Educational |
| 18 | Generator | O(n²) | O(1) | Pythonic |
| 19 | LRU cache | O(n²) | O(1) | Memoized |
| 20 | Final cleanest | O(n²) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Sort + Binary Search

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Sort + bisect_left | O(n² log n) | O(1) | Variant |
| 6 | Sort + bisect_right | O(n² log n) | O(1) | Variant |
| 7 | Fix largest + iterate k | O(n² log n) | O(1) | Variant |
| 13 | Manual BS | O(n² log n) | O(1) | Educational |

### 🟣 TIER 3: Brute Force

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | All triplets | O(n³) | O(1) | Easy |
| 4 | Brute sorted | O(n³) | O(1) | Educational |
| 11 | Itertools | O(n³) | O(1) | Functional |
| 15 | Counter/hashing | O(n³) | O(n) | Edge case |

### ⚪ TIER 4: Vectorized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 12 | Numpy | O(n² log n) | O(n) | Vectorized |

---

## 💎 THE 11-LINE SOLUTION (Memorize!)

```python
def triangle_number(nums):
    a = sorted(nums)
    n = len(a)
    count = 0
    for i in range(2, n):
        lo, hi = 0, i - 1
        while lo < hi:
            if a[lo] + a[hi] > a[i]:
                count += hi - lo
                hi -= 1
            else:
                lo += 1
    return count
```

**Time:** `O(n²)`
**Space:** `O(1)` extra (after sort)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Triangle Inequality Reduces to One Check

> For sorted a ≤ b ≤ c, a + b > c implies b + c > a AND a + c > b.

The triangle inequality has 3 conditions, but sorting means only ONE matters (the sum of the two shortest must exceed the longest).

**Connection to:**
- **Mathematical optimization:** Reduce 3 checks to 1.
- **Preprocessing:** Sort first.
- **Symmetry breaking:** Canonical form.

### Insight 2: The "count += hi - lo" Trick

> When a[lo] + a[hi] > c, ALL pairs (lo, hi), (lo+1, hi), ..., (hi-1, hi) work.

This is the magic. Array is sorted, so increasing lo only INCREASES a[lo]. Thus sum only grows. We count all valid pairs in O(1) per "successful" iteration.

**Connection to:**
- **Monotonicity exploitation:** Sorted enables counting.
- **Patience sort:** Same idea (count piles).
- **Range counting:** Bulk operations.

### Insight 3: Why Decrement hi, Not lo

> When we find a valid pair, we want to find more pairs, so DECREASE hi.

If we incremented lo instead, we'd move past a[lo] (which is small). The current a[lo] paired with current a[hi] works, but what about smaller a[lo']? We'd miss them. Decrementing hi keeps the "small" partner and tries smaller "large" partner.

**Connection to:**
- **Decision logic:** Opposite intuition.
- **Greedy: keep best, find more.**

### Insight 4: Amortized O(n) Per Iteration

> For each i, the two-pointer does O(i) work.

Sum of i from 2 to n-1 is O(n²). The pointer movement is amortized O(i) per i.

**Connection to:**
- **Amortized analysis:** Total cost analysis.
- **Loop invariants:** Each pass is O(i).

### Insight 5: Connection to 3Sum Smaller

> Same exact algorithm structure as LC 259 (3Sum Smaller).

LC 259: count triplets with a + b + c < target. Same trick: count += hi - lo when valid.

**Connection to:**
- **Problem family:** Triangle, 3Sum Smaller.
- **Universal pattern:** "Count with constraint."

### Insight 6: Connection to Container With Most Water

> Both use two-pointer on sorted array, decrementing when condition met.

**Connection to:**
- **Two-pointer:** Universal pattern.
- **Greedy:** Same structure.

### Insight 7: Why Not Hash Map?

> Two-pointer is better than hash map for this problem.

Hash map works for exact match (Two Sum, sum = k), but for "max/min sum < > value" we need ordering, which sort provides.

**Connection to:**
- **Hash vs sort:** Different problem types.
- **Ordering matters:** Sort enables monotonicity.

### Insight 8: Binary Search Alternative

> For each (i, j), find largest k > j with a[k] < a[i] + a[j].

O(n² log n). Two-pointer is O(n²). Same complexity in practice but BS is more general.

**Connection to:**
- **Parametric search:** Find threshold.
- **Range counting:** O(log n) per query.

### Insight 9: Why "Strict Inequality" Matters

> Triangle inequality is STRICT: a + b > c (not >=).

If non-strict (>=), we'd have a degenerate triangle (collinear). For strict count, decrement hi only when > not >=.

**Connection to:**
- **Strict vs non-strict:** Standard gotcha.
- **Geometry:** Degenerate vs proper.

### Insight 10: Real-World Applications

| Application | Use |
|-------------|-----|
| **Network design** | Triangle inequalities in routing |
| **GPS navigation** | Triangle inequality for distances |
| **Machine learning** | Triplet loss in embedding learning |
| **Computer graphics** | Triangle meshes |
| **Surveying** | Land measurement |
| **Finance** | Triangular arbitrage |

**ML triplet loss** is a huge application: anchor, positive, negative triplets in metric learning.

### Insight 11: ML Connection — Triplet Loss

> FaceNet, metric learning: anchor A, positive P, negative N. Want ||A-P|| < ||A-N||.

This is exactly the triangle inequality! Train embeddings where valid triplets push apart, invalid pull together.

**Connection to:**
- **Deep learning:** Embedding learning.
- **Metric learning:** Distance learning.
- **Computer vision:** Face recognition.

### Insight 12: Connection to Dilworth's Theorem

> Counting valid triangles = counting chains in a partial order.

The (a, b, c) triangle relation forms a partial order. Counting valid chains is related to Dilworth.

**Connection to:**
- **Order theory:** Partial orders.
- **Combinatorics:** Chain counting.

### Insight 13: Generalization to k-Sided Polygons

> Count k-tuples forming a valid k-gon (sum of k-1 sides > largest).

Extends recursively: fix largest, recurse on k-1.

**Connection to:**
- **Recursive structure:** Generalization.
- **Multi-dimensional:** Polygon inequality.

### Insight 14: The "Sort Once" Insight

> We sort ONCE, then two-pointer works because the sort is preserved.

If we needed to maintain order, we'd need a different approach. Sorting is destructive but enables monotonicity.

**Connection to:**
- **Preprocessing trade-off:** Sort cost vs query speed.
- **Cache-friendly:** Sequential access.

---

## 🧪 TEST CASES

| `nums` | Expected | Note |
|--------|----------|------|
| `[2,2,3,4]` | 3 | Standard |
| `[4,2,3,4]` | 4 | Two 4s |
| `[0,0,0]` | 0 | All zero, no valid |
| `[1,1,1]` | 1 | All same |
| `[1,2,3]` | 0 | 1+2 not > 3 |
| `[2,2,2]` | 1 | Triangle |
| `[3,4,5]` | 1 | Pythagorean |
| `[1]` | 0 | Single element |
| `[1,2]` | 0 | Two elements |
| `[1,2,3,4,5]` | 3 | (2,3,4),(2,4,5),(3,4,5) |
| `[3,3,4,4,5,5]` | 20 | All 6C3 valid |
| `[0,1,1,1]` | 1 | Only (1,1,1) |
| `[2,2,2,2]` | 4 | All 4C3 valid |
| `[5,5,5,5,5]` | 10 | All 5C3 valid |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Two-pointer** | **O(n²)** | **O(1)** | **✅ BEST** |
| Sort + BS | O(n² log n) | O(1) | ✅ Alternative |
| Brute force | O(n³) | O(1) | ✅ Easy |
| Numpy vectorized | O(n²) | O(n) | ✅ Fast constant |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| 3Sum (LC 15) | Sort + 2-ptr | https://leetcode.com/problems/3sum/ |
| 3Sum Smaller (LC 259) | Sort + 2-ptr | https://leetcode.com/problems/3sum-smaller/ |
| Container With Most Water (LC 11) | 2-ptr | https://leetcode.com/problems/container-with-most-water/ |
| Two Sum II (LC 167) | 2-ptr | https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/ |
| Valid Triangle Number (LC 611) | **This problem** | https://leetcode.com/problems/valid-triangle-number/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Sort + two-pointer** is THE pattern.
2. **count += hi - lo** is the magic trick.
3. **Sort + decrement hi** when valid.
4. **Strict inequality** matters (use `>`, not `>=`).
5. **O(n²)** dominates after sort.
6. **ML triplet loss** uses this structure.
7. **Network design** uses triangle inequality.
8. **3Sum Smaller (LC 259)** uses identical algorithm.
9. **Brute force O(n³)** acceptable for tiny n.
10. **Generator, itertools, numpy** all valid variants.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Triplet loss in ML** | Anchor/positive/negative embeddings |
| **Network routing** | Triangle inequality in metrics |
| **GPS / distance matrices** | Triangle inequality |
| **Computer graphics** | Triangle meshes, normals |
| **Graph algorithms** | Triangle counting |
| **Constraint satisfaction** | Geometric validity |
| **Vector databases** | Similarity triangles |
| **Recommendation systems** | Triplet ranking |
| **Conversational AI** | Embedding geometry |
| **Robotics** | Path planning with triangle constraints |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive two-pointer logic in 60 seconds
- [x] Can code the 11-line solution in 60 seconds
- [x] Know the complexity: O(n²) time, O(1) space
- [x] Know why count += hi - lo (monotonicity)
- [x] Know why decrement hi (find more pairs)
- [x] Know edge cases (zeros, n < 3, all same)
- [x] Can compare with BS and brute force
- [x] Know related problems (3Sum Smaller, Container)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 11.
**Insight:** "Sort. For each i as longest side, two-pointer: if a[lo]+a[hi]>a[i], count += hi - lo and decrement hi (since all pairs lo..hi-1 with hi work due to sorted order)."
