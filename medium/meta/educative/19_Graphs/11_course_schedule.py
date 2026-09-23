"""
COURSE SCHEDULE — LeetCode 207
==============================
There are `numCourses` courses labelled 0..numCourses-1. You are given
an array `prerequisites[i] = [a, b]` meaning you MUST take course `b`
BEFORE course `a`. Is it possible to finish ALL courses?

This is the CYCLE DETECTION problem on a DIRECTED graph.
Specifically: "given a directed graph, does it contain a cycle?"

WHY this problem matters
-----------------------
The Valid Tree problem (file 03) asks the same thing on an UNDIRECTED
graph — there, any revisited node = cycle. On a DIRECTED graph we must
use THREE colours instead of a single visited set, because we are
allowed to revisit a node via a DIFFERENT path without creating a cycle.

    WHITE  : unvisited
    GRAY   : in the current DFS stack (visiting)
    BLACK  : finished (safe to revisit)

If we ever encounter a GRAY node during DFS, we've found a back-edge
→ cycle → impossible.

Pattern: any time the input is an explicit "X must come before Y"
relation list, the question is almost always "is this a DAG?" (directed
acyclic graph). If yes → topological order exists → all courses doable.
"""

from typing import List
from collections import defaultdict


def can_finish(numCourses: int, prerequisites: List[List[int]]) -> bool:
    # Build adjacency list. Edge b → a means "b is a prereq of a".
    graph = defaultdict(list)
    for a, b in prerequisites:
        graph[b].append(a)

    # 0 = unvisited, 1 = in stack, 2 = finished
    state = [0] * numCourses

    def dfs(u: int) -> bool:
        if state[u] == 1:                # back-edge → cycle
            return False
        if state[u] == 2:                # already cleared, no cycle here
            return True
        state[u] = 1                     # mark "in stack"
        for v in graph[u]:
            if not dfs(v):
                return False
        state[u] = 2                     # mark "finished"
        return True

    for c in range(numCourses):
        if not dfs(c):
            return False
    return True


# ---- Iterative variant — avoids Python recursion limit on big inputs ----
def can_finish_iter(numCourses: int, prerequisites: List[List[int]]) -> bool:
    graph = defaultdict(list)
    for a, b in prerequisites:
        graph[b].append(a)
    state = [0] * numCourses

    # Simulate DFS with an explicit stack. Each frame remembers its
    # next child index to expand.
    for start in range(numCourses):
        if state[start] != 0:
            continue
        stack = [[start, 0]]             # [node, next_child_index]
        state[start] = 1
        while stack:
            u, i = stack[-1]
            if i == len(graph[u]):
                state[u] = 2             # finished
                stack.pop()
                continue
            stack[-1][1] = i + 1         # advance iterator
            v = graph[u][i]
            if state[v] == 1:
                return False             # cycle
            if state[v] == 0:
                state[v] = 1
                stack.append([v, 0])
    return True


if __name__ == "__main__":
    print(can_finish(2, [[1, 0]]))                # True
    print(can_finish(2, [[1, 0], [0, 1]]))        # False
    print(can_finish_iter(2, [[1, 0], [0, 1]]))   # False
