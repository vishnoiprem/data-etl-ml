"""Maximum Subarray (Kadane's) — largest sum of a contiguous subarray.

Time:  O(n) — single pass
Space: O(1) — two scalars
"""


def solve_max_subarray(nums):
    """Return the largest sum over all contiguous subarrays.

    >>> solve_max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    6
    """
    best = current = nums[0]
    for val in nums[1:]:
        # Either extend the current run, or start a new one.
        current = max(val, current + val)
        best = max(best, current)
    return best


if __name__ == "__main__":
    print(solve_max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))
