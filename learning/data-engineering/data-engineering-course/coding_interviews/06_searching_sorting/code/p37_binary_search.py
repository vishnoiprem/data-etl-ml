"""Binary Search — find target in a sorted array.

Time:  O(log n)
Space: O(1)
"""


def solve_binary_search(nums, target):
    """Return the index of target in nums, or -1.

    >>> solve_binary_search([-1, 0, 3, 5, 9, 12], 9)
    4
    """
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


if __name__ == "__main__":
    print(solve_binary_search([-1, 0, 3, 5, 9, 12], 9))
