"""
Game of Life
Medium | 30 min

The Game of Life is a cellular automaton by John Horton Conway.
Given an m x n board where each cell is 1 (alive) or 0 (dead), update the
board to its next state based on these rules:
1. Alive cell with < 2 alive neighbors dies (underpopulation).
2. Alive cell with 2 or 3 alive neighbors survives.
3. Alive cell with > 3 alive neighbors dies (overpopulation).
4. Dead cell with exactly 3 alive neighbors becomes alive (reproduction).

All updates happen simultaneously. Update the board IN PLACE.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/game-of-life

Constraints:
- m == board.length
- n == board[i].length
- 1 <= m, n <= 25
- board[i][j] is 0 or 1
"""


# =============================================================================
# WAY 1: In-place bit encoding (BEST — Memorize!)
# =============================================================================
def gameOfLife_1(board):
    """
    KEY INSIGHT: Encode intermediate state using bit 1.
    - bit 0: original state (0 or 1)
    - bit 1: new state (0 or 1)

    State encoding:
    - 0 (00): dead → dead (stays 0)
    - 1 (01): alive → alive (stays 1)
    - 2 (10): dead → alive (revived)
    - 3 (11): alive → dead (dies)

    Two passes:
    1. For each cell, count alive neighbors (using bit 0).
       Set bit 1 based on rules.
    2. Right-shift by 1 to get the new state.

    Time:  O(m * n)
    Space: O(1)
    """
    if not board or not board[0]:
        return

    m, n = len(board), len(board[0])
    # 8 directions
    DIRS = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)]

    def count_alive_neighbors(r, c):
        count = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                count += board[nr][nc] & 1  # bit 0 = original state
        return count

    # First pass: encode new state in bit 1
    for r in range(m):
        for c in range(n):
            alive_neighbors = count_alive_neighbors(r, c)
            if board[r][c] == 1:  # currently alive
                if alive_neighbors in (2, 3):
                    board[r][c] = 3  # stays alive: 01 -> 11 (bit 1 = 1)
                # else: dies, stays as 1 (bit 1 = 0)
            else:  # currently dead
                if alive_neighbors == 3:
                    board[r][c] = 2  # becomes alive: 00 -> 10 (bit 1 = 1)
                # else: stays dead (bit 1 = 0)

    # Second pass: shift right to extract new state
    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 2: Verbose version with named function
# =============================================================================
def gameOfLife_2(board):
    """Same as Way 1 with verbose naming."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def live_neighbors(r, c):
        cnt = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                cnt += board[nr][nc] & 1
        return cnt

    for r in range(m):
        for c in range(n):
            ln = live_neighbors(r, c)
            if board[r][c]:
                if ln in (2, 3):
                    board[r][c] = 3
            else:
                if ln == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 3: With copy (extra space) - simplest to understand
# =============================================================================
def gameOfLife_3(board):
    """
    Copy approach: easiest to understand, uses O(m*n) extra space.
    """
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    # Make a copy
    copy = [row[:] for row in board]

    def live_neighbors(r, c):
        cnt = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += copy[nr][nc]
        return cnt

    for r in range(m):
        for c in range(n):
            ln = live_neighbors(r, c)
            if copy[r][c]:
                board[r][c] = 1 if ln in (2, 3) else 0
            else:
                board[r][c] = 1 if ln == 3 else 0


# =============================================================================
# WAY 4: With copy + tuple iteration
# =============================================================================
def gameOfLife_4(board):
    """Copy approach using tuple of direction offsets."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    copy = [row[:] for row in board]
    DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += copy[nr][nc]
            if copy[r][c]:
                board[r][c] = 1 if cnt in (2, 3) else 0
            else:
                board[r][c] = 1 if cnt == 3 else 0


# =============================================================================
# WAY 5: With copy + sum generator
# =============================================================================
def gameOfLife_5(board):
    """Copy + sum generator expression."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    copy = [row[:] for row in board]

    for r in range(m):
        for c in range(n):
            cnt = sum(
                copy[nr][nc]
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)
                for nr, nc in [(r + dr, c + dc)]
                if 0 <= nr < m and 0 <= nc < n
            )
            if copy[r][c]:
                board[r][c] = 1 if cnt in (2, 3) else 0
            else:
                board[r][c] = 1 if cnt == 3 else 0


# =============================================================================
# WAY 6: With copy + if-elif
# =============================================================================
def gameOfLife_6(board):
    """Copy approach with if-elif logic."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    copy = [row[:] for row in board]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < m and 0 <= nc < n:
                        cnt += copy[nr][nc]
            if copy[r][c] == 1:
                if cnt < 2 or cnt > 3:
                    board[r][c] = 0
                else:
                    board[r][c] = 1
            else:
                if cnt == 3:
                    board[r][c] = 1
                else:
                    board[r][c] = 0


