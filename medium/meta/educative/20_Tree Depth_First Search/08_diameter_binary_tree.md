# Diameter of Binary Tree (Easy)

**LeetCode:** https://leetcode.com/problems/diameter-of-binary-tree/

## Problem
Return the length of the **diameter** of the binary tree — the longest path between any two nodes (measured in edges). The path may or may not pass through the root.

## How to Think
1. The diameter **through** any node is `left_height + right_height`.
2. Post-order DFS: each node returns its **height** (longest path from itself downward) to its parent.
3. While computing height, **also update the global max** of `left + right`.

## How to Remember
- **Pattern**: "Height is local; diameter is global — combine them."
- Recursion returns height upward; the diameter candidate `left_height + right_height` is computed at each node.
- **Memory cue**: a node is the **bridge** — its two longest arms form the candidate path.

## Algorithm
```
best = 0

function height(node):
    if node is None:
        return 0
    l = height(node.left)
    r = height(node.right)
    best = max(best, l + r)
    return 1 + max(l, r)
```

## Complexity
- **Time:** O(n).
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
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        self.best = 0
        def height(node):
            if not node:
                return 0
            l = height(node.left)
            r = height(node.right)
            self.best = max(self.best, l + r)
            return 1 + max(l, r)
        height(root)
        return self.best
```

## AI Use Cases
- **Network diameter** in graph-based ML — measures influence spread.
- **Communication latency** estimation in distributed neural net training.
- **Tree-structured model interpretability** — longest decision path length.
- **Phylogenetic tree spread** estimation.
- **Maximum dependency distance** in hierarchical reinforcement learning.
