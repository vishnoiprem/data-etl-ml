"""Clone Graph — deep-copy an undirected graph.

Time:  O(n) — each node visited once
Space: O(n) — the clone map
"""

from _graph_helpers import Node  # type: ignore


def solve_clone_graph(node):
    """Return a deep copy of the graph rooted at ``node``.

    >>> from _graph_helpers import neighbors_to_adj
    >>> root = neighbors_to_adj([[2,4],[1,3],[2,4],[1,3]])
    >>> clone = solve_clone_graph(root)
    >>> clone.val, sorted(n.val for n in clone.neighbors)
    (1, [2, 4])
    """
    if node is None:
        return None
    clones = {node.val: Node(node.val)}

    def dfs(orig):
        for nbr in orig.neighbors:
            if nbr.val not in clones:
                clones[nbr.val] = Node(nbr.val)
                dfs(nbr)
            clones[orig.val].neighbors.append(clones[nbr.val])

    dfs(node)
    return clones[node.val]


if __name__ == "__main__":
    from _graph_helpers import neighbors_to_adj  # type: ignore
    root = neighbors_to_adj([[2, 4], [1, 3], [2, 4], [1, 3]])
    clone = solve_clone_graph(root)
    print(clone.val, sorted(n.val for n in clone.neighbors))
