# Swim in Rising Water — 0.0001% Expert Guide

> **LeetCode 778** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/swim-in-rising-water
> **Problem:** `swimInWater(grid)` — min time to swim from (0,0) to (n-1,n-1) as water rises

---

## 📋 WHAT THE QUESTION ASKS

Given an `n×n` integer grid where `grid[i][j]` is the elevation at `(i,j)`. Rain starts to fall and water depth rises to `t` at time `t`. The swimmer can move 4-directionally between adjacent cells if BOTH cells have elevation `<= t`. Find the minimum time `t` at which the swimmer can travel from `(0,0)` to `(n-1,n-1)`.

### Constraints
- `n == grid.length == grid[i].length`
- `1 <= n <= 50`
- `0 <= grid[i][j] < n*n`
- All `grid[i][j]` are unique

### Example

```
Input:
[[0, 1, 2, 3],
 [12, 11, 10, 4],
 [13, 14, 9, 5],
 [15, 8, 7, 6]]
Output: 6
```

At t=6: cells with elevation <=6 are reachable from (0,0).
Path: 0 → 1 → 2 → 3 → 4 → 5 → 6.

### Why This Is Hard
- The grid is NOT sorted in any global sense.
- We need the **min over all paths** of the **max elevation along the path**.
- This is a "**min-max path**" problem — a variation of shortest path.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find the minimum time t at which a swimmer can cross the grid as water rises."

### Step 2: Reframe as Path Optimization (3 min)
> "The answer is the MIN over all paths from (0,0) to (n-1,n-1) of the MAX elevation along that path."

This is a **min-max path** problem.

### Step 3: Brainstorm Approaches (5 min)

**Three classic approaches:**

