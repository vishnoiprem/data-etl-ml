"""Search in Rotated Sorted Array — find target, return index or -1.

Time:  O(log n) — binary search
Space: O(1)
"""


def solve_search_rotated(nums, target):
    """Search for ``target`` in a once-rotated sorted array.

    >>> solve_search_rotated([4, 5, 6, 7, 0, 1, 2], 0)
    4
    """
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        # Determine which half is properly sorted.
        if nums[left] <= nums[mid]:
            # Left half is sorted.
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            # Right half is sorted.
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1


if __name__ == "__main__":
    print(solve_search_rotated([4, 5, 6, 7, 0, 1, 2], 0))
