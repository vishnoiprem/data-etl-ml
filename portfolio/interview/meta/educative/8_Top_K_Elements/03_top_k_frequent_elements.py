"""
TOP K FREQUENT ELEMENTS — LeetCode 347
======================================
Given an integer array, return the k most-frequent elements. Return the
answer in any order.

Pattern
-------
Counter + nlargest OR Counter + heap of (count, value).

We push `(count, value)` so that ties are broken by VALUE — Python
always compares tuples element-wise on collision. The "lexicographic
tie-break" turns out to be free.
"""

import heapq
from collections import Counter
from typing import List


def top_k_frequent(nums: List[int], k: int) -> List[int]:
    counts = Counter(nums)
    heap = [(-c, v) for v, c in counts.items()]    # negate count for MAX behaviour
    heapq.heapify(heap)
    out = []
    for _ in range(k):
        _, v = heapq.heappop(heap)                  # smallest first → most frequent
        out.append(v)
    return out


# One-liner using `nlargest`:
def top_k_frequent_oneliner(nums: List[int], k: int) -> List[int]:
    counts = Counter(nums)
    return heapq.nlargest(k, counts.keys(), key=counts.get)


if __name__ == "__main__":
    print(top_k_frequent([1,1,1,2,2,3], 2))              # [1, 2]
    print(top_k_frequent([1], 1))                       # [1]
    print(top_k_frequent_oneliner([1,1,1,2,2,3], 2))    # [1, 2]
