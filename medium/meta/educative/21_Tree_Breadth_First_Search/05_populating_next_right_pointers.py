"""
POPULATING NEXT RIGHT POINTERS — LeetCode 116
=============================================
Given a PERFECT binary tree where each node has a `next` pointer,
set every `next` to point to its right sibling at the same level.
The last node of each level's `next` should be None.

Why this problem matters
------------------------
It teaches the **LEVEL-LINKED BFS** trick: once you've processed a
level and you still have the next level in the queue, you can wire up
the next pointers by linking each consecutive pair (and carrying over
a `prev` variable). The O(1) extra-space solution is the famous one —
you can re-use the `next` pointers of the previous level as the queue.
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


def connect(root: Optional[Node]) -> Optional[Node]:
    if not root:
        return root
    q = deque([root])
    while q:
        prev = None
        for _ in range(len(q)):
            node = q.popleft()
            if prev:                          # wire prev → this
                prev.next = node
            prev = node
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        # prev's next is already None by default — that's the last node's next
    return root


# ---- O(1) EXTRA SPACE: use the previous level's next pointers as our queue ----
def connect_constant_space(root: Optional[Node]) -> Optional[Node]:
    if not root:
        return root
    leftmost = root
    while leftmost.left:                       # while there's a next level
        head = leftmost                        # start of THIS level
        while head:
            head.left.next = head.right        # wire the two children
            if head.next:
                head.right.next = head.next.left   # cross-level bridge
            head = head.next                   # next sibling on same level
        leftmost = leftmost.left               # descend one level
    return root


if __name__ == "__main__":
    n = Node(1, Node(2, Node(4), Node(5)), Node(3, Node(6), Node(7)))
    connect(n)
    print("Level 1 next:", n.next)             # None
    print("Level 2:    ", n.left.next.val, n.right.next)  # 3, None
    print("Level 3:    ",
          n.left.left.next.val,
          n.left.right.next.val,
          n.right.left.next.val,
          n.right.right.next)                 # 5, 6, 7, None
