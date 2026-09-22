# Rotate Image - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-image

## The Problem
```
Given an n x n matrix, rotate it 90 degrees clockwise IN PLACE.
The function returns the modified input matrix.

Examples:
    [[1,2,3],       [[7,4,1],
     [4,5,6],   ->   [8,5,2],
     [7,8,9]]        [9,6,3]]
    [[2,6,8],       [[9,3,2],
     [3,4,8],   ->   [8,4,6],
     [9,8,8]]        [8,8,8]]

Constraints:
- n == matrix.length == matrix[i].length
- 1 <= n <= 20
- -10^3 <= matrix[i][j] <= 10^3
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
For 90° CW rotation:
- Position (i, j) moves to (j, n-1-i).
- We must do this IN PLACE - no extra matrix.
```

### Step 2: The Trick
> "KEY INSIGHT: 90° CW rotation = TRANSPOSE + REVERSE each row.
>
> - Transpose: swap matrix[i][j] with matrix[j][i] for i < j.
> - Reverse each row: each row reversed left-to-right.
>
> Composition: (i, j) -> (j, i) [transpose] -> (j, n-1-i) [reverse row].
> That's exactly the 90° CW rotation formula."

### Step 3: Why it works
> "Transpose moves element at (i, j) to position (j, i).
> Reversing row j moves (j, i) to (j, n-1-i).
> So composed: (i, j) ends up at (j, n-1-i). ✓"

### Step 4: In-place?
> "Yes! Both transpose and reverse are in-place operations.
> Total space: O(1)."

### Step 5: Algorithm
> "1. Transpose: for i in [0, n), for j in [i+1, n): swap matrix[i][j], matrix[j][i].
> 2. Reverse each row: row.reverse() for each row.
> 3. Return matrix."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to rotate an n x n matrix 90 degrees clockwise IN PLACE."

**Key Insight:**
> "90° CW rotation = TRANSPOSE + REVERSE each row.
> - Transpose: swap matrix[i][j] and matrix[j][i].
> - Reverse each row: row[i], row[n-1-i] = row[n-1-i], row[i].
> - Composition gives the rotation."

**Algorithm:**
> "1. Transpose: nested loop swap upper-triangular elements.
> 2. Reverse each row: in-place row reversal.
> 3. Return matrix."

**Why this works:**
> "Element at (i, j) under transpose goes to (j, i).
> Element at (j, i) under reverse row goes to (j, n-1-i).
> Composed: (i, j) -> (j, n-1-i). ✓"

**Edge cases:**
- 1x1: no change.
- 2x2: transpose = reverse, so just transpose.
- n is odd: center element stays.

**Complexity:**
- Time:  O(n^2).
- Space: O(1) - in place.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Transpose + reverse (BEST - Memorize!)
```python
def rotate_image_1(matrix):
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Reverse each row
    for row in matrix:
        row.reverse()
    return matrix
```

### Way 2: Verbose version
### Way 3: Layer-by-layer 4-way swap
### Way 4: zip + reverse
### Way 5: New matrix with formula
### Way 6: enumerate for transpose
### Way 7: numpy.rot90
### Way 8: reversed + zip
### Way 9: Direct formula into new list
### Way 10: Single loop with reversed()
### Way 11: Recursive
### Way 12: Class-based
### Way 13: itertools
### Way 14: Slicing + list comp
### Way 15: Helper functions
### Way 16: Layer with cleaner offset
### Way 17: reversed builtin
### Way 18: Matrix slicing transpose
### Way 19: One-liner
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(n^2) in-pl |
| Want simple code   | Way 19   | One-liner    |
| numpy available    | Way 7    | Built-in     |
| Educational        | Way 3    | Layer-by-lay |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Transpose+Reverse (Way 1) | O(n^2) | O(1) | Best general |
| Layer-by-layer (Way 3) | O(n^2) | O(1) | One-pass |
| New matrix (Way 5) | O(n^2) | O(n^2) | Easier but more space |
| numpy (Way 7) | O(n^2) | O(n^2) | Built-in |

---

## Walkthrough Example

```
matrix = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]]

Step 1: Transpose
[[1, 4, 7],
 [4, 5, 8],  <- swap matrix[0][1]=2 with matrix[1][0]=4
 [7, 8, 9]]  <- swap matrix[0][2]=3 with matrix[2][0]=7, matrix[1][2]=6 with matrix[2][1]=8

After transpose:
[[1, 4, 7],
 [2, 5, 8],
 [3, 6, 9]]

Step 2: Reverse each row
Row 0: [1, 4, 7] -> [7, 4, 1]
Row 1: [2, 5, 8] -> [8, 5, 2]
Row 2: [3, 6, 9] -> [9, 6, 3]

Result:
[[7, 4, 1],
 [8, 5, 2],
 [9, 6, 3]]
```

