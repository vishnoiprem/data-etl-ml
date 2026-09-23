# Lowest Common Ancestor of a Binary Tree (Medium)

**LeetCode:** https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/

## Problem
Given a binary tree and two nodes `p` and `q`, find their **lowest common ancestor (LCA)** — the lowest node that has both `p` and `q` as descendants (a node can be a descendant of itself).

## How to Think
1. DFS from root. If the current node is `p` or `q`, return it ("I claim myself").
2. Recurse on left and right.
3. If both children return non-None, current node is the LCA — `p` and `q` split into different subtrees here.
4. If only one side returns non-None, that side contains the answer — propagate it upward.

## How to Remember
- **Pattern**: "If I'm `p` or `q`, claim myself. Else, merge my children's claims."
- Post-order DFS: collect answers from below, decide at current node.
- **Memory cue**: the LCA is the first node where `p` and `q` "split" into different subtrees.

## Algorithm
```
function LCA(node, p, q):
    if node is None or node is p or node is q:
        return node
    left  = LCA(node.left,  p, q)
    right = LCA(node.right, p, q)
    if left and right:
        return node   # split here
    return left or right  # propagate whichever found something
```

## Complexity
- **Time:** O(n).
- **Space:** O(h).

## Code (Python)
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def lowestCommonAncestor(self, root, p, q):
        if not root or root is p or root is q:
            return root
        left  = self.lowestCommonAncestor(root.left,  p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left and right:
            return root
        return left or right
```

## AI Use Cases
- **Hierarchical taxonomy resolution** — given two entities, find their broadest shared category.
- **File system path resolution** — closest common ancestor directory.
- **Knowledge-graph query optimization** — using hierarchies (e.g., RDFS subclass).
- **Transformer attention trees** — finding the parent token of two aligned tokens.
- **RAG with hierarchical document indices** — locating shared section between two retrieved chunks.
