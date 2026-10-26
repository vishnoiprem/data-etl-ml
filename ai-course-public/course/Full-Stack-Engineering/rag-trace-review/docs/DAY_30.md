# Day 30 — Algorithms: Graphs, Topological Sort, Union-Find
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

A **graph** is a set of nodes and edges. It's a generalization of a tree (a tree is a connected acyclic graph). Two problems show up constantly:

- **Reachability:** "is there a path from A to B?" — BFS/DFS.
- **Cycles:** "is there a cycle?" — DFS with 3 colors, or Union-Find.

**Topological sort** = linear ordering where every edge `u → v` has `u` before `v`. Only works on **DAGs** (directed acyclic graphs).

---

## 2. Technical concepts (20 min)

### Representations

| Form | Use | Memory |
|---|---|---|
| Adjacency list | Sparse graphs | O(V + E) |
| Adjacency matrix | Dense graphs, fast edge lookup | O(V²) |
| Edge list | Kruskal's algorithm | O(E) |

For interviews, **adjacency list** is the default: `dict[Node, list[Node]]` or `list[list[int]]`.

### BFS on a graph
```python
def bfs(graph, start):
    visited = {start}
    q = deque([start])
    while q:
        node = q.popleft()
        for nbr in graph[node]:
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)
```

### DFS with 3-color (cycle detection)
- **White:** unvisited.
- **Gray:** in current DFS stack.
- **Black:** fully processed.
- **Cycle** = edge to a gray node.

```python
WHITE, GRAY, BLACK = 0, 1, 2
def has_cycle(graph):
    color = {n: WHITE for n in graph}
    def dfs(u):
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY: return True  # cycle
            if color[v] == WHITE and dfs(v): return True
        color[u] = BLACK
        return False
    return any(color[n] == WHITE and dfs(n) for n in graph)
```

### Topological sort (Kahn's BFS)
1. Compute in-degree of each node.
2. Queue all in-degree-0 nodes.
3. Pop, append to output, decrement neighbors' in-degree.
4. If output is shorter than V → cycle.

### Union-Find (Disjoint Set)
- **Find:** with path compression, O(α(n)) ≈ O(1).
- **Union:** with rank/size, O(α(n)).
- Use for: "are A and B in the same component?", cycle detection in undirected graphs.

```python
class UF:
    def __init__(self, n):
        self.p = list(range(n))
        self.r = [0] * n
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]  # path compression
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False
        if self.r[ra] < self.r[rb]: ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]: self.r[ra] += 1
        return True
```

### Grid as a graph
- 2D grid → graph: 4 neighbors (up/down/left/right), 8 if diagonals allowed.
- Index = `r * cols + c`.
- DFS with **in-place mutation** (`grid[r][c] = "0"`) saves a `visited` set.

---

## 3. Coding (30 min)

