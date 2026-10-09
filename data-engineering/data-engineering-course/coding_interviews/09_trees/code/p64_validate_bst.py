"""Validate Binary Search Tree — every subtree must satisfy min < val < max.

Time:  O(n)
Space: O(h) — recursion stack
"""


def solve_validate_bst(root):
    """Return True if the binary tree is a valid BST.

    >>> solve_validate_bst(None)
    True
    """
    def helper(node, low, high):
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return helper(node.left, low, node.val) and helper(node.right, node.val, high)

    return helper(root, float("-inf"), float("inf"))


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([2, 1, 3])
    print(solve_validate_bst(root))  # True
