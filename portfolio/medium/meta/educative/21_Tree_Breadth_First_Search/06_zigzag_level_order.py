"""
BINARY TREE ZIGZAG LEVEL ORDER TRAVERSAL — LeetCode 103
======================================================
Level-order traversal, but alternate directions: level 0 left→right,
level 1 right→left, level 2 left→right, ...

Two clean ways:
  (1) BFS, then reverse every other level's bucket.
  (2) BFS, prepend to the level list based on a direction flag.

Both are O(n). Method 2 spares the allocations of a reversed copy.
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


def zigzag_level_order(root: Optional[Node]) -> List[List[int]]:
    if not root:
        return []
    result, q, left_to_right = [], deque([root]), True
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            if left_to_right:
                level.append(node.val)
            else:
                level.insert(0, node.val)      # prepend → reverse within level
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
        left_to_right = not left_to_right
    return result


# --- Variant: build normally and reverse odd layers afterwards ---
def zigzag_via_reverse(root: Optional[Node]) -> List[List[int]]:
    if not root:
        return []
    result, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    for i in range(1, len(result), 2):
        result[i].reverse()
    return result


if __name__ == "__main__":
    n = Node(3, Node(9), Node(20, Node(15), Node(7)))
    print(zigzag_level_order(n))        # [[3], [20, 9], [15, 7]]
    print(zigzag_via_reverse(n))        # [[3], [20, 9], [15, 7]]
