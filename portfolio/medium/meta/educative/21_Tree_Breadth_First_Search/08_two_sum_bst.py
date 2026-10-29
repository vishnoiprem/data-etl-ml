"""
TWO SUM IV — INPUT IS A BST — LeetCode 653
==========================================
Given a BST and a target, return True if there exist two distinct
nodes whose values sum to the target.

Two clean approaches:
  • BFS + hash set: walk the tree, for each value check if `target-v`
    has been seen.  Time O(n), space O(n).
  • In-order DFS + two pointers on the sorted array.  Time O(n), space O(n).

We use BFS because this folder is BFS, but in real interviews mention
the in-order trick — it leverages the BST property instead of brute-forcing.
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


def two_sum_bst(root: Optional[Node], target: int) -> bool:
    seen = set()
    q = deque([root]) if root else deque()
    while q:
        node = q.popleft()
        if target - node.val in seen:
            return True
        seen.add(node.val)
        if node.left:  q.append(node.left)
        if node.right: q.append(node.right)
    return False


# --- BST-optimised variant (in-order + two pointers) ---
def two_sum_bst_inorder(root: Optional[Node], target: int) -> bool:
    def inorder(n):
        return inorder(n.left) + [n.val] + inorder(n.right) if n else []

    arr = inorder(root)
    i, j = 0, len(arr) - 1
    while i < j:
        s = arr[i] + arr[j]
        if s == target: return True
        if s < target: i += 1
        else:          j -= 1
    return False


if __name__ == "__main__":
    n = Node(5, Node(3, Node(2), Node(4)), Node(6, None, Node(7)))
    print(two_sum_bst(n, 9))                  # True  (2+7)
    print(two_sum_bst_inorder(n, 9))          # True
    print(two_sum_bst(n, 28))                 # False
