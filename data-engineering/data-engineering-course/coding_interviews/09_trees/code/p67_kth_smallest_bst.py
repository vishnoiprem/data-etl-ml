"""Kth Smallest Element in a BST.

Time:  O(h + k) — inorder walk stops at the kth element
Space: O(h) — recursion stack
"""


def solve_kth_smallest_bst(root, k):
    """Return the kth smallest value in the BST (1-indexed).

    >>> solve_kth_smallest_bst(None, 1) is None
    True
    """
    result = None
    counter = [0]  # mutable so the inner function can update

    def inorder(node):
        nonlocal result
        if node is None or result is not None:
            return
        inorder(node.left)
        counter[0] += 1
        if counter[0] == k:
            result = node.val
            return
        inorder(node.right)

    inorder(root)
    return result


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([3, 1, 4, None, 2])
    print(solve_kth_smallest_bst(root, 1))  # 1
