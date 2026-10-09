"""Find Peak Element — index of any peak (greater than both neighbors).

Time:  O(log n) — binary search on the rising side
Space: O(1)
"""


def solve_find_peak(nums):
    """Return the index of any peak element (nums[-1] = nums[n] = -inf).

    >>> solve_find_peak([1, 2, 3, 1])
    2
    """
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < nums[mid + 1]:
            # Peak must be to the right of mid.
            left = mid + 1
        else:
            # Peak is at mid or to the left.
            right = mid
    return left


if __name__ == "__main__":
    print(solve_find_peak([1, 2, 3, 1]))
