# Invert Binary Tree (Easy)

**LeetCode:** https://leetcode.com/problems/invert-binary-tree/

> Famously asked by a Google interviewer who reportedly said "99% of candidates will not get this." Many didn't — even Max Howell, author of Homebrew.

## Problem
Given the `root` of a binary tree, invert the tree (mirror it) and return its root.

## How to Think
1. To invert a tree, swap each node's left and right children.
2. Recurse on both subtrees after the swap.
3. Classic "swap + recurse" DFS template.

## How to Remember
- **Pattern**: "At every node, `swap(children)`, then `recurse(left)`, then `recurse(right)`."
- Order of swap vs. recursion doesn't matter — same result.
- **Memory cue**: imagine flipping a photo horizontally — every branch mirrors across the central axis.

## Algorithm
```
function invert(node):
    if node is None:
        return None
    node.left, node.right = node.right, node.left
    invert(node.left)
    invert(node.right)
    return node
```

## Complexity
- **Time:** O(n) — every node visited once.
- **Space:** O(h) — recursion stack.

## Code (Python)
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if not root:
            return None
        root.left, root.right = root.right, root.left
        self.invertTree(root.left)
        self.invertTree(root.right)
        return root
```

## AI Use Cases
- **Mirror augmentation** in self-supervised vision training (horizontal flips).
- **Symmetric data generation** — reverse a sample's structure to enlarge the dataset.
- **Tree-based model ensembling** where left/right subtrees are swapped as a form of randomization.
- **Recursive reflection** in autoencoders operating on tree-encoded inputs.
- **Equivariant neural networks** that must handle reflections as part of the symmetry group.
