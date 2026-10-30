# Two Sum Less Than K — 0.0001% Expert Guide

> **LeetCode 1099** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/two-sum-less-than-k
> **Problem:** `two_sum_less_than_k(nums, k)` — max sum < k of any two elements.

---

## 📋 WHAT THE QUESTION ASKS

Given `nums[]` and `k`, find the maximum sum of two elements such that `sum < k`. Return `-1` if no such pair exists.

### Constraints
- `1 <= nums.length <= 100`
- `1 <= nums[i] <= 1000`
- `1 <= k <= 2000`

### Examples

```
nums=[34,23,1,24,75,33,54,8], k=60 → 58 (34+24)
nums=[10,20,30], k=15 → -1
nums=[1,2,3], k=6 → 5 (2+3)
```

### Why This Is "Easy"
- Sort + two-pointer is canonical.
- O(n log n) time, O(1) space.
- Standard pattern.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Max sum of two elements where sum < k. Return -1 if impossible."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort + two-pointer:** O(n log n). **Best.**
> 2. **Sort + binary search:** O(n log n).
> 3. **Brute force:** O(n²).
>
> Best: Two-pointer."

### Step 3: KEY INSIGHT — Two-Pointer Logic (5 min)
> "Sort. Two-pointer from both ends.
> - Sum < k: candidate. Try larger lo (increase sum).
> - Sum >= k: too big. Decrease hi."

This works because:
- Increasing lo → larger sum (for fixed hi).
- Decreasing hi → smaller sum (for fixed lo).

### Step 4: Algorithm (5 min)
```
1. Sort nums.
2. lo, hi = 0, n-1. best = -1.
3. While lo < hi:
   - s = a[lo] + a[hi]
   - If s < k: best = max(best, s); lo += 1
   - Else: hi -= 1
4. Return best.
```

### Step 5: Edge Cases (2 min)
- No valid pair: return -1.
- All same: handled.
- Single element: return -1.
- k=2 with nums=[1,1]: 2 not < 2, return -1.

### Step 6: Code It (5 min)

```python
def two_sum_less_than_k(nums, k):
    a = sorted(nums)
    lo, hi = 0, len(a) - 1
    best = -1
    while lo < hi:
        s = a[lo] + a[hi]
        if s < k:
            best = max(best, s)
            lo += 1
        else:
            hi -= 1
    return best
```

### Step 7: Verify (2 min)
For `[34,23,1,24,75,33,54,8], k=60`:
- Sort: [1,8,23,24,33,34,54,75]
- lo=0(1), hi=7(75): 76≥60, hi=6
- lo=0, hi=6(54): 55<60, best=55, lo=1
- lo=1(8), hi=6(54): 62≥60, hi=5(34): 42<60, best=55, lo=2
- lo=2(23), hi=5(34): 57<60, best=57, lo=3
- lo=3(24), hi=5(34): 58<60, best=58, lo=4
- lo=4(33), hi=5(34): 67≥60, hi=4. Exit.
- Return 58. ✓

### Step 8: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Two-pointer:** O(n log n) for sort, O(n) for two-pointer. **Best.**
> 2. **Binary search:** O(n log n) for sort + n binary searches.
> 3. **Brute force:** O(n²).
>
> I'll use two-pointer."

### Step 9: Why Two-Pointer Is Optimal (3 min)
> "Each iteration eliminates one element (lo or hi moves). Total O(n).
> With O(n log n) sort, total O(n log n).
> No extra space needed."

### Step 10: Final Clean Code (5 min)
Memorize the 8-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the max sum of two elements where sum < k.

KEY INSIGHT: Sort + two-pointer. Increase lo for bigger sum (when sum
< k), decrease hi for smaller sum (when sum >= k). Track max valid.

ALGORITHM:
1. Sort nums.
2. lo = 0, hi = n-1, best = -1.
3. While lo < hi:
   - s = a[lo] + a[hi]
   - If s < k: best = max(best, s); lo += 1
   - Else: hi -= 1
4. Return best.

COMPLEXITY: O(n log n) time, O(1) space.

EDGE CASES:
- No valid pair: return -1.
- All same: handled.
- Single element: -1.

