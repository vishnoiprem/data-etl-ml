"""Sliding Window Maximum.

Time:  O(n) — deque keeps decreasing indices
Space: O(k)
"""

from collections import deque


def solve_sliding_window_max(nums, k):
    """Return the max in each window of size k.

    >>> solve_sliding_window_max([1,3,-1,-3,5,3,6,7], 3)
    [3, 3, 5, 5, 6, 7]
    """
    if not nums or k == 0:
        return []
    dq = deque()  # indices of candidates (decreasing values)
    out = []
    for i, val in enumerate(nums):
        # Drop indices that fell out of the window.
        while dq and dq[0] <= i - k:
            dq.popleft()
        # Drop smaller values at the tail.
        while dq and nums[dq[-1]] < val:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out


if __name__ == "__main__":
    print(solve_sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3))
