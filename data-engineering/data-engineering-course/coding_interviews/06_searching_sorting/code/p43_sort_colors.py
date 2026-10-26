"""Sort Colors (Dutch National Flag) — sort 0/1/2 in-place.

Time:  O(n) — single pass with three pointers
Space: O(1)
"""


def solve_sort_colors(nums):
    """Sort an array of 0/1/2 in-place and return it.

    >>> solve_sort_colors([2, 0, 2, 1, 1, 0])
    [0, 0, 1, 1, 2, 2]
    """
    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:  # nums[mid] == 2
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1
    return nums


if __name__ == "__main__":
    a = [2, 0, 2, 1, 1, 0]
    print(solve_sort_colors(a))
