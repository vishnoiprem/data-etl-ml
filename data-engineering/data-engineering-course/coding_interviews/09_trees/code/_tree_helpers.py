"""Tree node + helpers used across Module 09 — Trees."""

from __future__ import annotations
from collections import deque
from typing import Optional, List, Iterable


class TreeNode:
    """A standard binary tree node."""

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def from_level_order(values):
    """Build a tree from a level-order list. ``None`` becomes an empty slot.

    >>> from_level_order([3,9,20,None,None,15,7]).__dict__
    {'val': 3, 'left': <...>, 'right': <...>}
    """
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root
