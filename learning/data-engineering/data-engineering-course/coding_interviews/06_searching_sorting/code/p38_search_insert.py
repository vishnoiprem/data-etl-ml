"""Search Insert Position — index of target, or where it would go.

Time:  O(log n)
Space: O(1)
"""


def solve_search_insert(nums, target):
    """Return the index at which target should be inserted to keep nums sorted.

    >>> solve_search_insert([1, 3, 5, 6], 5)
    2
    """
    left, right = 0, len(nums)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left


if __name__ == "__main__":
    print(solve_search_insert([1, 3, 5, 6], 5))
