"""
Problem 4 (Medium) — Find First and Last Position of Element in Sorted Array
Pattern shape: B — Boundary / lower_bound + upper_bound

Given an array of integers nums sorted in non-decreasing order, find the
starting and ending position of a given target value. If target is not
in the array, return [-1, -1]. The algorithm must run in O(log n).

Examples
--------
>>> search_range([5, 7, 7, 8, 8, 10], 8)
[3, 4]
>>> search_range([5, 7, 7, 8, 8, 10], 6)
[-1, -1]
>>> search_range([], 0)
[-1, -1]

How to think (interview script)
------------------------------
"I need two boundaries: the FIRST index where arr[i] >= target (lower_bound)
and the FIRST index where arr[i] > target (upper_bound), then subtract 1.

Both are textbook binary searches with the same shape but a flipped
predicate:
  - Lower bound: arr[mid] >= target → hi = mid; else → lo = mid + 1
  - Upper bound: arr[mid] > target  → hi = mid; else → lo = mid + 1

After both runs, if the lower bound is out of range or arr[lo] != target,
the target doesn't exist and I return [-1, -1]. Otherwise, the range is
[lower_bound, upper_bound - 1].

In Python the standard library gives us `bisect_left` and `bisect_right`,
which is exactly this. I'll write it from scratch to show I understand
the loop invariant, then mention the built-in.

I can also be clever and reuse the code from problem #6 (search_insert)
twice — that's the power of recognizing the lower_bound pattern."

Complexity: O(log n) time, O(1) space.

Edge cases
----------
- Empty array → [-1, -1]
- Target smaller than all elements → [-1, -1]
- Target larger than all elements → [-1, -1]
- All elements equal to target → [0, n-1]
- Target appears exactly once → [i, i]

Follow-ups the interviewer may ask
-----------------------------------
- "Can you reuse code from the search-insert problem?"
  Answer: yes — `search_insert` is exactly `bisect_left`.
- "What if the array isn't sorted?"
  Answer: degrade to O(n) by scanning, or sort first (changes the problem).
- "Stream the array — can you still do O(log n)?"
  Answer: no — sorting is required for BS.
"""


def lower_bound(nums: list[int], target: int) -> int:
    """Return the first index `i` such that nums[i] >= target, or len(nums)."""
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def upper_bound(nums: list[int], target: int) -> int:
    """Return the first index `i` such that nums[i] > target, or len(nums)."""
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def search_range(nums: list[int], target: int) -> list[int]:
    lo = lower_bound(nums, target)
    hi = upper_bound(nums, target) - 1
    if lo <= hi and lo < len(nums) and nums[lo] == target:
        return [lo, hi]
    return [-1, -1]


if __name__ == "__main__":
    assert search_range([5, 7, 7, 8, 8, 10], 8) == [3, 4]
    assert search_range([5, 7, 7, 8, 8, 10], 6) == [-1, -1]
    assert search_range([], 0) == [-1, -1]
    assert search_range([1, 1, 1, 1], 1) == [0, 3]
    assert search_range([1, 2, 3], 1) == [0, 0]
    assert search_range([1, 2, 3], 3) == [2, 2]
    print("All tests passed for first_and_last_position.")
