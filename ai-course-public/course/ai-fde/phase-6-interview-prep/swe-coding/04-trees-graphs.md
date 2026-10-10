# SWE Coding Sub-Lesson 4 — Trees & Graphs (DFS, BFS, topological sort, Dijkstra)

> **Trees and graphs are the fourth most common SWE coding pattern.** 10-15% of LeetCode medium-hard problems are tree/graph problems. The FDE signal: a candidate who can implement DFS/BFS recursively and iteratively, knows when to use a stack vs a queue, and can detect cycles — is showing they can debug graph-handling code in production. **This sub-lesson covers 4 sub-patterns: DFS, BFS, topological sort, Dijkstra.**

---

## Why trees + graphs are the FDE signal

The 3 things the interviewer is testing:

1. **Can you recognize the pattern?** Trees are graphs with no cycles. BFS for shortest path in unweighted graph; DFS for cycle detection; topological sort for dependencies; Dijkstra for shortest path in weighted graph.
2. **Can you write recursive + iterative code?** DFS is natural recursively; BFS is natural iteratively. The candidate who can write both is showing depth.
3. **Can you detect cycles?** Cycle detection is the most common graph bug. The candidate who uses 3 colors (white/gray/black) for DFS is showing they know the standard algorithm.

**The FDE pattern:** clarify → brute force → optimize → code → test. Same as arrays, but the data structure is a graph.

---

## Sub-pattern 1: DFS (Depth-First Search)

**The pattern:** traverse the graph depth-first, using a stack (iterative) or recursion (recursive). O(V + E) time, O(V) space.

**When to use:** cycle detection, connected components, path finding, tree traversals (pre/in/post-order).

**The template (recursive):**

```python
def dfs_recursive(node, visited):
    if node in visited:
        return
    visited.add(node)
    for neighbor in node.neighbors:
        dfs_recursive(neighbor, visited)
```

**The template (iterative):**

```python
def dfs_iterative(start):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in node.neighbors:
            if neighbor not in visited:
                stack.append(neighbor)
```

**Sample problem 1: Number of Islands**

> Given a 2D grid of '1's (land) and '0's (water), count the number of islands.

```python
def num_islands(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    visited = set()
    count = 0

    def dfs(r, c):
        if (r, c) in visited:
            return
        visited.add((r, c))
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '1':
                dfs(nr, nc)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1' and (r, c) not in visited:
                count += 1
                dfs(r, c)
    return count
```

**Time:** O(rows × cols). **Space:** O(rows × cols).

**Sample problem 2: Maximum Depth of Binary Tree**

> Given a binary tree, find its maximum depth.

```python
def max_depth(root) -> int:
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

**Time:** O(n). **Space:** O(h) where h is the height of the tree.

**The 3 edge cases:** empty tree, single node, skewed tree (linked list).

---

## Sub-pattern 2: BFS (Breadth-First Search)

**The pattern:** traverse the graph level-by-level, using a queue. O(V + E) time, O(V) space.

**When to use:** shortest path in unweighted graph, level-order tree traversal, connected components.

**The template:**

```python
from collections import deque

def bfs(start):
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in node.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

**Sample problem 1: Binary Tree Level Order Traversal**

> Given a binary tree, return the level-order traversal of its nodes' values.

```python
def level_order(root) -> list[list[int]]:
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Shortest Path in a Grid (with obstacles)**

> Given a 2D grid, find the shortest path from (0,0) to (m-1, n-1). 0 = empty, 1 = obstacle.

```python
def shortest_path(grid: list[list[int]]) -> int:
    if not grid or grid[0][0] == 1:
        return -1
    rows, cols = len(grid), len(grid[0])
    queue = deque([(0, 0, 1)])  # (row, col, distance)
    visited = {(0, 0)}
    while queue:
        r, c, dist = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return dist
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0 and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, dist + 1))
    return -1
```

**Time:** O(rows × cols). **Space:** O(rows × cols).

**The 3 edge cases:** empty grid, blocked start, unreachable end.

---

## Sub-pattern 3: Topological Sort

**The pattern:** order vertices such that for every directed edge (u, v), u comes before v. O(V + E) time, O(V) space.

**When to use:** task scheduling, build order, course prerequisites, dependency resolution.

**The template (Kahn's algorithm):**

```python
from collections import deque, defaultdict

def topological_sort(graph: dict[int, list[int]]) -> list[int]:
    """graph: {node -> [neighbors]}. Returns topological order or [] if cycle."""
    in_degree = defaultdict(int)
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    queue = deque([node for node in graph if in_degree[node] == 0])
    result = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result if len(result) == len(graph) else []  # Empty if cycle
