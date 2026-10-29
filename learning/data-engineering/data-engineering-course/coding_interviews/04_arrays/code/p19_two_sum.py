"""Two Sum — return indices of two numbers that add to a target.

Time:  O(n) — single pass with a hash map
Space: O(n) — the hash map
"""


def solve_two_sum(nums, target):
    """Return (i, j) with i < j such that nums[i] + nums[j] == target.

    >>> solve_two_sum([2, 7, 11, 15], 9)
    (0, 1)
    """
    seen = {}  # value -> index
    for idx, val in enumerate(nums):
        complement = target - val
        if complement in seen:
            return (seen[complement], idx)
        seen[val] = idx
    return (-1, -1)


if __name__ == "__main__":
    print(solve_two_sum([2, 7, 11, 15], 9))
