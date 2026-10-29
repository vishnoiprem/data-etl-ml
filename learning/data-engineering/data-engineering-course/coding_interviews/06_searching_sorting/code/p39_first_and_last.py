"""Find First and Last Position of Element in Sorted Array.

Time:  O(log n) — two binary searches
Space: O(1)
"""


def _find_bound(nums, target, want_first):
    """Return leftmost index where nums[idx] == target (want_first) or rightmost (!want_first)."""
    left, right = 0, len(nums) - 1
    result = -1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            result = mid
            if want_first:
                right = mid - 1
            else:
                left = mid + 1
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return result


def solve_first_and_last(nums, target):
    """Return [first_index, last_index] of target, or [-1, -1].

    >>> solve_first_and_last([5, 7, 7, 8, 8, 10], 8)
    [3, 4]
    """
    first = _find_bound(nums, target, want_first=True)
    if first == -1:
        return [-1, -1]
    last = _find_bound(nums, target, want_first=False)
    return [first, last]


if __name__ == "__main__":
    print(solve_first_and_last([5, 7, 7, 8, 8, 10], 8))
