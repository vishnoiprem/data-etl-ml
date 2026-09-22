# H-Index — 0.0001% Expert Guide

> **LeetCode 274** | **Difficulty:** Medium | **Avg Solve Time:** 20 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/h-index
> **Problem:** `hIndex(citations)` — max h such that h papers have ≥ h citations.

---

## 📋 WHAT THE QUESTION ASKS

Given `citations[]`, the H-index is the largest integer `h` such that the researcher has at least `h` papers with at least `h` citations each.

### Constraints
- `1 <= citations.length <= 5000`
- `0 <= citations[i] <= 1000`

### Examples

```
citations=[3,0,6,1,5] → 3
  Sorted desc: [6,5,3,1,0].
  h=1: 6≥1 ✓ (at least 1 paper with ≥1 cite).
  h=2: 5≥2 ✓ (at least 2 papers).
  h=3: 3≥3 ✓ (at least 3 papers).
  h=4: 1<4 ✗.
  H = 3.

citations=[1,3,1] → 1
  Sorted: [3,1,1]. h=1: 3≥1 ✓. h=2: 1<2 ✗. H=1.

citations=[0] → 0

citations=[100] → 1 (1 paper with ≥1 cite).
```

### Why This Is "Medium"
- Sort + linear scan is canonical.
- O(n log n) time.
- The "break early" optimization is critical.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Max h such that ≥ h papers have ≥ h citations."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Sort DESC + scan:** O(n log n). **Best.**
> 2. **Counting sort:** O(n) if citations ≤ n.
> 3. **Binary search on h:** O(n log n).
>
> Best: Sort + scan."

### Step 3: KEY INSIGHT — Sort DESC Reveals Structure (5 min)
> "Sort citations DESC. Now `citations[i]` is the i-th LARGEST citation count.
>
> `h-index ≥ i+1` iff `citations[i] ≥ i+1`.
>
> Proof: 'h-index ≥ k' means at least k papers with ≥ k cites. The top k papers (sorted desc) all need ≥ k. So `citations[k-1] ≥ k`.
>
> Conversely, if `citations[k-1] ≥ k`, then papers 0..k-1 (top k) all have ≥ k cites, so h-index ≥ k."

### Step 4: Early Break (3 min)
> "Once `citations[i] < i+1`, h-index is i (or i-1 if checking).
> Why break? After this point, all subsequent papers have even FEWER citations (sorted DESC). So `citations[j] < j+1` for j ≥ i."

### Step 5: Algorithm (5 min)
```
1. Sort citations descending.
2. h = 0.
3. For i, c in enumerate(a):
   - If c >= i + 1: h = i + 1
   - Else: break
4. Return h.
```

### Step 6: Edge Cases (2 min)
- Empty: 0.
- All zeros: 0.
- All same large: min(c, n).
- Single paper with high citation: depends on n.

### Step 7: Code It (5 min)

```python
def hIndex(citations):
    a = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(a):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h
```

### Step 8: Verify (2 min)
For `[3,0,6,1,5]`:
- Sorted: [6, 5, 3, 1, 0].
- i=0, c=6: 6 >= 1 ✓, h=1.
- i=1, c=5: 5 >= 2 ✓, h=2.
- i=2, c=3: 3 >= 3 ✓, h=3.
- i=3, c=1: 1 < 4, break.
- Return 3. ✓

For `[1,3,1]`:
- Sorted: [3, 1, 1].
- i=0, c=3: 3 >= 1, h=1.
- i=1, c=1: 1 < 2, break.
- Return 1. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Sort + scan:** O(n log n). Simple.
> 2. **Counting sort:** O(n) when citations ≤ n. Faster constant.
> 3. **Binary search on h:** O(n log n). Same complexity.
>
> I'll use sort + scan."

### Step 10: Why Sort DESC Is Optimal (3 min)
> "After sort, the i-th largest citation tells us if h-index ≥ i+1. Single pass."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the max h such that h papers have at least h citations.

KEY INSIGHT: Sort citations DESC. Then h-index = largest i where
citations[i] >= i+1.

Why? The i-th largest paper has >= i+1 cites iff we have at least
(i+1) papers with >= (i+1) cites — exactly the h-index >= i+1 condition.

Once citations[i] < i+1, all subsequent (smaller) papers have even
fewer citations, so we can break.

ALGORITHM:
1. Sort desc.
2. h = 0.
3. For i, c in enumerate(a):
   - If c >= i + 1: h = i + 1
   - Else: break
4. Return h.

COMPLEXITY: O(n log n) time, O(1) space.

