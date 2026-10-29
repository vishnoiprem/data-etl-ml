# Toeplitz Matrix - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/toeplitz-matrix

## The Problem
```
Given an m x n matrix, return True if the matrix is Toeplitz.
A matrix is Toeplitz if every diagonal from top-left to bottom-right
contains the same elements. Equivalently, matrix[i][j] must equal
matrix[i+1][j+1] for all valid (i, j).

Examples:
    [[1,2,3,4],
     [5,1,2,3],
     [9,5,1,2]] -> True
    [[1,2],
     [2,2]] -> False

Constraints:
- 1 <= m, n <= 20
- 0 <= matrix[i][j] <= 99
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
A Toeplitz matrix has constant diagonals. Every diagonal from top-left
to bottom-right has all the same value.
```

### Step 2: The Trick
> "KEY INSIGHT: The condition 'every diagonal has same elements' is
> EQUIVALENT to 'matrix[i][j] == matrix[i+1][j+1] for all (i, j)'.
>
> Why? If every diagonal has constant value, then consecutive diagonal
> elements (at positions (i, j) and (i+1, j+1)) must be equal.
> Conversely, if all consecutive pairs on each diagonal are equal,
> then the entire diagonal has the same value."

### Step 3: Algorithm
> "1. For each (i, j) in [0, m-1) x [0, n-1):
> 2. If matrix[i][j] != matrix[i+1][j+1]: return False.
> 3. Return True."

### Step 4: Why this works
> "Diagonal elements are at (i, j), (i+1, j+1), (i+2, j+2), ...
> For all to be equal, each adjacent pair must be equal. So we just
> check (i, j) vs (i+1, j+1) for all (i, j)."

### Step 5: Memory-constrained variant
> "If only one row at a time is in memory, keep prev_row and check
> prev_row[j] == curr_row[j+1] for all j."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to verify if a matrix is Toeplitz - every diagonal from
> top-left to bottom-right has identical elements."

**Key Insight:**
> "Equivalent condition: matrix[i][j] == matrix[i+1][j+1] for all
> valid (i, j). Adjacent diagonal cells must be equal."

**Algorithm:**
> "1. For each (i, j) in [0, m-1) x [0, n-1):
> 2. If matrix[i][j] != matrix[i+1][j+1]: return False.
> 3. Return True."

**Why this works:**
> "Diagonal elements are at (i, j), (i+1, j+1), (i+2, j+2), etc.
> For all to be equal, just check adjacent pairs."

**Edge cases:**
- 1x1 matrix: vacuously True.
- 1xN or Nx1: trivially True (no (i, j) with both i+1 and j+1 in bounds).
- All same values: True.
- Differ at any diagonal: False.

**Complexity:**
- Time:  O(m*n) - check each cell once.
- Space: O(1) - no extra data structures.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Direct comparison (BEST - Memorize!)
```python
def isToeplitzMatrix_1(matrix):
    if not matrix or not matrix[0]:
        return True
    m, n = len(matrix), len(matrix[0])
    for i in range(m - 1):
        for j in range(n - 1):
            if matrix[i][j] != matrix[i + 1][j + 1]:
                return False
    return True
```

### Way 2: all() with generator
### Way 3: zip adjacent rows
### Way 4: enumerate + zip
### Way 5: Iterate over diagonals
### Way 6: Use set for each diagonal
### Way 7: Numpy vectorized
### Way 8: Map zip diagonals
### Way 9: Group by (i-j) - diagonal grouping
### Way 10: reduce
### Way 11: Class-based
### Way 12: pairwise (Python 3.10+)
### Way 13: Memory-constrained (one row at a time)
### Way 14: all() compact
### Way 15: Generator check
### Way 16: itertools.product
### Way 17: Early return with flag
### Way 18: map with lambda
### Way 19: One-liner
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | Direct check |
| Memory-constrained | Way 13   | Row at a time|
| numpy available    | Way 7    | Vectorized   |
| Educational        | Way 5    | Clear diag   |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Direct (Way 1) | O(mn) | O(1) | Best general |
| numpy (Way 7) | O(mn) | O(mn) | Vectorized |
| Memory-constrained (Way 13) | O(mn) | O(n) | One row at a time |
| Diagonal grouping (Way 9) | O(mn) | O(m+n) | Hash-based |

---

## Walkthrough Example

```
matrix = [[1, 2, 3, 4],
          [5, 1, 2, 3],
          [9, 5, 1, 2]]

Check (0,0) vs (1,1): 1 == 1 ✓
Check (0,1) vs (1,2): 2 == 2 ✓
Check (0,2) vs (1,3): 3 == 3 ✓
Check (1,0) vs (2,1): 5 == 5 ✓
Check (1,1) vs (2,2): 1 == 1 ✓
Check (1,2) vs (2,3): 2 == 2 ✓

All checks pass. Return True. ✓

Verify diagonals:
- Diagonal from (0,0): 1, 1, 1 ✓
- Diagonal from (0,1): 2, 2, 2 ✓
- Diagonal from (0,2): 3, 3 ✓
- Diagonal from (0,3): 4 ✓
- Diagonal from (1,0): 5, 5 ✓
- Diagonal from (2,0): 9 ✓
All diagonals constant. Toeplitz!
```

