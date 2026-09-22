# Set Matrix Zeroes — 0.0001% Expert Guide

> **LeetCode 73** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/set-matrix-zeroes
> **Problem:** `setZeros(matrix)` — set rows and columns to zero if cell is zero

---

## 📋 WHAT THE QUESTION ASKS

Given an `m×n` matrix, if any element is zero, set its entire **row** and **column** to zero. Modify in place.

### Constraints
- `1 <= m, n <= 200`
- `-2^31 <= matrix[i][j] <= 2^31 - 1`

### Example

```
Input: [[1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]]

Output: [[1, 0, 1],
         [0, 0, 0],
         [1, 0, 1]]
```

### Why This Is "Medium"
- The catch is **in-place** modification.
- The solution uses the matrix itself as auxiliary storage.
- Subtle: row 0 and column 0 collide on `matrix[0][0]`.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "If any cell is zero, set its row and column to zero. In-place."

### Step 2: Brainstorm Approaches (3 min)
> "Three approaches:
> 1. **Extra space:** Use sets to track which rows/cols to zero.
> 2. **Marker values:** Use a special value (e.g., 0 itself or `float('inf')`) to mark cells.
> 3. **First row/col as markers:** Use matrix[0][c] and matrix[r][0] as flags.
>
> Best: First row/col as markers (O(1) extra space)."

### Step 3: Why First Row/Col Works (3 min)
> "When we see a zero at `(r, c)`:
> - Mark `matrix[r][0] = 0` (column 0 of row r).
> - Mark `matrix[0][c] = 0` (row 0 of column c).
>
> After first pass, we know which rows and cols need zeroing. Then a second pass zeroes them."

### Step 4: Subtle Issue — Cell (0,0) (3 min)
> "Cell `(0, 0)` is shared between row 0 and column 0 markers. We need a separate flag for whether ROW 0 itself has a zero."

A single bool `first_row_zero` solves this.

### Step 5: Algorithm (5 min)
```
1. Check if row 0 has any zero → first_row_zero.
2. Check if col 0 has any zero → first_col_zero.
3. First pass: for each zero at (r, c):
   - matrix[r][0] = 0
   - matrix[0][c] = 0
4. Second pass: for r=1..m-1, c=1..n-1:
   - If matrix[r][0] == 0 or matrix[0][c] == 0: matrix[r][c] = 0.
5. Third pass: zero out row 0 (if needed) and col 0 (if needed).
```

### Step 6: Edge Cases (2 min)
- 1x1: trivially zero (or unchanged).
- All zeros: stays all zeros.
- No zeros: unchanged.

### Step 7: Code It (5 min)

```python
def setZeros(matrix):
    if not matrix:
        return
    m, n = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][c] == 0 for c in range(n))
    first_col_zero = any(matrix[r][0] == 0 for r in range(m))
    
    # Mark
    for r in range(1, m):
        for c in range(1, n):
            if matrix[r][c] == 0:
                matrix[r][0] = 0
                matrix[0][c] = 0
    
    # Zero out (skip first row/col)
    for r in range(1, m):
        for c in range(1, n):
            if matrix[r][0] == 0 or matrix[0][c] == 0:
                matrix[r][c] = 0
    
    # Handle first row and column
    if first_row_zero:
        for c in range(n):
            matrix[0][c] = 0
    if first_col_zero:
        for r in range(m):
            matrix[r][0] = 0
```

### Step 8: Verify (2 min)
For `[[1,1,1],[1,0,1],[1,1,1]]`:
- first_row_zero = False, first_col_zero = False.
- Mark: matrix[1][0] = 0, matrix[0][1] = 0.
- Zero out: matrix[1][1] = 0 (matrix[1][0] is 0).
- Result: `[[1,0,1],[0,0,0],[1,0,1]]`. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Extra space:** O(m+n) space, O(mn) time.
> 2. **Marker value:** O(1) space, but may not work if values can be that sentinel.
> 3. **First row/col as markers:** O(1) space, O(mn) time. **Best.**

> I'll use first row/col as markers."

### Step 10: Final Clean Code (5 min)
Memorize the 25-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to zero out rows and columns containing zeros, using O(1)
extra space.

KEY INSIGHT: Use the FIRST ROW and FIRST COLUMN as markers.
- When I see a zero at (r, c), mark matrix[r][0] = 0 and matrix[0][c] = 0.
- Cell (0,0) is shared between row 0 and col 0 markers, so I need
  separate flags for whether row 0 and col 0 themselves have zeros.

ALGORITHM:
1. Check if row 0 has any zero (first_row_zero flag).
2. Check if col 0 has any zero (first_col_zero flag).
3. First pass (r=1..m-1, c=1..n-1): if matrix[r][c]==0, mark matrix[r][0]
   and matrix[0][c].
4. Second pass (r=1..m-1, c=1..n-1): if matrix[r][0]==0 or
   matrix[0][c]==0, set matrix[r][c]=0.
5. Third pass: zero out row 0 and col 0 if their flags are set.

