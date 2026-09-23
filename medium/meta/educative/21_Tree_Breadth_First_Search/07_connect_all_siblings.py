"""
CONNECT ALL SIBLINGS OF A BINARY TREE — Educative
================================================
Given a binary tree, set every node's `next` to point to its
CONTINUATION in level order (using `next` as a "linked-list" pointer).
The last node of the entire BFS order points to None.

This is the LEVEL-LINKED BFS (file 05) but without the level
boundary reset — the `prev` pointer just chains across every node.
"""

from collections import deque
from typing import Optional


class Node:
    def __init__(self, val: int = 0,
                 left: "Optional[Node]" = None,
                 right: "Optional[Node]" = None,
                 next: "Optional[Node]" = None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next


def connect_siblings(root: Optional[Node]) -> Optional[Node]:
    if not root:
        return root
    q = deque([root])
    prev = None
    while q:
        node = q.popleft()
        if prev:                              # chain the list
            prev.next = node
        prev = node
        if node.left:  q.append(node.left)
        if node.right: q.append(node.right)
    # prev.next stays None → terminator, which is correct
    return root


if __name__ == "__main__":
    n = Node(1, Node(2, Node(4), Node(5)), Node(3, Node(6), Node(7)))
    connect_siblings(n)
    # Walk the new linked list and print values
    cur, seen = n, set()
    out = []
    while cur and id(cur) not in seen:
        seen.add(id(cur))
        out.append(cur.val)
        cur = cur.next
    print(out)                              # [1, 2, 3, 4, 5, 6, 7]
