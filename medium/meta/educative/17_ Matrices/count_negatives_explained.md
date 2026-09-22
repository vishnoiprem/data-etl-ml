# Count Negative Numbers in a Sorted Matrix - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/count-negative-numbers-in-a-sorted-matrix

## The Problem
```
Given an m x n matrix grid sorted in NON-INCREASING order by both rows
and columns, return the number of NEGATIVE numbers in grid.

"Sorted in non-increasing order":
- Each row: left to right is non-increasing (>=)
- Each column: top to bottom is non-increasing (>=)

Examples:
    [[4, 3, 2, -1],     [[3, 2],
     [3, 2, 1, -1],      [1, 0]]
     [1, 1, -1, -2],
     [-1, -1, -2, -3]]
    -> 8                   -> 0

Constraints:
- 1 <= m, n <= 100
- -100 <= grid[i][j] <= 100

Follow-up: O(m + n) solution.
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The matrix is sorted in TWO ways: rows and columns are both
non-increasing. This means:
- Within a row: values decrease left to right (or stay same)
- Within a column: values decrease top to bottom (or stay same)

So the matrix looks like:
   5  4  3 -1
   4  3  2 -2
   2  1  0 -3
  -1 -2 -3 -4
```

### Step 2: The Trick (Best O(m+n))
> "Start at the TOP-RIGHT corner!
> - If current cell is NEGATIVE:
>   * All cells BELOW (in same column) are also negative (column sort).
>   * Add (m - r) to count. Move LEFT.
> - If current cell is NON-NEGATIVE:
>   * Cells to the LEFT might be negative.
>   * Move DOWN to find negatives."

### Step 3: Why Top-Right?
> "From top-right:
> - DOWN: column-sorted, smaller or equal.
> - LEFT: row-sorted, smaller or equal.
> - If current < 0: all below in this column are negative. Skip them all.
> - If current >= 0: keep moving down (column gets smaller).
>
> Each step eliminates a row OR a column, so O(m+n)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I have an m x n matrix sorted in non-increasing order by both rows
> and columns. I need to count the negative numbers."

**Key Insight:**
> "Start at TOP-RIGHT corner!
> - If negative: all below in column are negative. Count them. Move LEFT.
> - If non-negative: move DOWN to find negatives."

**Algorithm:**
> "1. r=0, c=n-1 (top-right), count=0
> 2. While r < m and c >= 0:
>    a. If grid[r][c] < 0: count += (m - r); c -= 1
>    b. Else: r += 1
> 3. Return count"

**Why this works:**
> "At top-right, current cell is grid[0][n-1].
> - DOWN (increase r): column is non-increasing, so values get smaller.
> - LEFT (decrease c): row is non-increasing, so values get smaller.
> - If current < 0: column BELOW is all negative. Add m-r (rows below).
>   Move left to count more negatives.
> - If current >= 0: row to left might be negative, but moving down
>   gives us smaller values in current column."

**Edge cases:**
- All non-negative: walk down through entire first column. Return 0.
- All negative: walk left through top row. Count all.
- Single row: only walk left.
- Single column: only walk down.

**Complexity:**
- Time: O(m+n) - each step eliminates a row or column
- Space: O(1) - just two pointers

---

## The 20 Implementations (Simple to Complex)

### Way 1: Top-right walk (BEST - Memorize!)
```python
def countNegatives(grid):
    if not grid or not grid[0]: return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += m - r
            c -= 1
        else:
            r += 1
    return count
```

### Way 2: Bottom-left walk (symmetric)
- Start at bottom-left, walk right or up.

### Way 3-4: Binary search per row
- Find first negative in each row using binary search. O(m log n).

### Way 5-9: Brute force variations
- Way 5: Nested loops
- Way 6: Flatten + count
- Way 7: Sum of bool
- Way 8: Filter + len
- Way 9: Numpy

### Way 10: Top-right with explicit logic

### Way 11: Bottom-left variant

### Way 12: Binary search per row from left

### Way 13: Bottom-left explicit pointer

### Way 14: Manual count (most explicit)