COMPLEXITY: O(mn) time, O(1) extra space."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: First Row/Col as Markers (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | First row/col (BEST) | O(mn) | O(1) | **THE ANSWER** |
| 8 | First row/col in-place | O(mn) | O(1) | Variant |
| 11 | Helper to clear | O(mn) | O(1) | Readable |
| 13 | Single bool flag | O(mn) | O(1) | Variant |
| 20 | Final cleanest | O(mn) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Extra Space (Simpler)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | Set for rows/cols | O(mn) | O(m+n) | Simpler |
| 3 | Two lists | O(mn) | O(m+n) | Educational |
| 6 | Tuples | O(mn) | O(m+n) | Variant |
| 7 | Dict flags | O(mn) | O(m+n) | Variant |
| 10 | List of bools | O(mn) | O(m+n) | Readable |
| 14 | Bitmask | O(mn) | O(m+n) | Bitwise |

### 🟣 TIER 3: Marker Values

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Sentinel value | O(mn) | O(1) | If sentinel safe |
| 5 | float('inf') | O(mn) | O(1) | If ints only |
| 9 | BitSet style | O(mn) | O(1) | Conceptual |
| 12 | One-pass marker | O(mn) | O(1) | Variant |
| 16 | Marker + sweep | O(mn) | O(1) | Educational |

### ⚪ TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 15 | Most concise | O(mn) | O(1) | One-liner |
| 17 | Numpy | O(mn) | O(mn) | Fast in practice |
| 18 | Recursive | O(mn) | O(mn) | Educational |
| 19 | Class OOP | O(mn) | O(1) | Reusable |

---

## 💎 THE 25-LINE SOLUTION (Memorize!)

```python
def setZeros(matrix):
    if not matrix:
        return
    m, n = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][c] == 0 for c in range(n))
    first_col_zero = any(matrix[r][0] == 0 for r in range(m))
    
    # Mark using first row/col
    for r in range(1, m):
        for c in range(1, n):
            if matrix[r][c] == 0:
                matrix[r][0] = 0
                matrix[0][c] = 0
    
    # Zero out based on markers
    for r in range(1, m):
        for c in range(1, n):
            if matrix[r][0] == 0 or matrix[0][c] == 0:
                matrix[r][c] = 0
    
    # Handle first row/col
    if first_row_zero:
        for c in range(n):
            matrix[0][c] = 0
    if first_col_zero:
        for r in range(m):
            matrix[r][0] = 0
```

**Time:** `O(m * n)`
**Space:** `O(1)` (in-place)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Use the Structure as Storage

> When you need O(1) space, use the existing data structure as auxiliary storage.

The matrix itself has `m*n` cells. We only need `m + n` flags. The first row and column give us exactly that.

**Connection to:**
- **In-place algorithms:** Always consider the data structure.
- **Memory-constrained systems:** Embedded, kernel.
- **Streaming:** When you can't buffer.

### Insight 2: The (0,0) Cell Collision

> Cell `(0, 0)` is shared between row 0 and column 0 markers. We need a separate flag.

This is a fundamental issue: the corner cell has dual meaning. A separate flag resolves it.

**Connection to:**
- **Cache coherence:** Shared resources.
- **Memory layout:** Address conflicts.
- **Hash collisions:** Different keys, same slot.

### Insight 3: Why Three Passes?

> Pass 1: Mark (using first row/col).
> Pass 2: Zero out (use markers).
> Pass 3: Handle first row/col separately.

The third pass is necessary because we need the original first row/col info until the end.

**Connection to:**
- **Streaming algorithms:** Multiple passes when memory is limited.
- **MapReduce:** Map, shuffle, reduce pattern.
- **Database transactions:** Read, modify, write.

### Insight 4: Trade-off Between Space and Sentinel

> Extra space O(m+n): use sets/lists.
> Sentinel value: use a special value that doesn't appear in input.
> First row/col: use the input itself.

The first row/col approach works **regardless of input values**.

**Connection to:**
- **Hash functions:** Different ways to encode sets.
- **Bloom filters:** Probabilistic, space-efficient.
- **Compressed sensing:** Sparse representations.

### Insight 5: Sentinel Approach Caveat

> If input can contain `float('inf')` (or whatever sentinel), the sentinel approach fails.

Many problems specify value ranges precisely to allow this. Here, ints in `[-2^31, 2^31-1]`, so `2^31` (out of range) works. But it's brittle.

**Connection to:**
- **Magic numbers:** Generally avoid.
- **Type systems:** Tagged unions vs sentinels.
- **API design:** Defensive programming.

### Insight 6: Why This Pattern is Common

> "Use existing data as auxiliary storage" is a fundamental technique.

Other examples:
- **Game of Life:** Use bit 1 for new state.
- **Missing Number:** XOR indices and values.
- **First Missing Positive:** Use array indices as markers.

**Connection to:**
- **In-place string algorithms:** Reverse, etc.
- **Database indexing:** Materialized views.
- **Cache algorithms:** LRU, LFU use linked list + hash map.

