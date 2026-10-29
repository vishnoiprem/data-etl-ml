# Magnetic Force Between Two Balls — 0.0001% Expert Guide

> **LeetCode 1552** | **Difficulty:** Medium | **Avg Solve Time:** 25 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/magnetic-force-between-two-balls
> **Problem:** `max_distance(position, m)` — maximize the minimum gap when placing m balls.

---

## 📋 WHAT THE QUESTION ASKS

Given `position[]` (basket positions) and `m` balls, place all `m` balls in baskets such that the **minimum** distance between any two balls is **maximized**. Return that maximum.

### Constraints
- `2 <= position.length <= 10^5`
- `2 <= m <= position.length`
- `0 <= position[i] <= 10^9`

### Examples

```
position=[1,2,3,4,7], m=3 → 3
  Place at 1, 4, 7. Min gap = 3.

position=[5,4,3,2,1,1000000000], m=2 → 999999999
  Place at 1 and 10^9.

position=[79,74,57,22], m=4 → 5
  Sorted: [22,57,74,79]. All 4 balls fit with gap 5.
```

### Why This Is "Medium"
- Binary search on answer + greedy check.
- O(n log(max_position)).
- The "Aggressive Cows" classic.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Maximize the minimum distance when placing m balls in sorted baskets."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort + BS on distance + greedy:** O(n log M). **Best.**
> 2. **Brute force:** try all d. Slow.
> 3. **DP:** overkill.
>
> Best: BS on distance."

### Step 3: KEY INSIGHT — Monotonic Feasibility (5 min)
> "For a candidate distance d, can we place m balls with min gap d?
> 
> Feasibility is MONOTONIC: if d works, d-1 works.
> 
> Why? Smaller gap = easier to fit more balls.
> 
> So binary search works on d."

### Step 4: Greedy Is Optimal (3 min)
> "For fixed d, GREEDY placement is optimal: place ball at first basket, then next ball at first basket ≥ last + d.
>
> Proof: greedy minimizes the position of the k-th ball, leaving more room for subsequent balls."

### Step 5: Algorithm (5 min)
```
1. Sort positions.
2. lo = 1, hi = max - min.
3. While lo < hi:
   - mid = (lo + hi + 1) // 2 (upper mid).
   - Greedy place: count = 1, last = a[0].
     For x in a[1:]: if x - last >= mid: count++, last = x.
   - If count >= m: lo = mid (feasible, try larger).
   - Else: hi = mid - 1 (infeasible).
4. Return lo.
```

### Step 6: Edge Cases (2 min)
- m = 2: just need max - min.
- m = n: min gap is min of consecutive diffs.
- All same: 0.
- Two baskets only: diff.

### Step 7: Code It (5 min)

```python
def max_distance(position, m):
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                if count >= m:
                    return True
                last = a[i]
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
```

### Step 8: Verify (2 min)
For `[1,2,3,4,7], m=3`:
- Sorted: [1,2,3,4,7]. lo=1, hi=6.
- mid=4: greedy 1, 5(no 4 too small wait), let me trace.
  - count=1, last=1. i=1, x=2: 2-1=1<4. i=2, x=3: 3-1=2<4. i=3, x=4: 4-1=3<4. i=4, x=7: 7-1=6>=4, count=2, last=7. End. count=2 < 3.
  - Infeasible. hi=3.
- mid=2: count=1, last=1. i=1, x=2: 2-1=1<2. i=2, x=3: 3-1=2>=2, count=2, last=3. i=3, x=4: 4-3=1<2. i=4, x=7: 7-3=4>=2, count=3. Return True.
  - Feasible. lo=2.
- mid=3: count=1, last=1. i=1,2,3: 1<3. i=4, x=7: 7-1=6>=3, count=2, last=7. End. count=2 < 3.
  - Wait that's wrong. Let me retrace. mid=3, last=1. x=2: 2-1=1<3, no. x=3: 3-1=2<3, no. x=4: 4-1=3>=3, count=2, last=4. x=7: 7-4=3>=3, count=3. Yes feasible. lo=3.
- lo=hi=3. Return 3. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **BS on d + greedy:** O(n log M). **Best.**
> 2. **Brute force try all d:** O(n * max_d). Slow.
> 3. **DP:** overkill.
>
> I'll use BS on d."

### Step 10: Why BS on Answer Is Optimal (3 min)
> "Monotonic predicate + log search = O(n log M) where M is range."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to place m balls to MAXIMIZE the MINIMUM distance between any
two balls.

