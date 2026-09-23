"""
GRAPH VALID TREE — LeetCode 261
==============================
Given n nodes labelled 0..n-1 and an edge list, decide whether these
edges form a VALID TREE.

A graph is a tree iff ALL of these are true:
    (a) it has exactly n - 1 edges,
    (b) it is fully connected (every node reachable from 0),
    (c) it has no cycles.
Equivalent one-liner of (b) + (c): the number of connected components
is exactly 1 after union-find merges.

Two valid approaches — know BOTH, interviewers ask follow-ups:
    1. Union-Find: union every edge, count roots at the end.
    2. DFS:        if during DFS we see an already-visited node that
                   isn't our parent → cycle.
"""

from typing import List


# ---------- Approach 1: Union-Find (the safer interview default) ----------
def valid_tree_uf(n: int, edges: List[List[int]]) -> bool:
    if len(edges) != n - 1:           # tree must have exactly n-1 edges
        return False

    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]   # path compression
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:                  # cycle detected
            return False
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return True

    for u, v in edges:
        if not union(u, v):
            return False
    return True


# ---------- Approach 2: DFS cycle + reachability check ----------
def valid_tree_dfs(n: int, edges: List[List[int]]) -> bool:
    if len(edges) != n - 1:
        return False
    from collections import defaultdict
    g = defaultdict(list)
    for u, v in edges:
        g[u].append(v)
        g[v].append(u)

    visited = set()

    def dfs(u: int, parent: int) -> bool:
        if u in visited:
            return False              # cycle (returned to a visited node)
        visited.add(u)
        for v in g[u]:
            if v == parent:           # don't count the edge we came from
                continue
            if not dfs(v, u):
                return False
        return True

    return dfs(0, -1) and len(visited) == n


if __name__ == "__main__":
    print(valid_tree_uf(5, [[0,1],[0,2],[0,3],[1,4]]))   # True
    print(valid_tree_uf(5, [[0,1],[1,2],[2,3],[1,3],[1,4]]))  # False
    print(valid_tree_dfs(5, [[0,1],[0,2],[0,3],[1,4]])) # True