```
matrix = [[1, 2],
          [2, 2]]

Check (0,0) vs (1,1): 1 != 2 ✗
Return False.

Diagonal from (0,0): 1, 2 — not constant. Not Toeplitz.
```

---

## Best Answer to Memorize

```python
def isToeplitzMatrix(matrix):
    return all(matrix[i][j] == matrix[i + 1][j + 1]
               for i in range(len(matrix) - 1)
               for j in range(len(matrix[0]) - 1))
```

**~3 lines. O(m*n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why check matrix[i][j] == matrix[i+1][j+1]?
> "Adjacent diagonal cells differ by one row and one column. So the
> pair (i, j) and (i+1, j+1) are adjacent on the same diagonal.
> For the diagonal to be constant, all such pairs must be equal."

### Why does this work for the memory-constrained case?
> "We only need prev_row[j] and curr_row[j+1] — these are adjacent
> diagonal cells. We don't need the whole matrix in memory."

### Why is numpy O(m*n) and not faster?
> "numpy slicing creates views, but the comparison is still O(m*n).
> The advantage is constant factor speedup due to vectorization."

### What about 1x1 or 1xN matrices?
> "1x1: vacuously True (no (i, j) with both i+1 and j+1 valid).
> 1xN: only one row, no (i+1) exists for i=0. True.
> Nx1: only one col, no (j+1) exists for j=0. True."

---

## Test Cases

| matrix | Expected |
|--------|----------|
| [[1,2,3,4],[5,1,2,3],[9,5,1,2]] | True |
| [[1,2],[2,2]] | False |
| [[99]] | True |
| [[1,2,3,4,5]] | True |
| [[1],[2],[3],[4]] | True |
| [[5,5,5],[5,5,5],[5,5,5]] | True |
| [[1,2],[3,4]] | False |
| [[1,2,3],[4,1,2],[5,4,1]] | True |
| [] | True |

---

## Common Pitfalls

1. **Forgetting the size check**: range(m-1), not range(m). Last row has no (i+1).
2. **Comparing wrong indices**: Use (i+1, j+1), not (i, j+1) or (i+1, j).
3. **Off-by-one**: m-1 x n-1 checks, not m x n.
4. **Memory-constrained = no full matrix**: Use prev_row pattern.
5. **Empty matrix**: Return True (vacuously).

---

## Why This Problem Matters

> "Tests:
> 1. Diagonal pattern recognition.
> 2. Adjacent pair comparison.
> 3. Memory-constrained variant.
> 4. Foundation for: matrix validation, image processing, signal processing."

---

## Beyond This Problem: Related Patterns

### 1. Valid Diagonal Sudoku (LC 2133)
```python
# Different: only check specific diagonals (3 in sudoku).
```

### 2. Diagonal Traverse (LC 498)
```python
# Visit elements along diagonals.
# Not Toeplitz check.
```

### 3. Search 2D Matrix II (LC 240)
```python
# Use sorted property (different from Toeplitz).
```

### 4. Set Matrix Zeroes (LC 73)
```python
# Different problem entirely.
```

---

## Connection to Matrix Validation Problems

This problem uses the "adjacent pair check" pattern:

```
For each (i, j), check that a specific adjacent cell satisfies
a property.

- Toeplitz: matrix[i][j] == matrix[i+1][j+1]
- Symmetric: matrix[i][j] == matrix[j][i]
- Identity-like: matrix[i][i] == 1
- Etc.

This pattern works for many matrix validation problems.
```

---

## Quick Checklist

When given a similar problem:
- [ ] What's the pattern? (diagonal, symmetric, etc.)
- [ ] What's the equivalent condition? (adjacent pair check)
- [ ] What's the boundary? (m-1, n-1)
- [ ] Is it memory-constrained? (use prev_row)
- [ ] Can numpy help? (yes for large matrices)

---

## Memory-Constrained Variant

The follow-up question is important: what if only one row at a time fits in memory?

```python
def isToeplitzMatrix_one_row(matrix):
    prev_row = None
    for row in matrix:
        if prev_row is not None:
            for j in range(len(row) - 1):
                if prev_row[j] != row[j + 1]:
                    return False
        prev_row = row
    return True
```

This uses only O(n) extra space (for prev_row) instead of O(m*n).

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 766 - Toeplitz Matrix](https://leetcode.com/problems/toeplitz-matrix/)
