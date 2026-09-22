# Search a 2D Matrix II — 0.0001% Expert Guide

> **LeetCode 240** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/search-a-2d-matrix-ii
> **Problem:** `searchMatrix(matrix, target)` — search in row+column sorted matrix

---

## 📋 WHAT THE QUESTION ASKS

Given an `m×n` integer matrix with:
- Each **row** sorted ascending (left to right).
- Each **column** sorted ascending (top to bottom).

Determine if `target` exists in the matrix.

### Constraints
- `1 <= m, n <= 300`
- `-10^9 <= matrix[i][j], target <= 10^9`

### Example

```
matrix = [[1, 4, 7, 11, 15],
          [2, 5, 8, 12, 19],
          [3, 6, 9, 16, 22],
          [10, 13, 14, 17, 24],
          [18, 21, 23, 26, 30]]

target = 5  → True  (found)
target = 20 → False (not found)
```

### Why This Is "Medium"
- Naive O(mn) is too slow for large m, n.
- The clever O(m+n) stair search is a classic trick.
- Choosing the right starting corner is key.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find target in matrix with row+column sorted. Want O(m+n) or better."

### Step 2: Identify the Algorithm (3 min)
> "Start at a CORNER where one direction is always smaller and the other is always larger. Move accordingly."

The top-right corner works:
- Values to the LEFT are smaller (row sorted).
- Values BELOW are larger (column sorted).
- Compare with target: if smaller, go down; if larger, go left.

### Step 3: Algorithm (5 min)
```
r = 0, c = n - 1
while r < m and c >= 0:
    if matrix[r][c] == target: return True
    elif matrix[r][c] > target: c -= 1
    else: r += 1
return False
```

