# Best Meeting Point - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/best-meeting-point

## The Problem
```
Given a 2D grid where:
- 1 = friend's home
- 0 = empty space

Find the minimum total travel distance from a meeting point to all
friends' homes. Distance = Manhattan distance = |x1 - x2| + |y1 - y2|.

Examples:
    grid = [[0,1,0],
            [0,0,0],
            [0,1,0]] -> 2
    (Friends at (0,1), (2,1). Best meeting: (1,1). Distances: 1+1=2.)

Constraints:
- 1 <= m, n <= 50
- grid[i][j] is 0 or 1
- At least 2 friends
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We want to find a meeting point (mr, mc) that minimizes
sum_{friends f} Manhattan(f, (mr, mc)) = sum |f.row - mr| + |f.col - mc|.
```

### Step 2: The Trick
> "KEY INSIGHT: Manhattan distance is SEPARABLE!
>
> |f.row - mr| + |f.col - mc| = |f.row - mr| + |f.col - mc|
>
> The row part and column part are INDEPENDENT.
> So we can minimize each separately:
> - Best mr = median of all friends' row coordinates
> - Best mc = median of all friends' col coordinates
>
> Why median? Because the sum of absolute deviations
> |x1 - m| + |x2 - m| + ... + |xk - m|
> is MINIMIZED when m is the median (or any value between the two
> middle values for even k)."

### Step 3: Why median?
> "If we plot sum |xi - m| vs m, it's a piecewise linear function with
> slope = (number of xi > m) - (number of xi < m). At the median,
> exactly half are above and half are below, so slope = 0 (minimum)."

### Step 4: Algorithm
> "1. Collect all row coordinates of friends into a list.
> 2. Collect all col coordinates of friends into a list.
> 3. Sort each and find median (middle value).
> 4. Sum Manhattan distances from (median_row, median_col) to each friend."

### Step 5: Verification
> "For [[0,1,0],[0,0,0],[0,1,0]]:
> - Friends: (0,1), (2,1).
> - Rows: [0, 2]. Median = 0 or 2. Use 0.
> - Cols: [1, 1]. Median = 1.
> - Meeting: (0, 1) (or (2,1)).
> - Distances: 0 + 2 = 2. ✓"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find a meeting point minimizing the total Manhattan
> distance to all friends' homes."

**Key Insight:**
> "Manhattan distance is SEPARABLE - row and column parts are
> independent. So I optimize each separately. The optimal value
> for sum |xi - m| is the MEDIAN of all xi's."

**Algorithm:**
> "1. Collect row coordinates and col coordinates of friends.
> 2. Sort and find median of each.
> 3. Sum Manhattan distances from (median_row, median_col) to friends."

