"""
Problem: Lowest Common Ancestor of a Binary Tree (Medium)
LeetCode: https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/

How to Think:
1. DFS from root. If current node is p or q, return it.
2. Recurse on left and right. If both return non-None, current is the LCA.
3. If only one returns non-None, propagate that up.

How to Remember:
- Pattern: "If I'm p or q, claim myself. Else, merge my children's claims."
- Post-order DFS: collect answers from below, then decide here.
- Memo clue: LCA is the first node where p and q 'split' into different subtrees.

AI Use Cases:
- Hierarchical taxonomy resolution (entity linking).
- File system path resolution (closest common ancestor directory).
- Knowledge graph query optimization.
- Transformer attention tree (parent token of two aligned tokens).
"""

from typing import Optional


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lowestCommonAncestor(self, root: Optional[TreeNode],
                             p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
        if not root or root is p or root is q:
            return root
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left and right:
            return root
        return left or right


if __name__ == "__main__":
    #       3
    #      / \
    #     5   1
    #    / \ / \
    #   6  2 0  8
    #     / \
    #    7   4
    root = TreeNode(3)
    root.left = TreeNode(5, TreeNode(6), TreeNode(2, TreeNode(7), TreeNode(4)))
    root.right = TreeNode(1, TreeNode(0), TreeNode(8))
    s = Solution()
    print(s.lowestCommonAncestor(root, root.left, root.right).val)  # 3 (LCA of 5 and 1)
    print(s.lowestCommonAncestor(root, root.left.left, root.left.right.right).val)  # 5 (LCA of 6 and 4)
