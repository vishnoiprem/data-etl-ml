"""Contiguous subarray with the largest sum (Kadane's algorithm).

Time:  O(n) — single pass
Space: O(1) — two scalars
"""


def solve_subarray_sum(nums):
    """Return the maximum sum over all contiguous subarrays.

    >>> solve_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    6
    """
    if not nums:
        return 0
    best = current = nums[0]
    for val in nums[1:]:
        # Either extend the running subarray or start fresh.
        current = max(val, current + val)
        best = max(best, current)
    return best


if __name__ == "__main__":
    sample = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(f"input:  {sample}")
    print(f"output: {solve_subarray_sum(sample)}")