# =============================================================================
# WAY 7: In-place using marker values (-1, 2)
# =============================================================================
def gameOfLife_7(board):
    """
    Alternative in-place encoding:
    - 1 -> -1 (alive → dies)
    - 0 -> 2 (dead → alive)
    Then second pass: convert -1 to 0, 2 to 1.
    """
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    # Count original live neighbors (using abs)
                    v = board[nr][nc]
                    if v == 1 or v == -1:
                        cnt += 1
            if board[r][c]:
                if cnt < 2 or cnt > 3:
                    board[r][c] = -1
            else:
                if cnt == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            if board[r][c] == -1:
                board[r][c] = 0
            elif board[r][c] == 2:
                board[r][c] = 1


# =============================================================================
# WAY 8: In-place with -1/2 markers + helper function
# =============================================================================
def gameOfLife_8(board):
    """Same as Way 7 with cleaner helper."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def cnt_live(r, c):
        c2 = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and abs(board[nr][nc]) == 1:
                c2 += 1
        return c2

    for r in range(m):
        for c in range(n):
            n_live = cnt_live(r, c)
            if board[r][c] == 1:
                if n_live < 2 or n_live > 3:
                    board[r][c] = -1
            else:
                if n_live == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] = 1 if board[r][c] > 0 else 0


# =============================================================================
# WAY 9: Copy + product iteration
# =============================================================================
def gameOfLife_9(board):
    """Copy + itertools.product for cleaner iteration."""
    from itertools import product

    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    copy = [row[:] for row in board]

    for r, c in product(range(m), range(n)):
        cnt = sum(
            copy[nr][nc]
            for dr, dc in product((-1, 0, 1), (-1, 0, 1))
            if (dr, dc) != (0, 0)
            for nr, nc in [(r + dr, c + dc)]
            if 0 <= nr < m and 0 <= nc < n
        )
        if copy[r][c]:
            board[r][c] = 1 if cnt in (2, 3) else 0
        else:
            board[r][c] = 1 if cnt == 3 else 0


# =============================================================================
# WAY 10: In-place bit encoding with sum generator
# =============================================================================
def gameOfLife_10(board):
    """In-place bit encoding, sum generator for live neighbors."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])

    for r in range(m):
        for c in range(n):
            cnt = sum(
                board[nr][nc] & 1
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)
                for nr, nc in [(r + dr, c + dc)]
                if 0 <= nr < m and 0 <= nc < n
            )
            if board[r][c]:
                if cnt in (2, 3):
                    board[r][c] = 3
            else:
                if cnt == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 11: Edge case handling upfront
# =============================================================================
def gameOfLife_11(board):
    """In-place with edge case checks."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    if m == 0 or n == 0:
        return
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def cnt(r, c):
        total = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                total += board[nr][nc] & 1
        return total

    for r in range(m):
        for c in range(n):
            n_live = cnt(r, c)
            if board[r][c] == 1:
                if n_live == 2 or n_live == 3:
                    board[r][c] = 3
            else:
                if n_live == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 12: Functional style with map
# =============================================================================
def gameOfLife_12(board):
    """Copy approach with map()."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

    def cnt(r, c, src):
        return sum(
            src[nr][nc] for dr, dc in DIRS
            for nr, nc in [(r + dr, c + dc)]
            if 0 <= nr < m and 0 <= nc < n
        )

    src = [row[:] for row in board]
    for r in range(m):
        for c in range(n):
            n_live = cnt(r, c, src)
            if src[r][c]:
                board[r][c] = 1 if n_live in (2, 3) else 0
            else:
                board[r][c] = 1 if n_live == 3 else 0


# =============================================================================
# WAY 13: With helper grid (separate marked array)
# =============================================================================
def gameOfLife_13(board):
    """
    Use a separate grid for marked states. The marked grid stores
    intermediate states (3 = alive-alive, 2 = dead-alive, 1 = alive-dead, 0 = dead-dead).
    """
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    marked = [[0] * n for _ in range(m)]
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += board[nr][nc]
            if board[r][c]:
                if cnt in (2, 3):
                    marked[r][c] = 1
                else:
                    marked[r][c] = 0
            else:
                if cnt == 3:
                    marked[r][c] = 1
                else:
                    marked[r][c] = 0

    for r in range(m):
        for c in range(n):
            board[r][c] = marked[r][c]


