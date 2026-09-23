"""
LEVEL ORDER TRAVERSAL → AVERAGE OF LEVELS — LeetCode 637
=======================================================
Same level-by-level BFS as file 01, but instead of COLLECTING the
values we REDUCE them (here: average). The only change is the
operation inside the inner for-loop.

This is the canonical "level-bucket" pattern: anything you can do
with a list of numbers (sum, average, max, mode, …) is now a
one-line addition to the template.
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


def average_of_levels(root: Optional[Node]) -> List[float]:
    if not root:
        return []
    avgs, q = [], deque([root])
    while q:
        level_sum = 0
        level_size = len(q)
        for _ in range(level_size):
            node = q.popleft()
            level_sum += node.val
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        avgs.append(level_sum / level_size)
    return avgs


if __name__ == "__main__":
    n = Node(3, Node(9), Node(20, Node(15), Node(7)))
    print(average_of_levels(n))           # [3.0, 14.5, 11.0]
