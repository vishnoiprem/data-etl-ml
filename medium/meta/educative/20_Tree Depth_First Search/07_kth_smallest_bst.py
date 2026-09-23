"""
Problem: Kth Smallest Element in a BST (Medium)
LeetCode: https://leetcode.com/problems/kth-smallest-element-in-a-bst/

How to Think:
1. Inorder traversal of a BST yields nodes in ascending order.
2. Walk inorder and stop when count reaches k.
3. Alternatively, augment the BST with subtree sizes for O(h) lookup.

How to Remember:
- Pattern: "BST + inorder = sorted list. Just count."
- If you remember 'sorted array from BST', you remember this.
- Memo clue: BST inorder is the same as reading a phone book in alphabetical order.

AI Use Cases:
- Order-statistic queries in learned indexes (Akamai, SageDB).
- Ranked retrieval in retrieval-augmented generation (RAG).
- Quantile computation on streaming trees.
- Top-k nearest-neighbor selection in k-d trees.
"""

from typing import Optional


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        self.k = k
        self.ans = None

        def inorder(node):
            if not node or self.ans is not None:
                return
            inorder(node.left)
            self.k -= 1
            if self.k == 0:
                self.ans = node.val
                return
            inorder(node.right)

        inorder(root)
        return self.ans


if __name__ == "__main__":
    #       5
    #      / \
    #     3   6
    #    / \
    #   2   4
    #  /
    # 1
    root = TreeNode(5, TreeNode(3, TreeNode(2, TreeNode(1)), TreeNode(4)), TreeNode(6))
    s = Solution()
    print(s.kthSmallest(root, 1))  # 1
    print(s.kthSmallest(root, 3))  # 3
