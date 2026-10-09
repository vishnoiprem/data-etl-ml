"""Container With Most Water — max area formed by two lines.

Time:  O(n) — two pointers from the ends
Space: O(1)
"""


def solve_container_water(heights):
    """Return the max area of water a container can hold.

    >>> solve_container_water([1, 8, 6, 2, 5, 4, 8, 3, 7])
    49
    """
    left, right = 0, len(heights) - 1
    best = 0
    while left < right:
        width = right - left
        area = width * min(heights[left], heights[right])
        best = max(best, area)
        # Move the shorter line — it can't improve by staying put.
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best


if __name__ == "__main__":
    print(solve_container_water([1, 8, 6, 2, 5, 4, 8, 3, 7]))
