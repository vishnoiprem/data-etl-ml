"""Lowest Common Ancestor of a Binary Tree.

Time:  O(n) — single DFS
Space: O(h) — recursion stack
"""


def solve_lca(root, p, q):
    """Return the lowest common ancestor of nodes ``p`` and ``q``.

    >>> solve_lca(None, None, None) is None
    True
    """
    if root is None or root is p or root is q:
        return root
    left = solve_lca(root.left, p, q)
    right = solve_lca(root.right, p, q)
    if left and right:
        return root
    return left or right


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    p, q = root.left, root.right
    print(solve_lca(root, p, q).val)  # 3
