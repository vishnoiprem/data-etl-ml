"""
Problem: Invert Binary Tree (Easy)
LeetCode: https://leetcode.com/problems/invert-binary-tree/

How to Think:
1. To invert: swap left and right children at every node.
2. Do this for root, then recursively for subtrees.
3. Classic example of "swap + recurse" DFS template.

How to Remember:
- Pattern: "At every node, swap(children), recurse(left), recurse(right)."
- Order of swap vs recursion doesn't matter — same result either way.
- Memo clue: imagine flipping a photo horizontally — every branch mirrors.

AI Use Cases:
- Mirror augmentation in self-supervised vision (image reflection).
- Symmetric data generation (reverse augmentation).
- Tree-based model ensembling where left/right subtrees are swapped.
- Recursive reflection in autoencoders applied to tree-encoded inputs.
"""

from typing import Optional


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if not root:
            return None
        root.left, root.right = root.right, root.left
        self.invertTree(root.left)
        self.invertTree(root.right)
        return root


if __name__ == "__main__":
    root = TreeNode(4, TreeNode(2, TreeNode(1), TreeNode(3)),
                    TreeNode(7, TreeNode(6), TreeNode(9)))
    inverted = Solution().invertTree(root)
    # Preorder of inverted: 4 7 9 6 2 3 1
    def preorder(node):
        return [node.val] + preorder(node.left) + preorder(node.right) if node else []
    print(preorder(inverted))  # [4, 7, 9, 6, 2, 3, 1]
