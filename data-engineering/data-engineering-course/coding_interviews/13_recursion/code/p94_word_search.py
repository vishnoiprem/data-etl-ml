"""Word Search — does a word exist on the board?

Time:  O(m · n · 4^L) — every cell, every direction, L = len(word)
Space: O(L) — recursion stack
"""


def solve_word_search(board, word):
    """Return True if ``word`` exists as an adjacent-letter path on board.

    >>> solve_word_search([["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCCED")
    True
    """
    if not board or not board[0]:
        return False
    rows, cols = len(board), len(board[0])
    visited = [[False] * cols for _ in range(rows)]

    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if (r < 0 or r >= rows or c < 0 or c >= cols
                or visited[r][c] or board[r][c] != word[idx]):
            return False
        visited[r][c] = True
        found = (dfs(r + 1, c, idx + 1) or dfs(r - 1, c, idx + 1)
                 or dfs(r, c + 1, idx + 1) or dfs(r, c - 1, idx + 1))
        visited[r][c] = False
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


if __name__ == "__main__":
    board = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    print(solve_word_search(board, "ABCCED"))
