"""Maximum Product Subarray — largest product of a contiguous subarray.

Time:  O(n) — single pass tracking min and max
Space: O(1) — a few scalars
"""


def solve_max_product(nums):
    """Return the largest product over all contiguous subarrays.

    >>> solve_max_product([2, 3, -2, 4])
    6
    """
    if not nums:
        return 0
    best = max_so_far = min_so_far = nums[0]
    for val in nums[1:]:
        # When val is negative, max and min swap roles.
        candidates = (max_so_far * val, min_so_far * val, val)
        max_so_far = max(candidates)
        min_so_far = min(candidates)
        best = max(best, max_so_far)
    return best


if __name__ == "__main__":
    print(solve_max_product([2, 3, -2, 4]))