### Step 4: Why It Works (3 min)
- At each position, the row to the left is fully smaller (we've already eliminated it by moving right→left).
- The column below is fully larger (we've already eliminated it by moving top→bottom).
- One comparison tells us which way to go.

### Step 5: Edge Cases (2 min)
- 1x1: check single element.
- target < matrix[0][0]: return False.
- target > matrix[-1][-1]: return False.

### Step 6: Code It (5 min)

```python
def searchMatrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            c -= 1
        else:
            r += 1
    return False
```

### Step 7: Verify with Example (2 min)
For matrix above, target=5:
- (0,4)=15 > 5 → c=3.
- (0,3)=11 > 5 → c=2.
- (0,2)=7 > 5 → c=1.
- (0,1)=4 < 5 → r=1.
- (1,1)=5 = 5 → True! ✓

### Step 8: Discuss Trade-offs (5 min)
> "Four approaches:
> 1. **Stair search from corner:** O(m+n) time, O(1) space. **Best.**
> 2. **Binary search per row:** O(m log n) time, O(1) space.
> 3. **Brute force:** O(mn) time, O(1) space.
> 4. **Diagonal + quadrants:** O(m+n) time, O(log) recursion.

> I'll use stair search."

### Step 9: Why the Corner Trick Works (3 min)
> "We're doing binary search implicitly. Each step eliminates one row OR one column. m + n steps total.

> Compare: full binary search on a 2D structure = O(log mn) would require a totally sorted matrix (LC 74). Here, we have weaker structure (row AND column sorted, not full sorted)."

### Step 10: Final Clean Code (5 min)
Memorize the 10-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find a target in an m x n matrix sorted both row-wise and
column-wise.

KEY INSIGHT: Start at the TOP-RIGHT corner.
- Values to the LEFT are smaller (row sorted).
- Values BELOW are larger (column sorted).
- One comparison decides direction:
  - Current > target: move LEFT (column -1).
  - Current < target: move DOWN (row +1).
- Each step eliminates one row OR one column.

Time: O(m + n), Space: O(1).

ALTERNATIVE: Start at BOTTOM-LEFT corner. Same idea, opposite directions.

EDGE CASE: If target < matrix[0][0] or target > matrix[-1][-1], return False."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Stair Search (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Top-right (BEST) | O(m+n) | O(1) | **THE ANSWER** |
| 2 | Bottom-left | O(m+n) | O(1) | Variant |
| 8 | Top-right verbose | O(m+n) | O(1) | Educational |
| 10 | BFS deque | O(m+n) | O(m+n) | Educational |
| 13 | Most concise | O(m+n) | O(1) | One-liner |
| 15 | Stair with break | O(m+n) | O(1) | Variant |
| 16 | Class OOP | O(m+n) | O(1) | Reusable |
| 17 | Bottom-left verbose | O(m+n) | O(1) | Educational |
| 19 | While True | O(m+n) | O(1) | Variant |
| 20 | Final cleanest | O(m+n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Binary Search

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Binary search per row | O(m log n) | O(1) | Simpler |
| 4 | Binary search per col | O(n log m) | O(1) | When cols < rows |
| 9 | Bisect | O(m log n) | O(1) | Pythonic |
| 11 | Binary + early exit | O(m log n) | O(1) | Optimized |

### 🟣 TIER 3: Divide & Conquer

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Diagonal + quadrants | O(m+n) | O(log) | Educational |
| 7 | D&C quadrants | O(m+n) | O(log) | Recursive |
| 18 | Diagonal + staircase | O(m+n) | O(log) | Variant |

### ⚪ TIER 4: Other

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | Brute force | O(mn) | O(1) | Tiny matrices |
| 12 | Numpy | O(mn) | O(mn) | Fast in practice |
| 14 | Lambda filter | O(mn) | O(1) | Functional |

---

## 💎 THE 10-LINE SOLUTION (Memorize!)

```python
def searchMatrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            c -= 1
        else:
            r += 1
    return False
```

**Time:** `O(m + n)`
**Space:** `O(1)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: The Corner Trick is a 2D Binary Search

> Stair search is **2D binary search in disguise**. Each step halves the search space.

For a fully sorted matrix (LC 74), we can halve BOTH dimensions in O(log m * log n). Here, weaker structure means we halve ONE dimension per step → O(m + n).

**Connection to:**
- **Binary search:** Same intuition, weaker structure.
- **Decision trees:** Each comparison branches.
- **Information theory:** log2(mn) bits needed in fully sorted case.

### Insight 2: The Corner Choice Matters

> Why top-right or bottom-left? Why NOT top-left or bottom-right?

At top-left: values to the right are larger, but values below are ALSO larger. Can't decide which way to go based on one comparison.

At top-right: left is smaller, below is larger. **Asymmetry = decisiveness**.

**Connection to:**
- **Decision theory:** Maximize information per bit.
- **Search trees:** Compare against nodes with asymmetric children.
- **Grammar parsing:** Lookahead where one direction is unambiguous.

### Insight 3: Search Space Reduction

> At each step, we eliminate one FULL row OR one FULL column.

This is the **fundamental invariant**. We never re-examine an eliminated row/column.

**Connection to:**
- **Constraint propagation:** Eliminate impossible regions.
- **Backtracking:** Pruning the search tree.
- **Branch and bound:** Skip based on bounds.

### Insight 4: Why This Beats Brute Force

Brute force: O(mn) = `9 × 10^4` for m=n=300. Stair search: O(m+n) = 600.

**600x speedup.** For larger matrices, this gap grows.

**Connection to:**
- **Algorithmic complexity:** Asymptotic vs constant factors.
- **Cache efficiency:** Stair search has great locality.
- **I/O patterns:** Sequential access.

### Insight 5: Connection to Kth Smallest Element

> In a sorted matrix (LC 378), the **kth smallest** uses a similar stair-search-with-binary-search-on-value idea.

The principle is the same: binary search on value, count via stair search.

**Connection to:**
- **Selection algorithms:** Median-of-medians, introselect.
- **Order statistics:** BST with rank.
- **Streaming quantiles:** t-digest uses similar counting.

### Insight 6: Why m, n ≤ 300?

The bound suggests O(mn) is acceptable but O(m+n) is preferable. For m=n=300:
- Brute force: 90,000 ops.
- Stair search: 600 ops.

**150x speedup.** Significant for repeated queries.

**Connection to:**
- **Database indexing:** Sorted indices enable O(log n) lookups.
- **Spatial indexing:** R-trees, quad-trees.
- **Search engines:** Inverted indices.

### Insight 7: Generalization to Multi-dimensional Search

> The stair search generalizes to **k-d sorted arrays** (sorted in each dimension).

For 2D: corner trick works because we have 2 dimensions and start at a 2D extreme.

**Connection to:**
- **k-d trees:** Multi-dimensional search.
- **R-tree range queries:** Bounding box searches.
- **OLAP cubes:** Multi-dimensional data.

### Insight 8: Real-World Applications

| Application | Use |
|-------------|-----|
| **Sparse matrices** | Quick lookup of non-zero elements |
| **Database indices** | Composite index lookup |
| **Image processing** | Pixel value search |
| **Genomic databases** | Coordinate-sorted SNP lookup |
| **GIS systems** | Spatial queries |
| **ML feature stores** | Multi-key lookups |

**Composite database indices** use the same principle: row + column sorted = O(m+n) lookup.

### Insight 9: When This Doesn't Work

> If the matrix is **only row-sorted** (not column), stair search fails.

For LC 74 (Search a 2D Matrix I), the matrix is FULLY sorted (treated as 1D). Pure binary search: O(log mn).

The **structure determines the algorithm**:
- Fully sorted → 1D binary search.
- Row + column sorted → stair search.
- Only row sorted → binary search per row.
- Unsorted → brute force.

**Connection to:**
- **Database indexes:** Different index types for different structures.
- **Information retrieval:** Inverted index for documents.
- **Spatial data:** Different data structures for different queries.

### Insight 10: Connection to Young Tableaus

> A matrix sorted row+column is a **Young tableau**.

Young tableaux have a beautiful theory: insertion, deletion, search in O(m+n).

**Connection to:**
- **Combinatorics:** RSK correspondence, Young's lattice.
- **Sort networks:** Bubble sort via Young tableau.
- **Heap variants:** Min-Young-tableau = priority queue.

---

## 🧪 TEST CASES

| Matrix | Target | Expected | Note |
|--------|--------|----------|------|
| `[[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]]` | 5 | True | Found |
| Same | 20 | False | Not found |
| `[[1]]` | 1 | True | 1x1 |
| `[[1]]` | 2 | False | 1x1 not found |
| `[[1,2,3]]` | 2 | True | 1xN |
| `[[1],[2],[3]]` | 2 | True | Nx1 |
| `[[1,5,9],[10,11,13],[12,13,15]]` | 13 | True | Duplicates |
| `[[-5]]` | -5 | True | Negative |
| `[[-5]]` | 5 | False | Negative not found |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Stair search** | **O(m+n)** | **O(1)** | **✅ BEST** |
| Binary search per row | O(m log n) | O(1) | ✅ Simpler |
| Brute force | O(mn) | O(1) | ❌ Slow |
| Diagonal + D&C | O(m+n) | O(log) | ✅ Educational |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Search a 2D Matrix (LC 74) | Fully sorted, 1D binary search | https://leetcode.com/problems/search-a-2d-matrix/ |
| Kth Smallest in Sorted Matrix (LC 378) | Same stair + value search | https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/ |
| Find Peak Element II (LC 1901) | Stair search for peak | https://leetcode.com/problems/find-peak-element-ii/ |
| Count Negative Numbers (LC 1351) | Stair search | https://leetcode.com/problems/count-negative-numbers-in-a-sorted-matrix/ |
| Search a 2D Matrix II (LC 240) | **This problem** | https://leetcode.com/problems/search-a-2d-matrix-ii/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Stair search from top-right or bottom-left corner.** Corner choice matters.
2. **At each step, eliminate one row OR one column.** O(m+n) total.
3. **One comparison decides direction** — that's why it works.
4. **Brute force is O(mn).** Stair search is 150x faster for m=n=300.
5. **Corner with asymmetry** = where one direction is smaller, other is larger.
6. **The structure determines the algorithm** — fully sorted vs row/col sorted.
7. **Generalizes to Young tableaux** — beautiful combinatorial theory.
8. **Same principle as Kth smallest** — binary search on value, count via stair.
9. **Composite database indices** use the same idea.
10. **Always test:** 1x1, 1xN, Nx1, target < min, target > max.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Database indices** | Composite row+column sorted lookup |
| **Sparse matrices** | Quick non-zero lookup |
| **Spatial indexing** | R-trees, k-d trees |
| **Young tableaux** | Combinatorial theory |
| **OLAP cubes** | Multi-dimensional search |
| **Genomic databases** | Coordinate-sorted SNP lookup |
| **ML feature stores** | Multi-key lookups |
| **Image processing** | Pixel value search |
| **Information retrieval** | Inverted indices |
| **Selection algorithms** | kth smallest in sorted matrix |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the corner choice in 60 seconds
- [x] Can code the 10-line solution in 90 seconds
- [x] Know the complexity: O(m+n) time, O(1) space
- [x] Can compare stair vs binary search per row vs brute force
- [x] Know why top-right works (asymmetry)
- [x] Know why top-left DOESN'T work (symmetric increases)
- [x] Know the Young tableau connection
- [x] Can list 5 real-world applications
- [x] Can generalize to multi-dimensional search

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 10.
**Insight:** "Start at top-right corner. Move left if current > target, down if current < target. Each step eliminates one row OR column."
