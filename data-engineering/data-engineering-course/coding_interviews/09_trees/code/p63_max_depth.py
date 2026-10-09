"""Maximum Depth of Binary Tree.

Time:  O(n) — visit every node once
Space: O(h) — recursion stack (h = tree height)
"""


def solve_max_depth(root):
    """Return the maximum depth (number of nodes on the longest root-to-leaf path).

    >>> solve_max_depth(None)
    0
    """
    if root is None:
        return 0
    return 1 + max(solve_max_depth(root.left), solve_max_depth(root.right))


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([3, 9, 20, None, None, 15, 7])
    print(solve_max_depth(root))  # 3
