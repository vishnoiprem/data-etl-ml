"""
Problem 1 (Medium) — Search in Rotated Sorted Array
Pattern shape: A — Index-based, sorted-half discarding

An integer array nums sorted in ascending order is rotated at some pivot.
For example, [0, 1, 2, 4, 5, 6, 7] might become [4, 5, 6, 7, 0, 1, 2].
Given the array nums (no duplicates) and an integer target, return the
index of target if it is in nums, or -1 if it is not. O(log n) required.

Examples
--------
>>> search([4, 5, 6, 7, 0, 1, 2], 0)
4
>>> search([4, 5, 6, 7, 0, 1, 2], 3)
-1
>>> search([1], 0)
-1

How to think (interview script)
------------------------------
"Plain binary search relies on monotonicity. A rotated array is NOT
monotonic overall, but AT LEAST ONE half around any middle element
is still sorted. That's the key insight.

At every step I look at nums[lo], nums[mid], nums[hi]:
  - If nums[mid] == target: return mid.
  - If nums[lo] <= nums[mid]: the LEFT half [lo..mid] is sorted.
      - If target is in [nums[lo], nums[mid]]: discard the right half.
      - Else: discard the left half.
  - Else: the RIGHT half [mid..hi] is sorted.
      - If target is in [nums[mid], nums[hi]]: discard the left half.
      - Else: discard the right half.

Each step halves the search space, so we get O(log n) as long as there
are NO duplicates. (Duplicates break this — see problem #2 for that
harder variant.)

Loop invariant: if target is in nums, it's in nums[lo..hi].
Termination: when lo > hi, return -1."

Complexity: O(log n) time, O(1) space.

Edge cases
----------
- Empty array -> -1
- Target at the pivot -> found immediately
- Array of size 1 -> trivial
- Array with no rotation -> behaves exactly like plain BS

Follow-ups the interviewer may ask
-----------------------------------
- "What if there are duplicates?" -> See problem #2.
- "Find the pivot itself." -> Find the index of the minimum element.
- "What about descending rotation?" -> Flip the comparison signs.
- "Can you find target in a doubly-rotated or shifted-by-k array?"
  Answer: yes, but you need an extra O(log n) to find the offset.
"""
from typing import List


def search(nums: List[int], target: int) -> int:
    """Return the index of target in rotated sorted array nums, or -1."""
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            # Left half is sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            # Right half is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


if __name__ == "__main__":
    assert search([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search([1], 0) == -1
    assert search([1], 1) == 0
    assert search([5, 1, 3], 3) == 2
    assert search([6, 7, 1, 2, 3, 4, 5], 4) == 5
    assert search([], 5) == -1
    print("All tests passed for search_rotated_sorted_array.")
