"""
Spiral Matrix II
Medium | 25 min

Given a positive integer n, generate an n x n matrix filled with elements
from 1 to n^2 in SPIRAL ORDER (clockwise from top-left, moving inward).

Examples:
    n = 3  ->  [[1, 2, 3],
                [8, 9, 4],
                [7, 6, 5]]

    n = 1  ->  [[1]]

    n = 4  ->  [[ 1,  2,  3, 4],
                [12, 13, 14, 5],
                [11, 16, 15, 6],
                [10,  9,  8, 7]]

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix-ii

Constraints:
- 1 <= n <= 20
"""


# =============================================================================
# WAY 1: Boundary shrinking with explicit loops (BEST - Memorize!)
# =============================================================================
def generate_matrix_1(n):
    """
    Fill the matrix in spiral order by tracking boundaries.
    Each round fills: top row, right column, bottom row, left column.
    Shrink boundaries inward after each pass.

    Time:  O(n^2)
    Space: O(1) extra (output matrix doesn't count)
    """
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    num = 1

    while top <= bottom and left <= right:
        # 1. Top row: left -> right
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        top += 1

        # 2. Right column: top -> bottom
        for i in range(top, bottom + 1):
            matrix[i][right] = num
            num += 1
        right -= 1

        # 3. Bottom row: right -> left (if still valid)
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num
                num += 1
            bottom -= 1

        # 4. Left column: bottom -> top (if still valid)
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num
                num += 1
            left += 1

    return matrix


# =============================================================================
# WAY 2: Verbose version (great for whiteboard)
# =============================================================================
def generate_matrix_2(n):
    """Same as Way 1 but with more descriptive variable names."""
    matrix = [[0] * n for _ in range(n)]
    top_row = 0
    bottom_row = n - 1
    left_col = 0
    right_col = n - 1
    current_num = 1

    while top_row <= bottom_row and left_col <= right_col:
        # Fill top row from left to right
        for col in range(left_col, right_col + 1):
            matrix[top_row][col] = current_num
            current_num += 1
        top_row += 1

        # Fill right column from top to bottom
        for row in range(top_row, bottom_row + 1):
            matrix[row][right_col] = current_num
            current_num += 1
        right_col -= 1

        # Fill bottom row from right to left
        if top_row <= bottom_row:
            for col in range(right_col, left_col - 1, -1):
                matrix[bottom_row][col] = current_num
                current_num += 1
            bottom_row -= 1

        # Fill left column from bottom to top
        if left_col <= right_col:
            for row in range(bottom_row, top_row - 1, -1):
                matrix[row][left_col] = current_num
                current_num += 1
            left_col += 1

    return matrix


# =============================================================================
# WAY 3: Direction vectors with visited set
# =============================================================================
def generate_matrix_3(n):
    """
    Walk through matrix using direction vectors.
    When next cell would be out of bounds or already filled, turn 90° right.

    Time:  O(n^2)
    Space: O(n^2) for visited set
    """
    # right, down, left, up
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    dir_idx = 0
    matrix = [[0] * n for _ in range(n)]
    r, c = 0, 0

    for num in range(1, n * n + 1):
        matrix[r][c] = num
        # Try next cell in current direction
        nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        # If out of bounds or already filled, turn right
        if not (0 <= nr < n and 0 <= nc < n) or matrix[nr][nc] != 0:
            dir_idx = (dir_idx + 1) % 4
            nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        r, c = nr, nc

    return matrix


# =============================================================================
# WAY 4: Direction vectors with explicit visited
# =============================================================================
def generate_matrix_4(n):
    """Same as Way 3 but with explicit visited tracking (safer for non-zero vals)."""
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    dir_idx = 0
    matrix = [[0] * n for _ in range(n)]
    visited = [[False] * n for _ in range(n)]
    r, c = 0, 0

    for num in range(1, n * n + 1):
        matrix[r][c] = num
        visited[r][c] = True
        # Try next cell
        nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        if not (0 <= nr < n and 0 <= nc < n) or visited[nr][nc]:
            dir_idx = (dir_idx + 1) % 4
            nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        r, c = nr, nc

    return matrix


