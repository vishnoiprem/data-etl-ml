# Smallest Rectangle Enclosing Black Pixels - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/smallest-rectangle-enclosing-black-pixels

## The Problem
```
An image is represented by a binary matrix of 0's (white) and 1's (black).
All 1's are CONNECTED (4-connected: up/down/left/right).

Given a coordinate (x, y) of one of the black pixels, find the AREA of the
smallest axis-aligned rectangle that encloses ALL black pixels.

Area = (max_row - min_row + 1) * (max_col - min_col + 1)

Examples:
    image = [[0, 0, 1, 0],
             [0, 1, 1, 0],
             [0, 1, 0, 0]]
    (x=0, y=2)
    -> Black pixels at: (0,2), (1,1), (1,2), (2,1)
    -> min_row=0, max_row=2, min_col=1, max_col=2
    -> area = (2-0+1) * (2-1+1) = 3 * 2 = 6

Constraints:
- 1 <= m, n <= 100
- image[i][j] is 0 or 1
- image[x][y] == 1
- All 1's form one 4-connected component
- Runtime should beat O(m*n) on average
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We have a binary image where 1 = black, 0 = white.
All the black pixels form ONE connected blob (4-connected).
We're given ONE pixel that's part of this blob.

We need to find the smallest rectangle that contains ALL black pixels.
The answer is just the area of this rectangle.
```

### Step 2: The Trick
> "Since all 1's are connected, BFS/DFS from the given (x, y) will
> reach EVERY black pixel. Track min/max row/col as we visit them.
> The rectangle is just from min to max (inclusive) on both axes."
>
> Area = (max_row - min_row + 1) * (max_col - min_col + 1)
> The +1 is CRITICAL - it's inclusive count, not distance.

### Step 3: Why +1?
> "If min_row=0 and max_row=2, there are 3 rows: 0, 1, 2.
> max - min = 2, but count = 3.
> So we need +1 to get the count."

