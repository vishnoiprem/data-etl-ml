# Minimum Time to Reach Destination Without Drowning - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-takes-to-reach-destination-without-drowning

## The Problem
```
Given an m x n grid 'land' of strings, find the minimum time to reach
the destination without drowning.

Grid cells:
- 'S': Source (start) - you start here
- 'D': Destination - goal (never floods)
- '.': Empty cell (walkable)
- 'X': Stone (impassable)
- '*': Flooded cell (impassable)

Movement: 1 cell per second in any of 4 cardinal directions.
Flooding: Each second, all empty (.) cells adjacent to flooded (*) cells
          also become flooded.

Constraints:
- Cannot step on X (stone) or * (flooded).
- Cannot step on a cell that becomes flooded at the moment of stepping.
- D never floods.

Return minimum seconds to reach D from S, or -1 if impossible.

Constraints:
- 2 <= m, n <= 100
- Exactly one S, one D
- Cells only contain S, D, ., *, X
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
This is BFS on a TIME-DEPENDENT grid. The "safe" cells change over time
because the flood spreads each second.

Key insight: A cell that's safe NOW might be flooded by the time I get
there. So I need to know WHEN each cell floods.

Example:
    . S X *
    . . X .
    . . D .
    . X . .
    * . . .

Flood starts at (0,3) and (4,0).
- t=0: flood at (0,3), (4,0)
- t=1: flood spreads to neighbors (e.g., (1,3), (3,0), (4,1))
- t=2: continues spreading
- ...

D never floods. We need to find shortest path where we ARRIVE at each
cell BEFORE it floods.
```

### Step 2: The Trick
> "Two-phase approach:
>
> **Phase 1: Multi-source BFS from all * cells.**
> Compute `flood_time[i][j]` = time when cell (i,j) becomes flooded.
> Use BFS starting from all * cells simultaneously.
>
> **Phase 2: BFS from S, but with flood awareness.**
> For each candidate next cell, only move there if:
>   `arrival_time < flood_time[next_cell]`
> The STRICT less-than is critical!
>
> The strict < handles the simultaneity: at second t, BOTH we move
> AND the flood spreads. If we arrive AT the same moment the cell
> floods, we drown."

### Step 3: Why Multi-source BFS?
> "All * cells are sources of flood. They all spread simultaneously.
> So we start BFS from ALL * cells at once (distance 0), and propagate
> to neighbors with distance 1, etc.
> This is exactly the same pattern as 'Rotting Oranges' (LeetCode 994)."

### Step 4: Why D never floods (but neighbors might)?
> "D is special - it's safe. But its NEIGHBORS can flood. So when we
> step onto D, we check that the path TO D was safe, but D itself
> is always safe."

### Step 5: Strict vs non-strict inequality
> "The problem says 'cells that will flood RIGHT WHEN you try to step on
> them because you'll drown.' This means arrival_time == flood_time
> IS drowning. So we use STRICT < : arrival_time < flood_time."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the shortest time to reach D from S while avoiding both
> stones and cells that flood. The flood spreads each second to adjacent
> empty cells."

**Key Insight:**
> "Standard BFS won't work because the 'safe' cells change over time.
> I need to know WHEN each cell gets flooded, then plan my path to
> arrive strictly BEFORE that time."

**Algorithm:**
> "1. PHASE 1: Multi-source BFS from all * cells to compute flood_time[i][j].
>    Each * cell has flood_time=0. Spread to neighbors with t+1.
>    D and X are skipped (D never floods, X is wall).
> 2. PHASE 2: BFS from S, but only move to a cell if arrival_time < flood_time.
> 3. Return time when D is reached, or -1 if BFS exhausts."

**Why strict less-than:**
> "At each second, BOTH I move AND the flood spreads. So if I arrive at
> a cell AT the same moment it floods, I drown. I need to arrive
> STRICTLY BEFORE the flood."

**Edge cases:**
- n=1: single row, simple path.
- S or D adjacent to *: depending on flood direction.
- D surrounded by safe cells: simple BFS without flood constraints.
- D unreachable due to flooding: return -1.

**Complexity:**
- Time:  O(m*n) - two BFS passes over the grid
- Space: O(m*n) - flood_time grid + visited grid

---

## The 20 Implementations (Simple to Complex)

