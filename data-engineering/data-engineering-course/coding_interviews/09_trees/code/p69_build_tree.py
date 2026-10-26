"""Construct Binary Tree from Preorder and Inorder Traversal.

Time:  O(n) — hash map for inorder indices
Space: O(n)
"""


def solve_build_tree(preorder, inorder):
    """Reconstruct the binary tree; return the root.

    >>> solve_build_tree([], [])
    """
    if not preorder:
        return None
    idx_map = {val: i for i, val in enumerate(inorder)}

    def build(pre_left, pre_right, in_left, in_right):
        if pre_left > pre_right:
            return None
        root_val = preorder[pre_left]
        root = _new_node(root_val)
        in_root = idx_map[root_val]
        left_size = in_root - in_left
        root.left = build(pre_left + 1, pre_left + left_size, in_left, in_root - 1)
        root.right = build(pre_left + left_size + 1, pre_right, in_root + 1, in_right)
        return root

    return build(0, len(preorder) - 1, 0, len(inorder) - 1)


def _new_node(val):
    from _tree_helpers import TreeNode  # type: ignore
    return TreeNode(val)


if __name__ == "__main__":
    root = solve_build_tree([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])
    print(root.val, root.left.val, root.right.val)  # 3 9 20