# =============================================================================
# WAY 5: Layer-by-layer (recursive concept, iterative)
# =============================================================================
def generate_matrix_5(n):
    """
    Process each LAYER (outer ring to inner ring) separately.
    Layer k has boundaries: top=k, bottom=n-1-k, left=k, right=n-1-k.
    """
    matrix = [[0] * n for _ in range(n)]
    num = 1
    layers = (n + 1) // 2

    for layer in range(layers):
        top = layer
        bottom = n - 1 - layer
        left = layer
        right = n - 1 - layer

        # If single cell remains (top == bottom and left == right)
        if top == bottom and left == right:
            matrix[top][left] = num
            break
        # If single row remains (top == bottom, left < right)
        if top == bottom:
            for j in range(left, right + 1):
                matrix[top][j] = num
                num += 1
            break
        # If single column remains (left == right, top < bottom)
        if left == right:
            for i in range(top, bottom + 1):
                matrix[i][left] = num
                num += 1
            break

        # Top row (left to right, EXCLUDE the last cell - covered by right col)
        for j in range(left, right):
            matrix[top][j] = num
            num += 1
        # Right column (top to bottom, INCLUDE both ends)
        for i in range(top, bottom + 1):
            matrix[i][right] = num
            num += 1
        # Bottom row (right to left, EXCLUDE the leftmost - covered by left col)
        for j in range(right - 1, left, -1):
            matrix[bottom][j] = num
            num += 1
        # Left column (bottom to top, EXCLUDE both ends - already filled)
        for i in range(bottom, top, -1):
            matrix[i][left] = num
            num += 1

    return matrix


# =============================================================================
# WAY 6: Recursive layer filling
# =============================================================================
def generate_matrix_6(n):
    """
    Recursively fill the outer ring, then recurse on inner (n-2) x (n-2).
    """
    def helper(matrix, top, bottom, left, right, num):
        if top > bottom or left > right:
            return num
        # Top row
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        # Right column
        for i in range(top + 1, bottom + 1):
            matrix[i][right] = num
            num += 1
        # Bottom row
        if top != bottom:
            for j in range(right - 1, left - 1, -1):
                matrix[bottom][j] = num
                num += 1
        # Left column
        if left != right:
            for i in range(bottom - 1, top, -1):
                matrix[i][left] = num
                num += 1
        # Recurse on inner ring
        return helper(matrix, top + 1, bottom - 1, left + 1, right - 1, num)

    matrix = [[0] * n for _ in range(n)]
    helper(matrix, 0, n - 1, 0, n - 1, 1)
    return matrix


# =============================================================================
# WAY 7: Pre-compute spiral positions, then assign
# =============================================================================
def generate_matrix_7(n):
    """
    First compute all positions in spiral order using Way 3 logic,
    then fill them with 1..n^2.
    """
    positions = []
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    dir_idx = 0
    r, c = 0, 0
    visited = [[False] * n for _ in range(n)]

    for _ in range(n * n):
        positions.append((r, c))
        visited[r][c] = True
        nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        if not (0 <= nr < n and 0 <= nc < n) or visited[nr][nc]:
            dir_idx = (dir_idx + 1) % 4
            nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        r, c = nr, nc

    matrix = [[0] * n for _ in range(n)]
    for idx, (r, c) in enumerate(positions):
        matrix[r][c] = idx + 1
    return matrix


# =============================================================================
# WAY 8: Using itertools.count for auto-incrementing
# =============================================================================
def generate_matrix_8(n):
    """Use itertools.count to auto-increment numbers."""
    from itertools import count
    matrix = [[0] * n for _ in range(n)]
    counter = count(1)
    top, bottom = 0, n - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = next(counter)
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = next(counter)
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = next(counter)
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = next(counter)
            left += 1

    return matrix


# =============================================================================
# WAY 9: With yield-based generator (clean & functional)
# =============================================================================
def generate_matrix_9(n):
    """
    Use a generator to produce numbers 1..n^2, then fill via boundaries.
    """
    def num_gen():
        num = 1
        while True:
            yield num
            num += 1

    g = num_gen()
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = next(g)
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = next(g)
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = next(g)
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = next(g)
            left += 1

    return matrix


# =============================================================================
# WAY 10: Peeling layers (mirrors spiral_order from problem 1)
# =============================================================================
def generate_matrix_10(n):
    """
    Build the matrix by appending the outer ring, then peeling inward.
    Same logic as reading a spiral matrix, but in reverse.
    """
    matrix = [[0] * n for _ in range(n)]
    num = 1
    top, bottom = 0, n - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        if top == bottom and left == right:
            # Center cell (odd n)
            matrix[top][left] = num
            break
        if top == bottom:
            # Single row
            for j in range(left, right + 1):
                matrix[top][j] = num
                num += 1
            break
        if left == right:
            # Single column
            for i in range(top, bottom + 1):
                matrix[i][left] = num
                num += 1
            break
        # Normal ring
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        for i in range(top + 1, bottom + 1):
            matrix[i][right] = num
            num += 1
        for j in range(right - 1, left, -1):
            matrix[bottom][j] = num
            num += 1
        for i in range(bottom, top, -1):
            matrix[i][left] = num
            num += 1
        top += 1
        bottom -= 1
        left += 1
        right -= 1

    return matrix


