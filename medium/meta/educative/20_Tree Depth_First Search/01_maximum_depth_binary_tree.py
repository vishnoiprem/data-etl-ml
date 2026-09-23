"""
Problem: Maximum Depth of Binary Tree (Easy)
LeetCode: https://leetcode.com/problems/maximum-depth-of-binary-tree/

How to Think:
1. The depth of a tree is 1 + max(depth(left), depth(right)).
2. Base case: empty node has depth 0.
3. DFS lets us explore left/right subtrees independently and combine answers.

How to Remember:
- Pattern: "Return 1 + max of children's answers."
- Recursion goes all the way down (post-order) then bubbles up.
- Memo clue: recursion = a Russian doll — open the smallest, ask it its depth, add 1.

AI Use Cases:
- Decision tree depth estimation (random forests, XGBoost trees).
- Token parse-tree depth in NLP (syntactic complexity).
- Recursive feature depth in hierarchical models.
- AST analysis in code generation LLMs (function call depth).
"""

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
        left_depth = self.maxDepth(root.left)
        right_depth = self.maxDepth(root.right)
        return 1 + max(left_depth, right_depth)


if __name__ == "__main__":
    #       3
    #      / \
    #     9   20
    #        /  \
    #       15    7
    root = TreeNode(3)
    root.left = TreeNode(9)
    root.right = TreeNode(20, TreeNode(15), TreeNode(7))
    print(Solution().maxDepth(root))  # 3
