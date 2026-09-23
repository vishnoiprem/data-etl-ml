# Minimize Maximum Value in a Grid - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimize-maximum-value-in-a-grid

## The Problem
```
Given an m x n integer matrix `grid` of DISTINCT positive integers,
replace each integer with a positive integer such that:
1. Preserve RELATIVE ORDER in rows AND columns (STRICT inequality).
2. Minimize the MAXIMUM value in the resulting grid.

Any valid solution is acceptable.

Examples:
    grid = [[2, 4, 5], [6, 3, 8]]
    Valid: [[1, 2, 3], [2, 1, 4]]  (max = 4)

Constraints:
- 1 <= m, n <= 30
- 1 <= m*n <= 900
- All values in grid are distinct positive integers
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We need to REPLACE each value with a new value (positive integer) such that:
- For any two cells in the same row, if A < B in original, then result[A] < result[B].
- For any two cells in the same column, if A < B in original, then result[A] < result[B].
- Minimize max(result).

This is a TOPOLOGICAL ORDERING problem. The original values give us a
partial order; we want to extend it to a total order using the smallest
possible numbers.
```

### Step 2: The Trick
> "KEY INSIGHT: The smallest cell MUST get value 1. For any other cell,
> its value = (max value already assigned to a smaller cell in its row OR column) + 1.
>
> Process cells in ASCENDING order of original values. Track the max
> value used so far in each row and each column."

### Step 3: Why ascending order?
> "When we process cell C, ALL cells smaller than C (in same row/col)
> have already been processed. So we know the max value used in C's row
> and column so far. C's value = that max + 1."

### Step 4: Why this minimizes the max?
> "Each cell takes the SMALLEST value possible (just one more than max
> of its predecessors). This greedy approach is optimal here because
> any constraint forces C > predecessor, and we choose the tightest bound."

### Step 5: Topological sort connection
> "The original values define a DAG (directed acyclic graph): A → B if
> A and B are in same row/col and A < B. We need a topological labeling.
> Our algorithm is essentially BFS in this DAG."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to replace each value with a positive integer that preserves
> relative order in rows AND columns, while minimizing the max value."

**Key Insight:**
> "The smallest cell gets value 1. Each other cell takes max value of its
> smaller row/col neighbors + 1. Process cells in ascending original order."

**Algorithm:**
> "1. Sort cells by original value, ascending.
> 2. Track row_max[r] and col_max[c] = 0.
> 3. For each (r, c) in sorted order:
>    result[r][c] = max(row_max[r], col_max[c]) + 1
>    row_max[r] = result[r][c]
>    col_max[c] = result[r][c]
> 4. Return result."

**Why it works:**
> "When we process cell (r, c), all smaller cells in its row/col are
> already assigned. We need result[r][c] > all of them, so the smallest
> valid choice is max + 1."

**Edge cases:**
- 1x1 grid: just [[1]].
- All in same row/col: linear ordering.
- Fully monotonic: works naturally.

**Complexity:**
- Time: O(m*n*log(m*n)) for sorting
- Space: O(m*n) for result + tracking arrays

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + BFS (BEST - Memorize!)
```python
def minimize_max_value(grid):
    if not grid or not grid[0]: return grid
    m, n = len(grid), len(grid[0])
    
    cells = sorted(((grid[i][j], i, j) for i in range(m) for j in range(n)))
    result = [[0] * n for _ in range(m)]
    row_max = [0] * m
    col_max = [0] * n
    
    for _, r, c in cells:
        result[r][c] = max(row_max[r], col_max[c]) + 1
        row_max[r] = result[r][c]
        col_max[c] = result[r][c]
    
    return result
```

### Way 2-11: Variations of the same approach
- Different styles of cell enumeration and sorting
- Heap-based (Way 3)
- Numpy vectorized (Way 10)
- Various Pythonic touches

### Way 12: Class-based OOP
```python
class GridMinMaxSolver:
    def __init__(self, grid): ...
    def solve(self): ...
    def _compute_result(self): ...
```

### Way 13: With validation helper function

### Way 14-16: Concise Pythonic variants

### Way 17: Topological BFS
```python
# Build in_degree (count of smaller row/col neighbors).
# BFS from cells with in_degree 0, level by level.
# Level number = value to assign.
```

### Way 18: Memoized recursive DP
```python
def get_value(r, c):
    if (r, c) in memo: return memo[(r, c)]
    # Check all smaller row/col neighbors, take max + 1
    memo[(r, c)] = ...
    return memo[(r, c)]
```

### Way 19: Iterative DP (no recursion)

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Most efficient   | Way 1    | Simple sort  |
| Educational      | Way 17   | Topo sort    |
| Recursive        | Way 18   | Memoization  |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + Greedy (Way 1) | O(mn log mn) | O(mn) | Standard |
| Topological BFS (Way 17) | O(mn) | O(mn) | Process by level |
| Memoized DP (Way 18) | O(mn^2) | O(mn) | Slowest |

---

## Walkthrough Example

