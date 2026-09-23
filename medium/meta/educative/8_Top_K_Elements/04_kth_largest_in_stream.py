"""
KTH LARGEST ELEMENT IN A STREAM — LeetCode 703
==============================================
Design a class to find the kth largest element in a stream of integers.
Operations:
    add(val)  → int   : append and return the kth largest so far.

Strategy
--------
Maintain a MIN-heap of size exactly K containing the k largest seen
so far. heap[0] is ALWAYS the kth largest.

    add(val):
        if len(heap) < k:  push
        elif val > heap[0]: heapreplace
        else: ignore (val ≤ kth largest, can't be top-k)
        return heap[0]

Every operation is O(log k) — independent of stream length.
"""

import heapq
from typing import List


class KthLargest:
    def __init__(self, k: int, nums: List[int]):
        self.k = k
        self.heap = nums[:]
        heapq.heapify(self.heap)
        # Trim down to exactly k elements
        while len(self.heap) > k:
            heapq.heappop(self.heap)              # pop smallest → keeps top-k

    def add(self, val: int) -> int:
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, val)
        elif val > self.heap[0]:
            heapq.heapreplace(self.heap, val)
        return self.heap[0]


if __name__ == "__main__":
    kth = KthLargest(3, [4, 5, 8, 2])
    print(kth.add(3))    # 4
    print(kth.add(5))    # 5
    print(kth.add(10))   # 5
    print(kth.add(9))    # 8
    print(kth.add(4))    # 8
