"""
Rotate Image
Medium | 30 min

Given an n x n matrix, rotate it 90 degrees clockwise IN PLACE.
The function should return the modified input matrix.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-image

Constraints:
- n == matrix.length == matrix[i].length
- 1 <= n <= 20
- -10^3 <= matrix[i][j] <= 10^3

Examples:
    [[1,2,3],
     [4,5,6],
     [7,8,9]] -> [[7,4,1],[8,5,2],[9,6,3]]
    [[2,6,8],
     [3,4,8],
     [9,8,8]] -> [[9,3,2],[8,4,6],[8,8,8]]
    (90° CW: position (i, j) -> (j, n-1-i).)

Key Insight:
Two equivalent approaches:
1. Transpose then reverse each row.
2. Layer-by-layer rotation (4-way swap).

For 90° CW rotation:
- new[i][j] = old[n-1-j][i]

Transpose + reverse each row is the cleanest in-place approach.

Time:  O(n^2).
Space: O(1) in-place.
"""


# =============================================================================
# WAY 1: Transpose + reverse each row (BEST - Memorize!)
# =============================================================================
def rotate_image_1(matrix):
    """
    Two-step in-place rotation:
    1. Transpose: swap matrix[i][j] with matrix[j][i] for i < j.
    2. Reverse each row: swap matrix[i][j] with matrix[i][n-1-j].

    Combined effect: 90° clockwise rotation.
    """
    n = len(matrix)
    # Step 1: Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Step 2: Reverse each row
    for i in range(n):
        matrix[i].reverse()

    return matrix


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def rotate_image_2(matrix):
    """Verbose version with comments."""
    n = len(matrix)

    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            temp = matrix[i][j]
            matrix[i][j] = matrix[j][i]
            matrix[j][i] = temp

    # Reverse each row
    for row in matrix:
        left = 0
        right = n - 1
        while left < right:
            row[left], row[right] = row[right], row[left]
            left += 1
            right -= 1

    return matrix


