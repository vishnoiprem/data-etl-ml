# Transpose Matrix - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/transpose-matrix

## The Problem
```
Given an m x n matrix, return the TRANSPOSE of matrix.

The transpose of a matrix is the matrix flipped over its main diagonal,
switching the row and column indices: result[j][i] = matrix[i][j].

Examples:
    [[1, 2, 3],           [[1, 4, 7],
     [4, 5, 6],     ->     [2, 5, 8],
     [7, 8, 9]]            [3, 6, 9]]

    [[1, 2, 3],           [[1, 4],
     [4, 5, 6]]     ->     [2, 5],
                          [3, 6]]

Constraints:
- m == matrix.length, n == matrix[i].length
- 1 <= m, n <= 1000
- 1 <= m * n <= 10^5
- -10^9 <= matrix[i][j] <= 10^9
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The transpose REFLECTS the matrix across its main diagonal.

For a 3x3 matrix:
   (0,0) (0,1) (0,2)
   (1,0) (1,1) (1,2)
   (2,0) (2,1) (2,2)

The element at (i, j) MOVES to (j, i):
   - (0,1) moves to (1,0)
   - (1,2) moves to (2,1)
   - (2,0) moves to (0,2)

So if matrix[i][j] = 5, then in the transpose result[j][i] = 5.
```

### Step 2: The Trick
> "Two main approaches depending on whether the matrix is SQUARE:
>
> **Square (m == n):**
> - Swap matrix[i][j] with matrix[j][i] in place.
> - Only iterate over the UPPER triangle (j starts from i+1).
> - This avoids double-swapping.
> - Time O(m*n), Space O(1).
>
> **Non-square (m != n):**
> - In-place is IMPOSSIBLE because rows and columns have different lengths.
> - Must build a NEW matrix of size n x m.
> - Time O(m*n), Space O(m*n).
>
> **Pythonic (any shape):**
> - `zip(*matrix)` is Python's built-in transpose.
> - Convert tuples to lists with `list(row)`."

### Step 3: Why j starts from i+1?
> "If we iterate the WHOLE matrix (j from 0), we'd swap (0,1) and (1,0),
> then later swap them back when i=1, j=0. That's wasted work.
> By starting j from i+1, we only visit each pair once."

### Step 4: Why in-place is impossible for non-square?
> "If matrix is 2x3, we need to produce a 3x2 matrix. The dimensions
> change, so we MUST allocate new storage."

---

## What to Say Aloud in the Interview

**Opening:**
> "The transpose swaps rows and columns: element at row i, column j
> moves to row j, column i. So result[j][i] = matrix[i][j]."

**Key Insight:**
> "If the matrix is square, I can do it IN-PLACE by swapping
> matrix[i][j] with matrix[j][i] over the upper triangle (j > i).
> If it's rectangular, I must build a new matrix since dimensions change.
> In Python, `zip(*matrix)` does this elegantly."

**Algorithm (In-place for square):**
> "1. Get n = len(matrix).
> 2. For i from 0 to n-1:
> 3.    For j from i+1 to n-1:
> 4.       swap matrix[i][j] and matrix[j][i].
> 5. Return matrix."

**Algorithm (New matrix for any):**
> "1. Let m = rows, n = cols.
> 2. Create result of size n x m.
> 3. For i in 0..m-1, j in 0..n-1: result[j][i] = matrix[i][j].
> 4. Return result."

**Edge cases:**
- 1x1: return as-is `[matrix[0][0]]`
- Single row (m=1): result is columnar with one element per row
- Single column (n=1): result is a single row
- Rectangular: dimensions swap (m x n) -> (n x m)
- Empty matrix: return `[]`

**Complexity:**
- Time: O(m*n) for all approaches
- Space: O(1) for in-place (square only), O(m*n) for new matrix

---

## The 20 Implementations (Simple to Complex)

### Way 1: In-place swap (BEST for square matrices)
```python
def transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    if m != n:
        return [list(col) for col in zip(*matrix)]
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    return matrix
```

### Way 2: Verbose in-place (whiteboard-friendly)
```python
def transpose_matrix(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            temp = matrix[i][j]
            matrix[i][j] = matrix[j][i]
            matrix[j][i] = temp
    return matrix
```

### Way 3: Build new matrix (works for any m x n)
```python
def transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    result = [[0] * m for _ in range(n)]
    for i in range(m):
        for j in range(n):
            result[j][i] = matrix[i][j]
    return result
```

### Way 4: List comprehension (Pythonic)
```python
def transpose_matrix(matrix):
    return [list(row) for row in zip(*matrix)]
```

### Way 5-8: Functional variants (map, zip_longest, etc.)
- See code file for full implementations.

### Way 9: Enumerate-based (explicit index tracking)

### Way 10: Dictionary-based grouping

### Way 11: Recursive (educational)
```python
def transpose_matrix(matrix):
    if not matrix or not matrix[0]: return []
    first_col = [row[0] for row in matrix]
    rest = [row[1:] for row in matrix if len(row) > 1]
    return [first_col] + transpose_matrix(rest) if rest else [first_col]
```

### Way 12: In-place with enumerate (square only)

### Way 13: Block transpose (cache-friendly)
```python
def transpose_matrix(matrix):
    m, n = len(matrix), len(matrix[0])
    result = [[None] * m for _ in range(n)]
    block = 32  # Cache-line friendly
    for i0 in range(0, m, block):
        for j0 in range(0, n, block):
            for i in range(i0, min(i0 + block, m)):
                for j in range(j0, min(j0 + block, n)):
                    result[j][i] = matrix[i][j]
    return result
```