### Way 15: Recursive approach
```python
def helper(r, c):
    if r >= m or c < 0: return 0
    if grid[r][c] < 0:
        return (m - r) + helper(r, c - 1)
    return helper(r + 1, c)
```

### Way 16: Per-row threshold
- For each row, find first negative. Count from there to end.

### Way 17: Two-pointer walk

### Way 18: Class-based

### Way 19: Most concise

### Way 20: Final cleanest (same as Way 1)

---

## Decision Tree

```
+------------------+------------+--------------+
| Scenario         | Best       | Why          |
+------------------+------------+--------------+
| Most efficient   | Way 1      | O(m+n)       |
| Educational      | Way 5      | Brute force  |
| Functional       | Way 15     | Recursive    |
+------------------+------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Top-right walk (Way 1) | O(m+n) | O(1) |
| Binary search per row | O(m log n) | O(1) |
| Brute force | O(mn) | O(1) |

---

## Walkthrough Example

```
grid = [
  [4, 3, 2, -1],
  [3, 2, 1, -1],
  [1, 1, -1, -2],
  [-1, -1, -2, -3]
]

Start: r=0, c=3 (top-right)

Step 1: grid[0][3] = -1 < 0
  count += 4 - 0 = 4. c = 2.
  All 4 cells in column 3 (rows 0-3) are negative.

Step 2: grid[0][2] = 2 >= 0
  r = 1.

Step 3: grid[1][2] = 1 >= 0
  r = 2.

Step 4: grid[2][2] = -1 < 0
  count += 4 - 2 = 2. c = 1.
  Rows 2-3 in column 2 are negative.

Step 5: grid[2][1] = 1 >= 0
  r = 3.

Step 6: grid[3][1] = -1 < 0
  count += 4 - 3 = 1. c = 0.
  Row 3 in column 1 is negative.

Step 7: grid[3][0] = -1 < 0
  count += 4 - 3 = 1. c = -1.

Loop ends.

Total count = 4 + 2 + 1 + 1 = 8 ✓
```

## Best Answer to Memorize

```python
def countNegatives(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] < 0:
            count += m - r
            c -= 1
        else:
            r += 1
    return count
```

**11 lines. O(m+n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why top-right (or bottom-left)?
> "From these corners, ONE direction moves toward negative (left/down or
> right/up), ONE direction stays sorted (down gives smaller or equal).
> At other corners (top-left or bottom-right), both directions could
> increase or decrease depending on direction."

### Why is it O(m+n)?
> "Each step eliminates either a row (move left) or a column (move down).
> Total eliminations: at most m + n."

### What if grid has duplicates?
> "Non-increasing allows duplicates. Algorithm still works."

### Why not just binary search each row?
> "O(m log n) is also good, but O(m+n) is the optimal follow-up answer."

---

## Test Cases

| grid | Result | Why |
|------|--------|-----|
| [[4,3,2,-1],[3,2,1,-1],[1,1,-1,-2],[-1,-1,-2,-3]] | 8 | Standard |
| [[3,2],[1,0]] | 0 | All non-negative |
| [[-1,-2],[-3,-4]] | 4 | All negative |
| [[5]] | 0 | Single non-neg |
| [[-5]] | 1 | Single neg |
| [[3,2,1,0,-1,-2]] | 2 | Single row |
| [[3],[2],[1],[0],[-1],[-2]] | 2 | Single col |
| [[0,0],[0,0]] | 0 | All zeros |

## Common Pitfalls

1. **Starting at wrong corner**: Top-left or bottom-right don't work.
2. **Forgetting to count m-r**: When negative, all rows below are too.
3. **Wrong direction**: Should move DOWN for non-negative, LEFT for negative.
4. **Confusing increasing vs non-increasing**: Sorted is non-increasing!
5. **Off-by-one in column count**: After moving left, check bounds.

## Why This Problem Matters

> "Tests:
> 1. Sorted matrix traversal with O(m+n) (CRITICAL pattern)
> 2. Choosing the right starting corner
> 3. Using sorted property to skip rows/columns
> 4. Pattern similar to: search 2D matrix, kth smallest in sorted matrix
> 5. Foundation: matrix binary search, divide and conquer on matrices"
