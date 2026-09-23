"""
Spiral Matrix
Medium | 30 min

Given an m x n matrix, return an array containing the matrix elements
in SPIRAL ORDER, starting from the top-left cell.

Spiral order:
1. Left to Right (along top row)
2. Top to Bottom (along right column)
3. Right to Left (along bottom row)
4. Bottom to Top (along left column)
Then repeat for the inner sub-matrix.

Examples:
    [[1, 2, 3],
     [4, 5, 6],
     [7, 8, 9]]
    -> [1, 2, 3, 6, 9, 8, 7, 4, 5]

    [[1, 2, 3, 4],
     [5, 6, 7, 8],
     [9, 10, 11, 12]]
    -> [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix

Constraints:
- 1 <= matrix.length <= 10
- 1 <= matrix[i].length <= 10
- -100 <= matrix[i][j] <= 100
"""


# =============================================================================
# WAY 1: Boundary shrinking (BEST - Memorize!)
# =============================================================================
def spiral_order_1(matrix):
    result = []
    if not matrix:
        return result
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1

    while top <= bottom and left <= right:
        # 1. Left -> Right (top row)
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1

        # 2. Top -> Bottom (right column)
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1

        # 3. Right -> Left (bottom row) - check bounds
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1

        # 4. Bottom -> Top (left column) - check bounds
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1

    return result


# =============================================================================
# WAY 2: Same but verbose
# =============================================================================
def spiral_order_2(matrix):
    if not matrix:
        return []
    result = []
    rows = len(matrix)
    cols = len(matrix[0])
    top = 0
    bottom = rows - 1
    left = 0
    right = cols - 1

    while top <= bottom and left <= right:
        # Top row
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1

        # Right column
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1

        # Bottom row (if still valid)
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1

        # Left column (if still valid)
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1

    return result


# =============================================================================
# WAY 3: Direction vectors with visited set
# =============================================================================
def spiral_order_3(matrix):
    if not matrix:
        return []
    m, n = len(matrix), len(matrix[0])
    result = []
    visited = [[False] * n for _ in range(m)]
    # Direction vectors: right, down, left, up
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    dir_idx = 0
    r, c = 0, 0

    for _ in range(m * n):
        result.append(matrix[r][c])
        visited[r][c] = True
        # Try next direction
        nr, nc = r + dirs[dir_idx][0], c + dirs[dir_idx][1]
        if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc]:
            r, c = nr, nc
        else:
            dir_idx = (dir_idx + 1) % 4
            r, c = r + dirs[dir_idx][0], c + dirs[dir_idx][1]

    return result


# =============================================================================
# WAY 4: Direction vectors with bounds check
# =============================================================================
def spiral_order_4(matrix):
    if not matrix:
        return []
    m, n = len(matrix), len(matrix[0])
    result = []
    visited = [[False] * n for _ in range(m)]
    # right, down, left, up
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    dir_idx = 0
    r, c = 0, 0

    for _ in range(m * n):
        result.append(matrix[r][c])
        visited[r][c] = True
        # Try to move in current direction
        nr = r + dirs[dir_idx][0]
        nc = c + dirs[dir_idx][1]
        if not (0 <= nr < m and 0 <= nc < n) or visited[nr][nc]:
            dir_idx = (dir_idx + 1) % 4
            nr = r + dirs[dir_idx][0]
            nc = c + dirs[dir_idx][1]
        r, c = nr, nc

    return result


# =============================================================================
# WAY 5: Recursive approach
# =============================================================================
def spiral_order_5(matrix):
    def helper(layer, top, bottom, left, right, result):
        if top > bottom or left > right:
            return
        # Top row
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        # Right column
        for i in range(top + 1, bottom + 1):
            result.append(matrix[i][right])
        # Bottom row (if different from top)
        if top != bottom:
            for j in range(right - 1, left - 1, -1):
                result.append(matrix[bottom][j])
        # Left column (if different from right)
        if left != right:
            for i in range(bottom - 1, top, -1):
                result.append(matrix[i][left])
        # Recurse on inner layer
        helper(layer + 1, top + 1, bottom - 1, left + 1, right - 1, result)

    result = []
    if matrix and matrix[0]:
        helper(0, 0, len(matrix) - 1, 0, len(matrix[0]) - 1, result)
    return result