# =============================================================================
# WAY 11: Using enumerate + boundary tracking (compact)
# =============================================================================
def generate_matrix_11(n):
    """Compact one-pass with enumerate over total cells."""
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    num = 1

    while num <= n * n:
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = num
            num += 1
        right -= 1
        for j in range(right, left - 1, -1):
            if top <= bottom:
                matrix[bottom][j] = num
                num += 1
            else:
                break  # Edge case: already finished
        bottom -= 1
        for i in range(bottom, top - 1, -1):
            if left <= right:
                matrix[i][left] = num
                num += 1
            else:
                break
        left += 1

    return matrix


# =============================================================================
# WAY 12: Using offsets from current top-left (relative positioning)
# =============================================================================
def generate_matrix_12(n):
    """
    For each layer, calculate positions using offsets from (top, left).
    """
    matrix = [[0] * n for _ in range(n)]
    num = 1
    for layer in range((n + 1) // 2):
        # For each cell in the ring, calculate its offset
        side_len = n - 2 * layer
        for offset in range(side_len - 1):
            matrix[layer][layer + offset] = num
            num += 1
        for offset in range(side_len - 1):
            matrix[layer + offset][n - 1 - layer] = num
            num += 1
        for offset in range(side_len - 1):
            matrix[n - 1 - layer][n - 1 - layer - offset] = num
            num += 1
        for offset in range(side_len - 1):
            matrix[n - 1 - layer - offset][layer] = num
            num += 1
    # Center cell for odd n
    if n % 2 == 1:
        matrix[n // 2][n // 2] = n * n
    return matrix


# =============================================================================
# WAY 13: With step-based direction rotation
# =============================================================================
def generate_matrix_13(n):
    """
    Use a current direction; turn right when at boundary or filled.
    Tracks only (r, c, direction).
    """
    matrix = [[0] * n for _ in range(n)]
    # 0=right, 1=down, 2=left, 3=up
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    d = 0
    r, c = 0, 0

    for num in range(1, n * n + 1):
        matrix[r][c] = num
        # Compute next position
        dr, dc = directions[d]
        nr, nc = r + dr, c + dc
        # Turn if invalid or filled
        if nr < 0 or nr >= n or nc < 0 or nc >= n or matrix[nr][nc] != 0:
            d = (d + 1) % 4
            dr, dc = directions[d]
            nr, nc = r + dr, c + dc
        r, c = nr, nc

    return matrix


# =============================================================================
# WAY 14: Compute via formula (mathematical approach)
# =============================================================================
def generate_matrix_14(n):
    """
    Each cell's value can be computed via a closed-form formula based
    on its layer and position within the layer.

    For layer k (0-indexed from outside):
    - The ring has 4 sides, each of length (n - 2k).
    - Going clockwise: top row (right), right col (down), bottom row (left), left col (up).
    """
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            layer = min(i, j, n - 1 - i, n - 1 - j)
            side_len = n - 2 * layer
            # Cells already filled before this layer:
            # 4 sides of (side_len - 1) cells each, except the very first layer
            base = 0 if layer == 0 else sum(
                4 * (n - 2 * k - 1) for k in range(layer)
            )
            # Position within current ring
            if i == layer:  # Top row, going right
                offset = j - layer
            elif j == n - 1 - layer:  # Right column, going down
                offset = (side_len - 1) + (i - layer)
            elif i == n - 1 - layer:  # Bottom row, going left
                offset = 2 * (side_len - 1) + ((n - 1 - layer) - j)
            else:  # Left column, going up
                offset = 3 * (side_len - 1) + ((n - 1 - layer) - i)
            matrix[i][j] = base + offset + 1
    return matrix


# =============================================================================
# WAY 15: Numpy-based vectorized approach
# =============================================================================
def generate_matrix_15(n):
    """Use numpy to create zeros array, then fill via indices."""
    import numpy as np
    matrix = np.zeros((n, n), dtype=int)
    num = 1
    top, bottom = 0, n - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        # Top row
        matrix[top, left:right + 1] = range(num, num + (right - left + 1))
        num += (right - left + 1)
        top += 1
        # Right column
        matrix[top:bottom + 1, right] = range(num, num + (bottom - top + 1))
        num += (bottom - top + 1)
        right -= 1
        # Bottom row
        if top <= bottom:
            vals = list(range(num, num + (right - left + 1)))[::-1]
            matrix[bottom, left:right + 1] = vals
            num += (right - left + 1)
            bottom -= 1
        # Left column
        if left <= right:
            vals = list(range(num, num + (bottom - top + 1)))[::-1]
            matrix[top:bottom + 1, left] = vals
            num += (bottom - top + 1)
            left += 1

    return matrix.tolist()


# =============================================================================
# WAY 16: Single loop with state machine
# =============================================================================
def generate_matrix_16(n):
    """
    State machine: states are the 4 sides.
    Track current side (0=top, 1=right, 2=bottom, 3=left) and remaining cells.
    """
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    side = 0  # 0=top, 1=right, 2=bottom, 3=left
    num = 1

    while num <= n * n:
        if side == 0:  # Top row: left -> right
            for j in range(left, right + 1):
                matrix[top][j] = num
                num += 1
            top += 1
        elif side == 1:  # Right col: top -> bottom
            for i in range(top, bottom + 1):
                matrix[i][right] = num
                num += 1
            right -= 1
        elif side == 2:  # Bottom row: right -> left
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num
                num += 1
            bottom -= 1
        else:  # Left col: bottom -> top
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num
                num += 1
            left += 1
        side = (side + 1) % 4

    return matrix


# =============================================================================
# WAY 17: Using deque for direction rotation
# =============================================================================
def generate_matrix_17(n):
    """
    Use collections.deque to rotate direction vectors.
    """
    from collections import deque
    matrix = [[0] * n for _ in range(n)]
    dirs = deque([(0, 1), (1, 0), (0, -1), (-1, 0)])
    r, c = 0, 0
    visited = [[False] * n for _ in range(n)]

    for num in range(1, n * n + 1):
        matrix[r][c] = num
        visited[r][c] = True
        dr, dc = dirs[0]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < n and 0 <= nc < n) or visited[nr][nc]:
            dirs.rotate(-1)
            dr, dc = dirs[0]
            nr, nc = r + dr, c + dc
        r, c = nr, nc

    return matrix


# =============================================================================
# WAY 18: Class-based OOP
# =============================================================================
class SpiralMatrixBuilder:
    def __init__(self, n):
        self.n = n
        self.matrix = [[0] * n for _ in range(n)]
        self.top = 0
        self.bottom = n - 1
        self.left = 0
        self.right = n - 1
        self.num = 1

    def fill_top_row(self):
        for j in range(self.left, self.right + 1):
            self.matrix[self.top][j] = self.num
            self.num += 1
        self.top += 1

    def fill_right_col(self):
        for i in range(self.top, self.bottom + 1):
            self.matrix[i][self.right] = self.num
            self.num += 1
        self.right -= 1

    def fill_bottom_row(self):
        if self.top <= self.bottom:
            for j in range(self.right, self.left - 1, -1):
                self.matrix[self.bottom][j] = self.num
                self.num += 1
            self.bottom -= 1

    def fill_left_col(self):
        if self.left <= self.right:
            for i in range(self.bottom, self.top - 1, -1):
                self.matrix[i][self.left] = self.num
                self.num += 1
            self.left += 1

    def build(self):
        while self.top <= self.bottom and self.left <= self.right:
            self.fill_top_row()
            self.fill_right_col()
            self.fill_bottom_row()
            self.fill_left_col()
        return self.matrix


def generate_matrix_18(n):
    """Class-based version - clean separation of concerns."""
    return SpiralMatrixBuilder(n).build()


# =============================================================================
# WAY 19: With explicit loop counter (no while-true)
# =============================================================================
def generate_matrix_19(n):
    """
    Use a counter variable for clarity. Avoids ambiguity with direction tracking.
    """
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    num = 1

    while num <= n * n:
        # Top row
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        top += 1
        if num > n * n:
            break
        # Right column
        for i in range(top, bottom + 1):
            matrix[i][right] = num
            num += 1
        right -= 1
        if num > n * n:
            break
        # Bottom row
        for j in range(right, left - 1, -1):
            matrix[bottom][j] = num
            num += 1
        bottom -= 1
        if num > n * n:
            break
        # Left column
        for i in range(bottom, top - 1, -1):
            matrix[i][left] = num
            num += 1
        left += 1

    return matrix


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def generate_matrix_20(n):
    """
    Final cleanest version. Combines best practices:
    - Clear variable names
    - Bounds checks for bottom and left
    - Single loop variable for the number
    """
    matrix = [[0] * n for _ in range(n)]
    top, bottom, left, right = 0, n - 1, 0, n - 1
    num = 1

    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            matrix[top][j] = num
            num += 1
        top += 1
        for i in range(top, bottom + 1):
            matrix[i][right] = num
            num += 1
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                matrix[bottom][j] = num
                num += 1
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                matrix[i][left] = num
                num += 1
            left += 1

    return matrix


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to fill an n x n matrix with numbers 1 to n^2 in spiral order,
starting from the top-left and going clockwise inward."

Key Insight:
"This is the REVERSE of the spiral order problem (where we READ in spiral
order, here we WRITE in spiral order). The same BOUNDARY SHRINKING trick works!