# =============================================================================
# WAY 3: Layer-by-layer 4-way swap
# =============================================================================
def rotate_image_3(matrix):
    """
    Rotate each layer (outer ring, then inner ring, etc.).
    For each layer, do 4-way swaps.
    """
    n = len(matrix)
    # Iterate over layers
    for layer in range(n // 2):
        first = layer
        last = n - 1 - layer
        for i in range(first, last):
            offset = i - first
            # Save top
            top = matrix[first][i]
            # Move left to top
            matrix[first][i] = matrix[last - offset][first]
            # Move bottom to left
            matrix[last - offset][first] = matrix[last][last - offset]
            # Move right to bottom
            matrix[last][last - offset] = matrix[i][last]
            # Move top to right
            matrix[i][last] = top
    return matrix


# =============================================================================
# WAY 4: One-pass zip + reverse
# =============================================================================
def rotate_image_4(matrix):
    """Use zip to transpose, then reverse rows."""
    n = len(matrix)
    # Transpose via zip
    # zip(*matrix) gives the transpose (as tuples)
    transposed = [list(row) for row in zip(*matrix)]
    # Reverse each row
    matrix[:] = [list(reversed(row)) for row in transposed]
    return matrix


# =============================================================================
# WAY 5: New matrix (not in-place, but easy to understand)
# =============================================================================
def rotate_image_5(matrix):
    """Create new matrix with rotation formula."""
    n = len(matrix)
    new_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            new_matrix[j][n - 1 - i] = matrix[i][j]
    matrix[:] = new_matrix
    return matrix


# =============================================================================
# WAY 6: Use enumerate
# =============================================================================
def rotate_image_6(matrix):
    """Enumerate for transpose."""
    n = len(matrix)
    # Transpose with enumerate
    for i, row in enumerate(matrix):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Reverse each row
    for row in matrix:
        row.reverse()

    return matrix


# =============================================================================
# WAY 7: Numpy-based
# =============================================================================
def rotate_image_7(matrix):
    """Use numpy.rot90 with k=-1 for clockwise."""
    try:
        import numpy as np
        n = len(matrix)
        arr = np.array(matrix)
        # np.rot90 with k=-1 rotates 90° clockwise
        rotated = np.rot90(arr, k=-1)
        matrix[:] = rotated.tolist()
        return matrix
    except ImportError:
        return rotate_image_1(matrix)


# =============================================================================
# WAY 8: Use reversed() and zip
# =============================================================================
def rotate_image_8(matrix):
    """Use reversed + zip for transpose and reverse."""
    # Transpose using zip
    matrix[:] = [list(row) for row in zip(*matrix)]
    # Reverse each row
    matrix[:] = [list(reversed(row)) for row in matrix]
    return matrix


# =============================================================================
# WAY 9: Direct formula with new list
# =============================================================================
def rotate_image_9(matrix):
    """Direct rotation formula into new list."""
    n = len(matrix)
    new = [[matrix[n - 1 - j][i] for j in range(n)] for i in range(n)]
    matrix[:] = new
    return matrix


# =============================================================================
# WAY 10: Single loop with reversed
# =============================================================================
def rotate_image_10(matrix):
    """Transpose + reverse in one pass using reversed."""
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Reverse each row using reversed()
    matrix[:] = [list(reversed(row)) for row in matrix]
    return matrix


# =============================================================================
# WAY 11: Recursive transpose + reverse
# =============================================================================
def rotate_image_11(matrix):
    """Recursive layer-by-layer rotation."""
    n = len(matrix)
    if n <= 1:
        return matrix

    # Rotate outer layer using 4-way swap
    for i in range(n - 1):
        # Save top element
        top = matrix[0][i]
        # Move left -> top
        matrix[0][i] = matrix[n - 1 - i][0]
        # Move bottom -> left
        matrix[n - 1 - i][0] = matrix[n - 1][n - 1 - i]
        # Move right -> bottom
        matrix[n - 1][n - 1 - i] = matrix[i][n - 1]
        # Move saved top -> right
        matrix[i][n - 1] = top

    # Recursively rotate inner matrix
    inner = [row[1:-1] for row in matrix[1:-1]]
    if inner:
        rotated_inner = rotate_image_11(inner)
        for i in range(len(rotated_inner)):
            matrix[i + 1][1:-1] = rotated_inner[i]

    return matrix


# =============================================================================
# WAY 12: Class-based
# =============================================================================
class MatrixRotator:
    def __init__(self, matrix):
        self.matrix = matrix
        self.n = len(matrix)

    def rotate(self):
        # Transpose
        for i in range(self.n):
            for j in range(i + 1, self.n):
                self.matrix[i][j], self.matrix[j][i] = \
                    self.matrix[j][i], self.matrix[i][j]

        # Reverse each row
        for row in self.matrix:
            row.reverse()

        return self.matrix


def rotate_image_12(matrix):
    """Class-based."""
    return MatrixRotator(matrix).rotate()


# =============================================================================
# WAY 13: Use itertools
# =============================================================================
def rotate_image_13(matrix):
    """Use itertools for transpose + reverse."""
    from itertools import zip_longest
    n = len(matrix)
    # Transpose using zip
    matrix[:] = [list(row) for row in zip(*matrix)]
    # Reverse each row
    for row in matrix:
        row.reverse()
    return matrix


# =============================================================================
# WAY 14: Use slicing and list comprehension
# =============================================================================
def rotate_image_14(matrix):
    """Use slicing for transpose + reverse."""
    n = len(matrix)
    # Transpose: each column becomes a row
    transposed = [[matrix[j][i] for j in range(n)] for i in range(n)]
    # Reverse each row
    matrix[:] = [row[::-1] for row in transposed]
    return matrix


# =============================================================================
# WAY 15: Two-pass with helper
# =============================================================================
def rotate_image_15(matrix):
    """Use helper functions for transpose and reverse."""
    n = len(matrix)

    def transpose(m):
        size = len(m)
        for i in range(size):
            for j in range(i + 1, size):
                m[i][j], m[j][i] = m[j][i], m[i][j]

    def reverse_rows(m):
        for row in m:
            row.reverse()

    transpose(matrix)
    reverse_rows(matrix)
    return matrix


# =============================================================================
# WAY 16: Layer-by-layer with offset
# =============================================================================
def rotate_image_16(matrix):
    """Layer-by-layer with cleaner offset."""
    n = len(matrix)
    for layer in range(n // 2):
        first = layer
        last = n - 1 - layer
        for i in range(first, last):
            top = matrix[first][i]
            matrix[first][i] = matrix[last - (i - first)][first]
            matrix[last - (i - first)][first] = matrix[last][last - (i - first)]
            matrix[last][last - (i - first)] = matrix[i][last]
            matrix[i][last] = top
    return matrix


# =============================================================================
# WAY 17: Using reversed built-in
# =============================================================================
def rotate_image_17(matrix):
    """Transpose + reversed each row."""
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Reverse each row
    for i in range(n):
        matrix[i] = list(reversed(matrix[i]))

    return matrix


# =============================================================================
# WAY 18: Use matrix slicing
# =============================================================================
def rotate_image_18(matrix):
    """Transpose via slicing then reverse."""
    n = len(matrix)
    # Transpose: build rows from columns
    transposed = [[matrix[j][i] for j in range(n)] for i in range(n)]
    # Use list comprehension for reverse
    matrix[:] = [list(reversed(row)) for row in transposed]
    return matrix


# =============================================================================
# WAY 19: One-liner using reversed zip
# =============================================================================
def rotate_image_19(matrix):
    """One-liner style."""
    matrix[:] = [list(reversed(row)) for row in zip(*matrix)]
    return matrix


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def rotate_image_20(matrix):
    """
    Final clean version.
    90° CW rotation = transpose + reverse each row.

    Why? Transpose swaps (i, j) and (j, i). After transposition,
    elements that were at (i, j) are now at (j, i). To rotate 90° CW,
    we want (i, j) to go to (j, n-1-i). After transpose, the element
    is at (j, i). Reversing each row moves (j, i) to (j, n-1-i). Done!

    Time:  O(n^2).
    Space: O(1) - in place.
    """
    n = len(matrix)
    # Step 1: Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Step 2: Reverse each row
    for row in matrix:
        row.reverse()

    return matrix


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to rotate an n x n matrix 90 degrees clockwise IN PLACE."

Key Insight:
"90° CW rotation = TRANSPOSE + REVERSE each row.
- Transpose: swap matrix[i][j] with matrix[j][i].
- Reverse each row: each row reversed left-to-right.
- Combined: 90° CW rotation in O(n^2) time, O(1) space."

Algorithm:
"1. Transpose: for i in [0, n), for j in [i+1, n): swap matrix[i][j], matrix[j][i].
2. Reverse each row: row.reverse() for each row.
3. Return matrix."

Why this works:
"Position (i, j) goes to (j, n-1-i) under 90° CW rotation.
- After transpose: position (i, j) moves to (j, i).
- After reverse row: position (j, i) moves to (j, n-1-i).
- Composition: (i, j) -> (j, i) -> (j, n-1-i). ✓"

Edge cases:
- 1x1 matrix: no change.
- 2x2 matrix: transpose == reverse, so just transpose.
- n is odd: center element stays in place.

Complexity:
- Time:  O(n^2) - touch each element.
- Space: O(1) - in place.

KEY TRICK:
Two-step approach: TRANSPOSE then REVERSE ROWS.
Alternative: layer-by-layer 4-way swap (more complex).

ALTERNATIVE: Layer-by-layer
For each layer (outer ring, inner ring, ...), do 4-way swaps.
More complex but doesn't require two passes.

ALTERNATIVE: New matrix
For each (i, j), set new[j][n-1-i] = matrix[i][j]. O(n^2) extra space.

RELATIONSHIP TO OTHER PROBLEMS:
- Rotate List (LC 189): Different - 1D rotation.
- Spiral Matrix (LC 54): Different - traverse spiral.
- Transpose Matrix: Half of this problem.

INTERVIEW TIPS:
1. Mention the transpose + reverse trick.
2. Explain why it works (transposition + reverse = rotation).
3. Note that it's IN PLACE.
4. Mention the layer-by-layer alternative.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Transpose + reverse (BEST)", rotate_image_1),
        ("Way 2: Verbose", rotate_image_2),
        ("Way 3: Layer-by-layer 4-way", rotate_image_3),
        ("Way 4: zip + reverse", rotate_image_4),
        ("Way 5: New matrix", rotate_image_5),
        ("Way 6: enumerate transpose", rotate_image_6),
        ("Way 7: numpy.rot90", rotate_image_7),
        ("Way 8: reversed + zip", rotate_image_8),
        ("Way 9: Direct formula new list", rotate_image_9),
        ("Way 10: Single loop reversed", rotate_image_10),
        ("Way 11: Recursive", rotate_image_11),
        ("Way 12: Class-based", rotate_image_12),
        ("Way 13: itertools", rotate_image_13),
        ("Way 14: Slicing + list comp", rotate_image_14),
        ("Way 15: Helper functions", rotate_image_15),
        ("Way 16: Layer with offset", rotate_image_16),
        ("Way 17: reversed builtin", rotate_image_17),
        ("Way 18: Matrix slicing", rotate_image_18),
        ("Way 19: One-liner", rotate_image_19),
        ("Way 20: Final cleanest", rotate_image_20),
    ]

    test_cases = [
        # Educative example (correct trace: 90° CW)
        # [[2,6,8],[3,4,8],[9,8,8]] -> [[9,3,2],[8,4,6],[8,8,8]]
        ([[2, 6, 8],
          [3, 4, 8],
          [9, 8, 8]], [[9, 3, 2],
                       [8, 4, 6],
                       [8, 8, 8]]),
        # Classic 3x3
        ([[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]], [[7, 4, 1],
                       [8, 5, 2],
                       [9, 6, 3]]),
        # 1x1 (no change)
        ([[42]], [[42]]),
        # 2x2
        ([[1, 2],
          [3, 4]], [[3, 1],
                    [4, 2]]),
        # 4x4
        ([[1, 2, 3, 4],
          [5, 6, 7, 8],
          [9, 10, 11, 12],
          [13, 14, 15, 16]], [[13, 9, 5, 1],
                               [14, 10, 6, 2],
                               [15, 11, 7, 3],
                               [16, 12, 8, 4]]),
        # All same values
        ([[5, 5], [5, 5]], [[5, 5], [5, 5]]),
    ]

    print("=" * 70)
    print("ROTATE IMAGE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-image")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for matrix, expected in test_cases:
            try:
                import copy
                matrix_copy = copy.deepcopy(matrix)
                result = func(matrix_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: matrix={matrix} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on matrix={matrix} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)