1. **Dijkstra's Algorithm** — Treat cost of entering a cell as its elevation. Use a min-heap with priority = max elevation seen so far.
2. **Union-Find (Kruskal's-like)** — Process cells in order of elevation. Union them with already-processed neighbors. When (0,0) and (n-1,n-1) become connected, that's the answer.
3. **Binary Search on Time + DFS** — For a given t, can the swimmer reach the end? The predicate is MONOTONE in t, so binary search t.

### Step 4: Pick the Best (2 min)
- **Dijkstra**: Most intuitive, O(n² log n²).
- **Union-Find**: Cleaner code, O(n² α(n²)) ≈ O(n²).
- **Binary Search**: O(n² log n²), also clean.

**Memorize: Union-Find** (slightly cleaner, slightly faster).

### Step 5: Union-Find Intuition (5 min)
> "At time t, all cells with elevation <= t are 'unlocked'. The swimmer can use any unlocked cell connected to (0,0). When (0,0) and (n-1,n-1) become connected via unlocked cells, t is the answer."

Process cells in order of elevation. When we add cell (r,c), union it with any already-added neighbor. After each union, check if (0,0) and (n-1,n-1) are in the same component.

### Step 6: Sanity Check (2 min)
- `n=1`: return `grid[0][0]`. ✓
- `grid[0][0]=8` (max): still works, we just start at t=8. ✓
- All cells same elevation: answer = max elevation.

### Step 7: Code It (10 min)

**Union-Find version:**
```python
def swimInWater(grid):
    n = len(grid)
    parent = list(range(n * n))
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    
    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])
    visited = [[False] * n for _ in range(n)]
    
    for elev, r, c in cells:
        visited[r][c] = True
        for dr, dc in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and visited[nr][nc]:
                a, b = r * n + c, nr * n + nc
                pa, pb = find(a), find(b)
                if pa != pb:
                    parent[pa] = pb
        if find(0) == find(n * n - 1):
            return elev
    return -1
```

### Step 8: Verify (2 min)
For `[[0,1,2,3],[12,11,10,4],[13,14,9,5],[15,8,7,6]]`:
- Add 0 (0,0): visited={(0,0)}, parent=(0,0). 0,0 not connected to 15.
- Add 1 (0,1): union with (0,0).
- Add 2 (0,2): union with (0,1).
- Add 3 (0,3): union with (0,2).
- Add 4 (1,3): union with (0,3).
- Add 5 (2,3): union with (1,3).
- Add 6 (3,3): union with (2,3). find(0) connects to (3,3)=6. ✓ Return 6.

### Step 9: Discuss Trade-offs (5 min)

> "Three approaches:
> 1. **Dijkstra**: O(n² log n²) time, O(n²) space. Intuitive.
> 2. **Union-Find**: O(n² α(n²)) ≈ O(n²) time, O(n²) space. Cleanest.
> 3. **Binary Search + DFS**: O(n² log n²) time, O(n²) space. Clean.

> I'll go with **Union-Find** for cleanliness, or **Dijkstra** for intuition."

### Step 10: Final Cleanest Code (5 min)
The 12-line solution that every interviewer wants to see.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"The swimmer needs to find the minimum time t such that they can cross
from (0,0) to (n-1,n-1) as water rises.

KEY INSIGHT: The answer is the MIN over all paths from start to end of the
MAX elevation along that path. This is the 'min-max path' problem.

THREE APPROACHES:

1. DIJKSTRA'S: Treat each cell as a node. Cost to enter = its elevation.
   Use min-heap with state (max_elev_so_far, row, col). Start at (grid[0][0], 0, 0).
   When we pop (n-1, n-1), the max_elev is the answer.

2. UNION-FIND: Sort cells by elevation. Add them in order, unioning with
   already-processed neighbors. When (0,0) and (n-1,n-1) become connected,
   the current elevation is the answer. Cleaner and slightly faster.

3. BINARY SEARCH + DFS: For a given t, can the swimmer reach the end?
   Predicate is monotone. Binary search t in [0, n²-1].

I'll go with Union-Find.

COMPLEXITY: O(n² α(n²)) time, O(n²) space."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Brute Force

| Way | Technique | Time | Space | Notes |
|-----|-----------|------|-------|-------|
| (none pure brute) | | | | n=50 makes full simulation infeasible |

### 🟡 TIER 2: Dijkstra's Algorithm

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Classic Dijkstra (heap, set) | O(n² log n²) | O(n²) | **The intuitive one** |
| 2 | 2D visited array | same | O(n²) | Variant |
| 3 | best[][] array | same | O(n²) | Variant |
| 8 | Verbose | same | O(n²) | Educational |
| 11 | dict visited | same | O(n²) | Variant |
| 12 | A* with heuristic | same | O(n²) | Faster in practice |
| 13 | Dijkstra iterative | same | O(n²) | Variant |
| 15 | Cleanest Dijkstra | same | O(n²) | **The clean one** |
| 16 | State class | same | O(n²) | OOP |
| 19 | Most concise | same | O(n²) | One-liner style |

### 🔴 TIER 3: Union-Find (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | Union-Find with rank | O(n² α(n²)) | O(n²) | **THE ANSWER** |
| 7 | Union-Find simple | same | O(n²) | Simpler |
| 10 | BFS by elevation | same | O(n²) | BFS variant |
| 14 | BFS by elevation simple | same | O(n²) | Variant |
| 18 | Union-Find inline | same | O(n²) | Educational |
| 20 | Final Union-Find | same | O(n²) | **THE ONE TO MEMORIZE** |

### 🟣 TIER 4: Binary Search + DFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Binary search + DFS | O(n² log n²) | O(n²) | **Alternative** |
| 5 | Binary search + BFS | same | O(n²) | Variant |
| 9 | Binary search + DFS visited | same | O(n²) | Variant |
| 17 | Binary search + Union-Find | same | O(n²) | Combination |

---

## 💎 THE 12-LINE UNION-FIND SOLUTION (Memorize!)

```python
def swimInWater(grid):
    n = len(grid)
    parent = list(range(n * n))
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    
    cells = sorted([(grid[i][j], i, j) for i in range(n) for j in range(n)])
    visited = [[False] * n for _ in range(n)]
    
    for elev, r, c in cells:
        visited[r][c] = True
        for dr, dc in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and visited[nr][nc]:
                a, b = r * n + c, nr * n + nc
                pa, pb = find(a), find(b)
                if pa != pb:
                    parent[pa] = pb
        if find(0) == find(n * n - 1):
            return elev
    return -1
```

**Time:** `O(n² α(n²))` ≈ `O(n²)`
**Space:** `O(n²)`

---

## 💎 ALTERNATIVE: THE 10-LINE DIJKSTRA

```python
def swimInWater(grid):
    n = len(grid)
    seen = set()
    heap = [(grid[0][0], 0, 0)]
    while heap:
        t, r, c = heapq.heappop(heap)
        if (r, c) in seen:
            continue
        if r == n - 1 and c == n - 1:
            return t
        seen.add((r, c))
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
                heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))
```

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Min-Max Path = Bottleneck Path

> The answer is the bottleneck — the path that minimizes its weakest link.

This is the dual of "max-min path" (Path with Maximum Minimum Value, LC 1102). Both are **bottleneck path** problems.

**Connection to operations research:**
- **Transportation:** Find the route that minimizes the maximum congestion.
- **Network reliability:** Find the path whose weakest link is strongest.
- **ML training:** Find the GPU pipeline whose slowest stage is fastest.

### Insight 2: Monotonicity + Binary Search

> The predicate "can the swimmer reach the end at time t?" is monotone.
> Binary search finds the smallest t where predicate is True.

This is the **same pattern** as the Kth Smallest in Multiplication Table!

**Connection to verification algorithms:**
- **Dafny/Coq proofs:** Binary search on a monotone predicate.
- **SAT solvers:** Binary search on assignment parameters.
- **Hyperparameter tuning:** Binary search on learning rate.

### Insight 3: Union-Find as Kruskal's MST Variant

> This problem is essentially Kruskal's MST algorithm running in reverse:
> Kruskal adds edges in order; here we add NODES in order of "cost" (elevation).

The connection: in Kruskal's, you stop when all nodes are connected. Here, you stop when two SPECIFIC nodes are connected.

**Connection to clustering:**
- **Single-linkage clustering:** Same Union-Find pattern.
- **Image segmentation:** Union pixels by intensity.
- **Connected components in graph ML:** Union-Find is the standard.

### Insight 4: Why Dijkstra Works for Min-Max

Dijkstra's algorithm finds shortest paths when:
- Edge weights are non-negative.
- The cost function is **monotone** along paths (here, max is monotone non-decreasing).

For min-max, "cost" = max elevation. When we relax an edge (cell), the new cost is `max(current_cost, cell_value)`, which is monotone. So Dijkstra's greedy expansion is correct.

**Connection to:**
- **Shortest path with constraints:** Each edge cost = max elevation = "bottleneck".
- **Bandwidth optimization:** Network paths with min-max bandwidth.

### Insight 5: Why Process Cells in Elevation Order

The "elevation order" processing is **Kruskal's** for a node-weighted graph. When nodes have weights, you can convert to edge weights by saying "edge cost = max of its two endpoints". Then Kruskal's MST algorithm gives you the order.

**Connection to:**
- **Image processing:** Region growing in order of intensity.
- **Watershed algorithms:** Process pixels in order of gradient.
- **Connected components with threshold:** Threshold-based segmentation.

### Insight 6: Off-by-One Considerations

For `grid[0][0]` not equal to 0:
- The answer is at LEAST `grid[0][0]` (need to wait for start cell to be uncovered).
- The answer is at LEAST `grid[n-1][n-1]` (need to wait for end cell).
- Binary search starts at `max(grid[0][0], grid[n-1][n-1])`, NOT 0.

In the Union-Find approach, this is automatic: the cells get added in order, and we only return when both are added AND connected.

### Insight 7: Complexity Comparison

| Approach | Time | Space | Pros | Cons |
|----------|------|-------|------|------|
| Dijkstra | O(n² log n²) | O(n²) | Intuitive | Heap overhead |
| Union-Find | O(n² α(n²)) | O(n²) | Cleanest | Less intuitive |
| Binary Search + DFS | O(n² log n²) | O(n²) | Easy to code | Re-traverses grid |

For n=50: Dijkstra ≈ 2500 × 6 = 15000 ops. Union-Find ≈ 2500 ops. BS+DFS ≈ 15000 ops. **Union-Find wins for cleanliness; Dijkstra wins for intuition.**

### Insight 8: A* Optimization

A* with admissible heuristic `h(r,c) = grid[r][c]` (lower bound on remaining max):
- `f = g + h = max_so_far + grid[r][c]`.
- Skips obviously bad paths.
- Often 2-3x faster than plain Dijkstra.

But complexity same asymptotically. Use only when needed.

### Insight 9: Why This Problem Tests Insight

The brute force is straightforward. The cleverness is realizing:
1. It's a **min-max path** problem.
2. **Union-Find** or **Dijkstra** solve it.
3. The **monotone predicate** enables binary search.

This is an **insight problem** — the *idea* is the hard part.

**Connection to AI:**
- **Heuristic search:** Same insight-driven approach.
- **A* variants:** All rely on clever insights about structure.
- **Reinforcement learning:** Reward shaping = monotonicity insights.

### Insight 10: Generalization

The pattern generalizes:

1. **Min-max path with weights** — LC 1102 (Path with Max Min Value): swap min/max.
2. **Min cost with constraints** — LC 787 (Cheapest Flight with K Stops).
3. **Shortest path with state** — LC 1928 (Min Cost to Reach Destination in Time).
4. **Multi-source Dijkstra** — LC 743 (Network Delay Time).

The core pattern: **Dijkstra where state encodes "max so far" or "min so far"**.

---

## 🧪 TEST CASES

| Grid | Answer | Reason |
|------|--------|--------|
| `[[0,1,2,3],[12,11,10,4],[13,14,9,5],[15,8,7,6]]` | 6 | Classic |
| `[[0]]` | 0 | Trivial |
| `[[0,1],[3,2]]` | 2 | Top path max=2 |
| `[[0,2],[1,3]]` | 3 | Both paths max=3 |
| `[[0,1],[2,3]]` | 3 | Both paths max=3 |
| `[[0,1,2],[3,4,5],[6,7,8]]` | 8 | Monotonic, must traverse all |
| `[[8,7,6],[5,4,3],[2,1,0]]` | 8 | Start is max |
| `[[0,1,2],[5,4,3],[6,7,8]]` | 8 | All paths include (2,2) |
| `[[0,1],[4,3]]` | 3 | Top path max=3 |
| `[[0,3,5],[1,4,2],[7,8,6]]` | 6 | Diagonal-ish path |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| Dijkstra | O(n² log n²) | O(n²) | ✅ Intuitive |
| **Union-Find** | **O(n² α(n²))** | **O(n²)** | **✅ BEST (cleanest)** |
| Binary Search + DFS | O(n² log n²) | O(n²) | ✅ Clean alternative |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Path with Max Min Value (LC 1102) | Same min-max | https://leetcode.com/problems/path-with-maximum-minimum-value/ |
| Cheapest Flights K Stops (LC 787) | Dijkstra with state | https://leetcode.com/problems/cheapest-flights-within-k-stops/ |
| Network Delay Time (LC 743) | Multi-source Dijkstra | https://leetcode.com/problems/network-delay-time/ |
| Min Cost to Reach Destination in Time (LC 1928) | BFS with time | https://leetcode.com/problems/minimum-cost-to-reach-destination-in-time/ |
| Swim in Rising Water (LC 778) | **This problem** | https://leetcode.com/problems/swim-in-rising-water/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Min-max path = bottleneck optimization.** Find path that minimizes its weakest link.
2. **Three approaches:** Dijkstra (intuition), Union-Find (cleanest), Binary Search (alternative).
3. **Union-Find is the answer to memorize.** Sort cells by elevation, union as you go.
4. **Dijkstra works because max is monotone.** State = (max_so_far, r, c).
5. **Binary search works because reachability is monotone.** `can_swim(t)` is monotone in `t`.
6. **Same pattern as Kth Smallest:** Both use binary search on a monotone predicate.
7. **Process in elevation order** = Kruskal's MST variant for node-weighted graphs.
8. **A* can speed up Dijkstra** by 2-3x with admissible heuristic `h = grid[r][c]`.
9. **The answer is at least `max(grid[0][0], grid[n-1][n-1])`** — both endpoints must be uncovered.
10. **This is an insight problem.** The brute force is easy; the cleverness is the algorithm choice.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Watershed segmentation** | Process pixels in order of gradient magnitude |
| **Image thresholding** | Find threshold where regions become connected |
| **Connected components** | Union-Find is the standard algorithm |
| **Region growing** | Process cells in cost order (similar to Union-Find) |
| **MST algorithms** | Kruskal's = process edges in order |
| **Network routing** | Min-max bandwidth path optimization |
| **ML pipeline optimization** | Find the bottleneck stage |
| **Transformer attention** | Top-k sparse attention = sort by score |
| **Bayesian optimization** | Acquisition function = monotone max |
| **Reinforcement learning** | Bottleneck policies, monotone value functions |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can reframe as min-max path in 60 seconds
- [x] Can code the Union-Find solution in 90 seconds
- [x] Know the complexity: O(n² α(n²)) time, O(n²) space
- [x] Can compare Dijkstra vs Union-Find vs Binary Search
- [x] Know why Union-Find works (process cells in elevation order)
- [x] Know why Dijkstra works (monotone cost function)
- [x] Know why Binary Search works (monotone reachability predicate)
- [x] Can discuss the Kruskal's MST connection
- [x] Can list 5 AI/data applications of min-max path

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 12 (Union-Find) or 10 (Dijkstra).
**Insight:** "Min-max path = Union-Find on cells sorted by elevation, OR Dijkstra with state (max_so_far, r, c)."
