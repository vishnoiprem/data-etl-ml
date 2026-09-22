# Set Matrix Zeros - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/set-matrix-zeroes

## The Problem
```
Given an m x n matrix mat. If any element is zero, set its entire row
and column to zero. Do it IN PLACE.

Examples:
    mat = [
      [1, 2, 3],
      [4, 0, 6],
      [7, 8, 9]
    ]
    -> [
      [1, 0, 3],
      [0, 0, 0],
      [7, 0, 9]
    ]

    mat = [
      [0, 1, 2, 0],
      [3, 4, 5, 2],
      [1, 3, 1, 5]
    ]
    -> [
      [0, 0, 0, 0],
      [0, 4, 5, 0],
      [0, 3, 1, 0]
    ]

Constraints:
- m, n in [1, 20]
- -2^31 <= mat[i][j] <= 2^31 - 1
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The challenge: zeroing cells based on others creates a CASCADE effect.
Once you zero a row/col, those zeros also affect other rows/cols.

Simple approach: track which ROWS and COLS have zeros, then zero them.
- Time: O(m*n) - visit each cell multiple times
- Space: O(m + n) - track row/col flags

Optimal approach: reuse the matrix itself as markers!
- Time: O(m*n)
- Space: O(1)
```

### Step 2: The Trick (Best Approach)
> "Use the FIRST ROW and FIRST COLUMN as markers!
>
> 1. Save state: did first row have a zero? did first col have a zero?
> 2. For each zero at mat[i][j] (i, j != 0):
>    - Set mat[i][0] = 0  (mark row i)
>    - Set mat[0][j] = 0  (mark col j)
> 3. For each cell (i, j) (i, j != 0):
>    - If mat[i][0] == 0 OR mat[0][j] == 0: set to 0
> 4. Handle first row/col based on saved flags"

### Step 3: Why First Row/Col?
> "The first row/col are ALREADY there in the matrix. Using them as
> markers means ZERO additional space!
>
> The trick: we can't process them as part of the inner loop because
> THEY are the markers. So save their state FIRST and process LAST."

---

## What to Say Aloud in the Interview

**Opening:**
> "I have an m x n matrix. For any cell that's zero, I need to set its
> entire row and column to zero. Must be done in place."

**Key Insight:**
> "Use the first row and first column as MARKERS!
> - When I see a zero at mat[i][j]: set mat[i][0] = 0 and mat[0][j] = 0
> - Later: if mat[i][0] == 0 OR mat[0][j] == 0, set mat[i][j] = 0
> - Handle first row/col separately (save their state first)."

**Algorithm:**
> "1. Detect if first row has any zero (save flag)
> 2. Detect if first col has any zero (save flag)
> 3. For i in 1..m-1, j in 1..n-1:
>    if mat[i][j] == 0:
>      mat[i][0] = 0
>      mat[0][j] = 0
> 4. For i in 1..m-1, j in 1..n-1:
>    if mat[i][0] == 0 or mat[0][j] == 0:
>      mat[i][j] = 0
> 5. If first row had zero, zero out first row
> 6. If first col had zero, zero out first col"

**Why save flags first:**
> "After step 3, mat[i][0] and mat[0][j] may have been set to 0 due to
> inner-cell zeros. We can't tell if first row/col ORIGINALLY had zeros.
> So we capture that BEFORE step 3."

**Edge cases:**
- Single cell [[0]]: zero stays
- Single row/col: handled
- All zeros: everything zeros
- No zeros: nothing changes
- Zero in first row: first row flags trigger final zeroing
- Zero in first col: first col flags trigger final zeroing

**Complexity:**
- Time: O(m*n) - each cell visited constant times
- Space: O(1) - only a few flags

---

## The 20 Implementations (Simple to Complex)

### Way 1: First row/col markers (BEST - Memorize!)
```python
def setMatrixZeros(mat):
    if not mat or not mat[0]: return mat
    m, n = len(mat), len(mat[0])
    fr = any(mat[0][j] == 0 for j in range(n))
    fc = any(mat[i][0] == 0 for i in range(m))
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = mat[0][j] = 0
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0
    if fr:
        for j in range(n): mat[0][j] = 0
    if fc:
        for i in range(m): mat[i][0] = 0
    return mat
```

### Way 2-3: With extra space
- Way 2: Use sets for zero rows and zero cols
- Way 3: Use boolean lists

### Way 4-5: Brute force with sentinels
- Way 4: Use None as marker
- Way 5: Use float('inf') as marker

### Way 6-7: Position tracking
- Way 6: List of (i, j) tuples
- Way 7: Dict for row/col flags