### Step 4: Why is this better than O(m*n)?
> "Full scan is O(m*n). BFS only visits black pixels (K = number of 1's).
> Since K <= m*n, BFS is at worst O(m*n) but typically MUCH faster.
> Worst case (all 1's): O(m*n). Best case (single 1): O(1)."

### Step 5: Connectivity exploitation
> "Without the connectivity guarantee, we'd need O(m*n) to find ALL blobs.
> Since they're connected, BFS from any 1 reaches all of them."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the area of the smallest axis-aligned rectangle
> enclosing all 1's. I'm given one (x, y) coordinate that's a 1."

**Key Insight:**
> "Since all 1's are connected (4-connected), BFS from (x, y) will
> reach all of them. I'll track min/max row and col as I visit each 1.
> Area is (max_row - min_row + 1) * (max_col - min_col + 1)."

**Algorithm:**
> "1. Initialize visited grid, queue with (x, y).
> 2. min_r = max_r = x, min_c = max_c = y.
> 3. While queue not empty:
>    a. Pop (r, c). Update min/max.
>    b. For each 4-neighbor that's 1 and not visited:
>       Mark visited, push to queue.
> 4. Return (max_r - min_r + 1) * (max_c - min_c + 1)."

**Why +1 in area:**
> "Inclusive count: rows 0 to 2 means 3 rows (0, 1, 2). Distance is 2."

**Edge cases:**
- Single 1: area = 1.
- All 1's: area = m*n.
- (x, y) at corner: still works.
- Rectangle is full row/column: works correctly.

**Complexity:**
- Time: O(K) where K = number of black pixels
- Space: O(K) for visited + queue

---

## The 20 Implementations (Simple to Complex)

### Way 1: BFS from (x,y) (BEST - Memorize!)
```python
def min_area(image, x, y):
    from collections import deque
    rows, cols = len(image), len(image[0])
    visited = [[False] * cols for _ in range(rows)]
    queue = deque([(x, y)])
    visited[x][y] = True

    min_r = max_r = x
    min_c = max_c = y
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        r, c = queue.popleft()
        min_r, max_r = min(min_r, r), max(max_r, r)
        min_c, max_c = min(min_c, c), max(max_c, c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and image[nr][nc] == 1):
                visited[nr][nc] = True
                queue.append((nr, nc))

    return (max_r - min_r + 1) * (max_c - min_c + 1)
```

### Way 2: Verbose version with explicit names

### Way 3: DFS recursive (with sys.setrecursionlimit)
```python
def dfs(r, c):
    visited[r][c] = True
    # update bounds
    for dr, dc in DIRS:
        if valid and not visited and image == 1:
            dfs(nr, nc)
```

### Way 4: DFS iterative with explicit stack

### Way 5: Full scan (O(m*n) baseline)
- Just iterate over the entire grid looking for 1's.

### Way 6: Linear scan up/down from (x,y)
- Step up while we see 1's in the column, etc.

### Way 7: DFS with tuple tracking in stack

### Way 8: BFS with in-place marking (mutates input)

### Way 9: BFS with negative marking + restoration

### Way 10-13: Various BFS style variations

### Way 14: Class-based OOP

### Way 15: BFS tracking rows/cols as sets

### Way 16-17: Heap-based, list-based bounds

### Way 18-19: Concise Pythonic versions

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Best general     | Way 1    | BFS, simple  |
| No mutation      | Way 1    | Uses visited |
| Memory opt       | Way 8    | In-place     |
| Educational      | Way 3    | DFS recursion|
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| BFS (Way 1) | O(K) | O(K) | Best general |
| DFS recursive (Way 3) | O(K) | O(K) | Stack depth risk |
| In-place BFS (Way 8) | O(K) | O(1) | Mutates input |
| Full scan (Way 5) | O(mn) | O(1) | Simple but slow |

Where K = number of black pixels.

---

## Walkthrough Example

```
image = [
  [0, 0, 1, 0],
  [0, 1, 1, 0],
  [0, 1, 0, 0]
]
(x=0, y=2)

BFS from (0, 2):
- Visit (0, 2). min_r=max_r=0, min_c=max_c=2.
- Neighbors: (0,1)=0, (0,3)=0, (1,2)=1, (-1,2)=OOB.
  -> Queue: [(1, 2)]
- Visit (1, 2). Update min/max: max_r=1.
- Neighbors: (0,2) visited, (2,2)=0, (1,1)=1, (1,3)=0.
  -> Queue: [(1, 1)]
- Visit (1, 1). Update min/max: min_c=1, max_r=1.
- Neighbors: (0,1)=0, (2,1)=1, (1,0)=0, (1,2) visited.
  -> Queue: [(2, 1)]
- Visit (2, 1). Update min/max: max_r=2, min_c=1.
- Neighbors: (1,1) visited, (3,1)=OOB, (2,0)=0, (2,2)=0.
  -> Queue: []

Bounds: min_r=0, max_r=2, min_c=1, max_c=2
Area = (2-0+1) * (2-1+1) = 3 * 2 = 6 ✓
```

---

## Best Answer to Memorize

```python
def min_area(image, x, y):
    from collections import deque
    if not image or not image[0] or image[x][y] != 1:
        return 0
    rows, cols = len(image), len(image[0])
    visited = [[False] * cols for _ in range(rows)]
    queue = deque([(x, y)])
    visited[x][y] = True

    min_r = max_r = x
    min_c = max_c = y
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while queue:
        r, c = queue.popleft()
        if r < min_r: min_r = r
        if r > max_r: max_r = r
        if c < min_c: min_c = c
        if c > max_c: max_c = c
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and image[nr][nc] == 1):
                visited[nr][nc] = True
                queue.append((nr, nc))

    return (max_r - min_r + 1) * (max_c - min_c + 1)
```

**~25 lines. O(K) time. O(K) space. Interview-ready!**

---

## Key Insights

### Why BFS/DFS and not just scan?
> "Full scan is O(m*n). BFS visits only black pixels (K). Since K <= m*n,
> BFS is at worst O(m*n) but typically much faster. Worst case (all 1's):
> O(m*n). Best case (single 1): O(1)."

### Why does connectivity matter?
> "If 1's weren't connected, we'd need to find ALL blobs (O(m*n)).
> With connectivity guarantee, BFS from any 1 reaches all of them."

### Why +1 in area calculation?
> "max_r - min_r gives DISTANCE between rows.
> We need COUNT of rows (inclusive).
> If max_r=2 and min_r=0, distance is 2 but count is 3."

### Why does the (x,y) parameter matter?
> "It tells us where to START BFS. Without it, we'd need to find ANY 1
> first (extra O(m*n) scan). With it, we start directly."

### Could we use binary search?
> "Yes! Since 1's are connected, once we know one row/col has 1's,
> we can binary search for the boundary. This gives O(m log n + n log m).
> But BFS is simpler and typically faster in practice for small m, n (<=100)."

---

## Test Cases

| image | (x,y) | Expected Area |
|-------|-------|---------------|
| [[0,0,1,0],[0,1,1,0],[0,1,0,0]] | (0,2) | 6 |
| [[1]] | (0,0) | 1 |
| [[1,1,1],[1,1,1]] | (0,0) | 6 |
| [[1],[1],[1]] | (1,0) | 3 |
| [[1,1,1,1]] | (0,2) | 4 |
| 2x2 block in middle of 4x4 | (1,1) | 4 |
| L-shape 3x4 | (0,0) | 12 |
| Horizontal pair | (0,1) | 2 |

---

## Common Pitfalls

1. **Forgetting +1**: Area = (max-min+1) * (max-min+1), not (max-min).
2. **Wrong 4-connectivity**: Use up/down/left/right, NOT diagonal.
3. **Not checking image[x][y] == 1**: Problem guarantees it but defensive check.
4. **Full scan when BFS suffices**: For dense grids they're equal, but BFS better for sparse.
5. **Mutating input without warning**: Way 8 marks cells - generally bad practice.
6. **Off-by-one in bounds**: Make sure to update min/max BEFORE adding neighbors.

---

## Why This Problem Matters

> "Tests:
> 1. BFS/DFS on binary matrix.
> 2. Coordinate tracking during traversal.
> 3. Area calculation with inclusive bounds.
> 4. Leveraging connectivity for efficiency.
> 5. Foundation for: image processing, blob detection, bounding boxes."

---

## Beyond This Problem: Related Patterns

### 1. Number of Islands (LC 200)
```python
# Same BFS/DFS pattern, count connected components of 1's
# Increment count for each new BFS
```

### 2. Max Area of Island (LC 695)
```python
# BFS that counts cells in each blob, return max
# Instead of bounds, just count
```

### 3. Surrounded Regions (LC 130)
```python
# BFS from boundary 'O's, mark safe. Others are flipped.
```

### 4. Making a Large Island (LC 827)
```python
# Find all blobs, label them, try flipping each 0 to find max area.
```

### 5. 01 Matrix (LC 542)
```python
# Multi-source BFS from all 0's, find distance to nearest 0.
```

---

## Connection to Image Processing

This problem is essentially **BOUNDING BOX** detection in image processing:

```
1. Find connected components (labeling).
2. Compute bounding box for each component.
3. The bounding box is (min_r, min_c) to (max_r, max_c).
4. Area = (max_r - min_r + 1) * (max_c - min_c + 1).
```

This is a FUNDAMENTAL operation in computer vision used in:
- Object detection (find objects in image)
- OCR (locate text regions)
- Face detection (bounding boxes around faces)
- Tracking (bounding boxes around moving objects)

---

## Quick Checklist for the Interview

When given a similar problem:
- [ ] What's the connectivity rule? (4-connected vs 8-connected)
- [ ] Are all the target pixels guaranteed connected?
- [ ] What do I return? (count, area, bounds, path?)
- [ ] Can I mutate the input? (in-place marking)
- [ ] What's the optimal time complexity given the constraints?
