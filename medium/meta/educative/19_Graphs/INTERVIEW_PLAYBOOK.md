# Graphs — Interview Playbook (Beginner → Confident)

> 10 solutions + the thinking framework. Read this once, then re-derive each problem from the framework — that's how the patterns stick.

---

## 0. The 3-sentence opener (say this at the start of any graph problem)

> "A graph is just a set of nodes and a set of edges. Most interview problems are a **walk** through that structure while maintaining some bookkeeping — *visited*, *distance*, *parent*, or *component*. The only question is *which* bookkeeping is needed and *which* traversal uses it correctly."

If you can say that clearly, you'll outclass half the candidates before writing a line.

---

## 1. Pick your algorithm in 4 questions

Before any code, ask (silently or out loud):

| # | Question | If YES, the answer is… |
|---|----------|------------------------|
| Q1 | Does every edge cost the same? | **BFS** (unweighted shortest path) |
| Q2 | Do edges have non-negative weights? | **Dijkstra** with a heap |
| Q3 | Do edges have negative weights (but no negative cycle)? | **Bellman-Ford** |
| Q4 | "Visit every edge/vertex exactly once" / "trace a path through all nodes"? | **Hierholzer** (Eulerian) — reverse-post-order for lex-smallest |
| Q5 | "Are X and Y in the same component?" / "merge nodes"? | **Union-Find** |
| Q6 | "Is there a cycle / is the graph a tree / connected?" | **DFS with parent** or Union-Find |
| Q7 | Grid-shaped graph (rooms, islands, mazes)? | **BFS in 4/8 dirs**, possibly *multi-source* |
| Q8 | No graph actually needed (in/out degree counter)? | **Counter only** — don't over-engineer |

The 10 problems in this folder cover exactly these 8 buckets.

---

## 2. The 10-file cheat sheet

| File | Algorithm | One-line idea |
|------|-----------|---------------|
| `01_introduction_to_graphs.py` | BFS + DFS | Two traversal templates; BFS uses a deque, DFS uses a stack/recursion |
| `02_clone_graph.py` | BFS/DFS + hashmap | `clone_map[old] = new`, build neighbours as you go |
| `03_graph_valid_tree.py` | Union-Find OR DFS | n−1 edges + one component + no cycle ⇒ tree |
| `04_find_town_judge.py` | In-degree − out-degree | A single counter, no graph needed |
| `05_find_center_star_graph.py` | Set intersection | Centre must appear in first two edges |
| `06_lucky_numbers_matrix.py` | Pre-compute row/col mins+maxes | Don't iterate cleverly, just scan |
| `07_walls_and_gates.py` | **Multi-source BFS** | Seed the queue with ALL sources, expand layer by layer |
| `08_shortest_path_binary_matrix.py` | BFS in 8 dirs | Same as ordinary BFS, just expand neighbours differently |
| `09_network_delay_time.py` | **Dijkstra** | Min-heap keyed on (distance, node); stale entries are skipped |
| `10_reconstruct_itinerary.py` | **Hierholzer reverse DFS** | Consume smallest neighbour last; append on unwind |

---

## 3. The 5 universal templates

### 3.1 BFS (unweighted shortest path)

```python
from collections import deque
def bfs(graph, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in graph[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist
```

### 3.2 DFS (connectedness, cycle detection, "visit all reachable")

```python
def dfs(graph, start):
    visited = set()
    def go(u, parent):
        visited.add(u)
        for v in graph[u]:
            if v not in visited:
                if not go(v, u): return False
        return True
    return go(start, -1)
```

### 3.3 Multi-source BFS (rotting oranges, walls-and-gates)

```python
q = deque([s for s in all_sources])   # seed with every source
while q:
    u = q.popleft()
    for v in neighbours(u):
        if not visited(v):
            visited(v); q.append(v)
```

### 3.4 Dijkstra (weighted, non-negative)

```python
dist[start] = 0; heap = [(0, start)]
while heap:
    d, u = heappop(heap)
    if d > dist[u]: continue          # stale entry
    for v, w in graph[u]:
        if d + w < dist[v]:
            dist[v] = d + w; heappush(heap, (dist[v], v))
```

