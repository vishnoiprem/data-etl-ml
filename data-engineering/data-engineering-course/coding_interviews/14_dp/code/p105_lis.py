"""Longest Increasing Subsequence.

Time:  O(n²) DP, or O(n log n) with patience-sort
Space: O(n)
"""

import bisect


def solve_lis(nums):
    """Return the length of the longest strictly increasing subsequence.

    >>> solve_lis([10, 9, 2, 5, 3, 7, 101, 18])
    4
    """
    sub = []  # tail values of increasing sequences of each length
    for val in nums:
        # Replace the first element >= val; this keeps the tail minimal.
        idx = bisect.bisect_left(sub, val)
        if idx == len(sub):
            sub.append(val)
        else:
            sub[idx] = val
    return len(sub)


if __name__ == "__main__":
    print(solve_lis([10, 9, 2, 5, 3, 7, 101, 18]))
