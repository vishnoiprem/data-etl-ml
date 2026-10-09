"""Pacific Atlantic Water Flow — cells that can reach both oceans.

Time:  O(m · n) — two BFS/DFS from the borders
Space: O(m · n) — visited sets
"""


def solve_pacific_atlantic(heights):
    """Return list of [r, c] cells from which water can reach both oceans.

    The Pacific touches the top and left edges; the Atlantic touches the
    bottom and right edges. Water can only flow from a cell to a neighbor
    of equal or lower height.
    """
    if not heights or not heights[0]:
        return []
    rows, cols = len(heights), len(heights[0])
    PACIFIC, ATLANTIC = 0, 1

    def bfs(ocean):
        # Start from the ocean border and walk "uphill" — any cell we
        # reach can flow into that ocean.
        visited = set()
        queue = []
        if ocean == PACIFIC:
            for r in range(rows):
                queue.append((r, 0))
            for c in range(cols):
                queue.append((0, c))
        else:
            for r in range(rows):
                queue.append((r, cols - 1))
            for c in range(cols):
                queue.append((rows - 1, c))
        for cell in queue:
            visited.add(cell)
        head = 0
        while head < len(queue):
            r, c = queue[head]
            head += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    if heights[nr][nc] >= heights[r][c]:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return visited

    pacific = bfs(PACIFIC)
    atlantic = bfs(ATLANTIC)
    return [list(cell) for cell in pacific & atlantic]


if __name__ == "__main__":
    h = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    out = solve_pacific_atlantic(h)
    out.sort()
    print(out)
