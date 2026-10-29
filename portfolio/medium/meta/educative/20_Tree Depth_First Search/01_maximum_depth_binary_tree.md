# Maximum Depth of Binary Tree (Easy)

**LeetCode:** https://leetcode.com/problems/maximum-depth-of-binary-tree/

## Problem
Given the `root` of a binary tree, return its maximum depth.
A binary tree's maximum depth is the number of nodes along the longest path from the root down to the farthest leaf node.

## How to Think
1. The depth of a tree equals `1 + max(depth(left), depth(right))`.
2. Base case: an empty node has depth `0`.
3. DFS lets us explore left and right subtrees independently, then combine the answers at each node.

## How to Remember
- **Pattern**: "Return `1 + max` of children's answers."
- Recursion goes all the way down (post-order), then bubbles the depth back up.
- **Memory cue**: recursion is a Russian doll — open the smallest one, ask it its depth, then add 1 for each outer shell.

## Algorithm (DFS Post-Order)
```
function maxDepth(node):
    if node is None:
        return 0
    return 1 + max(maxDepth(node.left), maxDepth(node.right))
```

## Complexity
- **Time:** O(n) — visits every node once.
- **Space:** O(h) — recursion stack, where `h` is tree height (O(n) worst case for skewed, O(log n) for balanced).

## Code (Python)
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        if not root:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
```

## AI Use Cases
- **Decision tree depth estimation** in random forests and XGBoost — used for capacity control.
- **Parse-tree depth in NLP** — measures syntactic complexity of a sentence.
- **Recursive feature depth** in hierarchical / hierarchical-rl models.
- **AST analysis in code generation LLMs** — guards against runaway recursion depth.
- **Beam search** in tree-decoding models — limits how deep decoding can go.
