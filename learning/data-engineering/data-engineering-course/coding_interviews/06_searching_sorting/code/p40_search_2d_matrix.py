"""Search a 2D Matrix — sorted row-major matrix, find target.

Time:  O(log(m·n)) — treat the matrix as a flat sorted array
Space: O(1)
"""


def solve_search_2d(matrix, target):
    """Return True if target is in the row-major sorted matrix.

    >>> solve_search_2d([[1,3,5,7],[10,11,16,20],[23,30,34,60]], 3)
    True
    """
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = (left + right) // 2
        val = matrix[mid // cols][mid % cols]
        if val == target:
            return True
        if val < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


if __name__ == "__main__":
    print(solve_search_2d([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3))