EDGE CASES:
- Empty: 0.
- All zero: 0.
- All same large: min(c, n).

THE TRICK: Sort DESC. The i-th paper's count IS the h-index threshold.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Sort + Scan (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sort DESC (BEST) | O(n log n) | O(1) | **THE ANSWER** |
| 2 | Sort ASC | O(n log n) | O(1) | Variant |
| 8 | Sort DESC explicit | O(n log n) | O(1) | Educational |
| 10 | Class OOP | O(n log n) | O(1) | Reusable |
| 12 | Linear scan | O(n log n) | O(1) | Variant |
| 14 | One-liner | O(n log n) | O(1) | Concise |
| 17 | Count consecutive | O(n log n) | O(1) | Educational |
| 19 | Zip | O(n log n) | O(1) | Pythonic |
| 20 | Final cleanest | O(n log n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Sort ASC + Iterate

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 11 | Sort ASC iterate | O(n log n) | O(1) | Variant |
| 18 | Sort ASC from end | O(n log n) | O(1) | Variant |

### 🟣 TIER 3: Binary Search / Counting

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | BS | O(n log n) | O(1) | Educational |
| 4 | Counting sort | O(n) | O(n) | When citations ≤ n |
| 6 | BS on index | O(n log n) | O(1) | Educational |
| 16 | Manual BS | O(n log n) | O(1) | Educational |

### ⚪ TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Brute force | O(n²) | O(1) | Easy |
| 7 | Heap | O(n log n) | O(n) | Functional |
| 9 | Recursive | O(n log n) | O(n) | Functional |
| 13 | Numpy | O(n log n) | O(n) | Vectorized |
| 15 | Generator | O(n log n) | O(1) | Pythonic |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def hIndex(citations):
    a = sorted(citations, reverse=True)
    h = 0
    for i, c in enumerate(a):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h
```

**Time:** `O(n log n)`
**Space:** `O(1)` extra

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Sort Desc Reveals Structure

> "The i-th largest value tells us the h-index threshold."

After sort, the i-th paper's citation count IS the question: is the h-index ≥ i+1?

**Connection to:**
- **Order statistics:** Top-k queries.
- **Sort enables monotonicity:** Same structure.

### Insight 2: Why Break Early

> Sorted DESC means after a[i] < i+1, all subsequent a[j] < j+1 too.

This is monotonicity. Once we find a fail, no future paper passes the stricter test.

**Connection to:**
- **Early termination:** Common optimization.
- **Monotonicity:** Same prerequisite.

### Insight 3: Counting Sort for O(n)

> When citations ≤ n, count frequencies in buckets.

Total papers with ≥ i cites is sum of buckets from i to n. O(n) time.

**Connection to:**
- **Bucket sort:** Linear time.
- **Constraint exploitation:** Citation bounds.

### Insight 4: Connection to Order Statistics

> H-index = max h such that citations[h-1] ≥ h.

Same as "find largest k where k-th smallest is ≥ k" in sorted array.

**Connection to:**
- **Order statistics:** Rank queries.
- **Selection:** Quickselect.

### Insight 5: Why This Beats Brute Force

> Brute force: try each h, count. O(n²).
> Sort + scan: O(n log n).

1000x speedup for n=10^4.

**Connection to:**
- **Asymptotic improvement:** Same insight everywhere.
- **Preprocessing:** Pay once.

### Insight 6: Connection to H-Index II (LC 275)

> LC 275: citations sorted ascending. Use binary search.

Different input structure, different algorithm. Both compute same thing.

**Connection to:**
- **Problem variants:** Same metric.
- **Binary search:** Logarithmic.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Academic evaluation** | Researcher impact |
| **Bibliometrics** | Citation analysis |
| **Funding decisions** | Grant selection |
| **University rankings** | Faculty impact |
| **Journal metrics** | Impact factor |
| **Tenure decisions** | Career assessment |

**Academic evaluation** is THE canonical use case (invented by Hirsch, 2005).

### Insight 8: Why H-Index Is Controversial

> A researcher with papers [99, 0, 0, 0, ...] has H=1 (not 99).

H-index doesn't capture the full picture. Modern metrics: i10-index, hα-index, etc.

**Connection to:**
- **Metric design:** Trade-offs.
- **Statistics:** Robustness.

### Insight 9: Connection to AI Citations

> AI papers use h-index for researcher ranking.

Same algorithm, applied to academic AI.

**Connection to:**
- **AI evaluation:** Researcher impact.
- **Bibliometrics:** Citation count.

### Insight 10: Why Sort DESC, Not ASC

> ASC: a[i] is i-th SMALLEST. Doesn't directly tell h-index.
> DESC: a[i] is i-th LARGEST. a[i] >= i+1 iff h-index >= i+1.

DESC has the right alignment.

**Connection to:**
- **Index alignment:** Right order matters.
- **Threshold matching:** Top-k queries.

### Insight 11: Edge Cases Summary

| Case | h-index |
|------|---------|
| All zero | 0 |
| All 1's (n=10) | 1 |
| All n's (n=10) | min(n, n) = n |
| [100] | 1 (only 1 paper) |
| [100, 100] | 2 |

**Connection to:**
- **Boundary conditions:** Standard gotcha.
- **Constraint satisfaction:** H-index bounds.

### Insight 12: Generalization to Weighted H-Index

> Each paper has weight (quality). H-index uses citations only.

Weighted variants: hα-index considers author position, etc.

**Connection to:**
- **Generalization:** Weighted metric.
- **Custom scoring:** Domain-specific.

### Insight 13: Why h-index Is Max-Min

> h-index = max h such that min(top h values) >= h.

It's a max-min problem: maximize h subject to constraint on top h.

**Connection to:**
- **Max-min optimization:** Standard pattern.
- **Threshold queries:** Same structure.

### Insight 14: Connection to Top-K Queries

> "Find max k where k-th largest >= k" is a top-k query.

Standard database operation. SQL: SELECT COUNT(*) FROM ... WHERE citations >= k.

**Connection to:**
- **SQL queries:** Top-k.
- **Database indexes:** Sort enables.

---

## 🧪 TEST CASES

| `citations` | Expected | Note |
|-------------|----------|------|
| `[3,0,6,1,5]` | 3 | Standard |
| `[1,3,1]` | 1 | Small |
| `[0]` | 0 | Single zero |
| `[1]` | 1 | Single one |
| `[100]` | 1 | High but only 1 paper |
| `[1,2,100]` | 2 | Mixed |
| `[3,3,3,3]` | 3 | All 3's |
| `[4,4,4,4,4]` | 4 | All 4's |
| `[0,1,0,1,0]` | 1 | Sparse |
| `[1,2,3,4,5]` | 3 | Increasing |
| `[25,8,5,3,3]` | 3 | Decreasing |
| `[10,8,5,4,3]` | 4 | Mixed |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Sort + scan** | **O(n log n)** | **O(1)** | **✅ BEST** |
| Counting sort | O(n) | O(n) | ✅ When citations ≤ n |
| Binary search | O(n log n) | O(1) | ✅ Same |
| Brute force | O(n²) | O(1) | ✅ Easy |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| H-Index II (LC 275) | BS on sorted | https://leetcode.com/problems/h-index-ii/ |
| Top K Frequent (LC 347) | Sort/heap | https://leetcode.com/problems/top-k-frequent-elements/ |
| Sort by Frequency | Counting sort | https://leetcode.com/problems/sort-the-array-by-increasing-frequency/ |
| K-th Largest (LC 215) | Quickselect | https://leetcode.com/problems/kth-largest-element-in-an-array/ |
| H-Index (LC 274) | **This problem** | https://leetcode.com/problems/h-index/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Sort DESC** is THE pattern.
2. **h = largest i where a[i] >= i+1.**
3. **Break early** when condition fails.
4. **O(n log n)** time, O(1) space.
5. **Counting sort for O(n)** when bounded.
6. **H-index II** uses BS on sorted input.
7. **Edge cases:** empty, all zero, single paper.
8. **Real-world:** academic evaluation.
9. **Used in AI** researcher ranking.
10. **Hirsch metric** (2005).

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Academic evaluation** | Researcher impact |
| **Bibliometrics** | Citation analysis |
| **AI researcher ranking** | Same metric |
| **Database top-k** | Related queries |
| **Sort + scan** | Universal pattern |
| **Order statistics** | Top-k queries |
| **Metric design** | Robust statistics |
| **Faculty hiring** | Impact assessment |
| **Grant funding** | Citation-based |
| **Journal selection** | Impact factor |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive sort DESC logic in 60 seconds
- [x] Can code the 8-line solution in 60 seconds
- [x] Know the complexity: O(n log n) time, O(1) space
- [x] Know why sort DESC reveals structure
- [x] Know why break early (monotonicity)
- [x] Know edge cases (empty, all zero, single)
- [x] Can compare with counting sort
- [x] Know related problems (H-Index II)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 8.
**Insight:** "Sort DESC. h = max i where a[i] >= i+1. Break early."
