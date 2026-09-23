"""
VERTICAL ORDER TRAVERSAL OF A BINARY TREE — LeetCode 987
========================================================
For each node at (row, col), `col` decreases on left moves and increases
on right moves. Return all values grouped by column (left → right) and
within each column, top → bottom. Within a cell, smaller value first.

Pattern: BFS WITH COORDINATES + SORT BY (col, row, val).
The BFS gives the top-to-bottom order for free (level-by-level),
so we only sort when there are ties at the same (col, row) cell.
"""

from collections import deque, defaultdict
from typing import Optional, List


class Node:
    def __init__(self, val: int = 0,
                 left: "Optional[Node]" = None,
                 right: "Optional[Node]" = None):
        self.val = val
        self.left = left
        self.right = right


def vertical_traversal(root: Optional[Node]) -> List[List[int]]:
    if not root:
        return []
    # node -> (col, row, val); col is the bucket key
    nodes = []
    q = deque([(root, 0, 0)])
    while q:
        node, col, row = q.popleft()
        nodes.append((col, row, node.val))
        if node.left:  q.append((node.left,  col - 1, row + 1))
        if node.right: q.append((node.right, col + 1, row + 1))

    nodes.sort()                              # lex sort: col, row, val
    cols = defaultdict(list)
    for col, _, val in nodes:
        cols[col].append(val)
    return [cols[k] for k in sorted(cols)]


if __name__ == "__main__":
    n = Node(3, Node(9, Node(4), Node(0)),
                 Node(8, Node(1), Node(7, None, Node(2))))
    for col in vertical_traversal(n):
        print(col)
    # [4], [9], [3, 0, 1], [8], [7], [2]
