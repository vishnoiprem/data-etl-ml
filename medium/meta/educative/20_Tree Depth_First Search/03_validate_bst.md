# Validate Binary Search Tree (Medium)

**LeetCode:** https://leetcode.com/problems/validate-binary-search-tree/

## Problem
Determine if a binary tree is a valid BST. The left subtree of a node contains only nodes with values **strictly less** than the node's value; the right subtree only nodes **strictly greater**. Both subtrees must also be BSTs.

## How to Think
1. **Naive trap**: only comparing a node with its direct children is wrong — descendants must also obey the constraint.
2. Pass a `(min, max)` valid range down the recursion. Each node must lie strictly inside its range.
3. **Alternative**: an inorder traversal of a valid BST must be strictly increasing.

## How to Remember
- **Pattern**: "Carry down a valid range; narrow it at each step."
- Initial range is `(-∞, +∞)`. At a node with value `v`: left gets `(-∞, v)`, right gets `(v, +∞)`.
- **Memory cue**: a BST is a sorted kingdom — every subtree has its own borders, enforced strictly.

## Algorithm
```
function isValid(node, lo, hi):
    if node is None:
        return True
    if not (lo < node.val < hi):
        return False
    return isValid(node.left, lo, node.val) and
           isValid(node.right, node.val, hi)

isValid(root, -inf, +inf)
```

## Complexity
- **Time:** O(n).
- **Space:** O(h).

## Code (Python)
```python
from typing import Optional
import math

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        def helper(node, lo, hi):
            if not node:
                return True
            if not (lo < node.val < hi):
                return False
            return helper(node.left, lo, node.val) and helper(node.right, node.val, hi)
        return helper(root, -math.inf, math.inf)
```

## AI Use Cases
- **Spatial indexing** (k-d trees, range trees) — same range-validation idea.
- **Decision-tree integrity checks** in ML pipelines before inference.
- **Database index validation** — verifying sorted invariants.
- **Order-statistic trees** used in learned-index systems (SageDB, ALEX).
- **Hierarchical clustering** validation — enforces distance ordering between siblings.
