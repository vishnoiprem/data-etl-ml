"""Graph Valid Tree — n nodes and n-1 edges, all connected, no cycles.

Time:  O(V + E) — DFS
Space: O(V + E)
"""


def solve_graph_valid_tree(n, edges):
    """Return True if the undirected graph is a valid tree.

    >>> solve_graph_valid_tree(5, [[0,1],[0,2],[0,3],[1,4]])
    True
    """
    if len(edges) != n - 1:
        return False
    graph = {i: [] for i in range(n)}
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    visited = {0}
    stack = [0]
    while stack:
        node = stack.pop()
        for nbr in graph[node]:
            if nbr not in visited:
                visited.add(nbr)
                stack.append(nbr)
    return len(visited) == n


if __name__ == "__main__":
    print(solve_graph_valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]))
