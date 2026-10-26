"""First Missing Positive — smallest positive integer not in the array.

Time:  O(n) — cyclic sort, two passes
Space: O(1) — in-place
"""


def solve_first_missing_positive(nums):
    """Return the smallest positive integer missing from the array.

    >>> solve_first_missing_positive([1, 2, 0])
    3
    """
    n = len(nums)
    # Place each number v in slot v-1 if 1 <= v <= n.
    for i in range(n):
        while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
            target_idx = nums[i] - 1
            nums[i], nums[target_idx] = nums[target_idx], nums[i]
    # Find the first slot whose value is wrong.
    for i in range(n):
        if nums[i] != i + 1:
            return i + 1
    return n + 1


if __name__ == "__main__":
    print(solve_first_missing_positive([1, 2, 0]))