### Way 8-13: Variations of Way 1
- Way 8: Cleaner version with explicit detection
- Way 9: BitSet (using bitwise operations)
- Way 10: Bool lists readable
- Way 11: With helper functions
- Way 12: 3-pass markers
- Way 13: Single bool flag for first row/col

### Way 14: Indices lists

### Way 15-16: Most concise variants

### Way 17: Numpy (vectorized)

### Way 18: Recursive (collect zeros, then apply)

### Way 19: Class-based

### Way 20: Final cleanest

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| In-place         | Way 1    | O(1) space   |
| Simpler          | Way 2/3  | Extra space  |
| Functional       | Way 19   | Class-based  |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Way 1 (in-place) | O(mn) | O(1) |
| Way 2-3 (extra space) | O(mn) | O(m+n) |
| Way 4-5 (sentinel) | O(mn²) | O(1) |

---

## Walkthrough Example

```
mat = [
  [1, 2, 3],
  [4, 0, 6],
  [7, 8, 9]
]

Step 1: Check first row/col for zeros.
- First row: [1, 2, 3], no zeros. fr = False
- First col: [1, 4, 7], no zeros. fc = False

Step 2: Mark rows/cols for inner cells.
- (1, 1) = 0: mat[1][0] = 0, mat[0][1] = 0
- After: [
    [1, 0, 3],
    [0, 0, 6],
    [7, 8, 9]
  ]

Step 3: Zero out based on markers.
- (1, 1): mat[1][0] = 0, set to 0
- (1, 2): mat[1][0] = 0, set to 0
- (2, 1): mat[0][1] = 0, set to 0
- After: [
    [1, 0, 3],
    [0, 0, 0],
    [7, 0, 9]
  ]

Step 4-5: First row/col unchanged (fr=False, fc=False).

Result: ✓
```

## Best Answer to Memorize

```python
def setMatrixZeros(mat):
    if not mat or not mat[0]:
        return mat
    m, n = len(mat), len(mat[0])
    fr = any(mat[0][j] == 0 for j in range(n))
    fc = any(mat[i][0] == 0 for i in range(m))
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][j] == 0:
                mat[i][0] = mat[0][j] = 0
    for i in range(1, m):
        for j in range(1, n):
            if mat[i][0] == 0 or mat[0][j] == 0:
                mat[i][j] = 0
    if fr:
        for j in range(n):
            mat[0][j] = 0
    if fc:
        for i in range(m):
            mat[i][0] = 0
    return mat
```

**17 lines. O(mn) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why use first row/col as markers?
> "Reuse what's already there! Saves O(m+n) extra space.
> But we need to handle them SEPARATELY because they ARE the markers."

### Why save flags before step 2?
> "After step 2, mat[0][j] and mat[i][0] may have been set to 0 due
> to inner cells. We lose info about original zeros in first row/col."

### Why not just create a copy?
> "Extra space. The in-place approach is the standard interview answer."

### What if we use a sentinel like None?
> "We can! First pass mark, second pass replace. But we need to be
> careful if None could be a valid value (use float('inf') instead)."

---

## Test Cases

| Input | Output | Why |
|-------|--------|-----|
| [[1,2,3],[4,0,6],[7,8,9]] | [[1,0,3],[0,0,0],[7,0,9]] | Standard |
| [[0,1,2,0],[3,4,5,2],[1,3,1,5]] | [[0,0,0,0],[0,4,5,0],[0,3,1,0]] | Multiple zeros |
| [[1,2],[3,4]] | [[1,2],[3,4]] | No zeros |
| [[0]] | [[0]] | Single |
| [[0,0],[0,0]] | [[0,0],[0,0]] | All zeros |
| [[1,0,3],[4,5,6],[7,8,9]] | [[0,0,0],[4,0,6],[7,0,9]] | First row zero |
| [[1,2,3],[0,5,6],[7,8,9]] | [[0,2,3],[0,0,0],[0,8,9]] | First col zero |

## Common Pitfalls

1. **Processing first row/col in inner loop**: They ARE markers, handle last.
2. **Forgetting to save flags**: Need original state for first row/col.
3. **Setting marker cells to 0 in step 2**: This OVERWRITES marker info!
   Only set them in step 2 as MARKERS, not actual zeros.
4. **Wrong sentinel value**: Use float('inf') or unique value, not None if
   valid.

## Why This Problem Matters

> "Tests:
> 1. In-place matrix manipulation (CRITICAL skill)
> 2. Using data structure as its own metadata
> 3. Order of operations matters
> 4. Pattern similar to: rotate image, spiral matrix, sudoku validation
> 5. Real-world: image processing, spreadsheet operations"
