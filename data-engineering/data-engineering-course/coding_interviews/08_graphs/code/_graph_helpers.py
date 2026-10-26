"""Graph node used across the graph problems in this module.

Self-contained: imports nothing.
"""

from __future__ import annotations
from collections import deque
from typing import Optional, List


class Node:
    """Undirected graph node with an integer value and a list of neighbors."""

    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors: List["Node"] = neighbors if neighbors is not None else []


def neighbors_to_adj(neighbors_list):
    """Convert a list-of-lists to (Node, list-of-Node) and return root + all nodes.

    This is a fixture helper used by tests and the __main__ blocks.
    """
    if not neighbors_list:
        return None
    nodes = [Node(i + 1) for i in range(len(neighbors_list))]
    for i, neigh in enumerate(neighbors_list):
        nodes[i].neighbors = [nodes[j - 1] for j in neigh]
    return nodes[0]


def grid_to_cells(grid):
    """Convert a 2D grid of 0/1 into (rows, cols) for graph problems.

    Returns a list-of-lists of bools where True means "land" / "1".
    """
    return [[c == "1" for c in row] for row in grid]
