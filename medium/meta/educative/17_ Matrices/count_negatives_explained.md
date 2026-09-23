# Count Negative Numbers in a Sorted Matrix — 0.0001% Expert Guide

> **LeetCode 1351** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/count-negative-numbers-in-a-sorted-matrix
> **Problem:** `countNegatives(grid)` — count negatives in row+column sorted matrix

---

## 📋 WHAT THE QUESTION ASKS

Given an `m×n` matrix where each **row and column** is sorted in **non-increasing** order, count the total number of negative numbers.

### Constraints
- `1 <= m, n <= 100`
- `-100 <= grid[i][j] <= 100`

### Example

```
grid = [[4, 3, 2, -1],
        [3, 2, 1, -1],
        [1, 1, -1, -2],
        [-1, -1, -2, -3]]

Negatives: -1, -1, -1, -1, -1, -2, -1, -1, -2, -3 = 8
Output: 8
```

### Why This Is "Easy"
- The structure (sorted descending) gives O(m+n) tricks.
- Multiple valid approaches.
- Small constraints (m, n <= 100).

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Count negatives in a matrix sorted row+column descending."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Stair search from top-right or bottom-left corner:** O(m+n).
> 2. **Binary search on each row:** O(m log n).
> 3. **Brute force:** O(mn).
>
> Best: Stair search."

### Step 3: Stair Search Logic (5 min)

**Start at top-right corner:**
- If `grid[r][c] >= 0`: move LEFT (column decreases). All values to the left are smaller or equal. No more negatives in this row's portion.
- If `grid[r][c] < 0`: count this column's negatives = `(m - r)` (all rows below in this column are also negative). Move DOWN (row increases).

**Why this works:**
- To the left of current: smaller (row sorted descending).
- Below current: smaller (column sorted descending).
- One comparison decides direction.

### Step 4: Why Bottom-Left Also Works (3 min)

**Start at bottom-left corner:**
- If `grid[r][c] < 0`: count = `(n - c)` (all columns to the right are also negative in this row). Move UP.
- If `grid[r][c] >= 0`: move RIGHT.

Both corners work — symmetric.

### Step 5: Edge Cases (2 min)
- 1x1: trivially check the single value.
- All positives: count = 0.
- All negatives: count = m*n.

### Step 6: Code It (5 min)

```python
def countNegatives(grid):
    m, n = len(grid), len(grid[0])
    r, c = 0, n - 1
    count = 0
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += (m - r)
            c -= 1
        else:
            r += 1
    return count
```

### Step 7: Verify with Example (2 min)
For the 4x4 example above:
- (0,3) = -1 < 0. count += 4 - 0 = 4. c=2.
- (0,2) = 2 >= 0. r=1.
- (1,2) = 1 >= 0. r=2.
- (2,2) = -1 < 0. count += 4 - 2 = 2. count=6. c=1.
- (2,1) = 1 >= 0. r=3.
- (3,1) = -1 < 0. count += 4 - 3 = 1. count=7. c=0.
- (3,0) = -1 < 0. count += 4 - 3 = 1. count=8. c=-1. Exit.
- Return 8. ✓

### Step 8: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Stair search:** O(m+n) time, O(1) space. **Best.**
> 2. **Binary search per row:** O(m log n) time, O(1) space. Simpler.
> 3. **Brute force:** O(mn) time, O(1) space.

> I'll use stair search."

### Step 9: Why O(m+n) Beats O(m log n) (3 min)

For m=n=100:
- O(m+n) = 200 steps.
- O(m log n) = 100 * 7 = 700 steps.
- ~3.5x speedup.

**Connection to:** Asymptotic complexity vs constant factors.

### Step 10: Final Clean Code (5 min)
Memorize the 10-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count negatives in a matrix where each row and column is
sorted in non-increasing order.

KEY INSIGHT: Start at the TOP-RIGHT corner.
- grid[r][c] >= 0: move LEFT (no negatives to the left in this row,
  but column might still have them).
- grid[r][c] < 0: ALL values in this column from row r down are negative.
  Add (m - r) to count, move LEFT.

Each step eliminates one row OR one column. O(m + n) total.

ALTERNATIVE: Start at BOTTOM-LEFT corner. Same logic, opposite directions.

