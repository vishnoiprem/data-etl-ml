# Minimum Time Difference — 0.0001% Expert Guide

> **LeetCode 539** | **Difficulty:** Medium | **Avg Solve Time:** 20 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-difference
> **Problem:** `findMinDifference(timePoints)` — min minutes between any two "HH:MM" times.

---

## 📋 WHAT THE QUESTION ASKS

Given time points in 24-hour "HH:MM" format, find the minimum difference (in minutes) between any two time points.

### Constraints
- `2 <= timePoints.length <= 2 * 10^4`
- `timePoints[i]` is in "HH:MM" format.

### Examples

```
timePoints=["23:59","00:00"] → 1
timePoints=["00:00","04:00","22:00"] → 120
timePoints=["12:00","23:59","00:00"] → 1
timePoints=["00:00","00:00"] → 0  (duplicate)
```

### Why This Is "Medium"
- Convert to minutes + sort + scan is canonical.
- O(n log n) time.
- The WRAP-AROUND is the trick.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Min minutes between any two 'HH:MM' times, considering circular 24-hour clock."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort + scan:** O(n log n). **Best.**
> 2. **Bucket sort:** O(n + 1440) ≈ O(n). Faster constant.
> 3. **Brute force:** O(n²).
>
> Best: Sort + scan."

### Step 3: KEY INSIGHT — Convert to Minutes + Sort (5 min)
> "Each time is 0-1439 (minutes in a day). Sort. Min difference between consecutive times IS the answer (in sorted order).
>
> Why? For any pair (i, j), their diff is bounded by consecutive pairs in the sorted list. Smallest gap is always between adjacent times."

### Step 4: The Wrap-Around Trick (3 min)
> "Clock is circular: 23:59 to 00:00 is 1 minute, not 1439.
>
> Wrap-around = (first_time + 1440) - last_time.
>
> Always include this check!"

### Step 5: Algorithm (5 min)
```
1. Convert each "HH:MM" to minutes: h*60 + m.
2. Sort minutes.
3. min_diff = (minutes[0] + 1440) - minutes[-1] (wrap-around).
4. For i in 1..n-1: min_diff = min(min_diff, minutes[i] - minutes[i-1]).
5. Return min_diff.
```

### Step 6: Edge Cases (2 min)
- Duplicates: return 0.
- Two times only: simple diff.
- Wrap: 23:59 and 00:00 → 1.

### Step 7: Code It (5 min)

```python
def findMinDifference(timePoints):
    minutes = sorted(int(t[:2]) * 60 + int(t[3:]) for t in timePoints)
    min_diff = (minutes[0] + 1440) - minutes[-1]
    for i in range(1, len(minutes)):
        min_diff = min(min_diff, minutes[i] - minutes[i - 1])
    return min_diff
```

### Step 8: Verify (2 min)
For `["23:59","00:00"]`:
- Minutes: [1439, 0]. Sorted: [0, 1439].
- Wrap: (0 + 1440) - 1439 = 1.
- Consecutive: 1439 - 0 = 1439.
- Min = 1. ✓

For `["00:00","04:00","22:00"]`:
- Minutes: [0, 240, 1320]. Sorted: [0, 240, 1320].
- Wrap: (0 + 1440) - 1320 = 120.
- Consecutive: 240, 1080.
- Min = 120. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Sort + scan:** O(n log n). Simple, clear.
> 2. **Bucket sort:** O(n + 1440). Faster constant, less code.
> 3. **Brute force:** O(n²). Easy but slow.
>
> I'll use sort + scan."

### Step 10: Why Sort Is Optimal (3 min)
> "After sort, O(n) scan covers all pairs (consecutive). Plus wrap-around. Total O(n log n)."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the minimum difference in minutes between any two
24-hour clock time points.

KEY INSIGHT: Convert to minutes (0-1439). Sort. The minimum difference
between consecutive times in the sorted list is the answer. Plus
WRAP-AROUND: (first + 1440) - last.

ALGORITHM:
1. Convert each time to minutes: h*60 + m.
2. Sort the minutes.
3. min_diff = (minutes[0] + 1440) - minutes[-1]  # wrap-around.
4. For i in 1..n-1: min_diff = min(min_diff, minutes[i] - minutes[i-1]).
5. Return min_diff.

COMPLEXITY: O(n log n) time, O(n) space.

EDGE CASES:
- Duplicates: return 0.
- Two times: simple diff.
- Wrap: 23:59 and 00:00 → 1.