> **Note on `Node` class:** Problems 2 and 3 use a different `Node` class than Day 29 (LeetCode's `Node` has `val` and `neighbors`, not `v`/`left`/`right`). Define it once at the top of your file:
> ```python
> class Node:
>     def __init__(self, val=0, neighbors=None):
>         self.val = val
>         self.neighbors = neighbors if neighbors is not None else []
> ```

Solve **3 problems**, ~10 min each.

### Problem 1: Number of Islands

Given a 2D grid of `'1'` (land) and `'0'` (water), count the islands.

```python
def num_islands(grid: list[list[str]]) -> int:
    if not grid or not grid[0]: return 0
    R, C = len(grid), len(grid[0])
    count = 0
    def dfs(r, c):
        if r < 0 or r >= R or c < 0 or c >= C or grid[r][c] != "1":
            return
        grid[r][c] = "0"  # mark visited in-place
        dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1)
    for r in range(R):
        for c in range(C):
            if grid[r][c] == "1":
                count += 1
                dfs(r, c)
    return count
```

- **Time:** O(R·C). **Space:** O(R·C) recursion stack in worst case (skewed grid). Use iterative to be safe.

### Problem 2: Course Schedule

Given `numCourses` and `prerequisites = [[a, b]]` (b must be done before a), can you finish all courses?

```python
def can_finish(num_courses: int, prereq: list[list[int]]) -> bool:
    g = [[] for _ in range(num_courses)]
    indeg = [0] * num_courses
    for a, b in prereq:
        g[b].append(a)
        indeg[a] += 1
    from collections import deque
    q = deque([i for i, d in enumerate(indeg) if d == 0])
    taken = 0
    while q:
        u = q.popleft()
        taken += 1
        for v in g[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return taken == num_courses
```

- **Time:** O(V + E). **Space:** O(V + E).
- **Sample:** `numCourses=2, prereq=[[1,0]]` → `True`. `[[1,0],[0,1]]` → `False` (cycle).

### Problem 3: Pacific Atlantic Water Flow

Given an m×n grid of heights, find cells that can flow to **both** the Pacific (top/left) and Atlantic (bottom/right). Water flows from high to low.

```python
def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    if not heights: return []
    R, C = len(heights), len(heights[0])
    dirs = [(0,1),(0,-1),(1,0),(-1,0)]
    def bfs(starts):
        seen = set(starts)
        q = deque(starts)
        while q:
            r, c = q.popleft()
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and (nr, nc) not in seen and heights[nr][nc] >= heights[r][c]:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return seen
    # Pacific: top row + left column (skip (0,0) — already in top row)
    pac_starts = [(0, c) for c in range(C)] + [(r, 0) for r in range(1, R)]
    # Atlantic: bottom row + right column (skip (R-1, C-1) — already in bottom row)
    atl_starts = [(R-1, c) for c in range(C)] + [(r, C-1) for r in range(R - 1)]
    pac = bfs(pac_starts)
    atl = bfs(atl_starts)
    return [list(p) for p in (pac & atl)]
```

- **Time:** O(R·C). **Space:** O(R·C).
- **Key insight:** instead of asking "where can this cell go?", ask "what can reach the ocean?".

---

## 4. Debugging & tests (20 min)

### Bug 1: number of islands counts diagonal
**Symptom:** diagonal `'1'`s are merged into one island.
**Fix:** only 4 directions. Diagonals = 8 directions (separate problem).

### Bug 2: course schedule misses self-loop
**Symptom:** A naive version that skips indegree computation (or uses an adjacency-only check) returns `True` for `prereq = [[0, 0]]` — it sees an edge but doesn't notice the cycle.
**Fix:** correctly compute `indeg[a] += 1` for each prereq `[a, b]`. With `[[0, 0]]`, indeg becomes `[1, 0]`, queue is empty, `taken=0`, so the function correctly returns `False`.

### Bug 3: pacific_atlantic reverses the flow
**Symptom:** water can't flow up, but the result includes cells that only flow up.
**Fix:** `heights[nr][nc] >= heights[r][c]`. Reverse BFS from the ocean.

### Bug 4: recursion stack overflow on large grid
**Symptom:** 1000×1000 grid → RecursionError.
**Fix:** convert to iterative with explicit stack. Or DFS in chunks of 1000 cells.

### Tests
```python
def test_num_islands():
    assert num_islands([
        ["1","1","0","0","0"],
        ["1","1","0","0","0"],
        ["0","0","1","0","0"],
        ["0","0","0","1","1"],
    ]) == 3

def test_can_finish():
    assert can_finish(2, [[1, 0]]) == True
    assert can_finish(2, [[1, 0], [0, 1]]) == False
    assert can_finish(1, []) == True
    assert can_finish(1, [[0, 0]]) == False

def test_pacific_atlantic():
    g = [[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]
    res = pacific_atlantic(g)
    assert (0, 4) in [tuple(r) for r in res]
    assert (1, 3) in [tuple(r) for r in res]
```

---

## 5. Mock interview practice (20 min)

**Q1 — "BFS or DFS for shortest path?"**
> BFS, because BFS expands in layers. DFS might find a longer path first.

**Q2 — "Why DFS with 3 colors for cycle detection?"**
> 2 colors (visited/unvisited) can confuse "currently exploring" with "fully done". Gray = currently exploring, so edge to gray = back edge = cycle.

**Q3 — "Topological sort on undirected graph?"**
> Doesn't work. Need a DAG. If your graph is undirected, you have a "constraint" problem, not a "prerequisite" problem.

**Q4 — "Union-Find vs DFS for connected components?"**
> Union-Find is faster for "add edges one at a time, query 'are A and B connected?'". DFS is simpler for "give me all components of this static graph".

**Q5 — "How do you handle graphs too big to fit in memory?"**
> External memory: stream edges; use multi-pass. Or pre-partition. For 1B edges, you'd use a graph DB (Neo4j, TigerGraph).

---

## 6. Success criteria check
- [ ] I can solve Number of Islands in 5 min.
- [ ] I can implement Kahn's algorithm.
- [ ] I can name 3 graph representations.
- [ ] I can implement Union-Find with path compression.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

## 8. Coding assignment
**Clone Graph** — given a node in a connected undirected graph, return a deep copy.

### Rubric (0–10)
- 0: doesn't compile
- 4: copies one node
- 6: handles neighbors
- 8: BFS/DFS with visited map
- 10: handles cycles correctly

### Solution
```python
def clone_graph(node):
    if not node: return None
    # Key on object identity, not value — graphs can have duplicate values
    seen: dict[int, "Node"] = {id(node): Node(node.val)}
    def dfs(u):
        for v in u.neighbors:
            if id(v) not in seen:
                seen[id(v)] = Node(v.val)
                dfs(v)  # recurse first to populate v's neighbors
            seen[id(u)].neighbors.append(seen[id(v)])
        return seen[id(u)]
    return dfs(node)
```

- **Time:** O(V + E). **Space:** O(V).
- **Key insight:** key the visited map by `id(node)`, not `node.val` — different nodes can have the same value.
- **Alternative (cleaner, iterative BFS):**
```python
from collections import deque
def clone_graph(node):
    if not node: return None
    seen = {id(node): Node(node.val)}
    q = deque([node])
    while q:
        u = q.popleft()
        for v in u.neighbors:
            if id(v) not in seen:
                seen[id(v)] = Node(v.val)
                q.append(v)
            seen[id(u)].neighbors.append(seen[id(v)])
    return seen[id(node)]
```

**Time: 90 min**