```

**Sample problem 1: Course Schedule**

> Given `numCourses` and a list of prerequisites, return true if you can finish all courses.

```python
def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    graph = defaultdict(list)
    for course, prereq in prerequisites:
        graph[prereq].append(course)

    in_degree = [0] * num_courses
    for course, prereq in prerequisites:
        in_degree[course] += 1

    queue = deque([c for c in range(num_courses) if in_degree[c] == 0])
    completed = 0
    while queue:
        course = queue.popleft()
        completed += 1
        for next_course in graph[course]:
            in_degree[next_course] -= 1
            if in_degree[next_course] == 0:
                queue.append(next_course)

    return completed == num_courses
```

**Time:** O(V + E). **Space:** O(V + E).

**The 3 edge cases:** no courses, no prerequisites, cycle (impossible to finish).

---

## Sub-pattern 4: Dijkstra's Algorithm

**The pattern:** shortest path in a weighted graph with non-negative weights. O((V + E) log V) time with a min-heap, O(V) space.

**When to use:** shortest path with weights (e.g., network routing, Google Maps).

**The template:**

```python
import heapq

def dijkstra(graph: dict[int, list[tuple[int, int]]], start: int) -> dict[int, int]:
    """graph: {node -> [(neighbor, weight)]}. Returns {node -> shortest distance}."""
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]  # (distance, node)
    while pq:
        dist, node = heapq.heappop(pq)
        if dist > distances[node]:
            continue
        for neighbor, weight in graph[node]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return distances
```

**Sample problem 1: Network Delay Time**

> Given a network of `n` nodes and edges with travel times, find the time for all nodes to receive a signal from node `k`.

```python
def network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))

    distances = dijkstra(graph, k)
    max_dist = max(distances[i] for i in range(1, n + 1))
    return max_dist if max_dist < float('inf') else -1
```

**Time:** O((V + E) log V). **Space:** O(V + E).

**The 3 edge cases:** unreachable nodes, single node, disconnected graph.

---

## Cycle detection (the most common graph bug)

The 3-color DFS for cycle detection in a directed graph:

```python
def has_cycle(graph: dict[int, list[int]]) -> bool:
    """graph: {node -> [neighbors]}. Returns True if cycle exists."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node):
        color[node] = GRAY
        for neighbor in graph[node]:
            if color[neighbor] == GRAY:  # Back edge = cycle
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(dfs(node) for node in graph if color[node] == WHITE)
```

**Time:** O(V + E). **Space:** O(V).

---

## The 5 anti-patterns for trees + graphs

1. **Jumping to code without a plan.** "I'll just start coding" is a junior answer. The plan is the signal.
2. **Skipping the edge cases.** Empty graph, single node, disconnected components. The edge cases are the signal.
3. **Using the wrong traversal.** DFS vs BFS. The candidate who picks the wrong one is signaling they don't know the trade-offs.
4. **Not detecting cycles.** Cycle detection is the most common graph bug. The candidate who mentions it is showing depth.
5. **Not naming the complexity.** "O(V + E) time, O(V) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for trees + graphs

1. **Clarify the problem first.** "Is the graph directed or undirected? Are there cycles? Are the weights non-negative?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(V²). Can I do better with BFS?" The brute force is the floor.
3. **State the optimized solution.** "I can use BFS for O(V + E)." The optimization is the signal.
4. **Walk through the code out loud.** "I start at node 0. I add it to the queue. I process it..." The walkthrough is the signal.
5. **Test with edge cases.** "If the graph is empty, I return 0. If the graph has a cycle, I return -1." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(V + E) time, O(V) space. BFS visits each node and edge once." |
| 2. "How would you test this?" | "3 cases: empty graph, single node, disconnected components. The edge cases are the canary." |
| 3. "How would you scale this to 1B nodes?" | "External sort + map-reduce. Or a distributed graph processing framework (e.g., Pregel, GraphX). The trade-off is accuracy vs memory." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../system-design/README.md` | The 9 patterns (graphs underpin Pattern 7: real-time collaborative systems) |
| `../swe-coding/01-arrays.md` | The 2 pointers / sliding window / prefix sum patterns |

---

## The thesis

**Trees and graphs are the fourth most common SWE coding pattern.** The candidate who can implement DFS/BFS recursively and iteratively, knows when to use a stack vs a queue, and can detect cycles — is showing they can debug graph-handling code in production.

**The 4 sub-patterns (DFS, BFS, topological sort, Dijkstra) cover 80% of tree/graph problems.** The 2 sample problems per sub-pattern (8 total) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**