THE TRICK: Wrap-around via (first + 1440) - last. Forgot this = wrong.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + Scan (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort + scan (BEST) | O(n log n) | O(n) | **THE ANSWER** |
| 2 | Sort + linear verbose | O(n log n) | O(n) | Educational |
| 5 | Sort + zip | O(n log n) | O(n) | Pythonic |
| 6 | Set + sorted | O(n log n) | O(n) | Variant |
| 8 | Reduce | O(n log n) | O(n) | Functional |
| 9 | Class OOP | O(n log n) | O(n) | Reusable |
| 11 | Sort + manual | O(n log n) | O(n) | Educational |
| 12 | Zip unpack | O(n log n) | O(n) | Pythonic |
| 13 | Generator | O(n log n) | O(n) | Pythonic |
| 14 | Enumerate | O(n log n) | O(n) | Variant |
| 15 | Sorted with key | O(n log n) | O(n) | Functional |
| 17 | Lambda map | O(n log n) | O(n) | Functional |
| 18 | Slice min | O(n log n) | O(n) | Variant |
| 19 | Recursive | O(n log n) | O(n) | Functional |
| 20 | Final cleanest | O(n log n) | O(n) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Bucket Sort

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Bucket sort | O(n + 1440) | O(1440) | Fixed domain |

### 🟣 TIER 3: Functional & Vectorized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Brute force | O(n²) | O(n) | Easy |
| 7 | Numpy | O(n log n) | O(n) | Vectorized |
| 10 | Itertools pairwise | O(n log n) | O(n) | Pythonic |
| 16 | Filter + early exit | O(n log n) | O(n) | Optimization |

---

## 💎 THE 7-LINE SOLUTION (Memorize!)

```python
def findMinDifference(timePoints):
    minutes = sorted(int(t[:2]) * 60 + int(t[3:]) for t in timePoints)
    min_diff = (minutes[0] + 1440) - minutes[-1]  # wrap-around
    for i in range(1, len(minutes)):
        min_diff = min(min_diff, minutes[i] - minutes[i - 1])
    return min_diff
```

**Time:** `O(n log n)`
**Space:** `O(n)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Cyclic Distance vs Linear Distance

> Times wrap around midnight. Need to consider both directions.

For times a, b, the cyclic distance is min(b-a, 1440-(b-a)).

**Connection to:**
- **Circular geometry:** Standard concept.
- **Modular arithmetic:** (a - b) mod 1440.

### Insight 2: Why Sort Consecutive Captures All Pairs

> Smallest gap is always between adjacent sorted elements.

If gap between non-adjacent was smaller, the gap between adjacent (in between) would be smaller still (triangle inequality on sorted sequence).

**Connection to:**
- **Consecutive pairs:** Universal.
- **Local minimum:** Adjacent.

### Insight 3: The Wrap-Around Trick

> Add 1440 to the first time and "look back" at last.

This elegantly handles circular nature without modular arithmetic.

**Connection to:**
- **Boundary handling:** Standard trick.
- **Cyclic arrays:** Same idea.

### Insight 4: Bucket Sort for O(n)

> 1440 is a fixed constant. Boolean array of size 1440 gives O(n).

For time-of-day problems, bucket sort is essentially O(n) due to fixed domain.

**Connection to:**
- **Bucket sort:** Linear time.
- **Constraint exploitation:** Use bounds.

### Insight 5: Why Duplicates Mean Zero

> Two identical times = 0 minute difference.

Early exit on duplicates saves time.

**Connection to:**
- **Hash set:** O(1) duplicate check.
- **Constraint optimization:** Early exit.

### Insight 6: Connection to Modular Arithmetic

> Wrap-around = min(d, 1440-d) where d = |a - b|.

This is the cyclic distance on a ring of 1440 elements.

**Connection to:**
- **Modular arithmetic:** Standard.
- **Group theory:** Z/nZ.

### Insight 7: Connection to Clock Problems

> Analog clocks, time zones, schedules all use this.

Same problem structure: cyclic distance on fixed domain.

**Connection to:**
- **Time series:** Cyclic patterns.
- **Scheduling:** Time intervals.

### Insight 8: Real-World Applications

| Application | Use |
|-------------|-----|
| **Event scheduling** | Min gap between meetings |
| **Bioinformatics** | Circadian rhythm analysis |
| **Transportation** | Bus/train schedule gaps |
| **Sleep tracking** | Sleep onset/offset |
| **Logistics** | Delivery time slots |
| **Astronomy** | Celestial events |

**Scheduling** is the canonical use case.

### Insight 9: Why 1440

> 24 hours × 60 minutes = 1440.

The domain size. Fixed, so bucket sort is O(n).

**Connection to:**
- **Constant domain:** Exploit bounds.
- **Time representation:** Standard.

### Insight 10: Connection to Car Pooling (LC 1094)

> Similar time-based interval scheduling.

Both involve sorting time points and scanning.

**Connection to:**
- **Time-based problems:** Same structure.
- **Interval scheduling:** Related.

### Insight 11: Why Itertools Pairwise

> `pairwise(a)` yields (a[0],a[1]), (a[1],a[2]), ...

Python 3.10+ feature. Cleaner than `zip(a, a[1:])`.

**Connection to:**
- **Python stdlib:** Modern Pythonic.
- **Iterator algebra:** Composition.

### Insight 12: Generalization to Multi-Day Cycles

> "Min gap over k-day window" extends naturally.

Apply cyclic distance with period k*1440.

**Connection to:**
- **Generalization:** Natural.
- **Multi-period:** Composite cycles.

### Insight 13: Why Sort Before Diff

> Sorting gives O(n) consecutive differences.

Without sort, we'd need O(n²) to check all pairs.

**Connection to:**
- **Sort as preprocessing:** Standard.
- **Asymptotic improvement:** Fundamental.

### Insight 14: Connection to Top-K Min

> "Min consecutive diff" is a related concept.

After sort, finding min diff is essentially top-1 of pairwise diffs.

**Connection to:**
- **Top-K queries:** Standard pattern.
- **Min-finding:** Linear scan.

### Insight 15: The "Add 1440" Trick

> Wrap-around = (first + 1440) - last.

Same as treating time as linear but adding 1440 to the first.

**Connection to:**
- **Coordinate transformation:** Standard.
- **Boundary handling:** Elegant trick.

---

## 🧪 TEST CASES

| `timePoints` | Expected | Note |
|--------------|----------|------|
| `["23:59","00:00"]` | 1 | Wrap |
| `["00:00","04:00","22:00"]` | 120 | Big gap |
| `["00:00","00:00"]` | 0 | Duplicate |
| `["01:01","02:02","03:03"]` | 61 | 61 min apart |
| `["00:00","12:00"]` | 720 | Half day |
| `["01:00","02:00","03:00"]` | 60 | 1 hour |
| `["12:00","23:59","00:00"]` | 1 | Mixed |
| `["05:31","22:08","00:35"]` | 147 | Complex |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Sort + scan** | **O(n log n)** | **O(n)** | **✅ BEST** |
| Bucket sort | O(n + 1440) | O(1440) | ✅ Fast constant |
| Brute force | O(n²) | O(n) | ✅ Easy |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Car Pooling (LC 1094) | Time intervals | https://leetcode.com/problems/car-pooling/ |
| Teemo Attacking (LC 495) | Time intervals | https://leetcode.com/problems/teemo-attacking/ |
| Maximum Pop Year (LC 1854) | Time tracking | https://leetcode.com/problems/maximum-population-year/ |
| Min Abs Diff BST (LC 530) | Tree traversal | https://leetcode.com/problems/minimum-absolute-difference-in-bst/ |
| Min Time Diff (LC 539) | **This problem** | https://leetcode.com/problems/minimum-time-difference/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Convert to minutes** (0-1439). Standardize.
2. **Sort.** Reveals structure.
3. **Consecutive diffs** capture all pairs.
4. **Wrap-around = (first + 1440) - last.**
5. **Duplicates = 0.** Early exit.
6. **O(n log n)** dominates.
7. **Bucket sort** for O(n) since 1440 is fixed.
8. **Real-world: scheduling, sleep tracking.**
9. **Cyclic distance** standard concept.
10. **Itertools pairwise** for cleaner code.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Event scheduling** | Meeting gap detection |
| **Bioinformatics** | Circadian analysis |
| **Transportation** | Schedule gaps |
| **Sleep tracking** | Sleep cycles |
| **Time series** | Cyclic patterns |
| **Database indexes** | Time bucketing |
| **Logistics** | Delivery slots |
| **Astronomy** | Celestial cycles |
| **Health monitoring** | Heart rate gaps |
| **ML preprocessing** | Cyclic features |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive sort + scan logic in 60 seconds
- [x] Can code the 7-line solution in 60 seconds
- [x] Know the complexity: O(n log n) time, O(n) space
- [x] Know the wrap-around trick
- [x] Know why consecutive diffs capture all pairs
- [x] Know edge cases (duplicates, n=2, wrap)
- [x] Can compare with bucket sort
- [x] Know related problems (Car Pooling, Teemo)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 7.
**Insight:** "Convert to minutes, sort, scan consecutive diffs, plus wrap-around (first + 1440 - last)."