### 3.5 Union-Find (components, "are X and Y connected?")

```python
parent = list(range(n)); rank = [0]*n
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]   # path compression
        x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb: return False           # already same set
    if rank[ra] < rank[rb]: ra, rb = rb, ra
    parent[rb] = ra
    if rank[ra] == rank[rb]: rank[ra] += 1
    return True
```

### 3.6 Hierholzer (Eulerian path, smallest-first variant)

```python
# Sort adjacency in REVERSE, pop smallest first, append on the way up.
def dfs(u):
    while graph[u]:
        dfs(graph[u].pop())
    route.append(u)
route = dfs(start)[::-1]
```

---

## 4. How to TALK through a graph problem (script)

1. **Classify (10 s).** "Unweighted, single source — that's BFS."
2. **State the state (10 s).** "I'll keep `dist[node]` and `visited`."
3. **Sketch (20 s).** "Queue starts with the source. Each pop expands neighbours and pushes them if unseen."
4. **Trace one example (60 s).** "From 0 I add 1, 2, 3 with distance 1. Popping 1 adds 4 with distance 2. …"
5. **Edge cases (10 s).** "What if start equals end? What if the grid is 1×1?"
6. **Complexity (10 s).** "Time O(V + E), space O(V) for the queue and distance map."

---

## 5. Traps (where candidates lose points)

| Trap | Symptom | Fix |
|------|---------|-----|
| Forgetting visited-mark on grids | Infinite loop / TLE | Mark when you ENQUEUE, not when you pop |
| Using BFS where Dijkstra is needed | Wrong answer on weighted graphs | Reach for the heap as soon as weights differ |
| Using Dijkstra where Bellman-Ford is needed | Wrong on negative edges | Ask about negative weights *before* coding |
| Building the adjacency list for star/degree problems | Wasted O(N+E) | Use a counter, not a graph |
| Sorting forward in Hierholzer | Wrong lex order | Sort **reverse**, pop smallest |
| Recursive DFS on a 10⁵-node graph | RecursionError | Iterative stack, or `sys.setrecursionlimit` |
| Path-compression skipped | TLE on big inputs | Always halve the path in `find()` |
| Not enqueuing neighbours from MULTIPLE sources | Slower solution | Multi-source BFS uses ALL sources in the initial queue |

---

## 6. Recommended re-derivation order

```
01 BFS/DFS  →  02 Clone Graph        (add hash map of old→new)
            →  03 Valid Tree          (add edge count + cycle check)
            →  08 Shortest Path Grid  (add 8-dir moves)

Counter patterns:
04 Town Judge   →  05 Star Center     (in/out degree + intersection)
            →  06 Lucky Numbers      (pre-compute row/col)

Grid BFS:
07 Walls & Gates  →  (built-in Rotting Oranges bonus in same file)

Advanced:
09 Network Delay  →  Dijkstra only when you really need it
10 Reconstruct    →  Hierholzer reverse — last problem you memorise
```

---

## 7. Post-interview review log

For each missed problem, fill in this template — 5 problems and you'll have a system.

1. **Bucket** (Q1–Q8 above) — which one did I miss?
2. **State** — what bookkeeping should I have used?
3. **Smallest failing test** — what input broke me and why?

If you keep missing the same bucket, drill that template for a week.

---

## 8. One-page visual cheat sheet

```
            ┌───────────────────────────────────────────────┐
            │      Pick the algorithm in 4 questions         │
            │  unweighted → BFS   weighted → Dijkstra       │
            │  negative   → Bellman-Ford                     │
            │  use every  → Hierholzer                       │
            │  components → Union-Find                       │
            └───────────────────────────────────────────────┘
                          │
   ┌──────────────┬───────┴─────────┬──────────────┐
   ▼              ▼                 ▼              ▼
  BFS           DFS              Dijkstra      Union-Find
   │              │                 │              │
   │       ┌──────┴──────┐         heap          find/union
   │       │             │                       path-comp
   │   grid walk    cycle/tree                  + rank
   │
multi-source BFS (seed with ALL sources)
```

Memorise the buckets. The code follows.
