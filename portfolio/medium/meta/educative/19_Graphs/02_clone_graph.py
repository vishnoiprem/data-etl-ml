"""
CLONE GRAPH — LeetCode 133
=========================
Given a reference to a node in a CONNECTED undirected graph, return a
DEEP COPY of the entire graph.

Node definition (LeetCode):
    class Node:
        def __init__(self, val, neighbors=[]):
            self.val = val
            self.neighbors = neighbors

Why interviewers love it
------------------------
It's a 5-line problem once you see the trick, but the trick — "use a
hash map from OLD node → NEW node" — generalises to:
  • copying random-pointer lists,
  • DFS deep copy of any object graph,
  • any "rebuild-with-different-representation" task.

Two valid approaches: BFS (queue) or DFS (recursion). BFS is what we
ship because it sidesteps Python's recursion limit on big inputs.
"""

from collections import deque
from typing import Optional


class Node:
    def __init__(self, val: int = 0, neighbors: Optional[list] = None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def clone_graph(node: Optional[Node]) -> Optional[Node]:
    if not node:
        return None

    # KEY IDEA: clone_map[old] = new. The moment we visit an old node we
    # also create its clone, so cycles never deadlock us.
    clone_map = {node: Node(node.val)}
    q = deque([node])
    while q:
        old = q.popleft()
        for nei in old.neighbors:
            if nei not in clone_map:
                clone_map[nei] = Node(nei.val)
                q.append(nei)
            clone_map[old].neighbors.append(clone_map[nei])
    return clone_map[node]


# --- Recursive DFS variant (cleaner but hits recursion limit) ---
def clone_graph_dfs(node: Optional[Node]) -> Optional[Node]:
    if not node:
        return None
    visited = {}

    def dfs(old: Node) -> Node:
        if old in visited:
            return visited[old]
        new = Node(old.val)
        visited[old] = new
        new.neighbors = [dfs(n) for n in old.neighbors]
        return new

    return dfs(node)


if __name__ == "__main__":
    # Build a tiny graph:  1 - 2 - 3 - 1  (triangle)
    n1, n2, n3 = Node(1), Node(2), Node(3)
    n1.neighbors = [n2, n3]
    n2.neighbors = [n1, n3]
    n3.neighbors = [n1, n2]

    cloned = clone_graph(n1)
    print("Clone root val:", cloned.val)                       # 1
    print("Clone neighbor vals:", [n.val for n in cloned.neighbors])  # [2, 3]
    print("Is a deep copy? ", cloned is not n1
          and cloned.neighbors[0] is not n2)                  # True