Algorithm:
"1. Initialize boundaries: top=0, bottom=n-1, left=0, right=n-1.
2. Initialize num = 1.
3. While top <= bottom and left <= right:
   a. Fill top row from left to right. Increment num. top += 1.
   b. Fill right column from top to bottom. Increment num. right -= 1.
   c. (if top <= bottom) Fill bottom row from right to left. bottom -= 1.
   d. (if left <= right) Fill left column from bottom to top. left += 1.
4. Return matrix."

Why check bounds in steps c and d:
"After step a, top has been incremented. If top > bottom, we've already
finished (e.g., single row case). Without the check, we'd over-write cells."

Edge cases:
- n=1: just return [[1]]
- n=2: full spiral (no center cell)
- n=3: outer ring + center cell (9)
- n=4: outer ring + inner ring
- Odd n: center cell (n*n) needs special handling in some approaches
- Even n: no center cell

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Boundary  | O(n^2) | O(1)   |
| Direction | O(n^2) | O(n^2) |
| Layer     | O(n^2) | O(1)   |
| Formula   | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
This is basically the INVERSE of "spiral order read":
- Read: append to result, shrink bounds
- Write: assign num to cell, increment num, shrink bounds

RELATIONSHIP TO OTHER PROBLEMS:
- Spiral Matrix I (read): same boundaries, just append instead of assign.
- Transpose: different operation (swap rows/cols), not directly related.
- Rotate 90°: related but different geometry.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Boundary shrinking (BEST)", generate_matrix_1),
        ("Way 2: Verbose boundary", generate_matrix_2),
        ("Way 3: Direction + check", generate_matrix_3),
        ("Way 4: Direction + visited", generate_matrix_4),
        ("Way 5: Layer-by-layer", generate_matrix_5),
        ("Way 6: Recursive layers", generate_matrix_6),
        ("Way 7: Pre-compute positions", generate_matrix_7),
        ("Way 8: itertools.count", generate_matrix_8),
        ("Way 9: Generator", generate_matrix_9),
        ("Way 10: Peeling layers", generate_matrix_10),
        ("Way 11: Compact one-pass", generate_matrix_11),
        ("Way 12: Offset-based", generate_matrix_12),
        ("Way 13: Step rotation", generate_matrix_13),
        ("Way 14: Mathematical formula", generate_matrix_14),
        ("Way 15: Numpy vectorized", generate_matrix_15),
        ("Way 16: State machine", generate_matrix_16),
        ("Way 17: Deque rotation", generate_matrix_17),
        ("Way 18: Class-based", generate_matrix_18),
        ("Way 19: With counter", generate_matrix_19),
        ("Way 20: Final cleanest", generate_matrix_20),
    ]

    test_cases = [
        # n=1
        (1, [[1]]),
        # n=2
        (2, [[1, 2], [4, 3]]),
        # n=3
        (3, [[1, 2, 3], [8, 9, 4], [7, 6, 5]]),
        # n=4
        (4, [[1, 2, 3, 4], [12, 13, 14, 5], [11, 16, 15, 6], [10, 9, 8, 7]]),
        # n=5
        (5, [
            [1, 2, 3, 4, 5],
            [16, 17, 18, 19, 6],
            [15, 24, 25, 20, 7],
            [14, 23, 22, 21, 8],
            [13, 12, 11, 10, 9]
        ]),
    ]

    print("=" * 70)
    print("SPIRAL MATRIX II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for n, expected in test_cases:
            try:
                result = func(n)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: n={n} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on n={n} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)