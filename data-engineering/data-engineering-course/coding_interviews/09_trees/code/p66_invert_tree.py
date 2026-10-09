"""Invert Binary Tree — swap left/right at every node.

Time:  O(n)
Space: O(h) — recursion stack
"""


def solve_invert_tree(root):
    """Invert the tree in place and return the new root.

    >>> solve_invert_tree(None) is None
    True
    """
    if root is None:
        return None
    root.left, root.right = solve_invert_tree(root.right), solve_invert_tree(root.left)
    return root


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([4, 2, 7, 1, 3, 6, 9])
    inv = solve_invert_tree(root)
    print(solve_level_order(inv))  # [[4], [7, 2], [9, 6, 3, 1]]
