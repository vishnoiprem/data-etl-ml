"""Network Delay Time — Dijkstra from node k.

Time:  O(E log V) — heap
Space: O(V + E)
"""

import heapq


def solve_network_delay(n, times, k):
    """Return the time for all nodes to receive the signal, or -1.

    >>> solve_network_delay(2, [[1,2,1]], 1)
    1
    """
    graph = {i: [] for i in range(1, n + 1)}
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {i: float("inf") for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    out = max(dist.values())
    return out if out != float("inf") else -1


if __name__ == "__main__":
    print(solve_network_delay(2, [[1, 2, 1]], 1))
