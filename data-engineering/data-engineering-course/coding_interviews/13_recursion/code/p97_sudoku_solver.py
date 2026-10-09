"""Sudoku Solver — fill the board so each row/col/box has 1-9.

Time:  O(9^m) — m empty cells; pruning keeps it tractable
Space: O(m) — recursion
"""


def solve_sudoku(board):
    """Solve the Sudoku in-place and return the board.

    ``board`` is a 9x9 list-of-lists with '.' for empty.
    """
    rows_used = [0] * 9
    cols_used = [0] * 9
    boxes_used = [0] * 9
    empties = []

    def box_index(r, c):
        return (r // 3) * 3 + c // 3

    for r in range(9):
        for c in range(9):
            ch = board[r][c]
            if ch == ".":
                empties.append((r, c))
            else:
                bit = 1 << (ord(ch) - ord("1"))
                rows_used[r] |= bit
                cols_used[c] |= bit
                boxes_used[box_index(r, c)] |= bit

    def backtrack(i):
        if i == len(empties):
            return True
        r, c = empties[i]
        b = box_index(r, c)
        used = rows_used[r] | cols_used[c] | boxes_used[b]
        # Only try numbers not yet used by row/col/box.
        for d in range(9):
            bit = 1 << d
            if used & bit:
                continue
            board[r][c] = str(d + 1)
            rows_used[r] |= bit
            cols_used[c] |= bit
            boxes_used[b] |= bit
            if backtrack(i + 1):
                return True
            rows_used[r] ^= bit
            cols_used[c] ^= bit
            boxes_used[b] ^= bit
        board[r][c] = "."
        return False

    backtrack(0)
    return board


if __name__ == "__main__":
    board = [
        ["5", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ]
    solve_sudoku(board)
    for row in board:
        print(row)
