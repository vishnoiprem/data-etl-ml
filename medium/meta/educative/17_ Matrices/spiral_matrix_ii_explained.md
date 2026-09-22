# Spiral Matrix II - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix-ii

## The Problem
```
Given a positive integer n, generate an n x n matrix filled with elements
from 1 to n^2 in SPIRAL ORDER (clockwise from top-left, moving inward).

Examples:
    n = 3  ->  [[1, 2, 3],
                [8, 9, 4],
                [7, 6, 5]]

    n = 1  ->  [[1]]

    n = 4  ->  [[ 1,  2,  3,  4],
                [12, 13, 14,  5],
                [11, 16, 15,  6],
                [10,  9,  8,  7]]

Constraints:
- 1 <= n <= 20
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
This is the INVERSE of "Spiral Matrix I" (which READS in spiral order).
Here, we WRITE in spiral order, filling cells with 1, 2, 3, ..., n^2.

For n=3:
- Start at (0,0): write 1
- Move right: (0,1)=2, (0,2)=3
- Move down: (1,2)=4, (2,2)=5
- Move left: (2,1)=6, (2,0)=7
- Move up: (1,0)=8
- Move right (inner ring): (1,1)=9

Result:
[[1, 2, 3],
 [8, 9, 4],
 [7, 6, 5]]
```

### Step 2: The Trick
> "Use the SAME BOUNDARY SHRINKING trick as Spiral Matrix I!
> - Track top, bottom, left, right.
> - Each round fills 4 sides: top row, right column, bottom row, left column.
> - After each side, shrink the boundary inward.
> - Instead of appending to a result list, ASSIGN num to matrix[r][c].
> - Use a counter `num` that increments from 1 to n^2."

### Step 3: Why Check Bounds?
> "After filling the top row, top is incremented. For the bottom row check,
> we need top <= bottom. For the left column, we need left <= right.
> Without checks, we'd over-write already-filled cells in single-row/col cases."

### Step 4: Relationship to Spiral Matrix I (read)
> "This problem is essentially the INVERSE operation:
> - Read spiral: append matrix[r][c] to result.
> - Write spiral: assign num to matrix[r][c].
> - Both use the same boundary-shrinking pattern.
> - If you've mastered Spiral Matrix I, this is just an INVERSION."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to fill an n x n matrix with numbers 1 to n^2 in spiral order,
> starting from the top-left and going clockwise inward. This is the
> inverse of reading a spiral matrix."

**Key Insight:**
> "Use BOUNDARY SHRINKING:
> - Track top, bottom, left, right.
> - Each round: fill top row (left to right), right column (top to bottom),
>   bottom row (right to left, if valid), left column (bottom to top, if valid).
> - Increment a counter `num` from 1 to n^2.
> - Shrink boundaries inward after each side."

**Algorithm:**
> "1. Initialize matrix = [[0]*n for _ in range(n)].
> 2. top=0, bottom=n-1, left=0, right=n-1, num=1.
> 3. While top <= bottom and left <= right:
>    a. Top row (left to right): matrix[top][j] = num; num++. top++.
>    b. Right column (top to bottom): matrix[i][right] = num; num++. right--.
>    c. (if top <= bottom) Bottom row (right to left): bottom--.
>    d. (if left <= right) Left column (bottom to top): left++.
> 4. Return matrix."

**Why check bounds in steps c and d:**
> "After step a, top has incremented. If top > bottom (e.g., single row case),
> we've already filled the whole matrix. Similarly for step d."

