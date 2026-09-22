# Spiral Matrix - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix

## The Problem
```
Given an m x n matrix, return an array of elements in SPIRAL ORDER,
starting from the top-left cell.

Spiral order:
1. Left to Right (top row)
2. Top to Bottom (right column)
3. Right to Left (bottom row)
4. Bottom to Top (left column)
Then repeat for inner sub-matrix.

Examples:
    [[1, 2, 3],           [[1, 2, 3, 4],
     [4, 5, 6],            [5, 6, 7, 8],
     [7, 8, 9]]            [9, 10, 11, 12]]
    -> [1,2,3,6,9,8,7,4,5]  -> [1,2,3,4,8,12,11,10,9,5,6,7]

Constraints:
- 1 <= matrix.length <= 10
- 1 <= matrix[i].length <= 10
- -100 <= matrix[i][j] <= 100
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The path is a SPIRAL. Think of it as a clock hand moving inward.

For a 3x3:
- Top row:    (0,0) (0,1) (0,2)
- Right col:           (1,2) (2,2)
- Bottom:     (2,1) (2,0)
- Left col:   (1,0)
- Center:     (1,1)

So the order is: 1 2 3 6 9 8 7 4 5
```

### Step 2: The Trick
> "Use BOUNDARY SHRINKING!
> - Track top, bottom, left, right.
> - Each round: traverse top row, right column, bottom row, left column.
> - After each pass, shrink the boundary inward:
>   top++, right--, bottom--, left++."

### Step 3: Why Check Bounds?
> "After traversing top row and right column, the boundaries may have
> crossed (e.g., top > bottom or left > right). For the bottom row and
> left column, we MUST check bounds, otherwise we'd re-process cells."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to return all matrix elements in spiral order from top-left.
> The path goes right, down, left, up, then repeats inward."

**Key Insight:**
> "Use BOUNDARY SHRINKING!
> - Track top, bottom, left, right.
> - Each round: 4 directional traversals.
> - After each direction, shrink the appropriate boundary."

**Algorithm:**
> "1. top=0, bottom=m-1, left=0, right=n-1
> 2. While top <= bottom and left <= right:
>    a. Top row (left to right). top += 1.
>    b. Right column (top to bottom). right -= 1.
>    c. (if top <= bottom) Bottom row (right to left). bottom -= 1.
>    d. (if left <= right) Left column (bottom to top). left += 1.
> 3. Return result"

**Why check bounds in steps c and d:**
> "After step a, top might exceed bottom. We don't want to reprocess
> the top row in step c. Similarly for step d."

**Edge cases:**
- 1x1: just return [matrix[0][0]]
- Single row: only step a executes (then loop ends since top > bottom)
- Single column: only step a and b execute
- Square matrix: full spiral
- Rectangular: shrinks may make single rows/cols (handled by checks)

**Complexity:**
- Time: O(m*n) - each cell visited once
- Space: O(1) - only the result list

---

## The 20 Implementations (Simple to Complex)

### Way 1: Boundary shrinking (BEST - Memorize!)
```python
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
```

### Way 2-4: Same logic with variations
- Way 2: Verbose
- Way 3-4: Direction vectors with visited set

### Way 5: Recursive layer-by-layer
```python
def helper(layer, top, bottom, left, right, result):
    # Traverse outer ring, recurse on inner
```

### Way 6: Pop first row + rotate rest
```python
result += matrix[0]
matrix = list(zip(*matrix[1:]))[::-1]
```

### Way 7: Layer-by-layer (iterative)
- Process each layer (outer to inner)

### Way 8: BFS with deque

### Way 9-10: Various while-loop styles

### Way 11-12: With zip + itertools

### Way 13: Generator-based (elegant recursion)
```python
def gen(m):
    if not m: return
    for val in m[0]: yield val
    rest = m[1:]
    if rest:
        rotated = [list(row) for row in zip(*rest)][::-1]
        yield from gen(rotated)
```

### Way 14: Most concise (one-liner)
```python
return matrix and list(matrix.pop(0)) + spiral_order([list(row) for row in zip(*matrix)][::-1] if matrix else [])
```

### Way 15: Direction arrays
- (dr, dc) for right, down, left, up

### Way 16-17: With explicit bounds tracking and class-based

### Way 18: Explicit shrinking with single-row/col checks

### Way 19: Numpy (vectorized)

### Way 20: Final cleanest

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Most efficient   | Way 1    | O(1) space   |
| Educational      | Way 5    | Recursive    |
| Functional       | Way 6/13 | Recursive    |
| Single liner     | Way 14   | Concise      |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Boundary (Way 1) | O(mn) | O(1) |
| Direction + visited | O(mn) | O(mn) |
| Recursive | O(mn) | O(mn) |

---

## Walkthrough Example

```
matrix = [
  [1, 2, 3, 4],
  [5, 6, 7, 8],
  [9, 10, 11, 12]
]

Initial: top=0, bottom=2, left=0, right=3

Round 1:
- Top row: (0,0)(0,1)(0,2)(0,3) = 1,2,3,4. top=1
- Right col: (1,3)(2,3) = 8,12. right=2
- Bottom row: (2,2)(2,1)(2,0) = 11,10,9. bottom=1
- Left col: (1,0) = 5. left=1

State: top=1, bottom=1, left=1, right=2

Round 2:
- Top row: (1,1)(1,2) = 6,7. top=2
- Right col: (2,2) = 11. right=1
- (top > bottom) skip bottom row
- (left > right) skip left col

State: top=2, bottom=1, exit loop

Result: [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7] ✓
```

## Best Answer to Memorize

```python
def spiralOrder(matrix):
    if not matrix:
        return []
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
```

**18 lines. O(mn) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why shrink boundaries?
> "Each round processes an OUTER RING. After processing, we move inward
> to process the next ring. Shrinking boundaries = moving inward."

### Why check bounds in steps c and d?
> "After step a, top might equal bottom (single row). After step b,
> left might equal right (single column). Without checks, we'd
> re-process cells."

### Why is "right -= 1" right after step b?
> "We've finished processing the right column. So the right boundary
> moves leftward for the next round."

### Why not just iterate over all cells?
> "That's O(mn) but doesn't give spiral order. We need the spatial
> order of traversal."

---

## Test Cases

| matrix | Result |
|--------|--------|
| [[1,2,3],[4,5,6],[7,8,9]] | [1,2,3,6,9,8,7,4,5] |
| [[1,2,3,4],[5,6,7,8],[9,10,11,12]] | [1,2,3,4,8,12,11,10,9,5,6,7] |
| [[1]] | [1] |
| [[1,2,3,4]] | [1,2,3,4] |
| [[1],[2],[3]] | [1,2,3] |
| [[1,2],[3,4]] | [1,2,4,3] |
| [[1,2,3],[4,5,6]] | [1,2,3,6,5,4] |

## Common Pitfalls

1. **Forgetting bounds check in step c/d**: Re-processes cells.
2. **Wrong range bounds**: `range(left, right+1)` includes right!
3. **Wrong direction order**: Right -> Down -> Left -> Up.
4. **Not handling single row/col**: Loop ends correctly via condition.
5. **Off-by-one in ranges**: `range(left, right-1, -1)` for reverse.

## Why This Problem Matters

> "Tests:
> 1. Matrix traversal with multiple boundaries (CRITICAL skill)
> 2. Loop invariant maintenance (boundaries)
> 3. Edge case handling (single row/col, square vs rectangle)
> 4. Pattern similar to: rotate image, search 2D matrix, set matrix zeros
> 5. Foundation for: matrix operations, image processing"
