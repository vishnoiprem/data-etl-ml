"""Kth Largest Element in an Array.

Time:  O(n log k) — bounded min-heap of size k
Space: O(k)
"""

import heapq


def solve_kth_largest(nums, k):
    """Return the kth largest element (1-indexed).

    >>> solve_kth_largest([3,2,1,5,6,4], 2)
    5
    """
    if k < 1 or k > len(nums):
        raise ValueError("k out of range")
    heap = []
    for val in nums:
        if len(heap) < k:
            heapq.heappush(heap, val)
        elif val > heap[0]:
            heapq.heapreplace(heap, val)
    return heap[0]


if __name__ == "__main__":
    print(solve_kth_largest([3, 2, 1, 5, 6, 4], 2))
