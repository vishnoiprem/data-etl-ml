"""
KTH LARGEST ELEMENT IN AN ARRAY — LeetCode 215
=============================================
Given an integer array, return the kth LARGEST element (1-indexed).
Note the ordering: k=1 means MAXIMUM, k=n means MINIMUM.

Two clean approaches:
    • Min-heap of size k — straightforward, O(n log k).
    • Quickselect — average O(n).

We ship the heap because it's deterministic and easier to derive in
an interview. Quickselect is faster but has a nasty worst case.
"""

import heapq
from typing import List


def find_kth_largest(nums: List[int], k: int) -> int:
    heap = []
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:                     # candidate for top-k
            heapq.heapreplace(heap, x)
    return heap[0]                            # min of the top-k = kth largest


if __name__ == "__main__":
    print(find_kth_largest([3, 2, 1, 5, 6, 4], 2))    # 5
    print(find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4))  # 4
