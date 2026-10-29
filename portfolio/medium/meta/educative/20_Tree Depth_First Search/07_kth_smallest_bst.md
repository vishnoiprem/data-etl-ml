# Kth Smallest Element in a BST (Medium)

**LeetCode:** https://leetcode.com/problems/kth-smallest-element-in-a-bst/

## Problem
Given the `root` of a BST and an integer `k`, return the `k`-th smallest value (1-indexed) among all the nodes.

## How to Think
1. Inorder traversal of a BST yields nodes in **ascending order**.
2. Walk inorder with a counter; stop when it reaches `k`.
3. For repeated queries, augment each node with the size of its left subtree — then descend directly to the `k`-th element in O(h).

## How to Remember
- **Pattern**: "BST + inorder = sorted list. Just count."
- If you remember "inorder BST = sorted", you remember this.
- **Memory cue**: BST inorder is the same as reading a phone book in alphabetical order.

## Algorithm
```
k_remaining = k
answer = None

function inorder(node):
    if node is None or answer is not None:
        return
    inorder(node.left)
    k_remaining -= 1
    if k_remaining == 0:
        answer = node.val
        return
    inorder(node.right)
```

## Complexity
- **Time:** O(h + k) in the worst case (we may need to traverse down to the `k`-th node). For balanced BST, O(log n + k).
- **Space:** O(h) recursion stack.

## Code (Python)
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        self.k = k
        self.ans = None
        def inorder(node):
            if not node or self.ans is not None:
                return
            inorder(node.left)
            self.k -= 1
            if self.k == 0:
                self.ans = node.val
                return
            inorder(node.right)
        inorder(root)
        return self.ans
```

## AI Use Cases
- **Order-statistic queries** in learned-index systems (Akamai, SageDB, ALEX).
- **Ranked retrieval in retrieval-augmented generation (RAG)** — finding the k-th most similar document.
- **Quantile computation** on streaming trees (online top-k).
- **Top-k nearest-neighbor selection** in k-d trees.
- **Approximate median / percentile** estimators in distributed ML.