KEY INSIGHT: Binary search on the ANSWER (distance d).
- Sort positions first.
- For each candidate d, check feasibility: can we place m balls with
  min gap d? Use greedy: place at first basket, then next at first
  basket >= last + d.
- Feasibility is MONOTONIC: if d works, d-1 works.
- BS on d in [1, max-min].

ALGORITHM:
1. Sort positions.
2. lo = 1, hi = max - min.
3. While lo < hi:
   - mid = (lo + hi + 1) // 2.
   - Greedy: count, last. For x: if x - last >= mid, count++, last = x.
   - If count >= m: lo = mid. Else: hi = mid - 1.
4. Return lo.

COMPLEXITY: O(n log(max-min)) time, O(n) space.

EDGE CASES:
- m = 2: just max - min.
- m = n: min of consecutive diffs.
- Duplicates: 0.

THE TRICK: Binary search on the answer (distance). Greedy feasibility
is monotonic. Always pick earliest next ball.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + BS + Greedy (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort + BS (BEST) | O(n log M) | O(n) | **THE ANSWER** |
| 2 | Sort + BS verbose | O(n log M) | O(n) | Educational |
| 3 | Sort + BS explicit | O(n log M) | O(n) | Educational |
| 4 | Sort + recursive BS | O(n log M) | O(n) | Functional |
| 5 | Sort + iterative | O(n log M) | O(n) | Variant |
| 7 | Sort + memoized | O(n log M) | O(n) | Memoized |
| 8 | Class OOP | O(n log M) | O(n) | Reusable |
| 9 | Sort + lambda BS | O(n log M) | O(n) | Variant |
| 10 | Sort + accumulate | O(n log M) | O(n) | Variant |
| 11 | Sort + bisect | O(n log M) | O(n) | Variant |
| 12 | Sort + one-liner | O(n log M) | O(n) | Concise |
| 13 | Sort + manual range | O(n log M) | O(n) | Educational |
| 14 | Sort + generator | O(n log M) | O(n) | Pythonic |
| 15 | Sort + while greedy | O(n log M) | O(n) | Educational |
| 16 | Sort + numpy | O(n log M) | O(n) | Vectorized |
| 17 | Sort + reduce | O(n log M) | O(n) | Functional |
| 18 | Sort + early term | O(n log M) | O(n) | Optimized |
| 19 | Sort + recursive | O(n log M) | O(n) | Functional |
| 20 | Final cleanest | O(n log M) | O(n) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Brute Force

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | Brute force | O(n * max_d) | O(n) | Easy |

---

## 💎 THE 18-LINE SOLUTION (Memorize!)

```python
def max_distance(position, m):
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                if count >= m:
                    return True
                last = a[i]
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
```

**Time:** `O(n log(max-min))`
**Space:** `O(n)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Binary Search on Answer

> When you binary search on a value, the predicate must be monotonic.

Feasibility: "can we place m balls with gap d?" Yes for small d, no for large d (monotonic decreasing in feasibility).

**Connection to:**
- **Parametric search:** Standard.
- **Decision problems:** Convert optimization to decision.

### Insight 2: Greedy Is Optimal

> Place earliest possible ball → maximizes remaining space.

If we delay placing a ball, we have less room. Greedy is provably optimal for fixed d.

**Connection to:**
- **Greedy with proof:** Exchange argument.
- **Earliest deadline first:** Same principle.

### Insight 3: Why Upper Mid

> `(lo + hi + 1) // 2` avoids infinite loop when lo = hi - 1.

Standard binary search pattern for finding maximum.

**Connection to:**
- **Off-by-one:** Standard.
- **Boundary handling:** Critical.

### Insight 4: Connection to Aggressive Cows

> Same problem on SPOJ with cows and stalls.

Classic competitive programming problem.

**Connection to:**
- **Same algorithm:** Universal.
- **Naming convention:** Different names.

### Insight 5: Connection to Capacity to Ship Packages (LC 1011)

> Both: find min/max value such that some predicate holds.

Same parametric search structure.

**Connection to:**
- **Problem family:** Parametric search.
- **Optimization patterns:** Universal.

### Insight 6: Why Sort First

> Sort enables monotonic placement.

After sort, greedy scanning is O(n).

**Connection to:**
- **Preprocessing:** Pay once.
- **Monotonicity:** Sort enables.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Aggressive cows** | Stall allocation |
| **Magnetic storage** | Disk head movement |
| **Wireless networks** | Cell tower placement |
| **Anti-aircraft** | Radar spacing |
| **Social distancing** | Maximum spacing |
| **Warehouse layout** | Storage spacing |

**Aggressive Cows** is THE canonical use case (SPOJ).

### Insight 8: Connection to Scheduling

> "Spread out m events over time" → same structure.

Same parametric search.

**Connection to:**
- **Scheduling:** Time allocation.
- **Resource distribution:** Same structure.

### Insight 9: Why O(n log M) and Not O(log n)

> M = max position value can be 10^9. log(10^9) ≈ 30.

M iterations of binary search × n greedy = n log M.

**Connection to:**
- **Range-based complexity:** Standard.
- **Asymptotic notation:** Different from log n.

### Insight 10: Connection to K-th Pair Distance

> Both: BS on value + count predicate.

Same skeleton.

**Connection to:**
- **Pattern family:** BS on value.
- **Reusable structure:** Same.

### Insight 11: When Greedy Fails

> Greedy fails when placement cost depends on order.

For this problem, order doesn't matter (sorted). For others (e.g., weighted), greedy fails.

**Connection to:**
- **Greedy limitations:** When to use.
- **DP when greedy fails:** Alternative.

### Insight 12: Why Not Heap-Based?

> Heap doesn't help here — just need greedy scan.

Heap is useful for top-k queries, not max-min gap.

**Connection to:**
- **Data structure choice:** Match problem.
- **Greedy + heap:** Sometimes combined.

### Insight 13: Connection to Top-K Spacing

> "Min gap between m items" relates to top-k.

Different objective: maximize min instead of sum.

**Connection to:**
- **Top-k:** Different but related.
- **Optimization:** Different metrics.

### Insight 14: Why Use Python's `sorted()`

> Timsort is O(n log n) with O(n) worst case.

Optimal for general sorting.

**Connection to:**
- **Built-in optimization:** Use stdlib.
- **Timsort:** Adaptive.

---

## 🧪 TEST CASES

| `position` | `m` | Expected | Note |
|------------|-----|----------|------|
| `[1,2,3,4,7]` | 3 | 3 | Standard |
| `[5,4,3,2,1,1000000000]` | 2 | 999999999 | Wide range |
| `[1,2,3,4,5]` | 2 | 4 | Ends |
| `[1,2,3,4,5]` | 3 | 2 | Spread |
| `[1,2,3,4,5]` | 5 | 1 | All |
| `[1,2]` | 2 | 1 | Simple |
| `[1,100]` | 2 | 99 | Wide |
| `[79,74,57,22]` | 4 | 5 | All balls |
| `[0,10,20]` | 2 | 20 | Even spread |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **BS + greedy** | **O(n log M)** | **O(n)** | **✅ BEST** |
| Brute force | O(n * max_d) | O(n) | ✅ Easy |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Aggressive Cows (SPOJ) | BS + greedy | https://www.spoj.com/problems/AGGRCOW/ |
| Capacity to Ship (LC 1011) | BS on value | https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/ |
| K-th Smallest Pair (LC 719) | BS on dist | https://leetcode.com/problems/find-k-th-smallest-pair-distance/ |
| Split Array Largest (LC 410) | BS on max | https://leetcode.com/problems/split-array-largest-sum/ |
| Magnetic Force (LC 1552) | **This problem** | https://leetcode.com/problems/magnetic-force-between-two-balls/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **BS on answer** when predicate is monotonic.
2. **Sort + greedy** for placement.
3. **Upper mid** `(lo + hi + 1) // 2` for max search.
4. **Earliest possible** placement is optimal.
5. **O(n log M)** dominates.
6. **Aggressive Cows** is the canonical example.
7. **Real-world: warehouse layout, network placement.**
8. **Same pattern as LC 1011, 410, 719.**
9. **Parametric search** universal technique.
10. **Greedy proof** via exchange argument.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Warehouse layout** | Storage spacing |
| **Wireless networks** | Tower placement |
| **Anti-aircraft** | Radar spacing |
| **Magnetic storage** | Disk head movement |
| **Social distancing** | Max spacing |
| **Scheduling** | Time allocation |
| **Resource distribution** | Spacing optimization |
| **Parametric search** | Universal pattern |
| **Logistics** | Storage allocation |
| **Robotics** | Path planning |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive BS + greedy in 90 seconds
- [x] Can code the 18-line solution in 90 seconds
- [x] Know the complexity: O(n log(max-min))
- [x] Know why greedy is optimal
- [x] Know why upper mid (not lower)
- [x] Know edge cases (m=2, m=n, duplicates)
- [x] Can compare with brute force
- [x] Know related problems (Aggressive Cows, LC 1011)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 18.
**Insight:** "Sort. BS on distance d. For each d, greedy place: count++ when next ball fits. Monotonic predicate = binary search."
