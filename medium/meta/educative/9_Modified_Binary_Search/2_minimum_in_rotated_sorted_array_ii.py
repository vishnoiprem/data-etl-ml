"""
Problem 2 (Hard) — Find Minimum in Rotated Sorted Array II
Pattern shape: A — Index-based, with duplicates

Same as problem #1 but the array MAY contain duplicates. Return the
minimum element. Worst case degrades from O(log n) to O(n) due to
duplicates, but the algorithm remains correct.

Examples
--------
>>> find_min([1, 3, 5])
1
>>> find_min([2, 2, 2, 0, 1])
0
>>> find_min([3, 3, 1, 3])
1

How to think (interview script)
------------------------------
"The basic rotated-array trick (problem #1) hinges on the fact that at
least one half is sorted. With duplicates, that's no longer true:
[1, 0, 1, 1, 1] has both halves 'sorted-looking' but no strict order.

My fix: when nums[lo] == nums[hi] == nums[mid], I can't decide based on
endpoints alone, so I shrink ONE side by one — `hi -= 1`. This costs
O(n) in the worst case (e.g. [1, 1, 1, ..., 1, 0]) but is always correct.

In the normal case (no duplicates at the edges):
  - If nums[mid] > nums[hi]: the min is in (mid, hi] -> lo = mid + 1
  - If nums[mid] < nums[hi]: the min is in [lo, mid] -> hi = mid
  - If equal: shrink (hi -= 1)

When lo == hi, that element is the minimum. Be honest about the
worst-case complexity in the interview — interviewers respect that."

Complexity: O(log n) average, O(n) worst case. O(1) space.

Edge cases
----------
- All elements equal -> return any one of them (the loop shrinks to lo)
- Empty array -> raise / handle explicitly
- No rotation (already sorted) -> first element
- Rotation at last position -> return nums[0]
- Single element -> return nums[0]

Follow-ups the interviewer may ask
-----------------------------------
- "What's the expected time complexity?"
  Answer: O(log n) on average. Worst case O(n) when most elements are
  duplicates. We can't do better because the array is indistinguishable
  from sorted when all values are equal.
- "Find the minimum in a NOT-rotated array with duplicates?"
  Answer: it's just nums[0] — the problem guarantees rotation though.
- "Find BOTH the minimum and its index?"
  Answer: track the index alongside the value during the loop.
"""
from typing import List


def find_min(nums: List[int]) -> int:
    """Return the minimum element in a rotated sorted array with duplicates."""
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        elif nums[mid] < nums[hi]:
            hi = mid
        else:
            # nums[mid] == nums[hi]; cannot decide — shrink from the right.
            hi -= 1
    return nums[lo]


if __name__ == "__main__":
    assert find_min([1, 3, 5]) == 1
    assert find_min([2, 2, 2, 0, 1]) == 0
    assert find_min([3, 3, 1, 3]) == 1
    assert find_min([1, 1, 1, 0, 1]) == 0
    assert find_min([1, 2, 3, 4, 5]) == 1
    assert find_min([5, 1, 2, 3, 4]) == 1
    assert find_min([2]) == 2
    assert find_min([1, 1]) == 1
    print("All tests passed for minimum_in_rotated_sorted_array_ii.")