# =============================================================================
# WAY 6: Pop first row, recurse on rotated rest
# =============================================================================
def spiral_order_6(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    # Take first row
    result.extend(matrix[0])
    # Rotate remaining (zip and transpose)
    rest = matrix[1:]
    if rest:
        # Transpose and reverse (rotate 90 deg counter-clockwise)
        rotated = list(zip(*rest))[::-1]
        # Convert tuples back to lists
        rotated = [list(row) for row in rotated]
        result.extend(spiral_order_6(rotated))
    return result


# =============================================================================
# WAY 7: Iterative layer-by-layer
# =============================================================================
def spiral_order_7(matrix):
    if not matrix:
        return []
    result = []
    m, n = len(matrix), len(matrix[0])
    layers = (min(m, n) + 1) // 2
    for layer in range(layers):
        # First row of this layer
        for j in range(layer, n - layer):
            result.append(matrix[layer][j])
        # Last column of this layer
        for i in range(layer + 1, m - layer):
            result.append(matrix[i][n - 1 - layer])
        # Last row of this layer (if different from first)
        if m - 1 - layer > layer:
            for j in range(n - 2 - layer, layer - 1, -1):
                result.append(matrix[m - 1 - layer][j])
        # First column of this layer (if different from last)
        if n - 1 - layer > layer:
            for i in range(m - 2 - layer, layer, -1):
                result.append(matrix[i][layer])
    return result


# =============================================================================
# WAY 8: BFS with deque
# =============================================================================
def spiral_order_8(matrix):
    if not matrix:
        return []
    from collections import deque
    result = []
    q = deque()
    for row in matrix:
        for val in row:
            q.append(val)
    while q:
        result.append(q.popleft())
    return result  # Note: this isn't actually spiral - placeholder for BFS
# Actually let me redo Way 8 properly

# =============================================================================
# WAY 8: BFS-style (using deque of directions)
# =============================================================================
def spiral_order_8(matrix):
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    result = []
    visited = [[False] * n for _ in range(m)]
    from collections import deque
    # Directions: right, down, left, up
    dirs = deque([(0, 1), (1, 0), (0, -1), (-1, 0)])
    r, c = 0, 0
    dr, dc = dirs[0]

    for _ in range(m * n):
        result.append(matrix[r][c])
        visited[r][c] = True
        nr, nc = r + dr, c + dc
        if not (0 <= nr < m and 0 <= nc < n) or visited[nr][nc]:
            dirs.rotate(-1)
            dr, dc = dirs[0]
            nr, nc = r + dr, c + dc
        r, c = nr, nc

    return result


# =============================================================================
# WAY 9: With while loop only
# =============================================================================
def spiral_order_9(matrix):
    if not matrix:
        return []
    result = []
    m, n = len(matrix), len(matrix[0])
    r, c = 0, 0
    # Direction: 0=right, 1=down, 2=left, 3=up
    direction = 0
    # Effective bounds shrink after each direction change
    top = 0
    bottom = m - 1
    left = 0
    right = n - 1

    while len(result) < m * n:
        if direction == 0:  # right
            for j in range(left, right + 1):
                result.append(matrix[r][j])
            r = top + 1
            top += 1
        elif direction == 1:  # down
            for i in range(top, bottom + 1):
                result.append(matrix[i][right])
            right -= 1
        elif direction == 2:  # left
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        elif direction == 3:  # up
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1
            r = top
        direction = (direction + 1) % 4
    return result


# =============================================================================
# WAY 10: Iterative with explicit boundaries (compact)
# =============================================================================
def spiral_order_10(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    m, n = len(matrix), len(matrix[0])
    top, bottom = 0, m - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        # Top row
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        # Right column
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        # Bottom row
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        # Left column
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1

    return result


# =============================================================================
# WAY 11: Using zip to rotate
# =============================================================================
def spiral_order_11(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    while matrix:
        # Take first row
        result += matrix[0]
        # Remove first row
        matrix = matrix[1:]
        if matrix:
            # Rotate the remaining matrix 90 degrees
            matrix = list(zip(*matrix))[::-1]
            matrix = [list(row) for row in matrix]
    return result


# =============================================================================
# WAY 12: With itertools chain
# =============================================================================
def spiral_order_12(matrix):
    if not matrix or not matrix[0]:
        return []
    from itertools import chain
    result = []
    m, n = len(matrix), len(matrix[0])
    top, bottom = 0, m - 1
    left, right = 0, n - 1

    while top <= bottom and left <= right:
        # Top row
        result.extend(matrix[top][left:right + 1])
        top += 1
        # Right column
        result.extend([matrix[i][right] for i in range(top, bottom + 1)])
        right -= 1
        # Bottom row
        if top <= bottom:
            result.extend(matrix[bottom][left:right + 1][::-1])
            bottom -= 1
        # Left column
        if left <= right:
            result.extend([matrix[i][left] for i in range(bottom, top - 1, -1)])
            left += 1

    return result


# =============================================================================
# WAY 13: Generator-based
# =============================================================================
def spiral_order_13(matrix):
    if not matrix or not matrix[0]:
        return []
    def gen(m):
        if not m or not m[0]:
            return
        # Yield first row
        for val in m[0]:
            yield val
        # Rotate and recurse
        rest = m[1:]
        if rest:
            rotated = [list(row) for row in zip(*rest)][::-1]
            yield from gen(rotated)
    return list(gen(matrix))


# =============================================================================
# WAY 14: Most concise
# =============================================================================
def spiral_order_14(matrix):
    return matrix and list(matrix.pop(0)) + spiral_order_14([list(row) for row in zip(*matrix)][::-1] if matrix else [])


# =============================================================================
# WAY 15: Direction-based with while loop
# =============================================================================
def spiral_order_15(matrix):
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    result = []
    r = c = 0
    visited = [[False] * n for _ in range(m)]
    # 0=right, 1=down, 2=left, 3=up
    d = 0
    drs = [0, 1, 0, -1]
    dcs = [1, 0, -1, 0]
    for _ in range(m * n):
        result.append(matrix[r][c])
        visited[r][c] = True
        # Try next direction
        nr, nc = r + drs[d], c + dcs[d]
        if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc]:
            r, c = nr, nc
        else:
            d = (d + 1) % 4
            r, c = r + drs[d], c + dcs[d]
    return result


# =============================================================================
# WAY 16: Using while loop with row/col tracking
# =============================================================================
def spiral_order_16(matrix):
    """Use boundary tracking with explicit top/bottom/left/right state."""
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    result = []
    top, bottom = 0, m - 1
    left, right = 0, n - 1
    while top <= bottom and left <= right:
        # Top row left -> right
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        if top > bottom:
            break
        # Right column top -> bottom
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        if left > right:
            break
        # Bottom row right -> left
        for j in range(right, left - 1, -1):
            result.append(matrix[bottom][j])
        bottom -= 1
        if top > bottom:
            break
        # Left column bottom -> top
        for i in range(bottom, top - 1, -1):
            result.append(matrix[i][left])
        left += 1
    return result


# =============================================================================
# WAY 17: Class-based
# =============================================================================
class SpiralOrder:
    def __init__(self, matrix):
        self.matrix = matrix

    def get_order(self):
        if not self.matrix or not self.matrix[0]:
            return []
        m, n = len(self.matrix), len(self.matrix[0])
        result = []
        top, bottom = 0, m - 1
        left, right = 0, n - 1
        while top <= bottom and left <= right:
            for j in range(left, right + 1):
                result.append(self.matrix[top][j])
            top += 1
            for i in range(top, bottom + 1):
                result.append(self.matrix[i][right])
            right -= 1
            if top <= bottom:
                for j in range(right, left - 1, -1):
                    result.append(self.matrix[bottom][j])
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1):
                    result.append(self.matrix[i][left])
                left += 1
        return result


def spiral_order_17(matrix):
    return SpiralOrder(matrix).get_order()


# =============================================================================
# WAY 18: With explicit matrix shrinking
# =============================================================================
def spiral_order_18(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    m, n = len(matrix), len(matrix[0])
    top, bottom = 0, m - 1
    left, right = 0, n - 1
    while top <= bottom and left <= right:
        if top == bottom:
            # Single row left
            for j in range(left, right + 1):
                result.append(matrix[top][j])
            break
        if left == right:
            # Single column
            for i in range(top, bottom + 1):
                result.append(matrix[i][left])
            break
        # Normal spiral - 4 sides
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        for i in range(top + 1, bottom + 1):
            result.append(matrix[i][right])
        for j in range(right - 1, left - 1, -1):
            result.append(matrix[bottom][j])
        for i in range(bottom - 1, top, -1):
            result.append(matrix[i][left])
        top += 1
        bottom -= 1
        left += 1
        right -= 1
    return result


# =============================================================================
# WAY 19: With numpy
# =============================================================================
def spiral_order_19(matrix):
    if not matrix or not matrix[0]:
        return []
    import numpy as np
    arr = np.array(matrix)
    result = []
    m, n = arr.shape
    top, bottom = 0, m - 1
    left, right = 0, n - 1
    while top <= bottom and left <= right:
        # Top row
        result.extend(arr[top, left:right + 1].tolist())
        top += 1
        # Right column
        if top <= bottom:
            result.extend(arr[top:bottom + 1, right].tolist())
            right -= 1
        # Bottom row
        if top <= bottom and left <= right:
            result.extend(arr[bottom, left:right + 1].tolist()[::-1])
            bottom -= 1
        # Left column
        if top <= bottom and left <= right:
            result.extend(arr[top:bottom + 1, left].tolist()[::-1])
            left += 1
    return result


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def spiral_order_20(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1
    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to return all matrix elements in spiral order, starting from
the top-left. The path goes right, down, left, up, then repeats for
the inner sub-matrix."

Key Insight:
"Use BOUNDARY SHRINKING!
- Maintain top, bottom, left, right boundaries.
- Each round: traverse top row (left to right), then right column
  (top to bottom), then bottom row (right to left), then left column
  (bottom to top).
- Shrink boundaries inward after each direction."

Algorithm:
"1. top=0, bottom=m-1, left=0, right=n-1
2. While top <= bottom and left <= right:
   a. Top row: for j in left..right, add matrix[top][j]. top += 1.
   b. Right column: for i in top..bottom, add matrix[i][right]. right -= 1.
   c. (if top <= bottom) Bottom row: for j in right..left, add. bottom -= 1.
   d. (if left <= right) Left column: for i in bottom..top, add. left += 1.
3. Return result"

Why check bounds in steps c and d:
"After step a and b, top might exceed bottom or left might exceed right.
We need to check before doing the bottom row (which would otherwise
re-process the top row) and left column."

Edge cases:
- 1x1 matrix: just return [matrix[0][0]]
- Single row: only step a executes
- Single column: only step a and b execute (with bounds check)
- Square matrix: full spiral
- Rectangular (m > n or n > m): some layers are single rows/columns

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Boundary  | O(mn)  | O(1)   |
| Direction | O(mn)  | O(mn)  |
| Recursive | O(mn)  | O(mn)  |
+-----------+--------+--------+

KEY TRICK:
The 4-direction cycle: Right -> Down -> Left -> Up.
Shrink boundaries after each pass.
Check bounds for bottom row and left column (since after top row and
right column, boundaries may have crossed).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Boundary shrinking (BEST)", spiral_order_1),
        ("Way 2: Verbose boundary", spiral_order_2),
        ("Way 3: Direction + visited", spiral_order_3),
        ("Way 4: Direction with bounds", spiral_order_4),
        ("Way 5: Recursive layer", spiral_order_5),
        ("Way 6: Pop + rotate", spiral_order_6),
        ("Way 7: Layer-by-layer", spiral_order_7),
        ("Way 8: BFS with deque", spiral_order_8),
        ("Way 9: While loop only", spiral_order_9),
        ("Way 10: Iterative compact", spiral_order_10),
        ("Way 11: Zip to rotate", spiral_order_11),
        ("Way 12: With chain", spiral_order_12),
        ("Way 13: Generator", spiral_order_13),
        ("Way 14: Most concise", spiral_order_14),
        ("Way 15: Direction arrays", spiral_order_15),
        ("Way 16: With bounds tracking", spiral_order_16),
        ("Way 17: Class-based", spiral_order_17),
        ("Way 18: Explicit shrinking", spiral_order_18),
        ("Way 19: Numpy", spiral_order_19),
        ("Way 20: Final cleanest", spiral_order_20),
    ]

    test_cases = [
        # 3x3
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
         [1, 2, 3, 6, 9, 8, 7, 4, 5]),
        # 3x4
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],
         [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]),
        # 4x3
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],
         [1, 2, 3, 6, 9, 12, 11, 10, 7, 4, 5, 8]),
        # Single cell
        ([[1]], [1]),
        # Single row
        ([[1, 2, 3, 4]], [1, 2, 3, 4]),
        # Single column
        ([[1], [2], [3]], [1, 2, 3]),
        # 2x2
        ([[1, 2], [3, 4]], [1, 2, 4, 3]),
        # 2x3
        ([[1, 2, 3], [4, 5, 6]], [1, 2, 3, 6, 5, 4]),
        # 1x5
        ([[1, 2, 3, 4, 5]], [1, 2, 3, 4, 5]),
        # 5x1
        ([[1], [2], [3], [4], [5]], [1, 2, 3, 4, 5]),
    ]

    print("=" * 70)
    print("SPIRAL MATRIX - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for mat, expected in test_cases:
            try:
                # Use deep copy for tests
                import copy
                mat_copy = copy.deepcopy(mat)
                result = func(mat_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: mat={mat} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on mat={mat} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
