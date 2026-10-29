"""
Problem: Build Binary Tree from Preorder and Inorder Traversal (Medium)
LeetCode: https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/

How to Think:
1. Preorder's first element is the root.
2. Find root in inorder; everything left of it is the left subtree, right is right subtree.
3. Recurse on the slices. Use a hash map for O(1) inorder lookup to get O(n).

How to Remember:
- Pattern: "Root from preorder's head; partition inorder via root index."
- Sizes of left/right in preorder match sizes in inorder — that's how you split.
- Memo clue: inorder = 'who's left of whom', preorder = 'who's first'.

AI Use Cases:
- Reconstructing AST from linearized code (preorder + inorder line numbers).
- Compiler/interpreter parse-tree recovery from bytecode.
- Reconstructing phylogenetic trees from character matrices.
- Document hierarchy reconstruction in OCR pipelines.
"""

from typing import Optional, List


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        idx_map = {v: i for i, v in enumerate(inorder)}
        self.pre_idx = 0

        def build(in_left, in_right):
            if in_left > in_right:
                return None
            root_val = preorder[self.pre_idx]
            self.pre_idx += 1
            root = TreeNode(root_val)
            mid = idx_map[root_val]
            root.left = build(in_left, mid - 1)
            root.right = build(mid + 1, in_right)
            return root

        return build(0, len(inorder) - 1)


if __name__ == "__main__":
    preorder = [3, 9, 20, 15, 7]
    inorder = [9, 3, 15, 20, 7]
    #       3
    #      / \
    #     9   20
    #        /  \
    #       15    7
    root = Solution().buildTree(preorder, inorder)
    print(root.val)             # 3
    print(root.left.val)        # 9
    print(root.right.val)       # 20
    print(root.right.left.val)  # 15
    print(root.right.right.val) # 7
