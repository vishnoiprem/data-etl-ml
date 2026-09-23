"""
SMALLEST RANGE COVERING ELEMENTS FROM K LISTS — LeetCode 632
============================================================
Given k sorted lists, find the smallest range [a, b] such that every
list has at least one element in [a, b].

The pattern: HEAP-OF-TUPLES (a min-heap across k lists).
    • Push the CURRENT head of every list into the heap as (value, list_idx,
      element_idx). Track the MAX as we go.
    • Pop the smallest, advance that list to its next element, push back
      and update the MAX.
    • The window [heap[0].value, current_max] is the current candidate
      range. Update best every iteration.

This is the SAME idea as merging k sorted iterators in a streaming
system, which is exactly where it appears in production data systems
(see §3 of the playbook).
"""

import heapq
from typing import List


def smallest_range(nums: List[List[int]]) -> List[int]:
    heap = []
    current_max = float("-inf")
    for i, lst in enumerate(nums):
        heapq.heappush(heap, (lst[0], i, 0))
        current_max = max(current_max, lst[0])

    best = [float("-inf"), float("inf")]
    while heap:
        v, i, j = heapq.heappop(heap)
        # Is [v, current_max] the smallest range seen so far?
        if current_max - v < best[1] - best[0]:
            best = [v, current_max]
        # Advance list i. If it's exhausted, range can't cover all lists anymore.
        if j + 1 == len(nums[i]):
            break
        nxt = nums[i][j + 1]
        current_max = max(current_max, nxt)
        heapq.heappush(heap, (nxt, i, j + 1))
    return best


if __name__ == "__main__":
    print(smallest_range([[4,10,15,24,26],
                          [0,9,12,20],
                          [5,18,22,30]]))                       # [20, 24]
    print(smallest_range([[1,2,3],[1,2,3],[1,2,3]]))            # [1, 1]
