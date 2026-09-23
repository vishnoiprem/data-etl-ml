"""
SYMMETRIC TREE — LeetCode 101
=============================
Check whether a binary tree is a mirror of itself around its centre.

Two valid approaches:
  • DFS pair recursion: `is_mirror(L.left, R.right) and is_mirror(L.right, R.left)`
  • BFS level by level: each level must be a palindrome

We show BFS because this is the BFS folder. The DFS version is shorter
to write but harder to debug — if you remember only one, remember the
pair-recursion form.
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


def is_symmetric(root: Optional[Node]) -> bool:
    if not root:
        return True
    q = deque([(root.left, root.right)])
    while q:
        l, r = q.popleft()
        if not l and not r:
            continue                            # both None → ok
        if not l or not r or l.val != r.val:
            return False                        # mismatch
        # Compare OUTER pair, then INNER pair
        q.append((l.left, r.right))
        q.append((l.right, r.left))
    return True


# --- DFS pair-recursion variant (worth knowing) ---
def is_symmetric_dfs(root: Optional[Node]) -> bool:
    def mirror(a: Optional[Node], b: Optional[Node]) -> bool:
        if not a and not b: return True
        if not a or not b or a.val != b.val: return False
        return mirror(a.left, b.right) and mirror(a.right, b.left)
    return mirror(root.left, root.right)


if __name__ == "__main__":
    t = Node(1, Node(2, Node(3), Node(4)), Node(2, Node(4), Node(3)))
    print(is_symmetric(t))                  # True
    print(is_symmetric_dfs(t))              # True