**Edge cases:**
- n=1: just return [[1]]
- n=2: outer ring (no center)
- n=3: outer ring + center cell
- n=4: outer ring + inner ring (no center)
- Even n: no center cell
- Odd n: center cell at (n//2, n//2) = n^2

**Complexity:**
- Time: O(n^2) - fill every cell
- Space: O(1) - only counter and boundaries (output matrix doesn't count)

---

## The 20 Implementations (Simple to Complex)

### Way 1: Boundary shrinking (BEST - Memorize!)
```python
def generate_matrix(n):
    matrix = [[0] * n for _ in range(n)]
    top, bottom, left, right = 0, n - 1, 0, n - 1
    num = 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = num; num += 1
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = num; num += 1
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num; num += 1
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num; num += 1
            left += 1
    return matrix
```

### Way 2: Verbose version (whiteboard-friendly)
- Same as Way 1 but with descriptive variable names.

### Way 3: Direction vectors with bounds check
```python
def generate_matrix(n):
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
    dir_idx = 0
    matrix = [[0] * n for _ in range(n)]
    r, c = 0, 0
    for num in range(1, n * n + 1):
        matrix[r][c] = num
        nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        if not (0 <= nr < n and 0 <= nc < n) or matrix[nr][nc] != 0:
            dir_idx = (dir_idx + 1) % 4
            nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        r, c = nr, nc
    return matrix
```

### Way 4: Direction vectors with visited set (safer for non-zero values)

### Way 5: Layer-by-layer (one ring at a time)
- Process each layer separately, handles center cell specially.

### Way 6: Recursive layer filling
```python
def helper(matrix, top, bottom, left, right, num):
    if top > bottom or left > right: return num
    # Fill 4 sides of the current ring
    for j in range(left, right + 1):
        matrix[top][j] = num; num += 1
    for i in range(top + 1, bottom + 1):
        matrix[i][right] = num; num += 1
    if top != bottom:
        for j in range(right - 1, left - 1, -1):
            matrix[bottom][j] = num; num += 1
    if left != right:
        for i in range(bottom - 1, top, -1):
            matrix[i][left] = num; num += 1
    return helper(matrix, top + 1, bottom - 1, left + 1, right - 1, num)
```

### Way 7: Pre-compute spiral positions, then assign

### Way 8: Using itertools.count for auto-incrementing
- Same as Way 1 but uses `next(count(1))` instead of `num += 1`.

### Way 9: Generator-based (functional)
- Uses a generator to yield 1, 2, 3, ... indefinitely.

### Way 10: Peeling layers (explicit single row/col handling)
- Breaks out of loop early for single row/col cases.

### Way 11: Compact one-pass with early termination

### Way 12: Offset-based (calculate position within layer)
```python
# For each layer, fill cells using offsets from (top, left)
# side_len = n - 2*layer
# Fill: top row, right col, bottom row, left col, each of (side_len - 1) cells
```

### Way 13: Step rotation (similar to Way 3)

### Way 14: Mathematical formula (closed-form)
- Computes each cell's value directly from its (i, j) position.
- Useful when you don't want iterative state.

### Way 15: Numpy vectorized (fastest for large n)
```python
import numpy as np
matrix = np.zeros((n, n), dtype=int)
# Use slicing to fill each side
matrix[top, left:right + 1] = range(num, num + ...)
```

### Way 16: State machine (4 states: top, right, bottom, left)

### Way 17: Using deque for direction rotation

### Way 18: Class-based OOP
```python
class SpiralMatrixBuilder:
    def fill_top_row(self): ...
    def fill_right_col(self): ...
    def fill_bottom_row(self): ...
    def fill_left_col(self): ...
    def build(self): ...
```

### Way 19: With explicit loop counter (avoids while-true)
- Checks `num <= n * n` to terminate cleanly.

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Most efficient   | Way 1    | O(1) extra   |
| Whiteboard       | Way 2    | Most readable|
| Direction-based  | Way 3    | State machine|
| Mathematical     | Way 14   | No iteration |
| Cache-friendly   | Way 15   | Numpy slicing|
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Boundary (Way 1) | O(n²) | O(1) | Best general purpose |
| Direction (Way 3) | O(n²) | O(1) | Elegant state machine |
| Layer (Way 5) | O(n²) | O(1) | One ring at a time |
| Recursive (Way 6) | O(n²) | O(n) | Call stack depth |
| Formula (Way 14) | O(n²) | O(1) | No state, pure compute |
| Numpy (Way 15) | O(n²) | O(1) | Vectorized slices |

---

## Walkthrough Example

```
n = 4

Initial: matrix = [[0]*4 for _ in range(4)]
          top=0, bottom=3, left=0, right=3, num=1

Round 1:
- Top row (j=0..3): matrix[0] = [1, 2, 3, 4]. top=1, num=5
- Right col (i=1..3): matrix[1][3]=5, [2][3]=6, [3][3]=7. right=2, num=8
- Bottom row (j=2..0): matrix[3] = [10, 9, 8, 7]. bottom=2, num=11
- Left col (i=2..1): matrix[2][0]=11, [1][0]=12. left=1, num=13

State: top=1, bottom=2, left=1, right=2

Round 2:
- Top row (j=1..2): matrix[1] = [12, 13, 14, 5]. top=2, num=16
- Right col (i=2..2): matrix[2][2]=15. right=1, num=16
- (top > bottom? top=2, bottom=2, equal) Bottom row (j=1..1): matrix[2][1]=16. bottom=1, num=17
- (left > right? left=1, right=1, equal) Left col (i=1..2): matrix[1][1]=17, [2]... already bottom=1 < top=2, no fill. left=2, num=17

State: top=2, bottom=1, exit loop

Result:
[[ 1,  2,  3,  4],
 [12, 17, 16,  5],   <- (1,1)=17 added in last iteration, (1,2)=16, (1,3)=5
 [11, 16, 15,  6],
 [10,  9,  8,  7]]

Wait, that's wrong! Let me retrace...

Actually round 2:
- Top row (j=1..2): matrix[1] = [12, 13, 14, 5]. num=16
- Right col (i=2..2): matrix[2][2]=15. num=16
- Bottom row check: top=2, bottom=2, valid. Fill j=1: matrix[2][1]=16. num=17. bottom=1
- Left col check: left=1, right=1, valid. Fill i=1: matrix[1][1]=17. num=18. left=2

Now top=2, bottom=1, exit loop.

Result:
[[ 1,  2,  3,  4],
 [12, 17, 16,  5],
 [11, 16, 15,  6],
 [10,  9,  8,  7]]

Hmm, expected:
[[ 1,  2,  3,  4],
 [12, 13, 14,  5],
 [11, 16, 15,  6],
 [10,  9,  8,  7]]

The issue: in round 2, when filling bottom row and left col, we over-write
matrix[2][1]=16 (correct) and matrix[1][1]=17 (WRONG - should be 13).

Actually re-checking: round 2 fills matrix[1][1..2] = 13, 14.
Then right col i=2..2: matrix[2][2]=15.
Then bottom row j=1..1: matrix[2][1]=16. (correct - this is position (2,1))
Then left col i=1..1: matrix[1][1]=17. WAIT - this overwrites 13!

The bounds check should be i range(bottom, top - 1, -1) = range(1, 1, -1) = empty!

Let me recheck: after top row, top=2. Then right col i range(top, bottom+1) = range(2, 3) = [2]. So:
matrix[2][2]=15. num=16
right=1. top=2, bottom=2, so bottom row executes:
j range(right, left-1, -1) = range(1, 0, -1) = [1]
matrix[2][1]=16. num=17
bottom=1. left=1, right=1, so left col executes:
i range(bottom, top-1, -1) = range(1, 1, -1) = []
NO cells to fill!
left=2.

State: top=2, bottom=1, exit loop.

Result:
[[ 1,  2,  3,  4],
 [12, 13, 14,  5],
 [11, 16, 15,  6],
 [10,  9,  8,  7]] ✓
```

---

## Best Answer to Memorize

```python
def generate_matrix(n):
    matrix = [[0] * n for _ in range(n)]
    top, bottom, left, right = 0, n - 1, 0, n - 1
    num = 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = num; num += 1
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = num; num += 1
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num; num += 1
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num; num += 1
            left += 1
    return matrix
```

**~20 lines. O(n²) time. O(1) extra space. Interview-ready!**

---

## Key Insights

### Why check `top <= bottom` before bottom row?
> "After filling top row, top has incremented. If top > bottom, the matrix
> is exhausted (single row/col case). Without the check, we'd fill already-filled cells."

### Why does the diagonal not get over-written?
> "The diagonal cells are visited ONLY ONCE - in either the top row or right
> column or bottom row or left column - depending on where they sit.
> For n=3, (0,0) is in top row, (1,1) is the center, (2,2) is in right column."

### Center cell for odd n:
> "When n is odd, the inner-most cell (n//2, n//2) is filled LAST, when
> top == bottom == left == right. Our while condition catches this:
> the top row covers just this one cell."

### Why is this the inverse of Spiral Matrix I?
> "Spiral Matrix I: result.append(matrix[r][c])
> Spiral Matrix II: matrix[r][c] = num
> Both use identical boundary-shrinking logic."

### Off-by-one considerations:
> "Right range for top row: `range(left, right + 1)` includes right.
> Reverse for bottom row: `range(right, left - 1, -1)` includes left.
> Right column down: `range(top, bottom + 1)` includes bottom.
> Left column up: `range(bottom, top - 1, -1)` includes top."

---

## Test Cases

| n | Expected Result |
|---|-----------------|
| 1 | [[1]] |
| 2 | [[1, 2], [4, 3]] |
| 3 | [[1, 2, 3], [8, 9, 4], [7, 6, 5]] |
| 4 | [[1, 2, 3, 4], [12, 13, 14, 5], [11, 16, 15, 6], [10, 9, 8, 7]] |
| 5 | [[1..5],[16..6],[15,24,25,20,7],[14,23,22,21,8],[13..9]] |

---

## Common Pitfalls

1. **Forgetting bounds check on bottom row/left col**: Over-writes cells.
2. **Off-by-one in for-range**: `range(left, right+1)` for inclusive.
3. **Wrong center handling**: For odd n, center is filled by top row when n=1 case.
4. **Incrementing num after the wrong line**: Each cell gets ONE number.
5. **Confusing the inverse relationship**: This is OPPOSITE of reading spiral.

---

## Why This Problem Matters

> "Tests:
> 1. Inverse of Spiral Matrix I (reading vs. writing).
> 2. Boundary shrinking technique (CRITICAL skill).
> 3. Loop invariant maintenance.
> 4. Pattern: rotate image, generate matrix, search 2D matrix.
> 5. Foundation for: image rotation, matrix generation in graphics."

---

## Beyond Spiral Matrix II: Related Operations

1. **Spiral Matrix I (read)**: Same boundaries, append to result.
2. **Spiral Matrix III (special)**: Start at center, walk in spiral expanding outward.
3. **Rotate 90° clockwise**: Reverse each row, then transpose.
4. **Rotate 90° counter-clockwise**: Transpose, then reverse each row.
5. **Diagonal spiral**: Different geometry, similar state machine.

---

## Connection: Spiral I vs Spiral II

```python
# SPIRAL I (READ): append, don't increment
result.append(matrix[top][j])

# SPIRAL II (WRITE): assign, increment num
matrix[top][j] = num; num += 1
```

```python
# SPIRAL I:
def spiralOrder(matrix):
    if not matrix: return []
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1
    return result

# SPIRAL II (same structure, different operation):
def generateMatrix(n):
    matrix = [[0] * n for _ in range(n)]
    top, bottom, left, right = 0, n - 1, 0, n - 1
    num = 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = num; num += 1
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = num; num += 1
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num; num += 1
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num; num += 1
            left += 1
    return matrix
```

> "If you master Spiral I, Spiral II is just swapping `result.append(x)` for `matrix[r][c] = num; num += 1`."
