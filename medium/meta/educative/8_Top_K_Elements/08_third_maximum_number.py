"""
THIRD MAXIMUM NUMBER — LeetCode 414
==================================
Return the THIRD distinct maximum in the array. If it doesn't exist,
return the maximum.

Why this problem matters
------------------------
It is the simplest case of "running top-K with constant memory".
Instead of a heap of size k, we keep THREE variables and update them
in O(1) per element. This is the right tool when k is tiny and known
in advance.

The 3-step update (in order):
    1. If x equals any of the three → skip (we want DISTINCT maxima).
    2. If x > first   → shift (third ← second, second ← first, first ← x).
    3. Else if x > second → shift (third ← second, second ← x).
    4. Else if x > third  → third ← x.
"""

from typing import List


def third_max(nums: List[int]) -> int:
    INF = float("inf")
    first = second = third = -INF
    for x in nums:
        if x == first or x == second or x == third:
            continue
        if x > first:
            third, second, first = second, first, x
        elif x > second:
            third, second = second, x
        elif x > third:
            third = x
    return int(third) if third != -INF else int(first)


if __name__ == "__main__":
    print(third_max([3, 2, 1]))              # 1
    print(third_max([1, 2]))                # 2  (no third distinct → max)
    print(third_max([2, 2, 3, 1]))          # 1