**Why median?**
> "The sum of |xi - m| is a piecewise linear function of m. The slope
> is (#xi > m) - (#xi < m). At the median, slope is 0 - it's the minimum."

**Edge cases:**
- Two friends: any point on the Manhattan path between them works.
- All friends in same row/col: median of that coordinate.
- Even number of friends: any value between the two middle values works.

**Complexity:**
- Time: O(m*n + k log k) where k = number of friends.
- Space: O(k) for coordinate lists.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Median + Manhattan distance (BEST - Memorize!)
```python
def best_meeting_point_1(grid):
    if not grid or not grid[0]:
        return 0
    rows = []
    cols = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)
    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]
    return sum(abs(r - median_row) + abs(c - median_col)
               for r in range(len(grid))
               for c in range(len(grid[0]))
               if grid[r][c] == 1)
```

### Way 2: numpy median
### Way 3: Brute force
### Way 4: BFS from each friend
### Way 5: Sort + median
### Way 6: List comprehension
### Way 7: statistics.median
### Way 8: Quickselect
### Way 9: enumerate
### Way 10: NumPy vectorized
### Way 11: Class-based
### Way 12: Functional
### Way 13: One-liner
### Way 14: All median candidates
### Way 15: Direct Manhattan sum
### Way 16: heapq.nsmallest
### Way 17: Sort friends
### Way 18: itertools
### Way 19: Compact itertools
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(mn + klgk) |
| Small grid         | Way 3    | Brute OK     |
| Educational        | Way 5    | Clear median |
| Want quickselect   | Way 8    | O(k) median  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Median + sort (Way 1) | O(mn + k log k) | O(k) | Best general |
| Brute (Way 3) | O((mn)^2) | O(1) | Small inputs |
| BFS (Way 4) | O(mn * mn) | O(mn) | General metric |
| Quickselect (Way 8) | O(mn + k) avg | O(k) | No sort |

---

## Walkthrough Example

```
grid = [[0, 1, 0],
        [0, 0, 0],
        [0, 1, 0]]

Friends: (0,1), (2,1)
Rows: [0, 2], Cols: [1, 1]
Median row: 0 (or 2)
Median col: 1
Meeting point: (0, 1)

Total distance:
  (0,1) -> (0,1): |0-0| + |1-1| = 0
  (2,1) -> (0,1): |2-0| + |1-1| = 2
Total: 2 ✓
```

```
grid = [[1, 0, 0],
        [0, 0, 0],
        [0, 0, 1]]

Friends: (0,0), (2,2)
Rows: [0, 2], Cols: [0, 2]
Median row: 0 or 2 (let's pick 1, which is also valid)
Median col: 1 (let's pick 1)
Meeting point: (1, 1)

Total distance:
  (0,0) -> (1,1): |0-1| + |0-1| = 2
  (2,2) -> (1,1): |2-1| + |2-1| = 2
Total: 4 ✓
```

```
grid = [[1, 1, 1, 1]]  (1x4, all friends)

Friends: (0,0), (0,1), (0,2), (0,3)
Rows: [0, 0, 0, 0], Cols: [0, 1, 2, 3]
Median row: 0
Median col: 1 or 2 (pick 1)
Meeting point: (0, 1)

Distances: 1+0+1+2 = 4 ✓
```

---

## Best Answer to Memorize

```python
def best_meeting_point(grid):
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])

    rows = []
    cols = []
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                rows.append(r)
                cols.append(c)

    rows.sort()
    cols.sort()
    median_row = rows[len(rows) // 2]
    median_col = cols[len(cols) // 2]

    return sum(abs(r - median_row) + abs(c - median_col)
               for r, c in zip(rows, cols))
```

**~12 lines. O(m*n + k log k) time. O(k) space. Interview-ready!**

---

## Key Insights

### Why Manhattan distance is separable?
> "Manhattan distance = |dx| + |dy|. The dx part depends only on
> x-coordinates; dy part only on y-coordinates. They're independent,
> so we can minimize each separately."

### Why median minimizes sum of absolute deviations?
> "Sum |xi - m| has slope = (#xi > m) - (#xi < m). At the median,
> slope changes sign - that's the minimum."

### Why not Euclidean distance?
> "Euclidean distance = sqrt(dx^2 + dy^2). NOT separable. The optimum
> is the GEOMETRIC MEDIAN, which has no closed form. The median
> trick only works for Manhattan distance."

### Why does the problem say "meeting point" not "anywhere"?
> "We're minimizing total distance. The meeting point is the location
> that achieves this minimum - it's not arbitrary."

---

## Test Cases

| grid | Expected |
|------|----------|
| [[0,1,0],[0,0,0],[0,1,0]] | 2 |
| [[1,0,1,0,1]] | 4 |
| [[1,0,0],[0,0,0],[0,0,1]] | 4 |
| [[1,0,0,0,1],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[1,0,0,0,1]] | 16 |
| [[1,1,0,1]] | 3 |
| [[1],[1],[0],[1]] | 3 |
| [[1,1],[1,1]] | 4 |

---

## Common Pitfalls

1. **Using Euclidean distance**: The problem specifies Manhattan distance.
2. **Wrong median for even count**: Either lower or upper median works.
   Both give the same minimum distance.
3. **Forgetting to optimize separately**: Manhattan distance is separable.
4. **Brute force for large grids**: O((m*n)^2) is too slow.
5. **Confusion with geometric median**: That works for Euclidean, not Manhattan.

---

## Why This Problem Matters

> "Tests:
> 1. Manhattan distance separability (key insight).
> 2. Median minimizes sum of absolute deviations.
> 3. Coordinate-wise optimization.
> 4. Foundation for: facility location, clustering, network design."

---

## Beyond This Problem: Related Patterns

### 1. 1D Best Meeting Point (LC 462 - Min Moves to Equal Array Elements)
```python
# Just find median of array.
# Sum of |xi - m| minimized at median.
```

### 2. Min Cost to Make Array Equal
```python
# Pick any median value.
# Total cost = sum |xi - median|.
```

### 3. Facility Location Problems
```python
# General: minimize sum of distances to facilities.
# Manhattan: median trick works.
# Euclidean: geometric median (harder).
```

### 4. Median Maintenance in Stream
```python
# Two heaps to maintain median in O(log n).
```

---

## Connection to Median Problems

This problem is a 2D extension of "find the point minimizing sum of
absolute deviations":

```
1D:    minimize sum |xi - m|     -> median
2D Manhattan: minimize sum |xi - m_x| + |yi - m_y|
            -> (median_x, median_y)  [INDEPENDENTLY]
```

The key trick: SEPARABILITY. Manhattan distance decomposes into
independent coordinates.

For Euclidean distance, this trick fails:
```
2D Euclidean: minimize sum sqrt((xi-m_x)^2 + (yi-m_y)^2)
            -> GEOMETRIC MEDIAN (no closed form, harder)
```

---

## Quick Checklist

When given a similar problem:
- [ ] What distance metric? (Manhattan -> median trick works)
- [ ] Is the metric separable? (Manhattan yes, Euclidean no)
- [ ] What's the optimum per coordinate? (median for L1, mean for L2)
- [ ] How to handle even count? (any value in [lower, upper] median works)
- [ ] Brute force vs median? (median O(k log k), brute O(mn * mn))

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 296 - Best Meeting Point](https://leetcode.com/problems/best-meeting-point/)