THE TRICK:
- Increase lo: sum gets bigger.
- Decrease hi: sum gets smaller.
- We want biggest sum < k, so try biggest first."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + Two-Pointer (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort + 2-ptr (BEST) | O(n log n) | O(1) | **THE ANSWER** |
| 2 | 2-ptr verbose | O(n log n) | O(1) | Educational |
| 9 | Class OOP | O(n log n) | O(1) | Reusable |
| 11 | Numpy | O(n log n) | O(1) | Vectorized |
| 12 | Recursive | O(n log n) | O(1) | Functional |
| 13 | Generator | O(n log n) | O(1) | Pythonic |
| 19 | One-liner | O(n log n) | O(1) | Concise |
| 20 | Final cleanest | O(n log n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Sort + Binary Search

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Sort + BS | O(n log n) | O(1) | Variant |
| 6 | Sort + bisect_right | O(n log n) | O(1) | Variant |
| 14 | Enumerate + BS | O(n log n) | O(1) | Variant |
| 16 | With heap | O(n log n) | O(1) | Variant |
| 17 | Manual BS | O(n log n) | O(1) | Educational |

### 🟣 TIER 3: Brute Force

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Brute force | O(n²) | O(1) | Easy |
| 4 | Brute early term | O(n²) | O(1) | Educational |
| 15 | Itertools | O(n²) | O(1) | Functional |
| 18 | Index tracking | O(n²) | O(1) | Variant |

### ⚪ TIER 4: Hash-Based

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 7 | Hash map | O(n²) | O(n) | Educational |
| 8 | Hash + sort | O(n log n) | O(n) | Variant |
| 10 | Sort desc | O(n²) | O(1) | Educational |

---

## 💎 THE 11-LINE SOLUTION (Memorize!)

```python
def two_sum_less_than_k(nums, k):
    a = sorted(nums)
    lo, hi = 0, len(a) - 1
    best = -1
    while lo < hi:
        s = a[lo] + a[hi]
        if s < k:
            best = max(best, s)
            lo += 1
        else:
            hi -= 1
    return best
```

**Time:** `O(n log n)`
**Space:** `O(1)` extra

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Two-Pointer on Sorted Array

> "Two-pointer exploits sorted structure for O(n) traversal."

After sorting, increasing lo increases sum, decreasing hi decreases sum. This single-pass gives O(n) per query.

**Connection to:**
- **Sliding window:** Same technique.
- **Two-sum II:** Same pattern.
- **Container With Most Water:** Same structure.

### Insight 2: The Movement Logic

> "If sum < k, advance lo (try bigger). Else retreat hi."

This is the OPPOSITE of standard two-sum. For exact sum = k, we'd move based on comparison. Here we want LESS than, so the logic inverts for one branch.

**Connection to:**
- **Comparison-based search:** Branch logic.
- **Decision trees:** Same structure.

### Insight 3: Why Sort Enables Greedy

> Without sort, no way to predict effect of lo/hi movement.

Sorted gives monotonicity: increasing lo strictly increases sum (for fixed hi).

**Connection to:**
- **Monotonicity:** Same prerequisite.
- **Greedy with proof:** Sorted enables greedy.

### Insight 4: Connection to Two Sum Variants

> Two Sum (LC 1): exact sum, hash map.
> Two Sum II (LC 167): exact sum, sorted array, 2-pointer.
> Two Sum Less Than K (LC 1099): max sum < k, sorted, 2-pointer.
> 3Sum (LC 15): exact sum = 0, sorted, 2-pointer nested.

All similar but with different stopping conditions.

**Connection to:**
- **Problem family:** 2-sum variants.
- **Sorting + 2-ptr:** Universal pattern.

### Insight 5: Why "Max Sum < k" Is Different

> For exact sum, we stop when we find it.
> For max < k, we KEEP looking for better.

Greedy: always try larger sum first, retreat when too big.

**Connection to:**
- **Decision vs optimization:** Different goals.
- **Parametric search:** Same structure.

### Insight 6: Amortized O(n) After Sort

> After sort, two-pointer is amortized O(n).

Each element is visited at most once (either by lo moving past or hi moving past it).

**Connection to:**
- **Amortized analysis:** Pay once.
- **Linear sweeps:** Single pass.

### Insight 7: Binary Search Alternative

> For each i, find largest j > i with a[i]+a[j] < k using BS.

Same complexity O(n log n) but different structure.

**Connection to:**
- **Parametric search:** Find threshold.
- **Order statistics:** Rank query.

### Insight 8: Connection to Constraint Satisfaction

> "Find max value satisfying constraint" = optimization.

Two-pointer gives max directly. BS gives each threshold.

**Connection to:**
- **Constraint satisfaction:** Optimization.
- **Lagrangian relaxation:** Duality.

### Insight 9: Why Brute Force Is Acceptable Here

> n ≤ 100. Brute force O(n²) = 10,000 ops. Trivial.

For small inputs, simpler code wins. But for interviews, always present optimal.

**Connection to:**
- **Asymptotic vs constant factors.**
- **Hardware limits:** 10^4 trivial.
- **Premature optimization:** For small n.

### Insight 10: Edge Cases Are Critical

> -1 means "no solution". Must check explicitly.
> Single element: trivially -1.
> Empty: -1.
> k = 0: return -1 (no positive sum < 0).

Edge case handling is half the battle.

**Connection to:**
- **Boundary conditions:** Standard gotcha.
- **Sentinel values:** -1 as no-solution marker.

### Insight 11: Real-World Applications

| Application | Use |
|-------------|-----|
| **Pair matching** | Max pair under constraint |
| **Auction bidding** | Two items under budget |
| **Travel planning** | Two flights under cost |
| **Investment** | Two stocks under capital |
| **Resource pairing** | Sum constraints |
| **Load balancing** | Pair tasks under threshold |

**Travel booking**: find two flights with sum < budget, max total cost.

### Insight 12: Generalization to k-Sum

> "Find max sum of m elements < k" — multi-pointer.

Extends naturally with m pointers, or recursion with pruning.

**Connection to:**
- **Multi-pointer:** Recursive structure.
- **Constraint satisfaction:** General.

---

## 🧪 TEST CASES

| `nums` | `k` | Expected | Note |
|--------|-----|----------|------|
| `[34,23,1,24,75,33,54,8]` | 60 | 58 | Standard |
| `[10,20,30]` | 15 | -1 | No valid |
| `[1,2,3]` | 6 | 5 | 2+3 |
| `[1,2,3]` | 5 | 4 | 1+3 |
| `[1,2,3]` | 100 | 5 | All valid |
| `[5,5,5]` | 10 | -1 | 10 not <10 |
| `[5,5,5]` | 11 | 10 | 5+5 |
| `[1]` | 5 | -1 | Single |
| `[1,2]` | 5 | 3 | 1+2 |
| `[1,2]` | 3 | -1 | 3 not <3 |
| `[1,2,3,4,5]` | 9 | 8 | 3+5 |
| `[1,2,3,4,5]` | 8 | 7 | 3+4 |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Two-pointer** | **O(n log n)** | **O(1)** | **✅ BEST** |
| Sort + BS | O(n log n) | O(1) | ✅ Alternative |
| Brute force | O(n²) | O(1) | ✅ Easy |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Two Sum (LC 1) | Hash map | https://leetcode.com/problems/two-sum/ |
| Two Sum II (LC 167) | 2-ptr sorted | https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/ |
| 3Sum (LC 15) | Sort + 2-ptr | https://leetcode.com/problems/3sum/ |
| Container With Most Water (LC 11) | 2-ptr | https://leetcode.com/problems/container-with-most-water/ |
| Two Sum < K (LC 1099) | **This problem** | https://leetcode.com/problems/two-sum-less-than-k/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Sort + two-pointer** is THE pattern.
2. **Move lo for bigger sum, hi for smaller.** Critical.
3. **Track max valid sum.**
4. **Return -1 if no valid pair.**
5. **O(n log n) time, O(1) space.**
6. **Amortized O(n) per query** after sort.
7. **Binary search alternative** gives same complexity.
8. **Brute force acceptable** for n ≤ 100.
9. **Edge cases: empty, single, no valid.**
10. **Used in auctions, bidding, travel.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Pair matching** | Max pair under constraint |
| **Auction bidding** | Two items under budget |
| **Travel planning** | Two flights under cost |
| **Investment** | Two stocks under capital |
| **Constraint optimization** | Maximize value |
| **Multi-pointer** | Recursive extension |
| **Order statistics** | Binary search |
| **Greedy with proof** | Exchange argument |
| **Combinatorial** | Pair selection |
| **Real-world pairing** | Sum constraints |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive two-pointer logic in 60 seconds
- [x] Can code the 11-line solution in 60 seconds
- [x] Know the complexity: O(n log n) time, O(1) space
- [x] Know why increase lo / decrease hi
- [x] Know the max tracking
- [x] Know edge case: return -1 if no valid
- [x] Can compare with brute force and BS
- [x] Know related problems (2 Sum, 3 Sum)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 11.
**Insight:** "Sort. Two-pointer: if sum < k, lo++ (try bigger); else hi--. Track max valid sum."