```
grid = [[2, 4, 5], [6, 3, 8]]

Sort cells by value: (2,0,0), (3,1,1), (4,0,1), (5,0,2), (6,1,0), (8,1,2)

Process (2, 0, 0):
  result[0][0] = max(0, 0) + 1 = 1
  row_max[0] = 1, col_max[0] = 1
  result = [[1, 0, 0], [0, 0, 0]]

Process (3, 1, 1):
  result[1][1] = max(0, 0) + 1 = 1
  row_max[1] = 1, col_max[1] = 1
  result = [[1, 0, 0], [0, 1, 0]]

Process (4, 0, 1):
  result[0][1] = max(row_max[0]=1, col_max[1]=1) + 1 = 2
  row_max[0] = 2, col_max[1] = 2
  result = [[1, 2, 0], [0, 1, 0]]

Process (5, 0, 2):
  result[0][2] = max(row_max[0]=2, col_max[2]=0) + 1 = 3
  row_max[0] = 3, col_max[2] = 3
  result = [[1, 2, 3], [0, 1, 0]]

Process (6, 1, 0):
  result[1][0] = max(row_max[1]=1, col_max[0]=1) + 1 = 2
  row_max[1] = 2, col_max[0] = 2
  result = [[1, 2, 3], [2, 1, 0]]

Process (8, 1, 2):
  result[1][2] = max(row_max[1]=2, col_max[2]=3) + 1 = 4
  row_max[1] = 4, col_max[2] = 4
  result = [[1, 2, 3], [2, 1, 4]]

Final: [[1, 2, 3], [2, 1, 4]], max = 4 ✓
```

Verify constraints:
- Row 0: 2<4<5 → 1<2<3 ✓
- Row 1: 6>3<8 → 2>1<4 ✓
- Col 0: 2<6 → 1<2 ✓
- Col 1: 4>3 → 2>1 ✓
- Col 2: 5<8 → 3<4 ✓

---

## Best Answer to Memorize

```python
def minimize_max_value(grid):
    if not grid or not grid[0]:
        return grid
    rows, cols = len(grid), len(grid[0])
    
    # Sort cells by original value, ascending
    cells = sorted(
        ((grid[i][j], i, j) for i in range(rows) for j in range(cols))
    )
    
    result = [[0] * cols for _ in range(rows)]
    row_max = [0] * rows
    col_max = [0] * cols
    
    for _, r, c in cells:
        new_value = max(row_max[r], col_max[c]) + 1
        result[r][c] = new_value
        row_max[r] = new_value
        col_max[c] = new_value
    
    return result
```

**~15 lines. O(mn log mn) time. O(mn) space. Interview-ready!**

---

## Key Insights

### Why ascending order?
> "When we process a cell, all its smaller row/col neighbors are done.
> So we know the precise bound on what value to assign."

### Why max + 1?
> "Strict inequality required. We need our value > all predecessors.
> Smallest valid = max predecessor value + 1."

### Why does this give MINIMUM max?
> "Greedy choice at each step. Each cell takes the smallest valid value.
> This is optimal because any larger value would unnecessarily increase
> the max without benefit."

### Topological sort interpretation:
> "The original values create a DAG: A→B if A<B in same row/col.
> Our algorithm does BFS in this DAG, level by level.
> Level k = value k."

---

## Test Cases

| grid | Result | Max |
|------|--------|-----|
| [[2,4,5],[6,3,8]] | [[1,2,3],[2,1,4]] | 4 |
| [[5]] | [[1]] | 1 |
| [[10,20],[30,40]] | [[1,2],[2,3]] | 3 |
| [[1,2,3],[4,5,6],[7,8,9]] | [[1,2,3],[2,3,4],[3,4,5]] | 5 |

---

## Common Pitfalls

1. **Forgetting to track row_max and col_max separately**: Each row/col has its own sequence.
2. **Using <= instead of <**: The problem requires STRICT inequality.
3. **Processing in wrong order**: Must be ascending for the algorithm to work.
4. **Not updating both row_max and col_max after assigning**: Forgetting one breaks the ordering.

---

## Why This Problem Matters

> "Tests:
> 1. Topological sorting.
> 2. Greedy choice with future constraints.
> 3. Multi-dimensional ordering (rows AND columns).
> 4. Pattern: topological labeling, scheduling, ordering problems."

---

## Relationship to Other Problems

### 1. LeetCode 2713: Strictly Increasing Cells in a Matrix
```python
# Almost identical - find longest increasing path.
# Our algorithm solves the strict labeling version.
```

### 2. Course Schedule (LC 207)
```python
# Topological sort over prerequisite DAG.
# Same approach: process in topological order.
```

### 3. Longest Increasing Path (LC 329)
```python
# Memoized DFS: f(i,j) = 1 + max of neighbors with smaller value.
# Related problem with same constraint.
```

---

## Quick Checklist

When given a similar problem:
- [ ] What's the constraint? (order preservation, monotonicity, etc.)
- [ ] What value goes to the smallest element?
- [ ] How do larger elements depend on smaller ones?
- [ ] Is the dependency a DAG (no cycles)?
- [ ] Can I process in topological order?

Sources:
- [LeetCode 2713 - Strictly Increasing Cells in a Matrix](https://leetcode.com/problems/strictly-increasing-cells-in-a-matrix/)
