"""N-Queens — place n queens so none attack each other.

Time:  O(n!) — bounded by permutations
Space: O(n) — recursion
"""


def solve_n_queens(n):
    """Return all distinct solutions to the n-queens puzzle.

    >>> solve_n_queens(0)
    [[]]
    """
    out = []
    cols = set()
    diag1 = set()  # r - c
    diag2 = set()  # r + c
    board = [["."] * n for _ in range(n)]

    def backtrack(row):
        if row == n:
            out.append(["".join(r) for r in board])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            board[row][col] = "Q"
            backtrack(row + 1)
            board[row][col] = "."
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    backtrack(0)
    return out


if __name__ == "__main__":
    print(solve_n_queens(4))
