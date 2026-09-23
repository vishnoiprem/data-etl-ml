"""
INTRODUCTION TO GRAPHS — Educative
=================================
Goal of this file: establish the vocabulary and the 3 representations
you'll reach for in every other file in this folder.

A graph G = (V, E) is just a set of vertices and a set of edges.
That's all. Everything else — BFS, DFS, Dijkstra, union-find — is
just a strategy for walking this structure while maintaining some
extra information (visited, distance, parent, rank).

Representations
--------------
1. Adjacency list   — graph[node] = [neighbors].   Default choice.
2. Adjacency matrix — graph[i][j] = 1 / weight.     Use for dense graphs.
3. Edge list        — list of (u, v[, w]) tuples.  Use for Kruskal/union-find.

For interviews you write `graph = defaultdict(list)` and move on.
"""

from collections import defaultdict, deque
from typing import List, Dict


# ---------- Build the three representations ----------
def build_adj_list(n: int, edges: List[List[int]]) -> Dict[int, List[int]]:
    g = defaultdict(list)
    for u, v in edges:
        g[u].append(v)
        g[v].append(u)               # comment out for directed graphs
    return g


def build_adj_matrix(n: int, edges: List[List[int]]) -> List[List[int]]:
    m = [[0] * n for _ in range(n)]
    for u, v in edges:
        m[u][v] = 1
        m[v][u] = 1
    return m


def build_edge_list(edges: List[List[int]]) -> List[tuple]:
    return [(u, v) for u, v in edges]


# ---------- BFS — shortest path in UNWEIGHTED graph ----------
def bfs(graph: Dict[int, List[int]], start: int) -> List[int]:
    """Return BFS order from `start`. O(V + E) time, O(V) space."""
    order, visited = [], {start}
    q = deque([start])
    while q:
        u = q.popleft()
        order.append(u)
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                q.append(v)
    return order


# ---------- DFS — explore-as-deep-as-possible ----------
def dfs(graph: Dict[int, List[int]], start: int) -> List[int]:
    """Iterative DFS using an explicit stack (no recursion-limit worries)."""
    order, visited = [], {start}
    stack = [start]
    while stack:
        u = stack.pop()
        order.append(u)
        # Reverse so traversal order matches the recursive version
        for v in reversed(graph[u]):
            if v not in visited:
                visited.add(v)
                stack.append(v)
    return order


if __name__ == "__main__":
    edges = [[0, 1], [0, 2], [1, 3], [2, 3]]
    g = build_adj_list(4, edges)
    print("Adj list :", dict(g))
    print("BFS from 0:", bfs(g, 0))   # [0, 1, 2, 3]
    print("DFS from 0:", dfs(g, 0))   # [0, 1, 3, 2]
