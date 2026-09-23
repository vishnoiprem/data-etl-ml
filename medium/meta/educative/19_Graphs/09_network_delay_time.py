"""
NETWORK DELAY TIME — LeetCode 743
================================
You are given a directed weighted graph with `n` nodes (labelled 1..n)
and a list of edges `times[i] = [u, v, w]` meaning u → v takes w time
to traverse. A signal is sent FROM `k`. Return the time it takes for
ALL nodes to receive the signal. If any node is unreachable, return -1.

This is the CANONICAL Dijkstra problem.
Recipe:
    1. min-heap keyed on (distance_so_far, node).
    2. Always pop the smallest. If we've seen a smaller distance,
       skip. Otherwise, relax every outgoing edge.
    3. Time is the max distance across all nodes; return -1 if any
       node stayed at infinity.

DIJKSTRA'S ASSUMPTION: all edge weights are NON-NEGATIVE. If you see
negative weights, it's Bellman-Ford. If you see weights that are 0 or 1,
reach for 0-1 BFS first (O(V+E) instead of O((V+E) log V)).
"""

import heapq
from typing import List


def network_delay_time(times: List[List[int]], n: int, k: int) -> int:
    from collections import defaultdict
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))

    dist = [float("inf")] * (n + 1)        # 1-indexed
    dist[k] = 0
    heap = [(0, k)]                         # (dist, node)

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:                     # stale heap entry
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))

    res = max(dist[1:])                     # ignore index 0
    return res if res != float("inf") else -1


if __name__ == "__main__":
    print(network_delay_time([[2,1,1],[2,3,1],[3,4,1]], 4, 2))  # 2
    print(network_delay_time([[1,2,1]], 2, 1))                 # 1
    print(network_delay_time([[1,2,1]], 2, 2))                 # -1
