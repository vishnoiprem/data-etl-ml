"""
Problem: Binary Tree Maximum Path Sum (Hard)
LeetCode: https://leetcode.com/problems/binary-tree-maximum-path-sum/

How to Think:
1. A path can start and end anywhere — possibly going through the root.
2. For each node, the best "single-branch" path going upward is:
   node.val + max(left_gain, right_gain, 0).
3. The best "through this node" path is:
   node.val + max(left_gain, 0) + max(right_gain, 0).
4. Track the global max of all through-paths.

How to Remember:
- Pattern: "Gain = node + max(0, best child gain). Update global max with node + left + right gains."
- The 0 in max(0, ...) means we can drop a negative branch (not use it).
- Memo clue: each node is a 'summit' — the best trail going up vs the best trail through.

AI Use Cases:
- Best-segment scoring in sequence models (max subarray on parse tree).
- Optimal routing through hierarchical networks.
- Reinforcement learning: best cumulative reward path through decision tree.
- Anomaly detection: max-deviation subtree.
"""

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
            left = max(0, gain(node.left))
            right = max(0, gain(node.right))
            self.best = max(self.best, node.val + left + right)
            return node.val + max(left, right)

        gain(root)
        return self.best


if __name__ == "__main__":
    #   -10
    #   /  \
    #   9   20
    #      /  \
    #     15    7
    root = TreeNode(-10)
    root.left = TreeNode(9)
    root.right = TreeNode(20, TreeNode(15), TreeNode(7))
    print(Solution().maxPathSum(root))  # 42 (15->20->7)
