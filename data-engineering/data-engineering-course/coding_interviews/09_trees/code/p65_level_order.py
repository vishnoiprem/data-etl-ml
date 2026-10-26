"""Level Order Traversal (BFS).

Time:  O(n)
Space: O(n) — queue
"""

from collections import deque


def solve_level_order(root):
    """Return a list of lists, one per level, top-down.

    >>> solve_level_order(None)
    []
    """
    if root is None:
        return []
    out = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        out.append(level)
    return out


if __name__ == "__main__":
    from _tree_helpers import from_level_order  # type: ignore
    root = from_level_order([3, 9, 20, None, None, 15, 7])
    print(solve_level_order(root))  # [[3], [9, 20], [15, 7]]
