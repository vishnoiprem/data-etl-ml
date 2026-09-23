"""
Problem: Diameter of Binary Tree (Easy)
LeetCode: https://leetcode.com/problems/diameter-of-binary-tree/

How to Think:
1. Diameter = longest path between any two nodes (in edges).
2. The path through a node has length = left_height + right_height.
3. For each node, compute its height (post-order) AND update the global best.

How to Remember:
- Pattern: "Height is local; diameter is global — combine them."
- Recursion returns height upward; update max(left_height + right_height) globally.
- Memo clue: a node is the 'bridge' — its two longest arms form the candidate.

AI Use Cases:
- Network diameter in graph-based ML (influence spread).
- Communication latency in distributed neural net training.
- Tree-structured model interpretability (longest decision path).
- Phylogenetic tree 'spread' estimation.
"""

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


if __name__ == "__main__":
    #       1
    #      / \
    #     2   3
    #    / \
    #   4   5
    root = TreeNode(1)
    root.left = TreeNode(2, TreeNode(4), TreeNode(5))
    root.right = TreeNode(3)
    print(Solution().diameterOfBinaryTree(root))  # 3 (4->2->1->3)
