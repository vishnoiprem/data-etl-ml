"""
K CLOSEST POINTS TO ORIGIN — LeetCode 973
========================================
Given an array of (x, y) points, return the k closest to (0, 0).
Euclidean distance squared = x² + y². (No need to sqrt — monotonic.)

Two patterns in one file:
    A) Sort by distance (O(n log n) full sort).
    B) Max-heap of size k keeping the k CLOSEST — note MAX-heap because
       we want to evict the FARTHEST among the current best k. We push
       (-d, x, y) since Python's heapq is a min-heap.

Both are valid. The heap version scales better when k << n.
"""

import heapq
from typing import List


# ---- A: sort ----
def k_closest_sort(points: List[List[int]], k: int) -> List[List[int]]:
    return sorted(points, key=lambda p: p[0]**2 + p[1]**2)[:k]


# ---- B: max-heap of size k ----
def k_closest(points: List[List[int]], k: int) -> List[List[int]]:
    heap = []                                       # max-heap via negation
    for x, y in points:
        d = -(x*x + y*y)                            # NEGATE so largest dist = smallest in heap
        if len(heap) < k:
            heapq.heappush(heap, (d, x, y))
        elif d > heap[0][0]:                        # new point is closer than farthest
            heapq.heapreplace(heap, (d, x, y))
    return [(x, y) for _, x, y in heap]


if __name__ == "__main__":
    pts = [[1,3],[-2,2],[2,-2]]
    print(k_closest(pts, 2))                    # [[-2,2],[2,-2]] (any order)
    print(k_closest_sort(pts, 2))               # [[-2,2],[2,-2]]
