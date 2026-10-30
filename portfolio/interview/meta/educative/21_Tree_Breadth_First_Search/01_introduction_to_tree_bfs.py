"""
INTRODUCTION TO TREE BFS — Educative
=====================================
Goal: establish the CORE BFS-on-a-tree template. The remaining 9 files
in this folder are tiny variations of it.

Why BFS for trees?
------------------
Trees (usually) don't have cycles, so DFS isn't required for correctness.
BFS gives you **level-by-level access** for free — that's worth more
than any line count. Any time the problem says "by level", "kth from
root", "minimum depth", "shortest path", BFS is your default.

The universal skeleton
----------------------
    1. queue starts with the root
    2. while queue is not empty:
           record current queue size  ← captures the level boundary
           for _ in range(level_size):  ← process one whole level
               node = queue.popleft()
               push children
That `level_size = len(queue)` line IS the idea. Everything else is
just measuring / grouping nodes.
"""

from collections import deque
from typing import Optional, List


class Node:
    def __init__(self, val: int = 0,
                 left: "Optional[Node]" = None,
                 right: "Optional[Node]" = None):
        self.val = val
        self.left = left
        self.right = right


# ---- THE template. Memorise this verbatim. ----
def level_order(root: Optional[Node]) -> List[List[int]]:
    if not root:
        return []
    result, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):             # ← THIS LINE is the trick
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result


# ---- "RECORD-AT-EVERY-VISIT" variant (no level grouping) ----
def bfs_order(root: Optional[Node]) -> List[int]:
    """Useful when the problem doesn't care about levels."""
    order, q = [], deque([root]) if root else deque()
    while q:
        node = q.popleft()
        order.append(node.val)
        if node.left:  q.append(node.left)
        if node.right: q.append(node.right)
    return order


if __name__ == "__main__":
    # Build:        1
    #             /   \
    #            2     3
    #           / \     \
    #          4   5     6
    n = Node(1, Node(2, Node(4), Node(5)), Node(3, None, Node(6)))
    print("Level order:", level_order(n))    # [[1],[2,3],[4,5,6]]
    print("Flat BFS   :", bfs_order(n))      # [1, 2, 3, 4, 5, 6]
