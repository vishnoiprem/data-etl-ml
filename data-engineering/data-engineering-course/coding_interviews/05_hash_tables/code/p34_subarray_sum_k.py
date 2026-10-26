"""Subarray Sum Equals K — count contiguous subarrays summing to ``k``.

Time:  O(n) — single pass with a prefix-sum counter
Space: O(n) — the counter
"""


def solve_subarray_sum_k(nums, k):
    """Return the number of contiguous subarrays whose sum equals ``k``.

    >>> solve_subarray_sum_k([1, 1, 1], 2)
    2
    """
    counts = {0: 1}
    prefix = 0
    total = 0
    for val in nums:
        prefix += val
        # If prefix - k has been seen, those subarrays sum to k.
        total += counts.get(prefix - k, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return total


if __name__ == "__main__":
    print(solve_subarray_sum_k([1, 1, 1], 2))