```
matrix = [[2, 6, 8],
          [3, 4, 8],
          [9, 8, 8]]

Step 1: Transpose
[[2, 3, 9],
 [6, 4, 8],
 [8, 8, 8]]

Step 2: Reverse each row
[[9, 3, 2],
 [8, 4, 6],
 [8, 8, 8]]
```

---

## Best Answer to Memorize

```python
def rotate_image(matrix):
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Reverse each row
    for row in matrix:
        row.reverse()
    return matrix
```

**~5 lines. O(n^2) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why transpose + reverse each row?
> "Composition of two operations: transpose then row-reverse.
> (i, j) -> (j, i) [transpose] -> (j, n-1-i) [row reverse].
> That's the 90° CW rotation formula."

### Why in-place?
> "Both operations (transpose and reverse) can be done in-place.
> No need for extra matrix."

### Why only swap upper-triangular in transpose?
> "Transpose swaps (i, j) and (j, i). Swapping the lower-triangular
> too would un-transpose. Only swap when i < j (upper triangle)."

### Why reverse rows, not columns?
> "For 90° CW: column-reverse would give 90° CCW. We want CW, so reverse rows."

---

## Test Cases

| matrix | Expected |
|--------|----------|
| [[1,2,3],[4,5,6],[7,8,9]] | [[7,4,1],[8,5,2],[9,6,3]] |
| [[2,6,8],[3,4,8],[9,8,8]] | [[9,3,2],[8,4,6],[8,8,8]] |
| [[42]] | [[42]] |
| [[1,2],[3,4]] | [[3,1],[4,2]] |
| [[1..4],[5..8],[9..12],[13..16]] | [[13,9,5,1],[14,10,6,2],[15,11,7,3],[16,12,8,4]] |
| [[5,5],[5,5]] | [[5,5],[5,5]] |

---

## Common Pitfalls

1. **Swapping both triangles**: Only swap i < j (upper triangle).
2. **Confusing CW vs CCW**: Row-reverse = CW. Column-reverse = CCW.
3. **Modifying original**: Need to modify input, not return new.
4. **Off-by-one in transpose**: range(i+1, n), not range(0, n).
5. **Not returning**: Function should return matrix.

---

## Why This Problem Matters

> "Tests:
> 1. In-place matrix manipulation.
> 2. Two-step composition (transpose + reverse).
> 3. Index calculation.
> 4. Foundation for: image rotation, matrix algorithms, computer graphics."

---

## Beyond This Problem: Related Patterns

### 1. Transpose Matrix (LC 867)
```python
# Just the transpose step.
```

### 2. Rotate List (LC 189)
```python
# 1D rotation - different algorithm.
```

### 3. Spiral Matrix (LC 54)
```python
# Traverse in spiral - different.
```

### 4. Image Rotation (in graphics)
```python
# Same principle: rotate pixel coordinates.
```

---

## Connection to Matrix Transformations

This problem uses "decomposition into simple operations":

```
90° CW rotation = TRANSPOSE + REVERSE each row
90° CCW rotation = TRANSPOSE + REVERSE each column
180° rotation = REVERSE each row + REVERSE each column
```

This decomposition is clean and efficient. The principle:
- Transpose swaps (i, j) and (j, i).
- Reversing rows moves elements horizontally.
- Reversing columns moves elements vertically.
- Various combinations give various rotations.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the rotation angle? (CW = row reverse, CCW = col reverse)
- [ ] In-place required? (use transpose + reverse)
- [ ] What dimensions? (square vs rectangular - transpose works for any, reverse needs square for rotation)
- [ ] Can I use numpy? (Way 7)
- [ ] Is the formula enough? (new[j][n-1-i] = old[i][j])

---

## Alternative: Direct Formula

```python
def rotate_image_direct(matrix):
    n = len(matrix)
    new = [[matrix[n - 1 - j][i] for j in range(n)] for i in range(n)]
    matrix[:] = new
    return matrix
```

This uses the formula `new[i][j] = old[n-1-j][i]` directly.
O(n^2) extra space, but easier to understand.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 48 - Rotate Image](https://leetcode.com/problems/rotate-image/)