### Insight 7: Connection to Sparse Matrices

> Sparse matrix storage formats (CSR, CSC) avoid storing zeros.

This problem is the OPPOSITE: we ADD zeros based on existing zeros. Both involve understanding zero structure.

**Connection to:**
- **Compressed sparse row (CSR):** Standard format.
- **Eigenvalues:** Zero rows affect rank.
- **Graph algorithms:** Sparse graph representation.

### Insight 8: Why Three Passes is Optimal

> In-place, we must read each cell to know if it's zero. Then write zeros. Then handle first row/col.

Lower bound: O(mn) reads + O(mn) writes. Three passes is optimal for the in-place approach.

**Connection to:**
- **I/O complexity:** External sorting.
- **Cache complexity:** Cache-oblivious algorithms.
- **Streaming algorithms:** One-pass, multi-pass.

### Insight 9: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image processing** | Mask propagation |
| **Database constraints** | Cascade nulls |
| **Spreadsheet formulas** | Cell references |
| **Boolean matrices** | Reachability, transitive closure |
| **Game boards** | Spread mechanics |
| **Physics simulations** | Boundary conditions |

**Image inpainting** uses similar logic: propagate known pixels to unknown regions.

### Insight 10: Generalization to Higher Dimensions

> The same trick works for 3D, 4D, ... tensors.

For 3D: use first 2D slice + first row + first column as markers. Adds complexity but follows the same pattern.

**Connection to:**
- **Tensors:** Multi-dimensional arrays.
- **NumPy/TensorFlow:** Same pattern in higher dimensions.
- **Distributed computing:** Partition along dimensions.

---

## 🧪 TEST CASES

| Matrix | Expected | Note |
|--------|----------|------|
| `[[1,1,1],[1,0,1],[1,1,1]]` | `[[1,0,1],[0,0,0],[1,0,1]]` | Standard |
| `[[0,1,2,0],[3,4,5,2],[1,3,1,5]]` | `[[0,0,0,0],[0,4,5,0],[0,3,1,0]]` | Multiple zeros |
| `[[1]]` | `[[1]]` | 1x1 no zero |
| `[[0]]` | `[[0]]` | 1x1 zero |
| `[[1,2,3,4],[5,0,7,8],[0,10,11,12],[13,14,15,0]]` | all rows/cols touched | Complex |
| `[[1,2,3],[4,5,6]]` | unchanged | No zeros |
| `[[1,0,3],[4,5,6]]` | `[[0,0,0],[4,0,6]]` | Single zero |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **First row/col** | **O(mn)** | **O(1)** | **✅ BEST** |
| Extra space | O(mn) | O(m+n) | ✅ Simpler |
| Sentinel | O(mn) | O(1) | ⚠️ Brittle |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Game of Life (LC 289) | Bit encoding | https://leetcode.com/problems/game-of-life/ |
| Spiral Matrix (LC 54) | Boundary shrinking | https://leetcode.com/problems/spiral-matrix/ |
| Rotate Image (LC 48) | In-place rotation | https://leetcode.com/problems/rotate-image/ |
| Transpose Matrix (LC 867) | Swap indices | https://leetcode.com/problems/transpose-matrix/ |
| Set Matrix Zeroes (LC 73) | **This problem** | https://leetcode.com/problems/set-matrix-zeroes/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Use existing data as auxiliary storage.** First row/col as markers.
2. **Cell (0,0) is special** — shared between row 0 and col 0. Use a separate flag.
3. **Three passes: mark, zero, handle first row/col.**
4. **O(m+n) extra space is the easy alternative.** But O(1) is achievable.
5. **Sentinel values are brittle.** Only use when input guarantees they won't appear.
6. **This pattern is common** — Game of Life, Missing Number, First Missing Positive.
7. **In-place algorithms** have a special elegance.
8. **Test edge cases:** 1x1, all zeros, no zeros, single row/col.
9. **The trick works for higher dimensions** but with more bookkeeping.
10. **Image inpainting** uses the same logic — propagate known to unknown.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Image inpainting** | Propagate known to unknown |
| **Sparse matrices** | CSR, CSC avoid zeros |
| **Database cascades** | Null propagation |
| **Boolean matrices** | Reachability |
| **Spreadsheets** | Cell references |
| **Game boards** | Spread mechanics |
| **In-place algorithms** | Use existing storage |
| **Cache algorithms** | LRU, LFU |
| **First Missing Positive** | Use indices as markers |
| **Game of Life** | Bit encoding |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive first-row/col trick in 60 seconds
- [x] Can code the 25-line solution in 90 seconds
- [x] Know the complexity: O(mn) time, O(1) space
- [x] Know the (0,0) collision issue
- [x] Can compare first-row/col vs extra space vs sentinel
- [x] Know why three passes is optimal
- [x] Can discuss the Game of Life parallel
- [x] Can list 5 real-world applications
- [x] Can generalize to higher dimensions

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 25.
**Insight:** "Use first row/col as markers. Cell (0,0) needs separate flag. Three passes: mark, zero, handle first row/col."