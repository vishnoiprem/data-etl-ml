"""
Problem 5 (Medium) — Find Peak Element
Pattern shape: C — Peak / neighbor-driven BS

A peak element is one that is strictly greater than its neighbors.
Given an array nums, find a peak element and return its index. The array
may contain multiple peaks — return any one of them. The algorithm must
run in O(log n). nums[i] is not adjacent to itself for edge positions:
nums[-1] and nums[n] are considered -infinity.

Examples
--------
>>> find_peak_element([1, 2, 3, 1])
2
>>> find_peak_element([1, 2, 1, 3, 5, 6, 4])
5

How to think (interview script)
------------------------------
"Standard binary search needs a monotonic predicate, but 'peak' isn't
monotone. However, there's still a useful invariant: in any adjacent
pair, at least one side must contain a peak.

  - If arr[mid] > arr[mid+1]: a peak exists to the left (including mid).
  - Else (arr[mid] < arr[mid+1] or equal): a peak exists to the right.

So at each step I discard the half that's guaranteed NOT to contain a
peak. With the -infinity boundary assumption, the algorithm always
terminates at a valid peak.

Edge case for n == 1: the single element is a peak by definition.

Complexity: O(log n) time, O(1) space. (Duplicates don't hurt us here
because of the strict inequality on the right edge — but if duplicates
are dense we may need to scan neighbors.)

Edge cases
----------
- n == 1 → return 0
- All increasing → return n - 1 (last element is a peak)
- All decreasing → return 0 (first element is a peak)
- Plateau [1, 1, 1, 1] → with strict neighbors this is ill-defined;
  the convention is to pick one of the boundary indices.

Follow-ups the interviewer may ask
-----------------------------------
- "What if duplicates are allowed?"
  Answer: worst case becomes O(n), but the algorithm is still correct.
  Standard solution: if arr[mid] == arr[mid+1], shrink both sides.
- "Return ALL peaks, not just one."
  Answer: drop the log-n constraint and do a linear scan, or do BS to
  find one then recurse on each side.
- "What if there are no -infinity boundaries, i.e. it's a circular array?"
  Answer: that's a different problem (find any local max on a circle).
"""
from typing import List


def find_peak_element(nums: List[int]) -> int:
    """Return any index `i` such that nums[i] > nums[i-1] and nums[i] > nums[i+1]."""
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > nums[mid + 1]:
            # Peak is in [lo, mid]
            hi = mid
        else:
            # Peak is in [mid + 1, hi]
            lo = mid + 1
    return lo


if __name__ == "__main__":
    # Spot-check that the returned index is actually a peak
    def is_peak(nums, i):
        n = len(nums)
        left = nums[i - 1] if i > 0 else float("-inf")
        right = nums[i + 1] if i + 1 < n else float("-inf")
        return nums[i] > left and nums[i] > right

    for arr in [[1, 2, 3, 1], [1, 2, 1, 3, 5, 6, 4], [1], [3, 1], [1, 3], [1, 2, 3, 4]]:
        i = find_peak_element(arr)
        assert is_peak(arr, i), f"index {i} is not a peak of {arr}"
    print("All tests passed for find_peak_element.")
