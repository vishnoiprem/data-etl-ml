def generate(numRows):
    """
    Generate the first numRows of Pascal's Triangle.
    Each row starts and ends with 1; interior entries are the sum of
    the two elements directly above.
    """
    triangle = []
    for row_idx in range(numRows):
        # Row `row_idx` has `row_idx + 1` elements.
        row = [1] * (row_idx + 1)
        # Fill interior (skip first and last elements, which are 1)
        for j in range(1, row_idx):
            row[j] = triangle[row_idx - 1][j - 1] + triangle[row_idx - 1][j]
        triangle.append(row)
    return triangle


if __name__ == "__main__":
    # Test cases
    for rows in generate(5):
        print(rows)
    # [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]

    print(generate(1))   # [[1]]
    print(generate(0))   # []
    print(generate(3))   # [[1], [1, 1], [1, 2, 1]]