# =============================================================================
# WAY 14: Most concise in-place (no copy, no helper)
# =============================================================================
def gameOfLife_14(board):
    """Concise in-place."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < m and 0 <= nc < n:
                        cnt += board[nr][nc] & 1
            if board[r][c]:
                if cnt in (2, 3):
                    board[r][c] |= 2  # set bit 1
            else:
                if cnt == 3:
                    board[r][c] |= 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 15: Inline direction iteration (no helper)
# =============================================================================
def gameOfLife_15(board):
    """Inline everything."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 == dc:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < m and 0 <= nc < n:
                        cnt += board[nr][nc] & 1
            cur = board[r][c]
            if cur and cnt in (2, 3):
                board[r][c] = 3
            elif not cur and cnt == 3:
                board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 16: With named constants
# =============================================================================
DEAD = 0
ALIVE = 1
DEAD_TO_ALIVE = 2
ALIVE_TO_DEAD = 3  # using same convention as Way 1


def gameOfLife_16(board):
    """In-place with named constants for clarity."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += board[nr][nc] & 1
            if board[r][c] == ALIVE:
                if cnt == 2 or cnt == 3:
                    board[r][c] = ALIVE_TO_DEAD  # bit 1 = 1
            else:
                if cnt == 3:
                    board[r][c] = DEAD_TO_ALIVE  # bit 1 = 1

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 17: Using numpy for fast computation
# =============================================================================
def gameOfLife_17(board):
    """Use numpy for efficient computation."""
    try:
        import numpy as np
    except ImportError:
        # Fallback to Way 1
        return gameOfLife_1(board)

    if not board or not board[0]:
        return
    b = np.array(board)
    m, n = b.shape
    # Count live neighbors using shifted arrays
    cnt = np.zeros((m, n), dtype=int)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            # Shift and pad with zeros
            shifted = np.zeros((m, n), dtype=int)
            src_r_start = max(0, -dr)
            src_r_end = min(m, m - dr)
            src_c_start = max(0, -dc)
            src_c_end = min(n, n - dc)
            dst_r_start = max(0, dr)
            dst_r_end = min(m, m + dr)
            dst_c_start = max(0, dc)
            dst_c_end = min(n, n + dc)
            shifted[dst_r_start:dst_r_end, dst_c_start:dst_c_end] = b[
                src_r_start:src_r_end, src_c_start:src_c_end
            ]
            cnt += shifted

    # Apply rules
    new_b = ((cnt == 3) | ((b == 1) & (cnt == 2))).astype(int)
    for r in range(m):
        for c in range(n):
            board[r][c] = int(new_b[r][c])


# =============================================================================
# WAY 18: Class-based OOP
# =============================================================================
class GameOfLife:
    def __init__(self, board):
        self.board = board

    def live_neighbors(self, r, c):
        m, n = len(self.board), len(self.board[0])
        DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        cnt = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                cnt += self.board[nr][nc] & 1
        return cnt

    def next_state(self):
        if not self.board or not self.board[0]:
            return
        m, n = len(self.board), len(self.board[0])
        for r in range(m):
            for c in range(n):
                ln = self.live_neighbors(r, c)
                if self.board[r][c]:
                    if ln in (2, 3):
                        self.board[r][c] = 3
                else:
                    if ln == 3:
                        self.board[r][c] = 2

        for r in range(m):
            for c in range(n):
                self.board[r][c] >>= 1


def gameOfLife_18(board):
    GameOfLife(board).next_state()


# =============================================================================
# WAY 19: With explicit rules function
# =============================================================================
def apply_rule(is_alive, n_live):
    """Apply Game of Life rule."""
    if is_alive:
        return 1 if n_live in (2, 3) else 0
    else:
        return 1 if n_live == 3 else 0


def gameOfLife_19(board):
    """In-place with separate rule function."""
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += board[nr][nc] & 1
            new_val = apply_rule(board[r][c] & 1, cnt)
            # Set bit 1 = new value, keep bit 0 = original
            board[r][c] = (new_val << 1) | (board[r][c] & 1)

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def gameOfLife_20(board):
    """
    THE ONE TO MEMORIZE.

    In-place bit encoding:
    - 0 (00): dead → dead
    - 1 (01): alive → alive
    - 2 (10): dead → alive (revived)
    - 3 (11): alive → dead (dies)

    Pass 1: Set bit 1 based on rules (using bit 0 of neighbors).
    Pass 2: Right-shift to extract new state.

    Time:  O(m * n)
    Space: O(1)
    """
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(m):
        for c in range(n):
            cnt = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    cnt += board[nr][nc] & 1
            if board[r][c] == 1:
                if cnt in (2, 3):
                    board[r][c] = 3
            else:
                if cnt == 3:
                    board[r][c] = 2

    for r in range(m):
        for c in range(n):
            board[r][c] >>= 1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to update an m x n board according to Conway's Game of Life rules.
Each cell becomes alive or dead based on its 8 neighbors, and ALL updates
happen simultaneously."

Key Insight:
"The challenge is that updates are simultaneous, so I can't update in-place
without losing original state for neighbor count."

Three Approaches:
1. COPY APPROACH: Make a copy of the board. Use the copy for neighbor counting.
   Update the original. Easy but uses O(m*n) extra space.

2. IN-PLACE BIT ENCODING (BEST): Use bit 1 to encode the new state.
   - 0 (00): dead → dead
   - 1 (01): alive → alive
   - 2 (10): dead → alive
   - 3 (11): alive → dead
   First pass: count neighbors (using bit 0), set bit 1.
   Second pass: shift right by 1 to extract new state.

3. SEPARATE GRID: Use a separate marked grid to track changes.
   Similar to copy approach but with explicit marker values.

Why bit encoding works:
"Since values are 0 or 1, we have 2 bits available (we only need 1).
Use bit 0 for the original state and bit 1 for the new state.
After processing all cells, shift right by 1 to get the new state."

Edge Cases:
- 1x1 board: 0 -> 0 (no neighbors), 1 -> 0 (underpopulation).
- All alive: All cells die (overpopulation, except none have 2-3 neighbors).
- All dead: All cells stay dead (need exactly 3 alive neighbors).

Complexity:
+--------------+------------+--------+
| Approach     | Time       | Space  |
+--------------+------------+--------+
| Copy         | O(mn)      | O(mn)  |
| Bit encoding | O(mn)      | O(1)   |
| Numpy        | O(mn)      | O(mn)  |
+--------------+------------+--------+

KEY TRICK:
Use bit encoding. Read bit 0 for original state. Write bit 1 for new state.
Right-shift to extract.

RELATED PROBLEMS:
- Set Matrix Zeroes: in-place marking with sentinel rows/cols.
- Rotate Image: in-place rotation.
- Spiral Matrix: matrix traversal.
- Image smoother (LC 661): similar averaging over neighbors.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Bit encoding (BEST)", gameOfLife_1),
        ("Way 2: Verbose bit encoding", gameOfLife_2),
        ("Way 3: Copy approach", gameOfLife_3),
        ("Way 4: Copy + tuple", gameOfLife_4),
        ("Way 5: Copy + sum gen", gameOfLife_5),
        ("Way 6: Copy + if-elif", gameOfLife_6),
        ("Way 7: In-place -1/2 markers", gameOfLife_7),
        ("Way 8: -1/2 with helper", gameOfLife_8),
        ("Way 9: Copy + itertools.product", gameOfLife_9),
        ("Way 10: Bit encoding + sum gen", gameOfLife_10),
        ("Way 11: With edge cases", gameOfLife_11),
        ("Way 12: Functional map", gameOfLife_12),
        ("Way 13: Helper grid", gameOfLife_13),
        ("Way 14: Most concise in-place", gameOfLife_14),
        ("Way 15: Inline", gameOfLife_15),
        ("Way 16: Named constants", gameOfLife_16),
        ("Way 17: Numpy", gameOfLife_17),
        ("Way 18: Class OOP", gameOfLife_18),
        ("Way 19: With rule function", gameOfLife_19),
        ("Way 20: Final cleanest", gameOfLife_20),
    ]

    def expected_next(board):
        """Brute force to compute expected next state."""
        m = len(board)
        n = len(board[0]) if m > 0 else 0
        result = [row[:] for row in board]
        for r in range(m):
            for c in range(n):
                cnt = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < m and 0 <= nc < n:
                            cnt += board[nr][nc]
                if board[r][c]:
                    result[r][c] = 1 if cnt in (2, 3) else 0
                else:
                    result[r][c] = 1 if cnt == 3 else 0
        return result

    test_cases_raw = [
        # Standard example
        [[0, 1, 0], [0, 1, 0], [0, 1, 0]],
        # 4x4 blinker
        [[0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        # Block (still life)
        [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        # 1x1 dead
        [[0]],
        # 1x1 alive
        [[1]],
        # 2x2 all alive
        [[1, 1], [1, 1]],
        # 2x2 all dead
        [[0, 0], [0, 0]],
        # 3x3 single live cell
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        # 3x3 with corners alive
        [[1, 0, 1], [0, 0, 0], [1, 0, 1]],
        # Glider
        [[0, 1, 0, 0], [0, 0, 1, 0], [1, 1, 1, 0], [0, 0, 0, 0]],
        # 2x3 mixed
        [[1, 0, 1], [0, 1, 0]],
        # Empty
        [[0, 0], [0, 0]],
    ]

    print("=" * 70)
    print("GAME OF LIFE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/game-of-life")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for raw_board in test_cases_raw:
            board = [row[:] for row in raw_board]
            expected = expected_next(raw_board)
            try:
                func(board)
                if board != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: board={raw_board}, expected={expected}, got={board}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on board={raw_board} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
