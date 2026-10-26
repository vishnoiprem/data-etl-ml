"""Trapping Rain Water — water trapped between bars.

Time:  O(n) — two passes with running maxes
Space: O(1) extra
"""


def solve_trapping_rain(heights):
    """Return the total units of water trapped.

    >>> solve_trapping_rain([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1])
    6
    """
    if not heights:
        return 0
    left, right = 0, len(heights) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if heights[left] < heights[right]:
            if heights[left] >= left_max:
                left_max = heights[left]
            else:
                water += left_max - heights[left]
            left += 1
        else:
            if heights[right] >= right_max:
                right_max = heights[right]
            else:
                water += right_max - heights[right]
            right -= 1
    return water


if __name__ == "__main__":
    print(solve_trapping_rain([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]))