### Way 14: array module (memory-efficient)
### Way 15: Generator (lazy streaming)
### Way 16: XOR swap (clever but not recommended)
```python
def transpose_matrix(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j] ^= matrix[j][i]
            matrix[j][i] ^= matrix[i][j]
            matrix[i][j] ^= matrix[j][i]
    return matrix
```

### Way 17: Most concise one-liner
```python
def transpose_matrix(matrix):
    return list(map(list, zip(*matrix)))
```

### Way 18: Pandas (dataframe-style)
### Way 19: Parallelized with ThreadPoolExecutor
### Way 20: Final clean version

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Square matrix    | Way 1    | O(1) space   |
| Non-square       | Way 4    | Most Pythonic|
| Interview (any)  | Way 1/4  | Either works |
| Cache-heavy      | Way 13   | Block-wise   |
| One-liner        | Way 17   | Concise      |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| In-place (square) | O(mn) | O(1) | Best when square |
| New matrix | O(mn) | O(mn) | Works for any shape |
| zip(*) | O(mn) | O(mn) | Pythonic |
| Block transpose | O(mn) | O(mn) | Cache-friendly |
| Recursive | O(mn) | O(mn) | Educational |

---

## Walkthrough Example

```
matrix = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]]

In-place (Way 1):
i=0: j=1 -> swap(0,1)=2 <-> (1,0)=4. Matrix: [[1,4,3],[2,5,6],[7,8,9]]
      j=2 -> swap(0,2)=3 <-> (2,0)=7. Matrix: [[1,4,7],[2,5,6],[3,8,9]]
i=1: j=2 -> swap(1,2)=6 <-> (2,1)=8. Matrix: [[1,4,7],[2,5,8],[3,6,9]]
i=2: (no inner loop)

Result: [[1,4,7],[2,5,8],[3,6,9]] ✓
```

```
Non-square example:
matrix = [[1, 2, 3],    Result = [[1, 4],
          [4, 5, 6]]               [2, 5],
                                   [3, 6]]

zip(*matrix) = zip([1,2,3], [4,5,6])
            = [(1,4), (2,5), (3,6)]
list(map(list, ...)) = [[1,4], [2,5], [3,6]] ✓
```

---

## Best Answer to Memorize

```python
def transpose_matrix(matrix):
    # In-place for square, new matrix otherwise
    m, n = len(matrix), len(matrix[0])
    if m == n:
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        return matrix
    return [list(col) for col in zip(*matrix)]
```

**OR the pure Pythonic version:**
```python
def transpose_matrix(matrix):
    return [list(col) for col in zip(*matrix)]
```

---

## Key Insights

### Why j starts from i+1?
> "Iterating the whole matrix would swap each pair twice (once when (i,j),
> once when (j,i)). Starting j from i+1 visits each pair exactly once.
> This works because matrix[i][j] == matrix[j][i] after a full transpose,
> so we cut the work in half."

### Why in-place is impossible for non-square?
> "A 2x3 matrix has 2 rows of 3 elements. The transpose is 3 rows of 2 elements.
> We can't reshape in-place - we MUST allocate new storage."

### What does zip(*matrix) do?
> "Python's `*` unpacks the matrix into individual rows as separate args.
> zip then groups them by index: element 0 from each row, element 1 from each,
> etc. These are exactly the COLUMNS of the original matrix, which become
> the ROWS of the transpose."

### Why prefer in-place when possible?
> "O(1) extra space vs O(mn). For huge square matrices, this matters.
> Modern systems may also be more cache-friendly (in-place vs allocation)."

### Off-by-one considerations:
> "Always use `j = i + 1` not `j = i`. Starting at i would swap diagonal
> elements with themselves (waste). Starting at 0 would double-swap."

---

## Test Cases

| matrix | Expected Result |
|--------|-----------------|
| [[1,2,3],[4,5,6],[7,8,9]] | [[1,4,7],[2,5,8],[3,6,9]] |
| [[1,2,3],[4,5,6]] | [[1,4],[2,5],[3,6]] |
| [[1]] | [[1]] |
| [[1,2,3,4]] | [[1],[2],[3],[4]] |
| [[1],[2],[3],[4]] | [[1,2,3,4]] |
| [[1,2],[3,4]] | [[1,3],[2,4]] |
| [[1,2,3,4],[5,6,7,8]] | [[1,5],[2,6],[3,7],[4,8]] |
| [] | [] |

---

## Common Pitfalls

1. **Double swapping**: Iterating j from 0 instead of i+1.
2. **Trying in-place on non-square**: Impossible - allocate new.
3. **Forgetting to convert tuples**: `zip` returns tuples, not lists.
4. **Wrong dimensions for new matrix**: Result is n x m, NOT m x n.
5. **Off-by-one in range**: `range(i+1, n)` not `range(i+1, n+1)`.
6. **Forgetting to handle empty matrix**.

---

## Why This Problem Matters

> "Tests:
> 1. Understanding the transpose operation (linear algebra basics).
> 2. Choosing between in-place and new-matrix based on shape.
> 3. Loop optimization (j starts from i+1).
> 4. Foundation for image processing, graph adjacency matrices,
>    and linear algebra operations.
> 5. Pattern similar to: rotate image, search 2D matrix, set matrix zeros,
>    multiply matrices, matrix diagonal sum."

---

## Beyond Transpose: Related Operations

1. **Rotate 90° clockwise**: Transpose + reverse each row.
2. **Rotate 90° counter-clockwise**: Transpose + reverse each column.
3. **Flip horizontal**: Reverse each row.
4. **Flip vertical**: Reverse row order.
5. **Rotate 180°**: Reverse rows + reverse each row.

```python
def rotate_90_clockwise(matrix):
    # Transpose, then reverse each row
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return matrix
```
