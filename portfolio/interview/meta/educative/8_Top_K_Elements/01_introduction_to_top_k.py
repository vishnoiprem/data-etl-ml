"""
INTRODUCTION TO TOP K ELEMENTS — Educative
==========================================
Goal: establish the two universal templates for any "top-k" problem.

The Two Templates
-----------------
Template A — Min-heap of size K (the most common)
    "Keep the k LARGEST items seen so far in a min-heap."
    Iterate through every element. If heap size < k: push. Else:
    if element > heap[0] (the current smallest of the k): pop and push.
    At the end, the heap contains the k largest; sorted descending = heap sort.

    Why a MIN-heap? Because heap[0] is the WEAKEST of the top-k so far,
    which is the natural candidate for eviction. A max-heap would make
    eviction O(k) instead of O(1).

    Time:  O(n log k)   — n pushes/pops each O(log k)
    Space: O(k)

Template B — Counter + heap
    For problems where the "score" is a frequency / count rather than
    the element itself. Compute `Counter(arr)`, then `heapq.nlargest(k, cnt,
    key=cnt.get)` or build a heap of `(count, value)` pairs.

Alternative: quickselect
    Hoare-style partitioning selects the k-th element in O(n) AVERAGE
    time, O(n²) worst case. It's faster than a heap when k is small
    AND the data is random AND you don't need to sort. We include it
    for completeness.
"""

import heapq
import random
from collections import Counter
from typing import List


# ---- Template A: k largest elements ----
def k_largest(nums: List[int], k: int) -> List[int]:
    if k <= 0:
        return []
    heap = []
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)            # pop min + push x, O(log k)
    # Sorted descending — the heap itself is in ascending order
    return sorted(heap, reverse=True)


# ---- Template B: k most-frequent elements ----
def k_most_frequent(nums: List[int], k: int) -> List[int]:
    counts = Counter(nums)
    # nlargest with key= is the one-liner; or build a heap of (count, value).
    return heapq.nlargest(k, counts.keys(), key=counts.get)


# ---- Alternative: quickselect ----
def kth_largest_quickselect(nums: List[int], k: int) -> int:
    """Average O(n), worst O(n²). 1-indexed k."""
    def partition(lo, hi):
        pivot = nums[hi]
        i = lo
        for j in range(lo, hi):
            if nums[j] >= pivot:                  # >= for "largest" order
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
        nums[i], nums[hi] = nums[hi], nums[i]
        return i

    lo, hi = 0, len(nums) - 1
    target = k - 1                                # 0-indexed rank
    while True:
        p = partition(lo, hi)
        if p == target:  return nums[p]
        if p < target:   lo = p + 1
        else:            hi = p - 1


if __name__ == "__main__":
    a = [3, 1, 5, 12, 2, 11, 7]
    print("k=3 largest :", k_largest(a, 3))                  # [12, 11, 7]
    print("k=2 freq    :", k_most_frequent([1,1,1,2,2,3], 2))  # [1, 2]
    print("kth largest :", kth_largest_quickselect(a[:], 3))   # 7