### Way 1: Precompute flood + BFS (BEST - Memorize!)
```python
def minimum_seconds(land):
    from collections import deque
    rows, cols = len(land), len(land[0])
    INF = float('inf')
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Find S
    si, sj = next((r, c) for r, row in enumerate(land)
                  for c, cell in enumerate(row) if cell == 'S')
    
    # Phase 1: Multi-source BFS for flood times
    flood_time = [[INF] * cols for _ in range(rows)]
    flood_queue = deque()
    for r in range(rows):
        for c in range(cols):
            if land[r][c] == '*':
                flood_time[r][c] = 0
                flood_queue.append((r, c))
    while flood_queue:
        r, c = flood_queue.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and land[nr][nc] not in ('X', 'D'):
                if flood_time[r][c] + 1 < flood_time[nr][nc]:
                    flood_time[nr][nc] = flood_time[r][c] + 1
                    flood_queue.append((nr, nc))
    
    # Phase 2: Person BFS with flood awareness
    visited = [[False] * cols for _ in range(rows)]
    person_queue = deque([(si, sj, 0)])
    visited[si][sj] = True
    while person_queue:
        r, c, t = person_queue.popleft()
        if land[r][c] == 'D':
            return t
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and land[nr][nc] != 'X' and t + 1 < flood_time[nr][nc]):
                visited[nr][nc] = True
                person_queue.append((nr, nc, t + 1))
    return -1
```

### Way 2: Verbose version with explicit variable names

### Way 3-4: Variations using `next()` for finding S

### Way 5: Simultaneous BFS (interleave flood and person)
```python
# Each "round":
#   - Person moves one step (all queued cells at this time)
#   - Then flood spreads to all eligible empty cells
# Repeat until D found or queue empty.
```

### Way 6-7: Standard BFS with state tracking

### Way 8: Named directions dictionary

### Way 9: A* search (advanced - uses Manhattan heuristic)
```python
# A* with flood-aware pruning.
# f(n) = g(n) + h(n) where h = Manhattan distance to D.
# Skip cells where arrival_time >= flood_time.
```

### Way 10-12: Various optimizations

### Way 13: Class-based OOP
```python
class FloodEscapeSolver:
    def solve(self): ...
    def _compute_flood_times(self): ...
    def _bfs_person(self, ...): ...
```

### Way 14: Namedtuple for state

### Way 15: List as queue (educational)

### Way 16: Separated concern with helper function

### Way 17: Set-based frontier for flood propagation

### Way 18: Integer-encoded state (memory-efficient)

### Way 19: Most concise (Pythonic one-liner style)

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Most efficient   | Way 1    | Two BFS O(mn)|
| Whiteboard       | Way 2    | Most readable|
| Functional       | Way 5    | Interleaved  |
| A* optimization  | Way 9    | Heuristic    |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Two-phase BFS (Way 1) | O(mn) | O(mn) | Best general |
| Simultaneous (Way 5) | O(mn) | O(1) | Mutates grid |
| A* (Way 9) | O(mn log n) | O(mn) | Better for large grids |
| DFS + memo (Way 11) | O(mn) | O(mn) | May stack overflow |

---

## Walkthrough Example

```
land = [
  ['.', 'S', 'X', '*'],
  ['.', '.', 'X', '.'],
  ['.', '.', 'D', '.'],
  ['.', 'X', '.', '.'],
  ['*', '.', '.', '.']
]

Phase 1: Multi-source BFS from * cells
=========================================
Initial: flood_time[*] = 0, others = INF
- (0,3)* and (4,0)* are sources.

BFS expansion:
- t=1: (1,3), (3,0), (4,1) flood
- t=2: (2,3), (3,1), (2,0), (4,2) flood
- t=3: (3,2), (1,0), (4,3) flood (D not flooded)

Phase 2: Person BFS from S=(0,1)
=========================================
t=0: queue = [(0,1, 0)]

t=1: Process (0,1).
  Neighbors: (0,0), (1,1), (0,2)
  - (0,0): flood_time=INF. arrival 1<INF OK. Add.
  - (1,1): flood_time=INF. Add.
  - (0,2): blocked by X. Skip.
  queue = [(0,0,1), (1,1,1)]

t=2: Process (0,0), (1,1).
  From (0,0): (1,0) flood_time=3, arrival 2<3 OK. Add.
  From (1,1): (2,1) flood_time=INF, add. (0,1) visited. (1,0) already in queue.
  queue = [(1,0,2), (2,1,2)]

t=3: Process (1,0), (2,1).
  From (2,1): (2,2)=D! Return 3.

Answer: 3 seconds ✓

Path: S(0,1) -> (1,1) -> (2,1) -> D(2,2)
```

---

## Best Answer to Memorize

```python
def minimum_seconds(land):
    from collections import deque
    if not land or not land[0]:
        return -1
    rows, cols = len(land), len(land[0])
    INF = float('inf')
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Locate S
    si, sj = next((r, c) for r, row in enumerate(land)
                  for c, cell in enumerate(row) if cell == 'S')

    # Phase 1: Flood times
    flood_time = [[INF] * cols for _ in range(rows)]
    flood_queue = deque()
    for r in range(rows):
        for c in range(cols):
            if land[r][c] == '*':
                flood_time[r][c] = 0
                flood_queue.append((r, c))
    while flood_queue:
        r, c = flood_queue.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and land[nr][nc] not in ('X', 'D'):
                if flood_time[r][c] + 1 < flood_time[nr][nc]:
                    flood_time[nr][nc] = flood_time[r][c] + 1
                    flood_queue.append((nr, nc))

    # Phase 2: Person BFS
    visited = [[False] * cols for _ in range(rows)]
    q = deque([(si, sj, 0)])
    visited[si][sj] = True
    while q:
        r, c, t = q.popleft()
        if land[r][c] == 'D':
            return t
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                    and land[nr][nc] != 'X' and t + 1 < flood_time[nr][nc]):
                visited[nr][nc] = True
                q.append((nr, nc, t + 1))
    return -1
```

