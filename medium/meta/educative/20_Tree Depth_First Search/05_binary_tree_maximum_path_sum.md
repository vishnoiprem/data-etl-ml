# Binary Tree Maximum Path Sum (Hard)

**LeetCode:** https://leetcode.com/problems/binary-tree-maximum-path-sum/

## Problem
A path is a sequence of adjacent nodes (up, down, left, right) that doesn't revisit. Find the maximum sum of any such path. Path may start and end anywhere.

## How to Think
1. For each node, two distinct things matter:
   - **Best single-branch path going upward** (so the parent can extend it).
   - **Best path *through* this node** (which is a candidate for the global answer).
2. Branch-up gain = `node.val + max(0, best child branch-up gain)`. The `max(0, ...)` lets us drop a negative branch.
3. Through-node candidate = `node.val + max(0, left_gain) + max(0, right_gain)`. Update global max.
4. Return branch-up gain to the parent.

## How to Remember
- **Pattern**: "Gain = `node + max(0, best child gain)`. Global max = `node + left + right gains`."
- The `0` is the "I can drop this branch if it's negative" knob.
- **Memory cue**: each node is a summit — the best trail going up vs. the best trail that crosses it.

## Algorithm
```
best = -inf
function gain(node):
    if node is None:
        return 0
    left  = max(0, gain(node.left))
    right = max(0, gain(node.right))
    best = max(best, node.val + left + right)
    return node.val + max(left, right)

gain(root)
return best
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
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        self.best = -math.inf
        def gain(node):
            if not node:
                return 0
            left  = max(0, gain(node.left))
            right = max(0, gain(node.right))
            self.best = max(self.best, node.val + left + right)
            return node.val + max(left, right)
        gain(root)
        return self.best
```

## AI Use Cases
- **Best-segment scoring on parse trees** (analogous to Kadane's on trees).
- **Optimal routing** through hierarchical networks — best throughput path.
- **Reinforcement learning** — best cumulative-reward path through a decision tree.
- **Anomaly / novelty detection** — subtree with maximum deviation.
- **Gradient boosting tree analysis** — strongest cumulative leaf path for explainability.
