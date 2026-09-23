"""
MINIMUM DEPTH OF BINARY TREE — LeetCode 111
==========================================
Given a binary tree, return the smallest number of EDGES from the root
to a LEAF (i.e. a node with no children).

Why DFS is wrong here (subtly)
------------------------------
A DFS would compute `1 + min(left_depth, right_depth)`, but for a node
with only one child that minimum would be 0 → wrong answer (it returns
a path that DOESN'T reach a leaf). BFS naturally avoids this because
we STOP the moment we encounter a leaf — the first leaf we pop is, by
level-order, the closest one to the root.

This is the **EARLY-EXIT BFS** pattern: return the moment your
goal-test is true, because BFS guarantees minimum distance.
"""

from collections import deque
from typing import Optional


class Node:
    def __init__(self, val: int = 0,
                 left: "Optional[Node]" = None,
                 right: "Optional[Node]" = None):
        self.val = val
        self.left = left
        self.right = right


def min_depth(root: Optional[Node]) -> int:
    if not root:
        return 0
    q = deque([(root, 1)])
    while q:
        node, depth = q.popleft()
        if not node.left and not node.right:     # first leaf wins
            return depth
        if node.left:  q.append((node.left,  depth + 1))
        if node.right: q.append((node.right, depth + 1))
    return 0                                    # should never reach here


if __name__ == "__main__":
    n = Node(3, Node(9), Node(20, Node(15), Node(7)))
    print(min_depth(n))                # 2  (3 → 9)