**~30 lines. O(mn) time. O(mn) space. Interview-ready!**

---

## Key Insights

### Why two-phase BFS?
> "We need to know flood times BEFORE searching for the path. So we
> compute them first (Phase 1), then use them to constrain the path
> search (Phase 2)."

### Why strict < (not <=)?
> "Movement and flooding happen SIMULTANEOUSLY each second. If we arrive
> at a cell AT THE SAME TIME it floods, we drown. We need to arrive
> STRICTLY BEFORE."

### Why multi-source BFS for floods?
> "All * cells are sources - they spread simultaneously. We start BFS
> from ALL of them at once with distance 0, and BFS naturally gives
> the minimum distance (time to flood) for each cell."

### Why D never floods (per problem guarantee)?
> "The problem states this. So D is always safe to step on.
> But we still need a path to reach D - the cells we step on BEFORE D
> might flood, so the strict < check still applies for those cells."

### Why does flood spread to S itself?
> "If S is adjacent to a * cell, S itself can flood at t=1. But we've
> already left S by then, so it doesn't affect us. However, we should
> NOT step back onto S after it floods."

### Why is this similar to Rotting Oranges?
> "Rotting Oranges (LC 994): BFS from all rotten oranges to find
> time for fresh oranges to rot.
> This problem: BFS from all * cells to find time for empty cells to flood.
> Same pattern, just different problem domain."

---

## Test Cases

| land | Expected |
|------|----------|
| [[. S X *], [.. X.], [...D.], [.X..], [*...]] | 3 |
| [[S.D], [XXX]] | 2 |
| [[S D]] | 1 |
| [[S X]] | -1 (D missing) |
| [[S*..D],[.....]] | -1 |
| [[SX X],[XXX],[XXD]] | -1 |
| [] | -1 |

---

## Common Pitfalls

1. **Using <= instead of <**: Drowns at same-time flooding.
2. **Forgetting to skip X in flood BFS**: Stones can be flooded neighbors.
3. **Allowing S to flood**: Should only matter if you re-enter S.
4. **Not handling empty grid**: Return -1.
5. **Treating D as floodable**: D never floods.
6. **Single BFS instead of two-phase**: Doesn't account for time-dependence.
7. **Wrong multi-source init**: All * should be in queue at t=0.

---

## Why This Problem Matters

> "Tests:
> 1. Time-dependent grid search (CRITICAL pattern).
> 2. Multi-source BFS (flood spreading).
> 3. Standard BFS with constraints.
> 4. Careful inequality (strict less-than).
> 5. Foundation for: Rotting Oranges, Walls and Gates, 01 Matrix,
>    and any 'time-spreading' problems."

---

## Beyond This Problem: Related Patterns

### 1. Rotting Oranges (LeetCode 994)
```python
# Same multi-source BFS pattern:
# - Initial: rotten oranges in queue
# - Spread to fresh oranges each minute
# - Return time until all fresh, or -1
```

### 2. Walls and Gates (LeetCode 286)
```python
# BFS from all gates (multi-source)
# Fill distance to nearest gate for each empty room
```

### 3. 01 Matrix (LeetCode 542)
```python
# BFS from all 0s, find distance to nearest 0 for each 1
```

### 4. Shortest Bridge (LeetCode 934)
```python
# Two-phase: mark one island, then BFS to find other
```

### 5. Escape a Large Maze (LeetCode 1036)
```python
# BFS with bounded grid (avoid infinite search)
```

---

## Connection to BFS Patterns

This problem combines THREE critical BFS patterns:

1. **Multi-source BFS** (flood spreading from all * cells)
2. **State-tracking BFS** (time as a state variable)
3. **Constraint-aware BFS** (only visit cells satisfying conditions)

Master this and you've mastered time-dependent grid problems!

---

## Quick Checklist for the Interview

When given a similar problem, ask:
- [ ] Is the grid dynamic (changes over time)?
- [ ] What changes? (flood, fire, monsters, etc.)
- [ ] Do I need to precompute when things change?
- [ ] What's the move constraint? (strict before, at, or after?)
- [ ] Is the goal cell special? (never changes, is the source, etc.)

If YES to most of these → two-phase BFS with multi-source precomputation.
