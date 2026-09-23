"""
Problem: Validate Binary Search Tree (Medium)
LeetCode: https://leetcode.com/problems/validate-binary-search-tree/

How to Think:
1. BST property: left < node < right for ALL descendants, not just direct children.
2. Pass a (min, max) range down the recursion. Each node must lie in its range.
3. Alternative: inorder traversal must be strictly increasing.

How to Remember:
- Pattern: "Carry down a valid range, narrow it at each step."
- Initial range is (-inf, +inf). At node with value v: left gets (-inf, v), right gets (v, +inf).
- Memo clue: BST is a sorted kingdom — every subtree has its own borders.

AI Use Cases:
- Spatial indexing (k-d trees, range trees) — same range-validation idea.
- Decision tree integrity checks in ML pipelines.
- Database index validation (sorted invariant).
- Order-statistic trees used in learned indexes.
"""

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


if __name__ == "__main__":
    # Valid BST
    valid = TreeNode(2, TreeNode(1), TreeNode(3))
    # Invalid: 6 in left subtree of 5 (root)
    invalid = TreeNode(5, TreeNode(1, None, TreeNode(6)), TreeNode(4))
    s = Solution()
    print(s.isValidBST(valid))    # True
    print(s.isValidBST(invalid))  # False
