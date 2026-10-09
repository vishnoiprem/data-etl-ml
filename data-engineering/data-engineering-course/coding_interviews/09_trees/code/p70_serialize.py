"""Serialize and Deserialize Binary Tree.

Time:  O(n) for both serialize and deserialize
Space: O(n)
"""

from collections import deque
from _tree_helpers import TreeNode  # type: ignore


def solve_serialize(root):
    """Serialize to a comma-separated string; use 'N' for nulls.

    >>> solve_serialize(None)
    'N'
    """
    if root is None:
        return "N"
    parts = []

    def dfs(node):
        if node is None:
            parts.append("N")
            return
        parts.append(str(node.val))
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return ",".join(parts)


def solve_deserialize(data):
    """Reconstruct the tree from the serialized string.

    >>> solve_deserialize('1,2,N,N,3,4,N,N,5,N,N')
    """
    tokens = iter(data.split(","))

    def build():
        try:
            tok = next(tokens)
        except StopIteration:
            return None
        if tok == "N":
            return None
        node = TreeNode(int(tok))
        node.left = build()
        node.right = build()
        return node

    return build()


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    s = solve_serialize(root)
    print(s)
    out = solve_deserialize(s)
    print(solve_serialize(out))
