"""Find Minimum in Rotated Sorted Array — no duplicates.

Time:  O(log n) — binary search
Space: O(1)
"""


def solve_min_rotated(nums):
    """Return the minimum element of a once-rotated sorted array.

    >>> solve_min_rotated([3, 4, 5, 1, 2])
    1
    """
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        # The pivot is in the right half if mid's value is bigger than right's.
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    return nums[left]


if __name__ == "__main__":
    print(solve_min_rotated([3, 4, 5, 1, 2]))
