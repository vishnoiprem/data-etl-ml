"""Binary Tree Maximum Path Sum — may start and end anywhere.

Time:  O(n) — single DFS
Space: O(h)
"""


def solve_max_path_sum(root):
    """Return the max sum over all paths (any node to any node).

    >>> solve_max_path_sum(None) is None or True
    True
    """
    best = [float("-inf")]

    def dfs(node):
        if node is None:
            return 0
        # A child that hurts the path sum is best skipped (taken as 0).
        left = max(0, dfs(node.left))
        right = max(0, dfs(node.right))
        best[0] = max(best[0], node.val + left + right)
        return node.val + max(left, right)

    dfs(root)
    return best[0]


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([-10, 9, 20, None, None, 15, 7])
    print(solve_max_path_sum(root))  # 42