COMPLEXITY: O(m + n) time, O(1) space."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Stair Search (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Top-right (BEST) | O(m+n) | O(1) | **THE ANSWER** |
| 2 | Bottom-left | O(m+n) | O(1) | Variant |
| 10 | Top-right explicit | O(m+n) | O(1) | Educational |
| 11 | Bottom-right (variant) | O(m+n) | O(1) | Variant |
| 13 | Bottom-left explicit | O(m+n) | O(1) | Educational |
| 17 | Two-pointer | O(m+n) | O(1) | Educational |
| 19 | Most concise | O(m+n) | O(1) | One-liner |
| 20 | Final cleanest | O(m+n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Binary Search

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Binary search per row | O(m log n) | O(1) | Simpler |
| 4 | Manual binary search | O(m log n) | O(1) | Educational |
| 12 | Binary search from left | O(m log n) | O(1) | Variant |
| 16 | Per-row threshold | O(m log n) | O(1) | Variant |

### 🟣 TIER 3: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 15 | Recursive | O(m+n) | O(log) | Educational |
| 18 | Class OOP | O(m+n) | O(1) | Reusable |

### ⚪ TIER 4: Brute Force / Simple

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Brute force | O(mn) | O(1) | Tiny matrices |
| 6 | Flatten and count | O(mn) | O(mn) | Educational |
| 7 | Sum of bools | O(mn) | O(1) | Pythonic |
| 8 | Filter and len | O(mn) | O(mn) | Functional |
| 9 | Numpy | O(mn) | O(mn) | Fast in practice |
| 14 | Count() method | O(mn) | O(mn) | Pythonic |

---

## 💎 THE 10-LINE SOLUTION (Memorize!)

```python
def countNegatives(grid):
    m, n = len(grid), len(grid[0])
    r, c = 0, n - 1
    count = 0
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += (m - r)
            c -= 1
        else:
            r += 1
    return count
```

**Time:** `O(m + n)`
**Space:** `O(1)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Stair Search is a Generalized Binary Search

> At each step, we eliminate one row OR one column. The decision is monotone.

For positive values, we move down (eliminating a row of positives). For negative, we move left (eliminating a column of negatives, adding all to count).

**Connection to:**
- **Binary search:** Same intuition.
- **Selection algorithms:** Median finding.
- **Order statistics:** kth element in sorted structure.

### Insight 2: The Asymmetric Corner Trick

> Top-right corner works because:
> - LEFT (in row) → smaller or equal values.
> - DOWN (in column) → smaller or equal values.
>
> Both directions have the SAME direction of monotonicity (descending), but we use different actions for positive vs negative.

This is the inverse of Search a 2D Matrix II (where we had ASCENDING order). Same structure, opposite logic.

**Connection to:**
- **Dual problems:** Find/search, count/find.
- **Mirror symmetry:** Ascending vs descending.
- **Information theory:** Same bit count, different semantics.

### Insight 3: Counting vs Finding

> "Find a target" and "count negatives" use the SAME stair search structure.

The difference is just **how we update the count** when we find a negative. Instead of returning True, we add `(m - r)` and continue.

**Connection to:**
- **Streaming aggregation:** Sum vs Find.
- **SQL:** COUNT vs EXISTS.
- **Selection vs enumeration:** Different goals, same traversal.

### Insight 4: Why This Is O(m+n) Not O(m log n)

> Binary search per row uses `log n` comparisons per row.
> Stair search uses 1 comparison per step (m+n total).

**Same logic, different shape.** Stair search is the optimal way to use the 2D structure.

**Connection to:**
- **Dimensional analysis:** m + n vs m * log n.
- **Asymptotic complexity:** Tighter bounds.
- **Cache efficiency:** Sequential access.

### Insight 5: Connection to Cumulative Distribution

> This is essentially computing the **CDF** of the 2D distribution.

The number of negatives = total count where value < 0. This is the empirical CDF at 0.

**Connection to:**
- **Statistics:** ECDF, percentile, quantile.
- **Streaming:** t-digest, KLL.
- **ML rank-loss:** Same structure.

### Insight 6: Why m, n ≤ 100?

The constraints suggest any approach works. O(mn) = 10,000 ops is trivial.

But for larger inputs (m, n = 10^5), the difference matters:
- O(m+n) = 200,000.
- O(mn) = 10^10.

**Connection to:**
- **Asymptotic vs constant factors.**
- **Big-O:** Different problems at different scales.
- **Hardware limits:** Cache, memory bandwidth.

### Insight 7: Generalization to kth Order Statistics

> Same trick generalizes to "find kth smallest in row+column sorted matrix".

Stair search + binary search on value.

**Connection to:**
- **Order statistics trees:** BST with rank.
- **Selection algorithms:** Quickselect.
- **Database queries:** ORDER BY + LIMIT.

### Insight 8: Connection to Sparse Matrices

> A sparse matrix (mostly zeros) can be efficiently scanned with similar techniques.

If "negative" = "non-zero", stair search gives O(m+n) counting.

**Connection to:**
- **Compressed sparse row (CSR):** Standard format.
- **Graph algorithms:** Sparse adjacency lists.
- **Eigenvalues:** Zero/non-zero structure.

### Insight 9: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image thresholding** | Count pixels below threshold |
| **Statistics** | ECDF, percentile |
| **Streaming quantiles** | t-digest, KLL |
| **Database queries** | COUNT with WHERE clause |
| **ML feature engineering** | Count rare events |
| **Signal processing** | Count samples below threshold |

**Image thresholding** uses this pattern: count pixels below a threshold value to determine foreground vs background.

### Insight 10: Connection to Search a 2D Matrix II

> Both use the corner trick. Same structure, opposite problems:
>
> - **Search 2D II:** Find target in ascending matrix.
> - **Count Negatives:** Count negatives in descending matrix.

The corner choice matters:
- Ascending + top-right corner = Search.
- Descending + top-right corner = Count Negatives.

Same algorithm, different comparisons!

**Connection to:**
- **Dual problems:** Mirror-image problems.
- **Symmetry:** Ascending ↔ Descending.
- **Transformations:** Inverse of each other.

---

## 🧪 TEST CASES

| Grid | Expected | Note |
|------|----------|------|
| `[[4,3,2,-1],[3,2,1,-1],[1,1,-1,-2],[-1,-1,-2,-3]]` | 8 | Standard |
| `[[3,2],[1,0]]` | 0 | All non-negative |
| `[[-3,-2],[-1,0]]` | 3 | 3 negatives |
| `[[-1]]` | 1 | 1x1 negative |
| `[[1]]` | 0 | 1x1 non-negative |
| `[[5,1,0],[-5,-5,-5]]` | 3 | Mixed |
| `[[-1,-2],[-3,-4]]` | 4 | All negatives |
| `[[3]]` | 0 | Single positive |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Stair search** | **O(m+n)** | **O(1)** | **✅ BEST** |
| Binary search per row | O(m log n) | O(1) | ✅ Simpler |
| Brute force | O(mn) | O(1) | ❌ Slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Search a 2D Matrix II (LC 240) | Same corner trick (ascending) | https://leetcode.com/problems/search-a-2d-matrix-ii/ |
| Kth Smallest in Sorted Matrix (LC 378) | Stair + value binary search | https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/ |
| Find Peak Element II (LC 1901) | Stair search for peak | https://leetcode.com/problems/find-peak-element-ii/ |
| Matrix Cells in Distance Order (LC 1030) | BFS by distance | https://leetcode.com/problems/matrix-cells-in-distance-order/ |
| Count Negatives (LC 1351) | **This problem** | https://leetcode.com/problems/count-negative-numbers-in-a-sorted-matrix/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Stair search from top-right or bottom-left corner.** Same as Search 2D II but reversed.
2. **For descending order, top-right works:** Left has smaller, down has smaller. Decide based on sign.
3. **When negative, add `(m - r)` to count** — all rows below in this column are negative.
4. **O(m+n) beats O(m log n).** ~3.5x faster for m=n=100.
5. **Counting vs Finding** — same algorithm, different updates.
6. **Asymmetric corner trick** — choose corner with monotonicity asymmetry.
7. **Generalizes to kth order statistics** — stair search + value binary search.
8. **This IS the empirical CDF at 0** — same structure as quantiles.
9. **Image thresholding uses the same logic.**
10. **Dual of Search 2D Matrix II** — ascending vs descending, count vs find.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Image thresholding** | Count pixels below threshold |
| **Statistics** | ECDF, percentile, quantile |
| **Streaming quantiles** | t-digest, KLL, Greenwald-Khanna |
| **Database queries** | COUNT with WHERE clause |
| **ML feature engineering** | Count rare events |
| **Signal processing** | Count samples below threshold |
| **Sparse matrices** | Counting non-zeros |
| **Order statistics** | kth smallest in sorted structure |
| **Selection algorithms** | Quickselect, median-of-medians |
| **Database optimization** | Index-based counting |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the stair search in 60 seconds
- [x] Can code the 10-line solution in 90 seconds
- [x] Know the complexity: O(m+n) time, O(1) space
- [x] Know why bottom-left also works (symmetry)
- [x] Know the count formula: `(m - r)` when negative
- [x] Can compare stair vs binary search vs brute force
- [x] Know the connection to Search 2D Matrix II
- [x] Can list 5 real-world applications
- [x] Can generalize to kth order statistics

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 10.
**Insight:** "Start at top-right corner. If grid[r][c] < 0, add (m-r) to count, move left. Else, move down. O(m+n) total."
